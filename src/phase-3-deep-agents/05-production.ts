/**
 * ========================================
 * Phase 3: Deep Agents 高级
 * Demo 05: Production Architecture - 生产级架构
 * ========================================
 *
 * 学习目标:
 * - 理解生产级多智能体系统设计
 * - 掌握监控、日志和可观测性
 * - 学习错误处理和恢复机制
 * - 实现可扩展和可维护的架构
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 日志和监控系统
// ============================================================================

console.log("=== 1. 日志和监控系统 ===\n");

enum LogLevel {
  DEBUG = "DEBUG",
  INFO = "INFO",
  WARN = "WARN",
  ERROR = "ERROR",
}

interface LogEntry {
  timestamp: Date;
  level: LogLevel;
  component: string;
  message: string;
  data?: unknown;
}

class Logger {
  private logs: LogEntry[] = [];

  log(level: LogLevel, component: string, message: string, data?: unknown) {
    const entry: LogEntry = {
      timestamp: new Date(),
      level,
      component,
      message,
      data,
    };

    this.logs.push(entry);

    const prefix = `[${entry.timestamp.toISOString()}] [${level}] [${component}]`;
    const logMessage = data ? `${prefix} ${message}\n  ${JSON.stringify(data, null, 2)}` : `${prefix} ${message}`;

    switch (level) {
      case LogLevel.ERROR:
        console.error(logMessage);
        break;
      case LogLevel.WARN:
        console.warn(logMessage);
        break;
      case LogLevel.DEBUG:
        console.debug(logMessage);
        break;
      default:
        console.log(logMessage);
    }
  }

  info(component: string, message: string, data?: unknown) {
    this.log(LogLevel.INFO, component, message, data);
  }

  warn(component: string, message: string, data?: unknown) {
    this.log(LogLevel.WARN, component, message, data);
  }

  error(component: string, message: string, data?: unknown) {
    this.log(LogLevel.ERROR, component, message, data);
  }

  debug(component: string, message: string, data?: unknown) {
    this.log(LogLevel.DEBUG, component, message, data);
  }

  getLogs(level?: LogLevel): LogEntry[] {
    return level ? this.logs.filter((l) => l.level === level) : this.logs;
  }

  clear() {
    this.logs = [];
  }
}

const logger = new Logger();

// ============================================================================
// 2. 指标收集系统
// ============================================================================

interface Metrics {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageLatency: number;
  agentExecutionCount: Record<string, number>;
  errorRate: number;
}

class MetricsCollector {
  private metrics: Metrics = {
    totalRequests: 0,
    successfulRequests: 0,
    failedRequests: 0,
    averageLatency: 0,
    agentExecutionCount: {},
    errorRate: 0,
  };

  private latencies: number[] = [];

  recordRequest(success: boolean, latency: number, agent?: string) {
    this.metrics.totalRequests++;

    if (success) {
      this.metrics.successfulRequests++;
    } else {
      this.metrics.failedRequests++;
    }

    this.latencies.push(latency);
    this.metrics.averageLatency = this.latencies.reduce((a, b) => a + b, 0) / this.latencies.length;

    this.metrics.errorRate = this.metrics.failedRequests / this.metrics.totalRequests;

    if (agent) {
      this.metrics.agentExecutionCount[agent] = (this.metrics.agentExecutionCount[agent] || 0) + 1;
    }
  }

  getMetrics(): Metrics {
    return { ...this.metrics };
  }

  reset() {
    this.metrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageLatency: 0,
      agentExecutionCount: {},
      errorRate: 0,
    };
    this.latencies = [];
  }
}

const metrics = new MetricsCollector();

// ============================================================================
// 3. 断路器模式
// ============================================================================

enum CircuitState {
  CLOSED = "CLOSED", // 正常工作
  OPEN = "OPEN", // 已熔断，拒绝请求
  HALF_OPEN = "HALF_OPEN", // 半开，尝试恢复
}

class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private lastFailureTime?: Date;
  private successCount = 0;

  constructor(
    private threshold: number = 5,
    private timeout: number = 60000, // 1分钟
    private halfOpenAttempts: number = 3
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitState.HALF_OPEN;
        logger.info("CircuitBreaker", "进入半开状态，尝试恢复");
      } else {
        throw new Error("Circuit breaker is OPEN, rejecting request");
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailureTime) return true;
    const now = new Date();
    return now.getTime() - this.lastFailureTime.getTime() > this.timeout;
  }

  private onSuccess() {
    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.halfOpenAttempts) {
        this.state = CircuitState.CLOSED;
        this.failureCount = 0;
        this.successCount = 0;
        logger.info("CircuitBreaker", "断路器已恢复，状态改为 CLOSED");
      }
    } else {
      this.failureCount = 0;
    }
  }

  private onFailure() {
    this.failureCount++;
    this.lastFailureTime = new Date();

    if (this.failureCount >= this.threshold) {
      this.state = CircuitState.OPEN;
      logger.error("CircuitBreaker", `断路器已打开，连续失败 ${this.failureCount} 次`);
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}

// ============================================================================
// 4. 重试机制
// ============================================================================

class RetryPolicy {
  async execute<T>(
    fn: () => Promise<T>,
    options: {
      maxAttempts?: number;
      baseDelay?: number;
      maxDelay?: number;
      backoffMultiplier?: number;
    } = {}
  ): Promise<T> {
    const {
      maxAttempts = 3,
      baseDelay = 1000,
      maxDelay = 10000,
      backoffMultiplier = 2,
    } = options;

    let lastError: Error | undefined;
    let delay = baseDelay;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        logger.warn("RetryPolicy", `第 ${attempt} 次尝试失败`, {
          error: lastError.message,
        });

        if (attempt < maxAttempts) {
          logger.info("RetryPolicy", `${delay}ms 后重试...`);
          await new Promise((resolve) => setTimeout(resolve, delay));
          delay = Math.min(delay * backoffMultiplier, maxDelay);
        }
      }
    }

    throw new Error(`所有 ${maxAttempts} 次尝试均失败: ${lastError?.message}`);
  }
}

const retryPolicy = new RetryPolicy();

// ============================================================================
// 5. 生产级状态和节点
// ============================================================================

const ProductionState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  output: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  errors: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  metadata: Annotation<Record<string, unknown>>({
    reducer: (x, y) => ({ ...x, ...y }),
    default: () => ({}),
  }),
});

type ProductionStateType = typeof ProductionState.State;

// 带监控和错误处理的节点
const createMonitoredNode = (
  name: string,
  fn: (state: ProductionStateType) => Promise<Partial<ProductionStateType>>,
  circuitBreaker: CircuitBreaker
) => {
  return async (state: ProductionStateType): Promise<Partial<ProductionStateType>> => {
    const startTime = Date.now();

    logger.info("Node", `开始执行节点: ${name}`, {
      input: state.input,
    });

    try {
      const result = await circuitBreaker.execute(async () => {
        return await retryPolicy.execute(async () => fn(state));
      });

      const latency = Date.now() - startTime;
      metrics.recordRequest(true, latency, name);

      logger.info("Node", `节点执行成功: ${name}`, {
        latency,
        outputKeys: Object.keys(result),
      });

      return {
        ...result,
        metadata: {
          ...state.metadata,
          [`${name}Latency`]: latency,
          [`${name}Success`]: true,
        },
      };
    } catch (error) {
      const latency = Date.now() - startTime;
      metrics.recordRequest(false, latency, name);

      const errorMessage = error instanceof Error ? error.message : String(error);

      logger.error("Node", `节点执行失败: ${name}`, {
        error: errorMessage,
        latency,
      });

      return {
        errors: [errorMessage],
        metadata: {
          ...state.metadata,
          [`${name}Latency`]: latency,
          [`${name}Success`]: false,
          [`${name}Error`]: errorMessage,
        },
      };
    }
  };
};

// ============================================================================
// 6. 构建生产级系统
// ============================================================================

console.log("构建生产级多智能体系统...\n");

// 为每个节点创建断路器
const primaryCircuitBreaker = new CircuitBreaker(5, 60000, 3);
const fallbackCircuitBreaker = new CircuitBreaker(3, 30000, 2);

// 主处理器
const primaryHandler = async (state: ProductionStateType): Promise<Partial<ProductionStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.7 });

  const response = await llm.invoke([
    new HumanMessage(`作为主要处理器，请处理: ${state.input}`),
  ]);

  return {
    output: response.content as string,
    messages: [new AIMessage(response.content as string)],
  };
};

// 降级处理器
const fallbackHandler = async (state: ProductionStateType): Promise<Partial<ProductionStateType>> => {
  // 简单的降级处理
  return {
    output: `[降级响应] 我们收到了您的请求: ${state.input}。系统正在处理中，请稍后重试以获得完整响应。`,
    messages: [new AIMessage("使用降级服务")],
  };
};

// 创建监控节点
const monitoredPrimary = createMonitoredNode("primary", primaryHandler, primaryCircuitBreaker);
const monitoredFallback = createMonitoredNode("fallback", fallbackHandler, fallbackCircuitBreaker);

// 错误处理节点
const errorHandler = (state: ProductionStateType): Partial<ProductionStateType> => {
  logger.error("ErrorHandler", "处理错误", { errors: state.errors });

  return {
    output: `[系统通知] 处理过程中遇到问题: ${state.errors.join("; ")}`,
  };
};

// 决策是否需要降级
const needsFallback = (state: ProductionStateType): string => {
  const primarySuccess = state.metadata.primarySuccess as boolean | undefined;
  return primarySuccess === false ? "fallback" : "success";
};

// 构建生产图
const productionGraph = new StateGraph({ stateSchema: ProductionState })
  .addNode("primary", monitoredPrimary)
  .addNode("fallback", monitoredFallback)
  .addNode("errorHandler", errorHandler)
  .addEdge(START, "primary")
  .addConditionalEdges("primary", needsFallback, {
    fallback: "fallback",
    success: END,
  })
  .addEdge("fallback", END);

const productionApp = productionGraph.compile();

// ============================================================================
// 7. 测试生产系统
// ============================================================================

console.log("=".repeat(60));
console.log("测试: 生产级多智能体系统");
console.log("=".repeat(60));

const testInputs = [
  "什么是 TypeScript？",
  "解释 LangGraph 的优势",
  "React 和 Vue 的区别",
];

for (const input of testInputs) {
  console.log(`\n输入: ${input}`);

  const result = await productionApp.invoke({ input });

  console.log(`输出: ${result.output?.substring(0, 100)}...`);

  if (result.errors.length > 0) {
    console.log(`错误: ${result.errors.join(", ")}`);
  }
}

// ============================================================================
// 8. 查看系统指标
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("系统指标");
console.log("=".repeat(60));

const currentMetrics = metrics.getMetrics();
console.log(`
总请求数: ${currentMetrics.totalRequests}
成功请求: ${currentMetrics.successfulRequests}
失败请求: ${currentMetrics.failedRequests}
成功率: ${((currentMetrics.successfulRequests / currentMetrics.totalRequests) * 100).toFixed(2)}%
平均延迟: ${currentMetrics.averageLatency.toFixed(2)}ms
错误率: ${(currentMetrics.errorRate * 100).toFixed(2)}%

智能体执行次数:
${Object.entries(currentMetrics.agentExecutionCount)
  .map(([agent, count]) => `  ${agent}: ${count}`)
  .join("\n")}
`);

console.log("\n断路器状态:");
console.log(`  主处理器: ${primaryCircuitBreaker.getState()}`);
console.log(`  降级处理器: ${fallbackCircuitBreaker.getState()}`);

// ============================================================================
// 9. 生产架构最佳实践
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("生产架构最佳实践");
console.log("=".repeat(60));

console.log(`
┌─────────────────────────────────────────────────────────┐
│                  生产级多智能体架构                        │
└─────────────────────────────────────────────────────────┘

1. 可观测性
   ✓ 结构化日志 (JSON格式)
   ✓ 指标收集 (Prometheus/Grafana)
   ✓ 分布式追踪 (OpenTelemetry)
   ✓ 实时监控仪表板

2. 弹性和容错
   ✓ 断路器模式
   ✓ 自动重试机制
   ✓ 超时控制
   ✓ 降级策略

3. 性能优化
   ✓ 请求缓存
   ✓ 连接池管理
   ✓ 异步处理
   ✓ 负载均衡

4. 安全性
   ✓ API 认证授权
   ✓ 请求限流
   ✓ 敏感数据加密
   ✓ 审计日志

5. 部署和运维
   ✓ 容器化 (Docker/K8s)
   ✓ 配置管理
   ✓ 健康检查
   ✓ 滚动更新

6. 测试和质量
   ✓ 单元测试
   ✓ 集成测试
   ✓ 压力测试
   ✓ 混沌工程
`);

// ============================================================================
// 总结
// ============================================================================

console.log("=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. 日志系统 - 结构化日志，分级记录");
console.log("2. 指标收集 - 性能和业务指标");
console.log("3. 断路器 - 防止级联失败");
console.log("4. 重试机制 - 自动恢复");
console.log("5. 降级策略 - 保证核心功能");
console.log("6. 监控节点 - 包装业务逻辑");
console.log("\n生产级系统特征:");
console.log("- 可观测: 清晰的日志和指标");
console.log("- 高可用: 容错和自愈能力");
console.log("- 可扩展: 水平扩展能力");
console.log("- 安全性: 完善的安全措施");
console.log("- 可维护: 易于调试和更新");

export {
  productionApp,
  logger,
  metrics,
  CircuitBreaker,
  RetryPolicy,
  LogLevel,
};
