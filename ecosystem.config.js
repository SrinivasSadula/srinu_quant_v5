// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "quant_v5_engine",
      script: "app.py",
      interpreter: "python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        NODE_ENV: "production",
        ACTIVE_BROKER: "KITE",
        MODE: "PAPER", // Change to LIVE when ready
        MONGO_URI: "mongodb+srv://Algo_user:KiteBotPassword2026@cluster0.s7l3e0d.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
        KITE_API_KEY: "your_key",
        KITE_API_SECRET: "your_secret"
      }
    }
  ]
};