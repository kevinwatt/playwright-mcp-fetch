# 更新日誌

## [未發布]

### 新增
- 

### 修改
- 放棄 stdio 傳輸方式，改用純 SSE 傳輸
- 移除 playwright-mcp-fetch 和 playwright-mcp-fetch-direct 入口點，只保留 playwright-mcp-fetch-sse
- 更新文檔以反映只使用 SSE 傳輸的變更

### 修復
- 


## [0.1.5] - 2025-03-16

### 新增
- 

### 修改
- 修改 FastMCP 服務器啟動方式，使用 anyio.run(server.run_stdio_async) 代替 asyncio.run(main_async())
- 優化 list_tools_handler 函數，在每次調用時檢查環境變數

### 修復
- 修復 'FastMCP' object has no attribute 'set_request_handler' 錯誤
- 修復測試中的環境變數檢查問題


## [0.1.4] - 2025-03-16

### 新增
- 

### 修改
- 更新 MCP Client Configuration 部分，添加 stdio 傳輸方式的配置示例
- 使用 uvx 作為 stdio 傳輸方式的命令，符合 MCP SDK 標準
- 清理項目結構，移除舊的 mcp_fetch 目錄

### 修復
- 


## [0.1.3] - 2025-03-16

### 新增
- 

### 修改
- 

### 修復
- 


## [0.1.3] - 2025-03-16

### 新增
- 

### 修改
- 

### 修復
- 


## [0.1.3] - 2025-03-16

### 新增
- 

### 修改
- 

### 修復
- 


## [0.1.2] - 2025-03-16

### 新增
- 

### 修改
- 將最低 Python 版本要求從 3.8 提高到 3.10
- 更新 GitHub Actions 工作流程，僅測試 Python 3.10 及更高版本
- 更新 mcp 依賴版本至 1.4.1（最新版本）

### 修復
- 


所有對 playwright-mcp-fetch 的重要更改都將記錄在此文件中。

## [0.1.1] - 2025-03-16

### 新增
- 

### 修改
- 

### 修復
- 

## [0.1.0] - 2024-03-16

### 新增
- 初始版本
- 支援 fetch_html、fetch_markdown、fetch_txt 和 fetch_json 工具
- 支援 stdio 和 SSE 傳輸模式
- Docker 支援
- GitHub Actions CI/CD 自動化 