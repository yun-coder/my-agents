import { BaseMessage } from "@langchain/core/messages";

/**
 * 通用类型定义
 * 用于所有 demo 的类型共享
 */

/**
 * 基础 Agent 状态
 */
export interface BaseAgentState {
  messages: BaseMessage[];
  input?: string;
  output?: string;
}

/**
 * 工具调用结果
 */
export interface ToolResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

/**
 * Agent 思考步骤
 */
export interface ThoughtStep {
  step: number;
  thought: string;
  action?: string;
  observation?: string;
}

/**
 * 多智能体团队状态
 */
export interface TeamState extends BaseAgentState {
  next: string;
  members: string[];
  currentMember?: string;
}

/**
 * 工作流节点
 */
export interface WorkflowNode {
  name: string;
  description: string;
  execute: (state: BaseAgentState) => Promise<BaseAgentState>;
}

/**
 * 条件边函数
 */
export type ConditionalEdge<T = BaseAgentState> = (state: T) => string | Promise<string>;

/**
 * 图节点函数
 */
export type GraphNode<T = BaseAgentState> = (state: T) => Promise<Partial<T>>;

/**
 * 工具定义
 */
export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  func: (...args: unknown[]) => Promise<string>;
}
