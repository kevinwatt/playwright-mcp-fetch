import { z } from "zod";

// 定義請求內容驗證結構
export const RequestPayloadSchema = z.object({
  url: z.string().url(),
  headers: z.record(z.string()).optional(),
});

// 定義傳入請求的型別
export type RequestPayload = z.infer<typeof RequestPayloadSchema>;
