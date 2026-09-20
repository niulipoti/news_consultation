import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'

// 导入Vant组件库
import {
  Button,
  NavBar,
  Tabbar,
  TabbarItem,
  Tab,
  Tabs,
  List,
  PullRefresh,
  Cell,
  CellGroup,
  Grid,
  GridItem,
  Empty,
  Form,
  Field,
  Image as VanImage,
  Icon,
  Popup,
  Radio,
  RadioGroup,
  Dialog,
  Loading,
  Divider,
} from 'vant'

// 导入Vant样式
import 'vant/lib/index.css'

// 导入全局样式
import './style.css'

// 引入国际化
import { setupI18n } from './i18n'

const app = createApp(App)

// 设置i18n
const i18n = setupI18n()
app.use(i18n)

// 注册Vant组件
// 注意：Dialog / Image 这类组件必须显式注册，否则模板里的
// <van-dialog> / <van-image> 会被当成未知标签而不渲染。
// Toast 是函数式组件（showToast / showDialog），不需要 app.use。
const vantComponents = [
  Button,
  NavBar,
  Tabbar,
  TabbarItem,
  Tab,
  Tabs,
  List,
  PullRefresh,
  Cell,
  CellGroup,
  Grid,
  GridItem,
  Empty,
  Form,
  Field,
  VanImage,
  Icon,
  Popup,
  Radio,
  RadioGroup,
  Dialog,
  Loading,
  Divider,
]

vantComponents.forEach((component) => app.use(component))

// 使用路由和状态管理
app.use(router)
app.use(pinia)

// 初始化主题（原始代码写在 app.mount 之后，属于「挂载后再初始化」，
// 已修正为挂载前执行，避免暗色主题下出现白屏闪烁）
import { useThemeStore } from './store/theme'

const themeStore = useThemeStore()
themeStore.initTheme()

app.mount('#app')
