# MCP Fetch 工具

**當前版本：1.2.0**

這個工具提供了一個 Model Context Protocol (MCP) 服務器，用於從網站獲取內容並轉換為不同格式。

## 最新更新

- 添加了完整的 Docker 支持
- 修復了 SSE 服務器的穩定性問題
- 改進了 Markdown 轉換功能

## 功能

- `fetch_html`: 獲取網站的原始 HTML 內容
- `fetch_markdown`: 獲取網站內容並轉換為 Markdown 格式
- `fetch_txt`: 獲取網站內容並轉換為純文本格式（移除 HTML 標籤）
- `fetch_json`: 獲取並解析 JSON 內容

## 安裝

### 從 npm 安裝

```bash
npm install @kevinwatt/biggo-eclimit-fetch-mcp
```

### 從源代碼安裝

```bash
git clone https://git.biggo.com/kevin/biggo-eclimit-fetch-mcp.git
cd biggo-eclimit-fetch-mcp
npm install
```

### 使用 Docker

#### 使用 Docker Compose（推薦）

```bash
git clone https://git.biggo.com/kevin/biggo-eclimit-fetch-mcp.git
cd biggo-eclimit-fetch-mcp
docker-compose up -d
```

#### 手動構建和運行 Docker 容器

```bash
git clone https://git.biggo.com/kevin/biggo-eclimit-fetch-mcp.git
cd biggo-eclimit-fetch-mcp
docker build -t biggo-eclimit-fetch-mcp .
docker run -d -p 3000:3000 --name fetch-mcp biggo-eclimit-fetch-mcp
```

## 使用方法

### 作為 stdio MCP 服務器運行

```bash
npm start
```

### 作為 SSE MCP 服務器運行

```bash
npm run start:sse
```

這將啟動一個 HTTP 服務器，提供以下端點：

- `GET /`: 服務器狀態頁面
- `GET /sse`: SSE 連接端點
- `POST /api/list-tools`: 列出可用工具
- `POST /api/call-tool`: 調用工具

### 環境變量

- `PORT`: HTTP 服務器端口（默認：3000）
- `TRANSPORT_TYPE`: 傳輸類型，可以是 `stdio` 或 `sse`（默認：`stdio`）
- `fetch_html`: 是否啟用 `fetch_html` 工具，可以是 `Enable` 或 `Disable`（默認：`Disable`）
- `DNListCheck`: 是否啟用 DNList 檢查，可以是 `Enable` 或 `Disable`（默認：`Enable`）

在 Docker 環境中，您可以通過修改 `docker-compose.yml` 文件中的 `environment` 部分來設置這些環境變量：

```yaml
environment:
  - PORT=3000
  - TRANSPORT_TYPE=sse
  - fetch_html=Enable  # 如果需要啟用 fetch_html 工具
  - DNListCheck=Enable
```

或者在運行 Docker 容器時使用 `-e` 參數：

```bash
docker run -d -p 3000:3000 -e fetch_html=Enable -e DNListCheck=Enable --name fetch-mcp biggo-eclimit-fetch-mcp
```

## MCP 客戶端配置

要在 MCP 客戶端中使用此服務器，請使用以下配置：

```json
{
  "mcpServers": {
    "fetch-tools": {
      "enabled": true,
      "transport": "sse",
      "url": "http://localhost:3000/sse"
    }
  }
}
```

您可以將 `fetch-tools` 替換為任何您喜歡的名稱，並根據您的部署環境調整 URL。

## API 示例

### 列出工具

```bash
curl -X POST http://localhost:3000/api/list-tools
```

### 調用工具

```bash
curl -X POST http://localhost:3000/api/call-tool \
  -H "Content-Type: application/json" \
  -d '{"name": "fetch_markdown", "arguments": {"url": "https://example.com"}}'
```

## SSE 客戶端示例

```javascript
const eventSource = new EventSource('http://localhost:3000/sse');

eventSource.addEventListener('tool-result', (event) => {
  const result = JSON.parse(event.data);
  console.log('Tool result:', result);
});

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

## 開發

```bash
npm run dev
```

## 測試

運行所有測試：

```bash
npm test
```

僅運行 Fetcher 測試（不包括 SSE 測試）：

```bash
npm run test -- --testPathIgnorePatterns=src/server.test.ts
```

### SSE 測試

SSE 服務器的單元測試位於 `src/server.test.ts` 文件中。這些測試使用 `supertest` 庫來測試 HTTP 端點，並模擬 Fetcher 方法以避免實際的網絡請求。

測試涵蓋以下方面：
- 服務器狀態頁面
- 列出可用工具
- 處理工具調用請求
- 處理不存在的工具調用
