/**
 * LangChain + MiniMax 简化示例
 *
 * 这个版本使用 MiniMax 模型 (Anthropic API 兼容模式)
 */
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __asyncValues = (this && this.__asyncValues) || function (o) {
    if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
    var m = o[Symbol.asyncIterator], i;
    return m ? m.call(o) : (o = typeof __values === "function" ? __values(o) : o[Symbol.iterator](), i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function () { return this; }, i);
    function verb(n) { i[n] = o[n] && function (v) { return new Promise(function (resolve, reject) { v = o[n](v), settle(resolve, reject, v.done, v.value); }); }; }
    function settle(resolve, reject, d, v) { Promise.resolve(v).then(function(v) { resolve({ value: v, done: d }); }, reject); }
};
import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage } from "@langchain/core/messages";
import * as dotenv from "dotenv";
// 加载环境变量
dotenv.config();
/**
 * 创建 MiniMax 模型实例 (使用 Anthropic API 兼容模式)
 */
function createMiniMaxModel(modelName = "claude-3-5-sonnet-20241022") {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    const baseURL = process.env.ANTHROPIC_BASE_URL || "https://api.minimaxi.com/anthropic";
    if (!apiKey) {
        throw new Error("请设置 ANTHROPIC_API_KEY 环境变量");
    }
    return new ChatAnthropic({
        model: modelName,
        temperature: 0.7,
        apiKey: apiKey,
        clientOptions: {
            baseURL: baseURL,
        },
    });
}
/**
 * 基础对话示例
 */
function basicChatExample() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("📌 基础对话示例");
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        const model = createMiniMaxModel();
        const response = yield model.invoke([
            new HumanMessage("你好，请用一句话介绍一下你自己。"),
        ]);
        console.log("MiniMax 回复:", response.content);
        console.log("\n");
    });
}
/**
 * 多轮对话示例
 */
function multiTurnChatExample() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("📌 多轮对话示例");
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        const model = createMiniMaxModel();
        const conversation = [
            new HumanMessage("我喜欢编程，特别是 TypeScript。"),
            new HumanMessage("你能根据我的兴趣推荐一些学习资源吗？"),
        ];
        for (const message of conversation) {
            console.log("用户:", message.content);
            const response = yield model.invoke([message]);
            console.log("GPT:", response.content);
            console.log();
        }
    });
}
/**
 * 结构化输出示例
 */
function structuredOutputExample() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("📌 结构化输出示例");
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        const model = createMiniMaxModel();
        const prompt = `请分析以下编程语言的特点，并以 JSON 格式返回：
- name: 语言名称
- type: 类型（如：静态类型、动态类型）
- use_cases: 主要应用场景（数组）
- difficulty: 学习难度（简单/中等/困难）

语言：TypeScript

请只返回 JSON，不要有其他内容。`;
        const response = yield model.invoke([new HumanMessage(prompt)]);
        console.log("GPT 回复:");
        console.log(response.content);
        try {
            // 尝试解析 JSON
            const parsed = JSON.parse(response.content);
            console.log("\n解析后的结构化数据:");
            console.log(JSON.stringify(parsed, null, 2));
        }
        catch (e) {
            console.log("\n（JSON 解析失败，显示原始内容）");
        }
        console.log("\n");
    });
}
/**
 * 流式输出示例
 */
function streamingChatExample() {
    return __awaiter(this, void 0, void 0, function* () {
        var _a, e_1, _b, _c;
        console.log("📌 流式输出示例");
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        const model = createMiniMaxModel();
        const stream = yield model.stream([
            new HumanMessage("请用三句话介绍一下 LangChain 框架。"),
        ]);
        console.log("GPT 流式回复:");
        console.log();
        try {
            for (var _d = true, stream_1 = __asyncValues(stream), stream_1_1; stream_1_1 = yield stream_1.next(), _a = stream_1_1.done, !_a; _d = true) {
                _c = stream_1_1.value;
                _d = false;
                const chunk = _c;
                const content = typeof chunk.content === 'string' ? chunk.content : String(chunk.content);
                process.stdout.write(content);
            }
        }
        catch (e_1_1) { e_1 = { error: e_1_1 }; }
        finally {
            try {
                if (!_d && !_a && (_b = stream_1.return)) yield _b.call(stream_1);
            }
            finally { if (e_1) throw e_1.error; }
        }
        console.log("\n\n");
    });
}
/**
 * 主函数
 */
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("🚀 LangChain + MiniMax (Anthropic API) 模型示例\n");
        console.log("使用模型: claude-3-5-sonnet-20241022 (通过 MiniMax Anthropic API)");
        console.log("API 地址: https://api.minimaxi.com/anthropic\n");
        try {
            // 示例 1: 基础对话
            yield basicChatExample();
            // 示例 2: 多轮对话
            yield multiTurnChatExample();
            // 示例 3: 结构化输出
            yield structuredOutputExample();
            // 示例 4: 流式输出
            yield streamingChatExample();
            console.log("✅ 所有示例执行完成!");
        }
        catch (error) {
            console.error("\n❌ 执行出错:", error.message);
            console.error("\n请检查:");
            console.error("1. .env 文件中是否设置了 ANTHROPIC_API_KEY");
            console.error("2. API Key 是否正确");
            console.error("3. 网络连接是否正常");
        }
    });
}
// 执行主函数
main();
//# sourceMappingURL=demo.js.map