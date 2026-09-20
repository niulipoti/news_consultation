<template>
  <div class="ai-chat-container">
    <van-nav-bar :title="$t('aiChat.title')" fixed />

    <div class="chat-content">
      <div class="messages-container" ref="messagesContainer">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-content">
            <div v-if="message.role === 'assistant' && message.content === ''" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div v-else v-html="formatMessage(message.content)"></div>
          </div>
        </div>
      </div>

      <div class="input-container">
        <van-field
          v-model="userInput"
          rows="1"
          autosize
          type="textarea"
          :placeholder="$t('aiChat.placeholder')"
          class="chat-input"
          @keypress.enter.prevent="sendMessage"
        />
        <van-button
          type="primary"
          class="send-button"
          :disabled="!isLoading && !userInput.trim()"
          @click="onSendClick"
        >
          {{ isLoading ? cancelText : sendText }}
        </van-button>
      </div>
    </div>

    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import TabBar from '../components/TabBar.vue';
import { showToast } from 'vant';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { aiChatConfig } from '../config/api';

const { t } = useI18n();
const sendText = t('aiChat.send');
const cancelText = t('common.cancel');

// 聊天消息
const messages = ref([
  { role: 'assistant', content: '你好！我是AI助手，有什么可以帮助你的吗？' }
]);
const userInput = ref('');
const messagesContainer = ref(null);
const isLoading = ref(false);

// 会话是否可用（后端有没有配置好 API Key）
const aiReady = ref(true);

// 用于中止正在进行的流式请求
let controller = null;

// 格式化消息内容（支持Markdown）
const formatMessage = (content) => {
  if (!content) return '';
  // 使用marked解析Markdown，并用DOMPurify清理HTML，防止 XSS
  return DOMPurify.sanitize(marked.parse(content));
};

// 组件挂载时：询问后端 AI 是否可用 + 滚动到底部
onMounted(async () => {
  try {
    const response = await fetch(aiChatConfig.configEndpoint);
    if (response.ok) {
      const body = await response.json();
      // 后端未配置密钥时提前提示，省得用户白打一段字
      aiReady.value = body?.data?.enabled !== false;
    }
  } catch (error) {
    // 后端没启动等情况：不阻塞界面，发消息时再报错
    console.warn('无法获取 AI 配置:', error);
  }
  scrollToBottom();
});

// 组件卸载时中断未完成的请求，避免内存泄漏
onBeforeUnmount(() => {
  controller?.abort();
});

// 发送 / 取消
const onSendClick = () => {
  if (isLoading.value) {
    controller?.abort();
    return;
  }
  sendMessage();
};

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  if (!aiReady.value) {
    showToast('AI 服务未配置，请在服务端 .env 中设置 DEEPSEEK_API_KEY');
    return;
  }

  // 添加用户消息
  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';

  // 添加AI消息占位
  messages.value.push({ role: 'assistant', content: '' });

  await nextTick();
  scrollToBottom();

  isLoading.value = true;
  try {
    await fetchAIResponse();
  } catch (error) {
    const isAbort = error?.name === 'AbortError';
    const last = messages.value[messages.value.length - 1];
    // 用户主动取消时保留已生成的内容
    if (isAbort) {
      if (!last.content) last.content = '（已停止生成）';
    } else {
      console.error('Error fetching AI response:', error);
      last.content = `发生错误: ${error.message || '请检查网络连接'}`;
    }
  } finally {
    isLoading.value = false;
    controller = null;
    await nextTick();
    scrollToBottom();
  }
};

// 获取AI响应（调用自己后端的 SSE 接口，密钥保存在服务端）
const fetchAIResponse = async () => {
  // 排除最后一条空的 assistant 占位消息，其余作为多轮对话上下文
  const history = messages.value
    .slice(0, -1)
    .filter((msg) => msg.content && msg.content.trim())
    .map((msg) => ({ role: msg.role, content: msg.content }));

  controller = new AbortController();

  const response = await fetch(aiChatConfig.streamEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({
      // 最后一条 user 消息作为本次提问，之前的作为历史
      message: history.length ? history[history.length - 1].content : '',
      history,
    }),
    signal: controller.signal,
  });

  if (!response.ok) {
    let detail = `HTTP error! status: ${response.status}`;
    try {
      const error = await response.json();
      detail = error.message || error.detail || detail;
    } catch (e) {
      // 响应体不是 JSON，沿用默认提示
    }
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error('当前浏览器不支持流式响应');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let aiResponse = '';

  // 处理SSE流
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    // SSE 以「空行」分隔事件，这里按行切分后保留最后一段不完整数据
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data:')) continue;

      const data = line.slice(5).trim();
      if (!data || data === '[DONE]') continue;

      try {
        const json = JSON.parse(data);

        // 后端在流中间报错时会推送 { error: "..." }
        if (json.error) {
          throw new Error(json.error);
        }

        const content = json.content || '';
        if (content) {
          aiResponse += content;
          messages.value[messages.value.length - 1].content = aiResponse;
          await nextTick();
          scrollToBottom();
        }
      } catch (e) {
        if (e instanceof SyntaxError) {
          console.error('Error parsing SSE data:', e);
          continue;
        }
        throw e;
      }
    }
  }

  // 如果后端一个字都没返回
  if (!aiResponse) {
    messages.value[messages.value.length - 1].content =
      '抱歉，我无法生成回复。请稍后再试。';
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 监听消息变化，自动滚动
watch(messages, () => {
  nextTick(scrollToBottom);
}, { deep: true });
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-top: 46px;
  padding-bottom: 50px;
  box-sizing: border-box;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.message {
  margin-bottom: 10px;
  max-width: 80%;
}

.user-message {
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 10px;
  border-radius: 10px;
  word-break: break-word;
}

.user-message .message-content {
  background-color: #007aff;
  color: white;
}

.ai-message .message-content {
  background-color: #f2f2f2;
  color: #333;
}

.input-container {
  display: flex;
  padding: 10px;
  border-top: 1px solid #eee;
  background-color: #fff;
}

.chat-input {
  flex: 1;
  margin-right: 10px;
}

.send-button {
  align-self: flex-end;
}

/* Markdown 样式 */
.message-content pre {
  background-color: #f8f8f8;
  padding: 10px;
  border-radius: 5px;
  overflow-x: auto;
}

.message-content code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 4px;
  border-radius: 3px;
}

.message-content img {
  max-width: 100%;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  padding: 5px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #999;
  border-radius: 50%;
  margin: 0 2px;
  display: inline-block;
  animation: bounce 1.5s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-5px);
  }
}

/* Markdown样式 */
:deep(pre) {
  background-color: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

:deep(code) {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 2px 4px;
  border-radius: 4px;
}

:deep(p) {
  margin: 8px 0;
}

:deep(ul), :deep(ol) {
  padding-left: 20px;
}

:deep(a) {
  color: #1989fa;
  text-decoration: none;
}
</style>
