import {createApp} from 'vue'
import StudioView from './src/views/StudioView.vue'
import './src/style.css'
import './src/app-theme.css'
window.studioErrors=[]
const app=createApp(StudioView)
app.config.errorHandler=(error)=>{window.studioErrors.push(String(error));console.error('Studio component error:',error)}
app.mount('#app')
