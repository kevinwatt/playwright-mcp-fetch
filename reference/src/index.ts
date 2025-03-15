#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { RequestPayloadSchema } from "./types.js";
import { Fetcher } from "./Fetcher.js";

const server = new Server(
  {
    name: "zcaceres/fetch",
    version: "0.1.0",
  },
  {
    capabilities: {
      resources: {},
      tools: {},
    },
  },
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  // 檢查 fetch_html 工具是否啟用
  const fetchHtmlEnv = process.env.fetch_html || "Disable";
  const isFetchHtmlEnabled = fetchHtmlEnv.toLowerCase() === "enable";
  
  // 準備工具列表
  const tools = [];
  
  // 根據環境變量決定是否添加 fetch_html 工具
  if (isFetchHtmlEnabled) {
    tools.push({
      name: "fetch_html",
      description: "Fetch and return the raw HTML content from a website",
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
    });
  }
  
  // 添加其他工具（這些工具始終啟用）
  tools.push(
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
    },
    {
      name: "fetch_txt",
      description: "Fetch and return plain text content from a website (HTML tags removed)",
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
    },
    {
      name: "fetch_json",
      description: "Fetch and return JSON content from a URL",
      inputSchema: {
        type: "object",
        properties: {
          url: {
            type: "string",
            description: "The URL of the JSON resource to fetch",
          },
          headers: {
            type: "object",
            description: "Optional request headers",
          },
        },
        required: ["url"],
      },
    }
  );
  
  return { tools };
});

const toolHandlers: { [key: string]: (payload: any) => Promise<any> } = {
  fetch_html: Fetcher.html,
  fetch_json: Fetcher.json,
  fetch_txt: Fetcher.txt,
  fetch_markdown: Fetcher.markdown,
};

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  // 檢查 fetch_html 工具是否啟用
  if (name === "fetch_html") {
    const fetchHtmlEnv = process.env.fetch_html || "Disable";
    const isFetchHtmlEnabled = fetchHtmlEnv.toLowerCase() === "enable";
    
    if (!isFetchHtmlEnabled) {
      throw new Error("The fetch_html tool is disabled. Please set the environment variable fetch_html=Enable to enable this tool.");
    }
  }
  
  const validatedArgs = RequestPayloadSchema.parse(args);
  const handler = toolHandlers[name];
  if (handler) {
    return handler(validatedArgs);
  }
  throw new Error("Tool not found");
});

async function main() {
  // 輸出環境變量設置信息
  console.log("Environment variables settings:");
  console.log(`- fetch_html: ${process.env.fetch_html || "Disable"} (default: Disable)`);
  console.log(`- DNListCheck: ${process.env.DNListCheck || "Enable"} (default: Enable)`);
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Critical error in main():", error);
  process.exit(1);
});
