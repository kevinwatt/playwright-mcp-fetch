# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1] - 2024-03-15

### Fixed
- 修復 SSE 服務器測試中的類型錯誤，改用實際 API 進行測試

## [1.1.0] - 2024-03-15

### Added
- 新增 MCP SSE 服務器支持，允許通過 Server-Sent Events 連接到 MCP 客戶端
- 新增 SSE 服務器的單元測試
- 更新 README 文件，添加 MCP 客戶端配置說明

### Changed
- 改進 Facebook 帖子內容轉換為 Markdown 的功能
- 使用 Mozilla 的 Readability.js 庫提取網頁主要內容
- 優化 Markdown 轉換過程，減少不必要的 CSS 和 JavaScript 代碼

### Fixed
- 修復 SSE 服務器單元測試中的類型錯誤
- 修復 Fetcher 模塊中的錯誤處理

## [1.0.0] - 2024-03-02

### Added
- 初始版本發布
- 基本的網頁內容獲取功能
- 支持 HTML、Markdown、Text 和 JSON 格式的內容獲取 