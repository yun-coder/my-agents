import { ChatAnthropic } from "@langchain/anthropic";
import { type BaseMessage } from "@langchain/core/messages";

/**
 * 共享 LLM 配置
 * 用于所有 demo 的 LLM 实例
 */

// 从环境变量获取 API Key
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "";

if (!ANTHROPIC_API_KEY) {
  console.warn("⚠️  ANTHROPIC_API_KEY not found in environment variables");
  console.warn("Please create a .env file with your API key");
}

/**
 * 创建 Claude 3.5 Sonnet 实例
 * 推荐用于大多数场景
 */
export const createClaudeSonnet = (options?: {
  temperature?: number;
  maxTokens?: number;
}) => {
  return new ChatAnthropic({
    apiKey: ANTHROPIC_API_KEY,
    model: "claude-3-5-sonnet-20241022",
    temperature: options?.temperature ?? 0.7,
    maxTokens: options?.maxTokens ?? 4096,
  });
};

/**
 * 创建 Claude 3 Haiku 实例
 * 快速且经济，适合简单任务
 */
export const createClaudeHaiku = (options?: {
  temperature?: number;
  maxTokens?: number;
}) => {
  return new ChatAnthropic({
    apiKey: ANTHROPIC_API_KEY,
    model: "claude-3-5-haiku-20241022",
    temperature: options?.temperature ?? 0.7,
    maxTokens: options?.maxTokens ?? 4096,
  });
};

/**
 * LLM 配置预设
 */
export const LLM_PRESETS = {
  /**
   * 创意写作 - 高温度
   */
  creative: {
    temperature: 0.9,
    maxTokens: 4096,
  },

  /**
   * 代码生成 - 中等温度
   */
  coding: {
    temperature: 0.3,
    maxTokens: 8192,
  },

  /**
   * 分析推理 - 低温度
   */
  analytical: {
    temperature: 0.1,
    maxTokens: 4096,
  },

  /**
   * 快速响应 - 使用 Haiku
   */
  fast: {
    model: "haiku",
    temperature: 0.7,
    maxTokens: 2048,
  },
} as const;
