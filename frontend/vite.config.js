import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    base: '/Agentic-AI-Interview-Training-System/',
    server: {
        port: 3000, // Frontend on 3000, Backend on 8000
        strictPort: false, // If 3000 is busy, automatically use next available port
        host: true // Allows access via local network IP
    }
})
