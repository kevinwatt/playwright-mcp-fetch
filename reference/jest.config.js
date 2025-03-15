/**
 * Jest 設定檔
 * 此配置使用 ts-jest 作為預設預置，並且設定測試執行環境為 Node.js
 */
export default {
  preset: "ts-jest",
  testEnvironment: "node",
  extensionsToTreatAsEsm: [".ts"],
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1"
  },
  transform: {
    "^.+\\.(ts|tsx)$": [
      "ts-jest", 
      { 
        useESM: true,
        tsconfig: "tsconfig.test.json",
        isolatedModules: true,
        skipTypechecking: true
      }
    ]
  },
  transformIgnorePatterns: [
    "node_modules/(?!(node-fetch)/)"
  ],
  // 只測試 src 目錄下的文件
  testMatch: ["**/src/**/*.test.ts"],
};
