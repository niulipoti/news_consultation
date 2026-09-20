import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()

// pinia-plugin-persistedstate v4：直接 use 默认导出即可
// （v3 的 createPersistedState({ storage }) 写法在 v4 里已废弃）
pinia.use(piniaPluginPersistedstate)

export default pinia
