import request from 'supertest';
import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { jest, expect, describe, beforeEach, afterEach, it } from '@jest/globals';
import SSE from 'express-sse';
import { RequestPayload } from './types.js';
import { Fetcher } from './Fetcher.js';

// 保存原始環境變量
const originalEnv = { ...process.env };

// 定義工具處理程序類型
type ToolHandler = (payload: RequestPayload) => Promise<{
  content: Array<{ type: string; text: string }>;
  isError: boolean;
}>;

describe('SSE Server', () => {
  let app: express.Application;
  let server: Server;
  let sse: SSE;
  
  beforeEach(() => {
    // 重置環境變量
    process.env = { ...originalEnv };
    process.env.TRANSPORT_TYPE = 'sse';
    
    // 創建 Express 應用
    app = express();
    app.use(cors());
    app.use(bodyParser.json());
    
    // 創建 MCP 服務器
    server = new Server(
      {
        name: "test-fetch",
        version: "0.1.0",
      },
      {
        capabilities: {
          resources: {},
          tools: {},
        },
      },
    );
    
    // 創建 SSE 實例
    sse = new SSE();
    
    // 設置 SSE 端點
    app.get('/sse', sse.init);
    
    // 設置 API 端點
    app.post('/api/list-tools', async (req, res) => {
      try {
        const tools = [
          {
            name: "fetch_markdown",
            description: "Fetch content from a website and convert it to Markdown format",
            inputSchema: {
              type: "object",
              properties: {
                url: {
                  type: "string",
                  description: "The URL of the website to fetch",
                },
                headers: {
                  type: "object",
                  description: "Optional request headers",
                },
              },
              required: ["url"],
            },
          }
        ];
        res.json({ tools });
      } catch (error) {
        console.error('Error handling listTools request:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });
    
    app.post('/api/call-tool', async (req, res) => {
      try {
        const { name, arguments: args } = req.body;
        
        // 獲取處理程序
        const toolHandlers: { [key: string]: ToolHandler } = {
          fetch_html: Fetcher.html as unknown as ToolHandler,
          fetch_json: Fetcher.json as unknown as ToolHandler,
          fetch_txt: Fetcher.txt as unknown as ToolHandler,
          fetch_markdown: Fetcher.markdown as unknown as ToolHandler,
        };
        
        const handler = toolHandlers[name];
        if (!handler) {
          throw new Error("Tool not found");
        }
        
        // 執行工具
        const result = await handler(args);
        
        // 通過 SSE 發送結果
        sse.send(result, 'tool-result');
        
        res.json({ status: 'ok', message: 'Tool call initiated, results will be sent via SSE' });
      } catch (error) {
        console.error('Error handling callTool request:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });
  });
  
  afterEach(() => {
    // 恢復環境變量
    process.env = { ...originalEnv };
  });
  
  it('應該返回服務器狀態頁面', async () => {
    // 添加根路由處理程序
    app.get('/', (req, res) => {
      res.send('MCP Fetch Server is running. Use /sse endpoint for SSE connections or /api for direct API access.');
    });
    
    const response = await request(app).get('/');
    expect(response.status).toBe(200);
    expect(response.text).toContain('MCP Fetch Server is running');
  });
  
  it('應該列出可用工具', async () => {
    const response = await request(app)
      .post('/api/list-tools')
      .send({});
    
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('tools');
    expect(response.body.tools).toBeInstanceOf(Array);
    expect(response.body.tools.length).toBeGreaterThan(0);
    expect(response.body.tools[0]).toHaveProperty('name', 'fetch_markdown');
  });
  
  it('應該處理工具調用請求', async () => {
    // 使用實際的 URL 進行測試
    const response = await request(app)
      .post('/api/call-tool')
      .send({
        name: 'fetch_markdown',
        arguments: { url: 'https://example.com' }
      });
    
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('status', 'ok');
  });
  
  it('應該處理不存在的工具調用', async () => {
    const response = await request(app)
      .post('/api/call-tool')
      .send({
        name: 'non_existent_tool',
        arguments: { url: 'https://example.com' }
      });
    
    expect(response.status).toBe(500);
    expect(response.body).toHaveProperty('error');
  });
}); 