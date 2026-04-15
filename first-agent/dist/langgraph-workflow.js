/**
 * LangGraph 工作流 Demo
 * 基于 LangChain 官方教程: LangGraph
 *
 * 学习资源: https://docs.langchain.com/oss/javascript/tutorials/graph
 *          https://docs.langchain.com/oss/javascript/concepts/graph_api
 *
 * 功能特性:
 * - 状态机工作流
 * - 条件路由
 * - 循环和迭代
 * - 子图和复合工作流
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
import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage } from "@langchain/core/messages";
import * as dotenv from "dotenv";
// 加载环境变量
dotenv.config();
/**
 * 创建 MiniMax 模型实例 (使用 Anthropic API 兼容模式)
 */
function createMiniMaxModel(modelName = "claude-3-5-sonnet-20241022", temperature = 0.7) {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    const baseURL = process.env.ANTHROPIC_BASE_URL || "https://api.minimaxi.com/anthropic";
    if (!apiKey) {
        throw new Error("请设置 ANTHROPIC_API_KEY 环境变量");
    }
    return new ChatAnthropic({
        model: modelName,
        temperature,
        apiKey: apiKey,
        clientOptions: {
            baseURL: baseURL,
        },
    });
}
/**
 * 工作流图
 */
class WorkflowGraph {
    constructor(initialState = {}) {
        this.nodes = new Map();
        this.edges = new Map();
        this.state = {
            current: "start",
            data: initialState,
            history: [],
            metadata: {},
        };
        this.model = createMiniMaxModel();
    }
    /**
     * 添加节点
     */
    addNode(node) {
        this.nodes.set(node.name, node);
        console.log(`✅ 添加节点: ${node.name}`);
    }
    /**
     * 添加边（连接节点）
     */
    addEdge(from, to) {
        const targets = Array.isArray(to) ? to : [to];
        const existing = this.edges.get(from) || [];
        this.edges.set(from, [...new Set([...existing, ...targets])]);
        console.log(`✅ 添加边: ${from} -> ${targets.join(', ')}`);
    }
    /**
     * 获取状态
     */
    getState() {
        return this.state;
    }
    /**
     * 更新状态数据
     */
    updateData(key, value) {
        this.state.data[key] = value;
    }
    /**
     * 获取状态数据
     */
    getData(key) {
        return this.state.data[key];
    }
    /**
     * 添加历史记录
     */
    addHistory(node, result) {
        this.state.history.push({
            node,
            result: result.data,
            timestamp: Date.now(),
        });
    }
    /**
     * 执行工作流
     */
    execute() {
        return __awaiter(this, arguments, void 0, function* (maxIterations = 10) {
            console.log("\n🚀 开始执行工作流");
            console.log("=".repeat(60));
            let iteration = 0;
            while (iteration < maxIterations) {
                const currentNodeName = this.state.current;
                // 检查是否到达终止状态
                if (currentNodeName === "end" || currentNodeName === "done") {
                    console.log("✅ 工作流执行完成");
                    break;
                }
                // 获取当前节点
                const currentNode = this.nodes.get(currentNodeName);
                if (!currentNode) {
                    console.log(`⚠️ 节点 ${currentNodeName} 不存在，工作流终止`);
                    break;
                }
                console.log(`\n📍 执行节点: ${currentNodeName} (迭代 ${iteration + 1})`);
                console.log("─".repeat(60));
                // 执行节点
                try {
                    const result = yield currentNode.execute(this.state);
                    this.addHistory(currentNodeName, result);
                    // 更新状态数据
                    Object.assign(this.state.data, result.data);
                    // 转移到下一状态
                    if (!result.shouldContinue) {
                        console.log("🛑 节点请求终止工作流");
                        break;
                    }
                    // 验证下一状态是否有效
                    const possibleNextStates = this.edges.get(currentNodeName) || [];
                    if (possibleNextStates.length > 0 && !possibleNextStates.includes(result.nextState)) {
                        console.log(`⚠️ 无效的状态转移: ${currentNodeName} -> ${result.nextState}`);
                        console.log(`   可选的下一状态: ${possibleNextStates.join(', ')}`);
                        break;
                    }
                    this.state.current = result.nextState;
                    console.log(`➡️ 转移到: ${result.nextState}`);
                }
                catch (error) {
                    console.error(`❌ 执行节点 ${currentNodeName} 时出错:`, error.message);
                    break;
                }
                iteration++;
            }
            if (iteration >= maxIterations) {
                console.log(`⚠️ 达到最大迭代次数 (${maxIterations})，工作流终止`);
            }
            console.log("\n" + "=".repeat(60));
            console.log("📊 工作流执行统计:");
            console.log(`   总迭代次数: ${iteration}`);
            console.log(`   历史记录数: ${this.state.history.length}`);
            console.log(`   最终状态: ${this.state.current}`);
            console.log("=".repeat(60) + "\n");
            return this.state;
        });
    }
    /**
     * 获取执行历史
     */
    getHistory() {
        return this.state.history;
    }
    /**
     * 重置状态
     */
    reset(initialData) {
        this.state = {
            current: "start",
            data: initialData || {},
            history: [],
            metadata: {},
        };
        console.log("🔄 工作流状态已重置");
    }
}
/**
 * 示例工作流节点：内容审核工作流
 */
// 开始节点
class StartNode {
    constructor() {
        this.name = "start";
    }
    execute(state) {
        return __awaiter(this, void 0, void 0, function* () {
            console.log("📝 初始化工作流");
            const content = state.data.content;
            if (!content) {
                throw new Error("缺少必要的内容数据");
            }
            console.log(`输入内容: ${content.substring(0, 100)}...`);
            return {
                nextState: "safety_check",
                data: { originalContent: content },
                shouldContinue: true,
            };
        });
    }
}
// 安全检查节点
class SafetyCheckNode {
    constructor() {
        this.name = "safety_check";
        this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.1);
    }
    execute(state) {
        return __awaiter(this, void 0, void 0, function* () {
            console.log("🔍 执行安全检查");
            const content = state.data.originalContent;
            const prompt = `检查以下内容是否包含不当、有害或敏感信息。

内容：${content}

请仅回答 "安全" 或 "不安全"，不要有其他内容。`;
            const response = yield this.model.invoke([
                new HumanMessage("你是一个内容安全审核专家，负责检测不当内容。\n\n" + prompt),
            ]);
            const result = typeof response.content === 'string'
                ? response.content.toLowerCase()
                : String(response.content).toLowerCase();
            const isSafe = result.includes("安全");
            console.log(`安全检查结果: ${isSafe ? "通过 ✅" : "未通过 ❌"}`);
            return {
                nextState: isSafe ? "quality_check" : "reject",
                data: { safetyCheck: { passed: isSafe, reason: isSafe ? "" : "内容存在安全问题" } },
                shouldContinue: true,
            };
        });
    }
}
// 质量检查节点
class QualityCheckNode {
    constructor() {
        this.name = "quality_check";
        this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.2);
    }
    execute(state) {
        return __awaiter(this, void 0, void 0, function* () {
            console.log("📊 执行质量检查");
            const content = state.data.originalContent;
            const prompt = `评估以下内容的质量，从以下维度打分（1-10分）：
1. 准确性
2. 完整性
3. 可读性
4. 实用性

内容：${content}

请以 JSON 格式返回评分，例如：
{
  "accuracy": 8,
  "completeness": 7,
  "readability": 9,
  "usefulness": 8,
  "overall": 8
}`;
            const response = yield this.model.invoke([
                new HumanMessage("你是一个内容质量评估专家。\n\n" + prompt),
            ]);
            let scores = { accuracy: 5, completeness: 5, readability: 5, usefulness: 5, overall: 5 };
            try {
                const content = typeof response.content === 'string'
                    ? response.content
                    : String(response.content);
                // 尝试提取 JSON
                const jsonMatch = content.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    scores = JSON.parse(jsonMatch[0]);
                }
            }
            catch (e) {
                console.log("⚠️ 无法解析评分，使用默认分数");
            }
            const overallScore = scores.overall || 5;
            const passed = overallScore >= 6;
            console.log(`质量检查结果: ${overallScore}/10 ${passed ? "通过 ✅" : "未通过 ❌"}`);
            return {
                nextState: passed ? "enhance" : "reject",
                data: { qualityCheck: { passed, scores } },
                shouldContinue: true,
            };
        });
    }
}
// 内容增强节点
class EnhanceNode {
    constructor() {
        this.name = "enhance";
        this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.5);
    }
    execute(state) {
        return __awaiter(this, void 0, void 0, function* () {
            console.log("✨ 执行内容增强");
            const content = state.data.originalContent;
            const prompt = `对以下内容进行优化和增强，使其更加清晰、专业和有用。

原始内容：${content}

请提供增强后的内容，保持原意但改进表达。`;
            const response = yield this.model.invoke([
                new HumanMessage("你是一个专业的内容编辑，擅长优化和改进文本内容。\n\n" + prompt),
            ]);
            const enhancedContent = typeof response.content === 'string'
                ? response.content
                : String(response.content);
            console.log(`内容增强完成`);
            return {
                nextState: "approve",
                data: { enhancedContent },
                shouldContinue: true,
            };
        });
    }
}
// 批准节点
class ApproveNode {
    constructor() {
        this.name = "approve";
    }
    execute(state) {
        return __awaiter(this, void 0, void 0, function* () {
            console.log("✅ 内容已批准");
            const enhancedContent = state.data.enhancedContent || state.data.originalContent;
            return {
                nextState: "end",
                data: {
                    finalContent: enhancedContent,
                    status: "approved",
                    approvedAt: new Date().toISOString(),
                },
                shouldContinue: true,
            };
        });
    }
}
// 拒绝节点
class RejectNode {
    constructor() {
        this.name = "reject";
    }
    execute(state) {
        return __awaiter(this, void 0, void 0, function* () {
            var _a, _b;
            console.log("❌ 内容已拒绝");
            const reason = ((_a = state.data.qualityCheck) === null || _a === void 0 ? void 0 : _a.passed) === false
                ? "质量检查未通过"
                : ((_b = state.data.safetyCheck) === null || _b === void 0 ? void 0 : _b.passed) === false
                    ? state.data.safetyCheck.reason || "安全检查未通过"
                    : "未通过审核";
            return {
                nextState: "end",
                data: {
                    status: "rejected",
                    rejectionReason: reason,
                    rejectedAt: new Date().toISOString(),
                },
                shouldContinue: true,
            };
        });
    }
}
/**
 * 创建内容审核工作流
 */
function createContentModerationWorkflow() {
    const workflow = new WorkflowGraph();
    // 添加节点
    workflow.addNode(new StartNode());
    workflow.addNode(new SafetyCheckNode());
    workflow.addNode(new QualityCheckNode());
    workflow.addNode(new EnhanceNode());
    workflow.addNode(new ApproveNode());
    workflow.addNode(new RejectNode());
    // 添加边
    workflow.addEdge("start", "safety_check");
    workflow.addEdge("safety_check", ["quality_check", "reject"]);
    workflow.addEdge("quality_check", ["enhance", "reject"]);
    workflow.addEdge("enhance", "approve");
    workflow.addEdge("approve", "end");
    workflow.addEdge("reject", "end");
    return workflow;
}
/**
 * 内容审核工作流演示
 */
function contentModerationDemo() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("🚀 LangGraph 工作流演示 - 内容审核工作流");
        console.log("基于 LangChain 官方教程: LangGraph\n");
        try {
            // 创建工作流
            const workflow = createContentModerationWorkflow();
            // 测试案例
            const testCases = [
                {
                    name: "高质量内容",
                    content: "TypeScript 是一种由微软开发的自由和开源的编程语言。它是 JavaScript 的一个超集，而且本质上向这个语言添加了可选的静态类型和基于类的面向对象编程。TypeScript 为大型项目提供了更好的工具支持和代码可维护性。",
                },
                {
                    name: "低质量内容",
                    content: "ts 好用 学它 有用 编程 喜欢",
                },
            ];
            for (const testCase of testCases) {
                console.log(`\n📋 测试案例: ${testCase.name}`);
                console.log("=".repeat(60));
                console.log(`内容: ${testCase.content}\n`);
                // 重置工作流并设置测试数据
                workflow.reset({ content: testCase.content });
                // 执行工作流
                const finalState = yield workflow.execute();
                // 显示结果
                console.log("\n📊 最终结果:");
                console.log("─".repeat(60));
                console.log(`状态: ${finalState.data.status}`);
                if (finalState.data.status === "approved") {
                    console.log(`最终内容: ${finalState.data.finalContent}`);
                    console.log(`批准时间: ${finalState.data.approvedAt}`);
                }
                else {
                    console.log(`拒绝原因: ${finalState.data.rejectionReason}`);
                    console.log(`拒绝时间: ${finalState.data.rejectedAt}`);
                }
                // 显示执行历史
                console.log("\n📜 执行历史:");
                console.log("─".repeat(60));
                for (let i = 0; i < finalState.history.length; i++) {
                    const record = finalState.history[i];
                    console.log(`${i + 1}. ${record.node} - ${new Date(record.timestamp).toLocaleTimeString()}`);
                }
                yield new Promise(resolve => setTimeout(resolve, 2000)); // API限流延迟
            }
            console.log("\n✅ 工作流演示完成！");
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
/**
 * 自定义工作流演示
 */
function customWorkflowDemo() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("\n\n🔧 自定义工作流演示 - 文章生成流程");
        console.log("=".repeat(60) + "\n");
        // 创建自定义工作流
        const workflow = new WorkflowGraph();
        // 研究节点
        class ResearchNode {
            constructor() {
                this.name = "research";
                this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.3);
            }
            execute(state) {
                return __awaiter(this, void 0, void 0, function* () {
                    console.log("🔍 研究阶段");
                    const topic = state.data.topic;
                    const prompt = `为"${topic}"这个主题提供关键的研究要点，包括：
1. 核心概念
2. 主要特点
3. 应用场景
4. 发展趋势

请以简洁的要点形式回答。`;
                    const response = yield this.model.invoke([
                        new HumanMessage("你是一个专业的研究员，擅长提取关键信息。\n\n" + prompt),
                    ]);
                    const research = typeof response.content === 'string'
                        ? response.content
                        : String(response.content);
                    return {
                        nextState: "outline",
                        data: { research },
                        shouldContinue: true,
                    };
                });
            }
        }
        // 大纲节点
        class OutlineNode {
            constructor() {
                this.name = "outline";
                this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.4);
            }
            execute(state) {
                return __awaiter(this, void 0, void 0, function* () {
                    console.log("📝 大纲设计");
                    const topic = state.data.topic;
                    const research = state.data.research;
                    const prompt = `基于以下研究内容，为"${topic}"设计一个文章大纲：

研究内容：
${research}

请提供一个结构清晰的文章大纲。`;
                    const response = yield this.model.invoke([
                        new HumanMessage("你是一个专业的内容策划，擅长设计文章结构。\n\n" + prompt),
                    ]);
                    const outline = typeof response.content === 'string'
                        ? response.content
                        : String(response.content);
                    return {
                        nextState: "write",
                        data: { outline },
                        shouldContinue: true,
                    };
                });
            }
        }
        // 写作节点
        class WriteNode {
            constructor() {
                this.name = "write";
                this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.7);
            }
            execute(state) {
                return __awaiter(this, void 0, void 0, function* () {
                    console.log("✍️ 内容写作");
                    const topic = state.data.topic;
                    const outline = state.data.outline;
                    const prompt = `基于以下大纲，写一篇关于"${topic}"的文章：

大纲：
${outline}

要求：
1. 内容丰富，观点明确
2. 结构清晰，逻辑连贯
3. 语言生动，易于理解
4. 字数控制在500字左右`;
                    const response = yield this.model.invoke([
                        new HumanMessage("你是一个专业的内容创作者，擅长撰写高质量文章。\n\n" + prompt),
                    ]);
                    const article = typeof response.content === 'string'
                        ? response.content
                        : String(response.content);
                    return {
                        nextState: "review",
                        data: { article },
                        shouldContinue: true,
                    };
                });
            }
        }
        // 审核节点
        class ReviewNode {
            constructor() {
                this.name = "review";
                this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.2);
            }
            execute(state) {
                return __awaiter(this, void 0, void 0, function* () {
                    console.log("🔎 内容审核");
                    const article = state.data.article;
                    const prompt = `审核以下文章，提供评估意见：

文章内容：
${article}

请从以下维度评估：
1. 内容质量（1-10分）
2. 结构完整性（1-10分）
3. 语言表达（1-10分）
4. 是否需要修改

请以 JSON 格式返回评估结果。`;
                    const response = yield this.model.invoke([
                        new HumanMessage("你是一个专业的内容审核员。\n\n" + prompt),
                    ]);
                    let review = { quality: 7, structure: 7, expression: 7, needsRevision: false };
                    try {
                        const content = typeof response.content === 'string'
                            ? response.content
                            : String(response.content);
                        const jsonMatch = content.match(/\{[\s\S]*\}/);
                        if (jsonMatch) {
                            review = Object.assign(Object.assign({}, review), JSON.parse(jsonMatch[0]));
                        }
                    }
                    catch (e) {
                        console.log("⚠️ 无法解析审核结果，使用默认值");
                    }
                    console.log(`审核结果: 质量 ${review.quality}/10`);
                    return {
                        nextState: review.needsRevision ? "write" : "end",
                        data: { review, needsRevision: review.needsRevision },
                        shouldContinue: !review.needsRevision || state.data.revisionCount < 2,
                    };
                });
            }
        }
        // 添加节点
        workflow.addNode(new ResearchNode());
        workflow.addNode(new OutlineNode());
        workflow.addNode(new WriteNode());
        workflow.addNode(new ReviewNode());
        // 添加边
        workflow.addEdge("start", "research");
        workflow.addEdge("research", "outline");
        workflow.addEdge("outline", "write");
        workflow.addEdge("write", "review");
        workflow.addEdge("review", ["write", "end"]);
        // 执行工作流
        workflow.reset({ topic: "AI Agent 的未来发展趋势", revisionCount: 0 });
        const finalState = yield workflow.execute(15);
        console.log("\n📊 最终结果:");
        console.log("─".repeat(60));
        if (finalState.data.article) {
            console.log(finalState.data.article);
        }
        console.log("\n✅ 自定义工作流演示完成！");
    });
}
/**
 * 主函数
 */
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        // 运行内容审核工作流演示
        yield contentModerationDemo();
        // 运行自定义工作流演示
        yield customWorkflowDemo();
    });
}
// 执行主函数
main();
//# sourceMappingURL=langgraph-workflow.js.map