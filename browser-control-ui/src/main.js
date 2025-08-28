import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

const app = createApp(App)

// 글로벌 오류 핸들러
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Error Info:', info)
}

app.mount('#app')