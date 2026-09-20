<template>
  <div class="home">
    <van-nav-bar :title="$t('home.title')" fixed />

    <!-- 更多选项独立div -->
    <div class="more-options">
      <div class="more-tab" @click="goToCategory">
        {{ $t('home.more') }} <van-icon name="arrow" />
      </div>
    </div>

    <div class="category-tabs">
      <van-tabs v-model:active="activeTab" sticky swipeable animated @change="onTabChange">
        <van-tab
          v-for="category in displayCategories"
          :key="category.id"
          :title="getCategoryTranslation(category.name)"
        >
          <van-pull-refresh v-model="newsStore.refreshing" @refresh="onRefresh">
            <van-list
              v-model:loading="newsStore.loading"
              :finished="newsStore.finished"
              :finished-text="$t('home.noMore')"
              @load="onLoad"
            >
              <news-item
                v-for="item in newsStore.newsList"
                :key="item.id"
                :news="item"
              />
            </van-list>
          </van-pull-refresh>
        </van-tab>
      </van-tabs>
    </div>

    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { useNewsStore } from '../store/modules/news'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NewsItem from '../components/NewsItem.vue'
import TabBar from '../components/TabBar.vue'

const newsStore = useNewsStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const activeTab = ref(0)
const tabsTop = ref(0)

// 计算属性：显示的分类（只显示非"更多"分类）
const displayCategories = computed(() => {
  return newsStore.categories.filter((category) => category.name !== '更多')
})

// 获取分类名称的翻译
const getCategoryTranslation = (categoryName) => {
  const categoryMap = {
    头条: 'headline',
    社会: 'society',
    国内: 'domestic',
    国际: 'international',
    娱乐: 'entertainment',
    体育: 'sports',
    军事: 'military',
    科技: 'technology',
    财经: 'finance',
    更多: 'more',
  }

  const key = categoryMap[categoryName]
  return key ? t(`home.categories.${key}`) : categoryName
}

// 标签切换：分类列表为空时直接返回，避免越界报错
const onTabChange = (index) => {
  const category = displayCategories.value[index]
  if (!category) return
  newsStore.changeCategory(category.id)
}

// 监听路由变化
watch(
  () => route.query.categoryId,
  (newCategoryId) => {
    if (!newCategoryId) return

    const categoryId = parseInt(newCategoryId, 10)
    const index = displayCategories.value.findIndex((cat) => cat.id === categoryId)

    if (index !== -1) {
      activeTab.value = index
      newsStore.changeCategory(categoryId)
    }
  },
  { immediate: true },
)

// 跳转到分类页面
const goToCategory = () => {
  router.push('/category')
}

// 获取分类导航栏的位置并设置滚动监听
const updateTabsPosition = () => {
  const tabsElement = document.querySelector('.van-tabs__wrap')
  if (tabsElement) {
    tabsTop.value = tabsElement.getBoundingClientRect().top
  }
}

// 滚动事件处理
const handleScroll = () => {
  updateTabsPosition()
}

// 下拉刷新
const onRefresh = () => {
  newsStore.getNewsList(true)
}

// 上拉加载更多
const onLoad = () => {
  newsStore.getNewsList()
}

onMounted(async () => {
  // 先拿到分类再拉列表，否则 currentCategory 还是空的
  await newsStore.getCategories()

  // 支持 /home?categoryId=x 直接定位到某个分类
  const queryCategoryId = parseInt(route.query.categoryId, 10)
  if (!Number.isNaN(queryCategoryId)) {
    const index = displayCategories.value.findIndex((cat) => cat.id === queryCategoryId)
    if (index !== -1) {
      activeTab.value = index
      newsStore.currentCategory = queryCategoryId
    }
  }

  await newsStore.getNewsList(true)

  // 初始化位置
  setTimeout(updateTabsPosition, 300)

  // 添加滚动事件监听
  window.addEventListener('scroll', handleScroll)
})

// 组件销毁前移除事件监听
onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.home {
  padding-top: 46px;
  padding-bottom: 50px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

.category-tabs {
  margin-bottom: 10px;
  position: relative;
}

:deep(.van-tabs__wrap) {
  background-color: #fff;
}

:deep(.van-tab) {
  font-size: 14px;
}

:deep(.van-tab--active) {
  font-weight: bold;
  color: #1989fa;
}

.more-options {
  position: fixed;
  right: 0;
  background-color: #fff;
  padding: 0;
  border-radius: 4px 0 0 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  /* 通过计算属性动态设置top */
  top: v-bind('tabsTop + "px"');
  height: 44px; /* 与van-tabs__wrap高度一致 */
  display: flex;
  align-items: center;
}

.more-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #1989fa;
  font-weight: bold;
  height: 100%;
  padding: 0 10px;
}
</style>
