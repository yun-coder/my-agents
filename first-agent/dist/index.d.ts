/**
 * LangChain + MiniMax 模型 TypeScript 示例
 *
 * 使用 MiniMax Anthropic API 兼容模式
 * 文档: https://platform.minimaxi.com/docs/guides/quickstart-preparation
 */
import { ChatAnthropic } from "@langchain/anthropic";
/**
 * 创建 MiniMax 模型实例 (使用 Anthropic API 兼容模式)
 */
declare function createMiniMaxModel(modelName?: string): ChatAnthropic;
/**
 * 获取天气工具函数
 */
declare function getWeather(city: string): string;
/**
 * 计算器工具函数
 */
declare function calculator(expression: string): string;
/**
 * 获取当前时间工具函数
 */
declare function getCurrentTime(): string;
export { createMiniMaxModel, getWeather, calculator, getCurrentTime };
//# sourceMappingURL=index.d.ts.map