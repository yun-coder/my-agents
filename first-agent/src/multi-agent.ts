/**
 * LangChain 多 Agent 协作 Demo
 * 基于 LangChain 官方教程: Multi-agent
 *
 * 学习资源: https://docs.langchain.com/oss/javascript/tutorials/multi_agent
 *
 * 功能特性:
 * - 多个专业 Agent 协作
 * - Agent 任务分配
 * - 结果聚合和验证
 * - 使用 MiniMax 模型实现
 */

import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import * as dotenv from "dotenv";

// 加载环境变量
dotenv.config();

/**
 * 创建 MiniMax 模型实例 (使用 Anthropic API 兼容模式)
 */
function createMiniMaxModel(modelName: string = "MiniMax-M2.7", temperature: number = 0.7) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  const baseURL = process.env.ANTHROPIC_BASE_URL;

  if (!apiKey) {
    throw new Error("请设置 ANTHROPIC_API_KEY 环境变量");
  }

  return new ChatAnthropic({
    model: modelName,
    temperature,
    topP: 1.0,
    apiKey: apiKey,
    clientOptions: {
      baseURL: baseURL,
    },
  });
}

/**
 * Agent 基础接口
 */
interface Agent {
  name: string;
  role: string;
  description: string;
  model: ChatAnthropic;
  execute(task: string, context?: string): Promise<string>;
}

/**
 * 研究员 Agent
 */
class ResearcherAgent implements Agent {
  name = "研究员";
  role = "researcher";
  description = "负责收集和分析信息，提供背景资料和研究数据";
  model: ChatAnthropic;

  constructor() {
    this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.3);
  }

  async execute(task: string, context?: string): Promise<string> {
    console.log(`🔍 ${this.name} 正在研究: ${task}`);

    const prompt = context
      ? `作为研究员，请分析以下任务并提供详细的背景信息和相关数据：

任务：${task}

上下文信息：
${context}

请提供：
1. 相关背景信息
2. 关键数据和事实
3. 现有研究成果
4. 需要进一步研究的问题

用清晰的格式组织你的回答。`
      : `作为研究员，请分析以下任务并提供详细的背景信息和相关数据：

任务：${task}

请提供：
1. 相关背景信息
2. 关键数据和事实
3. 现有研究成果
4. 需要进一步研究的问题

用清晰的格式组织你的回答。`;

    const response = await this.model.invoke([
      new SystemMessage(`你是一位专业的研究员，擅长收集和分析信息，提供准确、详实的背景资料。`),
      new HumanMessage(prompt),
    ]);

    const content = typeof response.content === 'string'
      ? response.content
      : String(response.content);

    console.log(`✅ ${this.name} 完成研究\n`);
    return content;
  }
}

/**
 * 分析师 Agent
 */
class AnalystAgent implements Agent {
  name = "分析师";
  role = "analyst";
  description = "负责分析数据，识别模式和趋势，提供洞察";
  model: ChatAnthropic;

  constructor() {
    this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.4);
  }

  async execute(task: string, context?: string): Promise<string> {
    console.log(`📊 ${this.name} 正在分析: ${task}`);

    const prompt = context
      ? `作为分析师，请基于以下研究数据进行深入分析：

任务：${task}

研究数据：
${context}

请提供：
1. 关键发现和洞察
2. 数据模式和趋势
3. 潜在机会和风险
4. 基于数据的建议

用数据支撑你的分析。`
      : `作为分析师，请分析以下任务：

任务：${task}

请提供：
1. 可能的关键指标
2. 分析方法建议
3. 需要关注的数据点
4. 初步分析框架`;

    const response = await this.model.invoke([
      new SystemMessage(`你是一位专业的数据分析师，擅长从数据中发现模式、趋势和洞察，提供基于数据的建议。`),
      new HumanMessage(prompt),
    ]);

    const content = typeof response.content === 'string'
      ? response.content
      : String(response.content);

    console.log(`✅ ${this.name} 完成分析\n`);
    return content;
  }
}

/**
 * 策划师 Agent
 */
class StrategistAgent implements Agent {
  name = "策划师";
  role = "strategist";
  description = "负责制定策略和规划，设计解决方案";
  model: ChatAnthropic;

  constructor() {
    this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.5);
  }

  async execute(task: string, context?: string): Promise<string> {
    console.log(`🎯 ${this.name} 正在制定策略: ${task}`);

    const prompt = context
      ? `作为策划师，请基于研究和分析结果制定详细的策略：

任务：${task}

研究和分析结果：
${context}

请提供：
1. 总体策略方向
2. 具体行动计划
3. 资源分配建议
4. 时间线和里程碑
5. 风险评估和应对措施

确保策略具有可操作性和实用性。`
      : `作为策划师，请为以下任务制定初步策略：

任务：${task}

请提供：
1. 初步策略框架
2. 关键行动点
3. 需要考虑的因素
4. 策略制定的思路`;

    const response = await this.model.invoke([
      new SystemMessage(`你是一位资深的策略规划师，擅长制定清晰、可执行的战略计划，平衡理想与现实。`),
      new HumanMessage(prompt),
    ]);

    const content = typeof response.content === 'string'
      ? response.content
      : String(response.content);

    console.log(`✅ ${this.name} 完成策略制定\n`);
    return content;
  }
}

/**
 * 审核员 Agent
 */
class ReviewerAgent implements Agent {
  name = "审核员";
  role = "reviewer";
  description = "负责审核和验证结果，确保质量";
  model: ChatAnthropic;

  constructor() {
    this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.2);
  }

  async execute(task: string, context?: string): Promise<string> {
    console.log(`🔎 ${this.name} 正在审核: ${task}`);

    const prompt = context
      ? `作为审核员，请全面评估以下工作的质量：

原始任务：${task}

工作成果：
${context}

请从以下维度进行评估：
1. 完整性：是否完整回应了任务需求
2. 准确性：信息是否准确，逻辑是否严密
3. 可行性：建议和策略是否可执行
4. 质量：输出内容的整体质量

提供：
1. 总体评价（优/良/中/差）
2. 具体优点
3. 需要改进的地方
4. 最终建议（通过/需要修改/重新做）`
      : `作为审核员，请评估以下任务的完成标准：

任务：${task}

请提供：
1. 任务完成的核心标准
2. 质量检查要点
3. 常见问题和风险
4. 验收建议`;

    const response = await this.model.invoke([
      new SystemMessage(`你是一位严格但公正的审核员，擅长发现问题和确保工作质量。你的评价应该客观、具体、有建设性。`),
      new HumanMessage(prompt),
    ]);

    const content = typeof response.content === 'string'
      ? response.content
      : String(response.content);

    console.log(`✅ ${this.name} 完成审核\n`);
    return content;
  }
}

/**
 * 协调器 Agent
 */
class CoordinatorAgent implements Agent {
  name = "协调器";
  role = "coordinator";
  description = "负责协调各 Agent 的工作，分配任务，整合结果";
  model: ChatAnthropic;
  private agents: Agent[];

  constructor() {
    this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.3);
    this.agents = [];
  }

  registerAgent(agent: Agent): void {
    this.agents.push(agent);
    console.log(`✅ 已注册 Agent: ${agent.name} (${agent.role})`);
  }

  getAgents(): Agent[] {
    return this.agents;
  }

  async execute(task: string, context?: string): Promise<string> {
    console.log(`🎛️ ${this.name} 正在协调任务: ${task}`);

    // 分析任务并分配给合适的 Agent
    const taskAnalysis = await this.analyzeTask(task);
    console.log(`📋 任务分析:\n${taskAnalysis}\n`);

    // 执行多阶段工作流
    const results = await this.executeWorkflow(task);

    // 整合结果
    const integration = await this.integrateResults(task, results);

    console.log(`✅ ${this.name} 完成协调\n`);
    return integration;
  }

  private async analyzeTask(task: string): Promise<string> {
    const availableAgents = this.agents
      .map(agent => `- ${agent.name}: ${agent.description}`)
      .join('\n');

    const prompt = `分析以下任务，确定需要哪些 Agent 参与以及工作流程：

任务：${task}

可用的 Agent：
${availableAgents}

请提供：
1. 任务类型和复杂度评估
2. 需要参与的 Agent（按优先级排序）
3. 建议的工作流程
4. 预期的输出

用简洁清晰的格式回答。`;

    const response = await this.model.invoke([
      new SystemMessage(`你是一位项目经理，擅长分析任务、分配资源和规划工作流程。`),
      new HumanMessage(prompt),
    ]);

    return typeof response.content === 'string'
      ? response.content
      : String(response.content);
  }

  private async executeWorkflow(task: string): Promise<Map<string, string>> {
    const results = new Map<string, string>();

    // 阶段 1: 研究阶段
    const researcher = this.agents.find(a => a.role === "researcher");
    if (researcher) {
      const researchResult = await researcher.execute(task);
      results.set("research", researchResult);
      await this.delay(1000); // 避免API限流
    }

    // 阶段 2: 分析阶段
    const analyst = this.agents.find(a => a.role === "analyst");
    if (analyst && results.has("research")) {
      const analysisResult = await analyst.execute(task, results.get("research"));
      results.set("analysis", analysisResult);
      await this.delay(1000);
    }

    // 阶段 3: 策划阶段
    const strategist = this.agents.find(a => a.role === "strategist");
    if (strategist && results.has("analysis")) {
      const combinedContext = `研究结果：\n${results.get("research")}\n\n分析结果：\n${results.get("analysis")}`;
      const strategyResult = await strategist.execute(task, combinedContext);
      results.set("strategy", strategyResult);
      await this.delay(1000);
    }

    // 阶段 4: 审核阶段
    const reviewer = this.agents.find(a => a.role === "reviewer");
    if (reviewer && results.has("strategy")) {
      const fullContext = `研究成果：\n${results.get("research")}\n\n分析成果：\n${results.get("analysis")}\n\n策略方案：\n${results.get("strategy")}`;
      const reviewResult = await reviewer.execute(task, fullContext);
      results.set("review", reviewResult);
    }

    return results;
  }

  private async integrateResults(task: string, results: Map<string, string>): Promise<string> {
    const resultsText = Array.from(results.entries())
      .map(([stage, content]) => `## ${stage.toUpperCase()}\n${content}`)
      .join('\n\n');

    const prompt = `作为协调器，请整合以下所有 Agent 的工作成果，为原始任务提供最终的综合性答案：

原始任务：${task}

各 Agent 的工作成果：
${resultsText}

请提供：
1. 执行摘要（200字以内）
2. 关键发现和建议
3. 详细行动计划
4. 风险和注意事项

确保整合后的内容连贯、完整、可执行。`;

    const response = await this.model.invoke([
      new SystemMessage(`你是一位经验丰富的项目负责人，擅长整合多方意见，形成清晰、可执行的方案。`),
      new HumanMessage(prompt),
    ]);

    return typeof response.content === 'string'
      ? response.content
      : String(response.content);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * 多 Agent 协作演示
 */
async function multiAgentDemo() {
  console.log("🚀 LangChain 多 Agent 协作演示");
  console.log("基于 LangChain 官方教程: Multi-agent\n");

  try {
    // 创建协调器并注册 Agent
    const coordinator = new CoordinatorAgent();

    coordinator.registerAgent(new ResearcherAgent());
    coordinator.registerAgent(new AnalystAgent());
    coordinator.registerAgent(new StrategistAgent());
    coordinator.registerAgent(new ReviewerAgent());

    console.log(`\n📋 已注册 ${coordinator.getAgents().length} 个专业 Agent\n`);
    console.log("=".repeat(60));

    // 示例任务 1: 技术选型
    console.log("\n📌 任务 1: 技术选型建议");
    console.log("=".repeat(60));
    const task1 = "为一个中等规模的电商平台推荐前端技术栈，考虑性能、开发效率和团队规模";

    const result1 = await coordinator.execute(task1);

    console.log("\n📊 最终整合结果:");
    console.log("─".repeat(60));
    console.log(result1);
    console.log("─".repeat(60));

    await new Promise(resolve => setTimeout(resolve, 2000));

    // 示例任务 2: 产品规划
    console.log("\n\n📌 任务 2: AI 聊天机器人产品规划");
    console.log("=".repeat(60));
    const task2 = "规划一个面向开发者市场的 AI 聊天机器人产品，考虑市场需求、技术可行性和商业模式";

    const result2 = await coordinator.execute(task2);

    console.log("\n📊 最终整合结果:");
    console.log("─".repeat(60));
    console.log(result2);
    console.log("─".repeat(60));

    console.log("\n✅ 多 Agent 协作演示完成！");

  } catch (error: any) {
    console.error("\n❌ 执行出错:", error.message);
    console.error("\n请检查:");
    console.error("1. .env 文件中是否设置了 ANTHROPIC_API_KEY");
    console.error("2. API Key 是否正确");
    console.error("3. 网络连接是否正常");
    console.error("4. API 余额是否充足");
  }
}

/**
 * Agent 能力展示
 */
async function agentCapabilitiesDemo() {
  console.log("\n\n🔧 Agent 能力展示");
  console.log("=".repeat(60));

  const researcher = new ResearcherAgent();
  const analyst = new AnalystAgent();
  const strategist = new StrategistAgent();
  const reviewer = new ReviewerAgent();

  const sampleTask = "分析远程工作趋势";

  console.log(`\n任务: ${sampleTask}\n`);

  // 展示每个 Agent 的独特视角
  console.log("👥 各 Agent 的专业视角:");
  console.log("─".repeat(60));

  const research = await researcher.execute(sampleTask);
  console.log(`\n🔍 研究员视角:\n${research.substring(0, 200)}...\n`);

  await new Promise(resolve => setTimeout(resolve, 1000));

  const analysis = await analyst.execute(sampleTask, research);
  console.log(`📊 分析师视角:\n${analysis.substring(0, 200)}...\n`);

  await new Promise(resolve => setTimeout(resolve, 1000));

  const strategy = await strategist.execute(sampleTask, `${research}\n\n${analysis}`);
  console.log(`🎯 策划师视角:\n${strategy.substring(0, 200)}...\n`);

  await new Promise(resolve => setTimeout(resolve, 1000));

  const review = await reviewer.execute(sampleTask, strategy);
  console.log(`🔎 审核员视角:\n${review.substring(0, 200)}...\n`);
}

/**
 * 主函数
 */
async function main() {
  // 运行多 Agent 协作演示
  await multiAgentDemo();

  // 运行 Agent 能力展示
  await agentCapabilitiesDemo();
}

// 执行主函数
main();
