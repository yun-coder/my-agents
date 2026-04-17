# TypeScript AI Agent 开发学习路线
## 从 LangChain → LangGraph → Deep Agents 完整指南

---

## 📚 学习路径总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        学习路径总览                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 1: LangChain 基础          │
│  ├─ Prompts & Templates           │
│  ├─ Chains (LLMChain, Sequential) │
│  ├─ Tools & Function Calling      │
│  └─ Memory & Chat History         │
│                                                                     │
│           ⬇️ 进阶                                                 │
│                                                                     │
│  Phase 2: LangGraph 状态管理     │
│  ├─ Graph Architecture            │
│  ├─ State Management              │
│  ├─ Nodes & Edges                 │
│  └─ Conditional Routing           │
│                                                                     │
│           ⬇️ 高级                                                 │
│                                                                     │
│  Phase 3: Deep Agents 多智能体   │
│  ├─ Multi-Agent Orchestration     │
│  ├─ Agent Communication           │
│  ├─ Hierarchical Teams            │
│  └─ Real-world Applications       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: LangChain 基础 (Week 1-2)

### 学习目标
- 理解 LangChain 核心概念
- 掌握 Prompt 模板和 Chain 组合
- 实现 Tool 调用和 Memory 管理

### 核心概念
| 概念 | 说明 | Demo 文件 |
|------|------|-----------|
| **Prompts** | 提示词模板管理 | `01-prompts.ts` |
| **Chains** | 链式调用组合 | `02-chains.ts` |
| **Tools** | 函数工具调用 | `03-tools.ts` |
| **Memory** | 对话历史管理 | `04-memory.ts` |
| **Agents** | 基础智能体 | `05-basic-agent.ts` |

### 关键代码模式
```typescript
// Prompt Template
const prompt = ChatPromptTemplate.fromMessages([
  ["system", "You are a helpful assistant"],
  ["human", "{input}"]
]);

// Chain
const chain = prompt | llm | parser;

// Tool
const tool = {
  name: "get_weather",
  description: "Get current weather",
  func: async (city: string) => getWeatherData(city)
};
```

---

## Phase 2: LangGraph 状态管理 (Week 3-4)

### 学习目标
- 理解状态图架构
- 掌握复杂工作流设计
- 实现条件分支和循环

### 核心概念
| 概念 | 说明 | Demo 文件 |
|------|------|-----------|
| **StateGraph** | 状态图定义 | `01-state-graph.ts` |
| **Nodes** | 处理节点 | `02-nodes.ts` |
| **Edges** | 连接边 | `03-edges.ts` |
| **Conditional** | 条件路由 | `04-conditional.ts` |
| **Persistence** | 状态持久化 | `05-persistence.ts` |

### LangGraph 架构
```typescript
// 状态定义
interface AgentState {
  messages: BaseMessage[];
  nextStep?: string;
}

// 图定义
const graph = new StateGraph<AgentState>({
  channels: {
    messages: {
      value: (x, y) => x.concat(y),
      default: () => []
    }
  }
});

// 添加节点和边
graph.addNode("agent", agentNode);
graph.addNode("tools", toolNode);
graph.addEdge("agent", "tools");
graph.addConditionalEdges("agent", shouldContinue);
```

---

## Phase 3: Deep Agents 多智能体 (Week 5-6)

### 学习目标
- 构建多智能体协作系统
- 实现层级化团队架构
- 掌握智能体通信模式

### 核心模式
| 模式 | 说明 | Demo 文件 |
|------|------|-----------|
| **Supervisor** | 中心协调模式 | `01-supervisor.ts` |
| **Hierarchical** | 层级团队 | `02-hierarchical.ts` |
| **Peer-to-Peer** | 平等协作 | `03-peer-to-peer.ts` |
| **Debate** | 辩论决策 | `04-debate.ts` |
| **Production** | 生产级架构 | `05-production.ts` |

### 多智能体架构示例
```typescript
// Supervisor 模式
const supervisorNode = async (state: TeamState) => {
  const response = await supervisorLLM.invoke([
    { role: "system", content: supervisorPrompt },
    { role: "user", content: JSON.stringify(state) }
  ]);
  return { next: response.tool_calls[0].args.next };
};

// 研究者智能体
const researcherAgent = createReactAgent({
  llm: researchLLM,
  tools: [searchTool, crawlTool],
  state: TeamState
});

// 编写者智能体
const writerAgent = createReactAgent({
  llm: writerLLM,
  tools: [fileTool, formatTool],
  state: TeamState
});
```

---

## 📁 项目结构

```
my-agents/
├── README.md
├── LEARNING_ROADMAP.md           # 本文件
├── package.json
├── tsconfig.json
├── .env.example
│
├── src/
│   ├── phase-1-langchain/        # LangChain 基础
│   │   ├── 01-prompts.ts
│   │   ├── 02-chains.ts
│   │   ├── 03-tools.ts
│   │   ├── 04-memory.ts
│   │   └── 05-basic-agent.ts
│   │
│   ├── phase-2-langgraph/        # LangGraph 进阶
│   │   ├── 01-state-graph.ts
│   │   ├── 02-nodes.ts
│   │   ├── 03-edges.ts
│   │   ├── 04-conditional.ts
│   │   └── 05-persistence.ts
│   │
│   ├── phase-3-deep-agents/      # Deep Agents 高级
│   │   ├── 01-supervisor.ts
│   │   ├── 02-hierarchical.ts
│   │   ├── 03-peer-to-peer.ts
│   │   ├── 04-debate.ts
│   │   └── 05-production.ts
│   │
│   └── shared/                   # 共享工具
│       ├── llm.ts
│       ├── tools.ts
│       └── types.ts
│
└── notebooks/                    # Jupyter 笔记 (可选)
    └── learning-notes.ipynb
```

---

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 添加你的 API Keys
```

### 3. 运行 Demo
```bash
# Phase 1: LangChain
npm run demo:1-1    # Prompts
npm run demo:1-2    # Chains
npm run demo:1-3    # Tools

# Phase 2: LangGraph
npm run demo:2-1    # State Graph

# Phase 3: Deep Agents
npm run demo:3-1    # Supervisor
```

---

## 📖 学习资源

### 官方文档
- [LangChain JS Docs](https://js.langchain.com/)
- [LangGraph JS Docs](https://langchain-ai.github.io/langgraphjs/)
- [Anthropic Claude API](https://docs.anthropic.com/)

### 推荐阅读
- [Building Agents with LangChain](https://python.langchain.com/docs/tutorials/agents/)
- [LangGraph Concepts](https://langchain-ai.github.io/langgraph/concepts/)
- [Multi-Agent Systems](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/)

---

## 🎯 学习检查点

### Phase 1 完成标准
- [ ] 能独立创建 PromptTemplate
- [ ] 理解 LCEL (LangChain Expression Language)
- [ ] 实现带 Tools 的 Agent
- [ ] 使用 Memory 保持对话上下文

### Phase 2 完成标准
- [ ] 理解 StateGraph 架构
- [ ] 实现条件路由
- [ ] 使用 Checkpoint 持久化状态
- [ ] 调试复杂工作流

### Phase 3 完成标准
- [ ] 构建多智能体系统
- [ ] 理解不同协作模式
- [ ] 实现生产级架构
- [ ] 性能优化和错误处理

---

## 📝 学习建议

1. **循序渐进** - 每个 Phase 建议花 1-2 周时间
2. **动手实践** - 每个 Demo 都要亲自运行和修改
3. **阅读源码** - 查看 LangChain/LangGraph 的实现
4. **构建项目** - 学完每个 Phase 后做一个实际项目
5. **参与社区** - 加入 Discord/GitHub 讨论

---

*最后更新: 2026-04-17*
