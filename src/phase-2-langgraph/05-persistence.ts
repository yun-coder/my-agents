/**
 * ========================================
 * Phase 2: LangGraph 进阶
 * Demo 05: Persistence - 状态持久化
 * ========================================
 *
 * 学习目标:
 * - 理解 Checkpoint 机制
 * - 掌握状态保存和恢复
 * - 学习记忆管理
 * - 实现长时间运行的工作流
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph-checkpoint";
import { BaseMessage, HumanMessage, AIMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 基础 Checkpoint - MemorySaver
// ============================================================================

console.log("=== 1. 基础 Checkpoint ===\n");

const PersistState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  step: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
});

type PersistStateType = typeof PersistState.State;

const step1Node = async (state: PersistStateType): Promise<Partial<PersistStateType>> => {
  console.log(`[步骤1] 当前 step: ${state.step}`);
  await new Promise((resolve) => setTimeout(resolve, 100));
  return {
    step: 1,
    messages: [new HumanMessage("步骤1完成")],
  };
};

const step2Node = async (state: PersistStateType): Promise<Partial<PersistStateType>> => {
  console.log(`[步骤2] 当前 step: ${state.step}`);
  await new Promise((resolve) => setTimeout(resolve, 100));
  return {
    step: 2,
    messages: [new HumanMessage("步骤2完成")],
  };
};

const step3Node = async (state: PersistStateType): Promise<Partial<PersistStateType>> => {
  console.log(`[步骤3] 当前 step: ${state.step}`);
  await new Promise((resolve) => setTimeout(resolve, 100));
  return {
    step: 3,
    messages: [new HumanMessage("步骤3完成")],
  };
};

// 创建带 checkpointer 的图
const checkpointer = new MemorySaver();

const persistGraph = new StateGraph({ stateSchema: PersistState })
  .addNode("step1", step1Node)
  .addNode("step2", step2Node)
  .addNode("step3", step3Node)
  .addEdge(START, "step1")
  .addEdge("step1", "step2")
  .addEdge("step2", "step3")
  .addEdge("step3", END);

const persistApp = persistGraph.compile({ checkpointer });

console.log("执行流程 (thread_id: demo-1):");
const config = { configurable: { thread_id: "demo-1" } };

// 第一次执行
console.log("\n--- 第一次执行 ---");
const result1 = await persistApp.invoke({}, config);
console.log(`最终 step: ${result1.step}`);
console.log(`消息数: ${result1.messages.length}`);

// 从 checkpoint 获取状态
console.log("\n--- 获取 checkpoint ---");
const state = await persistApp.getState(config);
console.log(`当前 step: ${state.values.step}`);
console.log(`消息数: ${state.values.messages.length}`);

// ============================================================================
// 2. 暂停和恢复
// ============================================================================

console.log("\n=== 2. 暂停和恢复 ===\n");

const PauseState = Annotation.Root({
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  processed: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  approved: Annotation<boolean>({
    reducer: (x, y) => y ?? x,
    default: () => false,
  }),
});

type PauseStateType = typeof PauseState.State;

const processNode = async (state: PauseStateType): Promise<Partial<PauseStateType>> => {
  console.log(`[处理] 输入: ${state.input}`);
  const processed = `已处理: ${state.input}`;
  return {
    processed: [processed],
  };
};

const reviewNode = (state: PauseStateType): Partial<PauseStateType> => {
  console.log(`[审核] 等待人工审核...`);
  return {}; // 暂停等待
};

const finalNode = (state: PauseStateType): Partial<PauseStateType> => {
  console.log(`[完成] 流程结束`);
  return {};
};

const shouldContinue = (state: PauseStateType): string => {
  return state.approved ? "finish" : "wait";
};

const pauseGraph = new StateGraph({ stateSchema: PauseState })
  .addNode("process", processNode)
  .addNode("review", reviewNode)
  .addNode("finish", finalNode)
  .addEdge(START, "process")
  .addEdge("process", "review")
  .addConditionalEdges("review", shouldContinue, {
    wait: END,
    finish: "finish",
  })
  .addEdge("finish", END);

const pauseApp = pauseGraph.compile({ checkpointer });

const pauseConfig = { configurable: { thread_id: "pause-demo" } };

// 第一次运行 - 会暂停在 review 节点
console.log("--- 第一次运行 (暂停) ---");
const pauseResult1 = await pauseApp.invoke(
  { input: "重要文档" },
  pauseConfig
);
console.log("状态:", pauseResult1);

// 获取当前状态
const pauseState = await pauseApp.getState(pauseConfig);
console.log("当前节点:", pauseState.next);

// 模拟人工审核后恢复
console.log("\n--- 人工审核通过后恢复 ---");
const pauseResult2 = await pauseApp.invoke(
  { approved: true },
  pauseConfig
);
console.log("最终结果:", pauseResult2);

// ============================================================================
// 3. 多会话管理
// ============================================================================

console.log("\n=== 3. 多会话管理 ===\n");

const ChatState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  userId: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type ChatStateType = typeof ChatState.State;

const chatNode = async (state: ChatStateType): Promise<Partial<ChatStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.7 });
  const lastMessage = state.messages[state.messages.length - 1];

  console.log(`[${state.userId}] 处理消息: ${(lastMessage as HumanMessage).content}`);

  const response = await llm.invoke(state.messages);
  return {
    messages: [response as AIMessage],
  };
};

const chatGraph = new StateGraph({ stateSchema: ChatState })
  .addNode("chat", chatNode)
  .addEdge(START, "chat")
  .addEdge("chat", END);

const chatApp = chatGraph.compile({ checkpointer });

// 模拟多个用户
const users = ["user-001", "user-002"];

for (const userId of users) {
  const config = { configurable: { thread_id: userId } };

  console.log(`\n--- 用户 ${userId} ---`);

  // 第一轮对话
  await chatApp.invoke(
    {
      userId,
      messages: [new HumanMessage(`我是 ${userId}，你好！`)],
    },
    config
  );

  // 第二轮对话
  await chatApp.invoke(
    {
      userId,
      messages: [new HumanMessage("我叫什么名字？")],
    },
    config
  );

  // 查看历史
  const chatState = await chatApp.getState(config);
  console.log(`历史消息数: ${chatState.values.messages.length}`);
}

// ============================================================================
// 4. 时间旅行 - 回滚到之前的状态
// ============================================================================

console.log("\n=== 4. 时间旅行 ===\n");

const TimeTravelState = Annotation.Root({
  step: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  data: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
});

type TimeTravelStateType = typeof TimeTravelState.State;

const addStepNode = (state: TimeTravelStateType): Partial<TimeTravelStateType> => {
  const newStep = state.step + 1;
  const newData = `步骤${newStep}数据`;
  console.log(`[步骤${newStep}] 添加: ${newData}`);
  return {
    step: newStep,
    data: [newData],
  };
};

const timeTravelGraph = new StateGraph({ stateSchema: TimeTravelState })
  .addNode("addStep", addStepNode)
  .addEdge(START, "addStep")
  .addEdge("addStep", "addStep"); // 循环

const timeTravelApp = timeTravelGraph.compile({ checkpointer });

const ttConfig = { configurable: { thread_id: "time-travel" } };

// 执行3步
console.log("--- 执行 3 步 ---");
for (let i = 0; i < 3; i++) {
  await timeTravelApp.invoke({}, ttConfig);
}

const state3 = await timeTravelApp.getState(ttConfig);
console.log(`状态: step=${state3.values.step}, data=${JSON.stringify(state3.values.data)}`);

// 获取历史 checkpoint
console.log("\n--- 查看 checkpoint 历史 ---");
const checkpointConfig = { configurable: { thread_id: "time-travel" } };

// 回滚到步骤2
console.log("\n--- 回滚到步骤 2 ---");
// 注意: 实际实现需要使用 checkpoint ID
// 这里简化演示

// ============================================================================
// 5. 长时间运行的工作流
// ============================================================================

console.log("\n=== 5. 长时间运行的工作流 ===\n");

const LongRunningState = Annotation.Root({
  taskId: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  status: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  progress: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  result: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type LongRunningStateType = typeof LongRunningState.State;

const startTaskNode = (state: LongRunningStateType): Partial<LongRunningStateType> => {
  console.log(`[启动] 任务: ${state.taskId}`);
  return {
    status: "running",
    progress: 0,
  };
};

const updateProgressNode = async (state: LongRunningStateType): Promise<Partial<LongRunningStateType>> => {
  const newProgress = state.progress + 25;
  console.log(`[进度] ${state.progress}% → ${newProgress}%`);
  await new Promise((resolve) => setTimeout(resolve, 200));

  if (newProgress >= 100) {
    return {
      progress: newProgress,
      status: "completed",
      result: `任务 ${state.taskId} 完成`,
    };
  }
  return { progress: newProgress };
};

const longRunningGraph = new StateGraph({ stateSchema: LongRunningState })
  .addNode("start", startTaskNode)
  .addNode("update", updateProgressNode)
  .addEdge(START, "start")
  .addEdge("start", "update")
  .addConditionalEdges("update", (state) => (state.status === "completed" ? "end" : "continue"), {
    continue: "update",
    end: END,
  });

const longRunningApp = longRunningGraph.compile({ checkpointer });

const lrConfig = { configurable: { thread_id: "long-task" } };

// 启动长时间任务
console.log("--- 启动长时间任务 ---");
const lrResult = await longRunningApp.invoke(
  { taskId: "task-001" },
  { ...lrConfig, streamMode: "values" } as any
);
console.log(`\n最终状态:`, lrResult);

// ============================================================================
// 总结
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. MemorySaver - 内存中的 checkpointer");
console.log("2. 暂停恢复 - 人工审核和干预");
console.log("3. 多会话 - 不同用户的独立状态");
console.log("4. 时间旅行 - 回滚到历史状态");
console.log("5. 长时间任务 - 跨时段的工作流");
console.log("\nCheckpoint 使用场景:");
console.log("- 人机协作: 需要人工审核的流程");
console.log("- 长时间任务: 跨天或跨周的流程");
console.log("- 错误恢复: 失败后从断点恢复");
console.log("- 多用户会话: 每个用户独立状态");
console.log("- 时间旅行: 实验和回滚");

export { persistApp, pauseApp, chatApp, timeTravelApp, longRunningApp };
