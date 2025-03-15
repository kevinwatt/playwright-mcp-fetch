import { JSDOM } from "jsdom";
import TurndownService from "turndown";
import { RequestPayload } from "./types.js";
import { DNList } from "./DNList.js";
import { chromium } from "playwright";
import { Readability } from "@mozilla/readability";

export class Fetcher {
  // 最大重試次數
  private static MAX_RETRIES = 2;
  // 基本超時時間（毫秒）
  private static BASE_TIMEOUT = 10000;
  // 最大重定向次數
  private static MAX_REDIRECTS = 3;

  private static async _fetch({
    url,
    headers,
  }: RequestPayload): Promise<{ content: string; contentType: string }> {
    // 檢查是否需要進行 DNList 檢查
    const dnListCheckEnv = process.env.DNListCheck || "Enable";
    const shouldCheckDNList = dnListCheckEnv.toLowerCase() !== "disable";
    
    if (shouldCheckDNList) {
      const allowed = await DNList.isAllowed(url);
      if (!allowed) {
        throw new Error("Not an EC site. Fetch Tools only crawl EC Sites.");
      }
    }

    let lastError: Error | null = null;
    
    // 重試邏輯
    for (let attempt = 0; attempt <= Fetcher.MAX_RETRIES; attempt++) {
      try {
        // 啟動 Playwright 瀏覽器
        const browser = await chromium.launch({ 
          headless: true,
          // 增加啟動超時時間
          timeout: 30000
        });
        
        const context = await browser.newContext({
          userAgent:
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
          extraHTTPHeaders: headers,
        });
        
        const page = await context.newPage();

        try {
          console.log(`Attempt ${attempt + 1} to fetch ${url}`);
          
          // 追蹤重定向次數
          let redirectCount = 0;
          
          // 設置路由處理程序來監控和限制重定向
          await page.route('**/*', async (route) => {
            const request = route.request();
            
            // 檢查是否為重定向請求
            if (request.isNavigationRequest() && request.redirectedFrom()) {
              redirectCount++;
              console.log(`Redirect #${redirectCount}: ${request.redirectedFrom()?.url()} -> ${request.url()}`);
              
              // 如果重定向次數超過限制，則中止請求
              if (redirectCount > Fetcher.MAX_REDIRECTS) {
                console.error(`Redirect count exceeded limit (${Fetcher.MAX_REDIRECTS}), aborting request`);
                await route.abort('failed');
                return;
              }
            }
            
            // 繼續請求
            await route.continue();
          });
          
          // 使用最基本的導航方式，不等待任何特定事件
          const response = await page.goto(url, { 
            waitUntil: "commit", // 只等待開始接收頁面內容
            timeout: Fetcher.BASE_TIMEOUT * (attempt + 1)
          });
          
          if (!response) {
            throw new Error("No response received");
          }
          
          if (response.status() >= 400) {
            throw new Error(`HTTP error: ${response.status()}`);
          }
          
          // 等待一小段時間讓頁面內容加載
          await page.waitForTimeout(2000);
          
          // 獲取內容類型
          const contentType = response.headers()["content-type"] || "";
          
          // 獲取頁面內容
          const content = await page.content();
          
          // 成功獲取內容，返回結果
          return { content, contentType };
        } finally {
          // 確保瀏覽器關閉
          await browser.close();
        }
      } catch (e: unknown) {
        lastError = e instanceof Error ? e : new Error(String(e));
        console.error(`Attempt ${attempt + 1} failed: ${lastError.message}`);
        
        // 如果不是最後一次嘗試，則等待一段時間後重試
        if (attempt < Fetcher.MAX_RETRIES) {
          const delay = 1000 * (attempt + 1); // 逐漸增加延遲時間
          console.log(`Waiting ${delay}ms before retry...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    // 所有重試都失敗了，拋出最後一個錯誤
    throw new Error(`Failed to fetch ${url} after ${Fetcher.MAX_RETRIES + 1} attempts: ${lastError?.message || "Unknown error"}`);
  }

  private static _handleError(error: unknown) {
    return {
      content: [{ type: "text", text: (error as Error).message }],
      isError: true,
    };
  }

  static async html(requestPayload: RequestPayload) {
    try {
      const { content } = await Fetcher._fetch(requestPayload);
      return { content: [{ type: "text", text: content }], isError: false };
    } catch (error) {
      return Fetcher._handleError(error);
    }
  }

  static async json(requestPayload: RequestPayload) {
    try {
      const { content } = await Fetcher._fetch(requestPayload);
      
      // 嘗試從HTML中提取JSON
      let jsonContent = content;
      
      // 檢查是否是HTML包裝的JSON
      if (content.includes("<pre>") && content.includes("</pre>")) {
        const preMatch = content.match(/<pre>([\s\S]*?)<\/pre>/);
        if (preMatch && preMatch[1]) {
          jsonContent = preMatch[1].trim();
        }
      }
      
      // 嘗試解析JSON
      try {
        const jsonObj = JSON.parse(jsonContent);
        return {
          content: [{ type: "text", text: JSON.stringify(jsonObj) }],
          isError: false,
        };
      } catch (parseError) {
        throw new Error("Response is not valid JSON");
      }
    } catch (error) {
      return Fetcher._handleError(error);
    }
  }

  static async txt(requestPayload: RequestPayload) {
    try {
      const { content } = await Fetcher._fetch(requestPayload);

      const dom = new JSDOM(content);
      const document = dom.window.document;

      const scripts = document.getElementsByTagName("script");
      const styles = document.getElementsByTagName("style");
      Array.from(scripts).forEach((script) => script.remove());
      Array.from(styles).forEach((style) => style.remove());

      const text = document.body.textContent || "";

      const normalizedText = text.replace(/\s+/g, " ").trim();

      return {
        content: [{ type: "text", text: normalizedText }],
        isError: false,
      };
    } catch (error) {
      return Fetcher._handleError(error);
    }
  }

  static async markdown(requestPayload: RequestPayload) {
    try {
      const { content } = await Fetcher._fetch(requestPayload);
      
      // 使用 JSDOM 解析 HTML
      const dom = new JSDOM(content, { url: requestPayload.url });
      const document = dom.window.document;
      
      try {
        // 嘗試使用 Readability 提取主要內容
        const reader = new Readability(document);
        const article = reader.parse();
        
        if (article && article.content) {
          // 使用提取的主要內容創建新的 DOM
          const cleanDom = new JSDOM(article.content);
          const cleanDocument = cleanDom.window.document;
          
          // 創建 TurndownService 實例並配置選項
          const turndownService = new TurndownService({
            headingStyle: 'atx',           // 使用 # 風格的標題
            codeBlockStyle: 'fenced',      // 使用 ``` 風格的代碼塊
            emDelimiter: '*',              // 使用 * 作為斜體分隔符
            strongDelimiter: '**',         // 使用 ** 作為粗體分隔符
            bulletListMarker: '-',         // 使用 - 作為無序列表標記
            hr: '---',                     // 使用 --- 作為水平線
            linkStyle: 'inlined'           // 使用內聯風格的鏈接
          });
          
          // 自定義轉義函數，減少過度轉義
          turndownService.escape = function(text) {
            // 只轉義必要的 Markdown 字符
            return text
              // 轉義反斜線
              .replace(/\\/g, '\\\\')
              // 轉義標題前的數字列表格式
              .replace(/^(\d+)\.\s/gm, '$1\\. ')
              // 轉義 * 和 _ 但只在它們可能被解釋為格式化標記時
              .replace(/([*_])/g, '\\$1')
              // 轉義 ` 但只在單個反引號時
              .replace(/`/g, '\\`')
              // 轉義 [] 和 ()
              .replace(/\[/g, '\\[')
              .replace(/\]/g, '\\]')
              .replace(/\(/g, '\\(')
              .replace(/\)/g, '\\)')
              // 轉義 # 但只在行首時
              .replace(/^#/gm, '\\#');
          };
          
          // 添加文章標題（如果有）
          let markdown = '';
          if (article.title) {
            markdown += `# ${article.title}\n\n`;
          }
          
          // 添加作者信息（如果有）
          if (article.byline) {
            markdown += `*作者: ${article.byline}*\n\n`;
          }
          
          // 轉換清理後的 HTML 為 Markdown
          markdown += turndownService.turndown(cleanDocument.body.innerHTML);
          
          // 清理多餘的轉義和空行
          const cleanedMarkdown = markdown
            // 移除連續的空行，將多個空行替換為最多兩個空行
            .replace(/\n{3,}/g, '\n\n')
            // 移除行尾空白
            .replace(/[ \t]+$/gm, '')
            // 修復過度轉義的問題
            .replace(/\\\\([*_`\[\]()#])/g, '\\$1')
            // 移除空的 Markdown 鏈接
            .replace(/\[]\(.*?\)/g, '')
            // 移除只包含空白的行
            .replace(/^\s+$/gm, '');
          
          return { content: [{ type: "text", text: cleanedMarkdown }], isError: false };
        } else {
          // 如果 Readability 無法提取內容，回退到原始的清理方法
          console.log("Readability 無法提取內容，回退到原始清理方法");
          throw new Error("Readability 無法提取內容");
        }
      } catch (readabilityError) {
        console.error("Readability 處理失敗:", readabilityError);
        
        // 回退到原始的清理方法
        // 移除所有 script 標籤
        const scripts = document.getElementsByTagName("script");
        Array.from(scripts).forEach((script) => script.remove());
        
        // 移除所有 style 標籤
        const styles = document.getElementsByTagName("style");
        Array.from(styles).forEach((style) => style.remove());
        
        // 移除所有 link 標籤 (通常用於引入外部 CSS)
        const links = document.getElementsByTagName("link");
        Array.from(links).filter(link => link.getAttribute("rel") === "stylesheet").forEach(link => link.remove());
        
        // 移除所有 noscript 標籤
        const noscripts = document.getElementsByTagName("noscript");
        Array.from(noscripts).forEach((noscript) => noscript.remove());
        
        // 移除所有 iframe 標籤
        const iframes = document.getElementsByTagName("iframe");
        Array.from(iframes).forEach((iframe) => iframe.remove());
        
        // 移除所有 svg 標籤
        const svgs = document.getElementsByTagName("svg");
        Array.from(svgs).forEach((svg) => svg.remove());
        
        // 移除所有 inline 樣式
        const elementsWithStyle = document.querySelectorAll("[style]");
        Array.from(elementsWithStyle).forEach((el) => el.removeAttribute("style"));
        
        // 獲取清理後的 HTML
        const cleanedHtml = document.documentElement.outerHTML;
        
        // 創建 TurndownService 實例並配置選項
        const turndownService = new TurndownService({
          headingStyle: 'atx',
          codeBlockStyle: 'fenced',
          emDelimiter: '*',
          strongDelimiter: '**',
          bulletListMarker: '-',
          hr: '---',
          linkStyle: 'inlined'
        });
        
        // 自定義轉義函數，減少過度轉義
        turndownService.escape = function(text) {
          return text
            .replace(/\\/g, '\\\\')
            .replace(/^(\d+)\.\s/gm, '$1\\. ')
            .replace(/([*_])/g, '\\$1')
            .replace(/`/g, '\\`')
            .replace(/\[/g, '\\[')
            .replace(/\]/g, '\\]')
            .replace(/\(/g, '\\(')
            .replace(/\)/g, '\\)')
            .replace(/^#/gm, '\\#');
        };
        
        // 轉換清理後的 HTML 為 Markdown
        const markdown = turndownService.turndown(cleanedHtml);
        
        // 清理多餘的轉義和空行
        const cleanedMarkdown = markdown
          .replace(/\n{3,}/g, '\n\n')
          .replace(/[ \t]+$/gm, '')
          .replace(/\\\\([*_`\[\]()#])/g, '\\$1')
          .replace(/\[]\(.*?\)/g, '')
          .replace(/^\s+$/gm, '');
        
        return { content: [{ type: "text", text: cleanedMarkdown }], isError: false };
      }
    } catch (error) {
      return Fetcher._handleError(error);
    }
  }
}
