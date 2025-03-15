import { JSDOM } from "jsdom";
import TurndownService from "turndown";
import { DNList } from "./DNList.js";
import { chromium } from "playwright";
import { jest, expect, describe, beforeEach, afterEach, it } from '@jest/globals';
import { Fetcher } from "./Fetcher.js";

// 保存原始環境變量
const originalEnv = { ...process.env };

// 測試用的真實網站
const testSites = {
  ec: "https://www.rakuten.com.tw/", // 電商網站
  nonEc: "https://www.google.com/", // 非電商網站
  json: "https://jsonplaceholder.typicode.com/todos/1", // JSON API
  error: "https://httpstat.us/404" // 錯誤頁面
};

// 測試套件
describe("Fetcher", () => {
  // 在每個測試前執行
  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("DNList 檢查", () => {
    it("應允許 EC 網站", async () => {
      // 確保 DNList 檢查啟用
      process.env.DNListCheck = "Enable";
      
      // 使用真實的 EC 網站
      const result = await Fetcher.html({ url: testSites.ec });
      
      // 驗證結果
      expect(result.isError).toBe(false);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toBeDefined();
    }, 30000); // 增加超時時間

    it("應拒絕非 EC 網站", async () => {
      // 確保 DNList 檢查啟用
      process.env.DNListCheck = "Enable";
      
      // 使用非 EC 網站
      const result = await Fetcher.html({ url: testSites.nonEc });
      
      // 驗證結果
      expect(result.isError).toBe(true);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toContain("Not an EC site");
    }, 30000); // 增加超時時間

    it("當 DNListCheck 設置為 Disable 時應跳過 DNList 檢查", async () => {
      // 設置環境變量
      process.env.DNListCheck = "Disable";
      
      // 使用 jest.spyOn 監視 DNList.isAllowed 方法
      const isAllowedSpy = jest.spyOn(DNList, 'isAllowed');
      
      // 使用非 EC 網站，但由於 DNListCheck 為 Disable，應該可以訪問
      const result = await Fetcher.html({ url: testSites.nonEc });
      
      // 驗證 isAllowed 沒有被調用
      expect(isAllowedSpy).not.toHaveBeenCalled();
      
      // 驗證結果
      expect(result.isError).toBe(false);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toBeDefined();
      
      // 恢復原始方法
      isAllowedSpy.mockRestore();
    }, 30000); // 增加超時時間
  });

  describe("html", () => {
    beforeEach(() => {
      // 禁用 DNList 檢查，以便測試其他功能
      process.env.DNListCheck = "Disable";
    });

    it("應返回原始 HTML 內容", async () => {
      const result = await Fetcher.html({ url: testSites.nonEc });
      expect(result.isError).toBe(false);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toBeDefined();
      expect(result.content[0].text).toContain("<html");
    }, 30000); // 增加超時時間

    it("應處理錯誤", async () => {
      const result = await Fetcher.html({ url: testSites.error });
      expect(result.isError).toBe(true);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toContain("HTTP error: 404");
    }, 30000); // 增加超時時間
  });

  describe("json", () => {
    beforeEach(() => {
      // 禁用 DNList 檢查，以便測試其他功能
      process.env.DNListCheck = "Disable";
    });

    it("應解析並返回 JSON 內容", async () => {
      const result = await Fetcher.json({ url: testSites.json });
      expect(result.isError).toBe(false);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toBeDefined();
      // 驗證 JSON 格式
      const parsed = JSON.parse(result.content[0].text);
      expect(parsed).toHaveProperty("id");
      expect(parsed).toHaveProperty("title");
    }, 30000); // 增加超時時間

    it("應處理非 JSON 內容", async () => {
      const result = await Fetcher.json({ url: testSites.nonEc });
      // 即使不是 JSON，也應該嘗試解析
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toBeDefined();
    }, 30000); // 增加超時時間
  });

  describe("txt", () => {
    beforeEach(() => {
      // 禁用 DNList 檢查，以便測試其他功能
      process.env.DNListCheck = "Disable";
    });

    it("應返回不含 HTML 標籤的純文字內容", async () => {
      const result = await Fetcher.txt({ url: testSites.nonEc });
      expect(result.isError).toBe(false);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toBeDefined();
      // 不應包含 HTML 標籤
      expect(result.content[0].text).not.toContain("<html");
      expect(result.content[0].text).not.toContain("<body");
    }, 30000); // 增加超時時間
  });

  describe("markdown", () => {
    beforeEach(() => {
      // 禁用 DNList 檢查，以便測試其他功能
      process.env.DNListCheck = "Disable";
    });

    it("應將 HTML 轉換為 Markdown", async () => {
      const result = await Fetcher.markdown({ url: testSites.nonEc });
      expect(result.isError).toBe(false);
      expect(result.content[0].type).toBe("text");
      expect(result.content[0].text).toBeDefined();
      // Markdown 格式檢查
      expect(result.content[0].text).not.toContain("<html");
      expect(result.content[0].text).not.toContain("<body");
    }, 30000); // 增加超時時間
  });
});
