FROM node:20-slim

# 安裝 Playwright 依賴
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 創建工作目錄
WORKDIR /app

# 複製 package.json 和 package-lock.json
COPY package*.json ./

# 安裝依賴，跳過 prepare 腳本
RUN npm ci --omit=dev --ignore-scripts

# 複製預構建的文件
COPY dist/ ./dist/

# 安裝 Playwright 瀏覽器
RUN npx playwright install chromium

# 暴露端口
EXPOSE 3000

# 設置環境變量
ENV PORT=3000
ENV TRANSPORT_TYPE=sse
ENV fetch_html=Disable
ENV DNListCheck=Enable

# 啟動命令
CMD ["node", "dist/server.js"] 