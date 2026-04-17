# TypeScript AI Agent 学习项目

一个完整的 TypeScript AI Agent 开发学习路线，从 LangChain 基础到 LangGraph 状态管理，再到 Deep Agents 多智能体系统。

## 项目结构

```
my-agents/
├── LEARNING_ROADMAP.md       # 完整学习路线指南
├── package.json
├── tsconfig.json
├── .env.example
│
├── src/
│   ├── phase-1-langchain/        # Phase 1: LangChain 基础
│   │   ├── 01-prompts.ts        # Prompts & Prompt Templates
│   │   ├── 02-chains.ts         # Chains - 链式调用组合
│   │   ├── 03-tools.ts          # Tools & Function Calling
│   │   ├── 04-memory.ts         # Memory & Conversation History
│   │   └── 05-basic-agent.ts    # Basic Agent
│   │
│   ├── phase-2-langgraph/        # Phase 2: LangGraph 进阶
│   │   ├── 01-state-graph.ts    # StateGraph - 状态图基础
│   │   ├── 02-nodes.ts          # Nodes - 节点深入
│   │   ├── 03-edges.ts          # Edges - 边的连接与路由
│   │   ├── 04-conditional.ts    # Conditional Logic - 条件逻辑
│   │   └── 05-persistence.ts    # Persistence - 状态持久化
│   │
│   ├── phase-3-deep-agents/      # Phase 3: Deep Agents 高级
│   │   ├── 01-supervisor.ts     # Supervisor Pattern - 中心协调模式
│   │   ├── 02-hierarchical.ts   # Hierarchical Teams - 层级团队
│   │   ├── 03-peer-to-peer.ts   # Peer-to-Peer - 平等协作模式
│   │   ├── 04-debate.ts         # Debate Pattern - 辩论对抗模式
│   │   └── 05-production.ts     # Production Architecture - 生产级架构
│   │
│   └── shared/                   # 共享工具
│       ├── llm.ts              # LLM 配置
│       └── types.ts            # 通用类型
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的 Anthropic API Key:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. 运行 Demo

#### Phase 1: LangChain 基础

```bash
npm run demo:1-1    # Prompts & Prompt Templates
npm run demo:1-2    # Chains - 链式调用组合
npm run demo:1-3    # Tools & Function Calling
npm run demo:1-4    # Memory & Conversation History
npm run demo:1-5    # Basic Agent
```

#### Phase 2: LangGraph 进阶

```bash
npm run demo:2-1    # StateGraph - 状态图基础
npm run demo:2-2    # Nodes - 节点深入
npm run demo:2-3    # Edges - 边的连接与路由
npm run demo:2-4    # Conditional Logic - 条件逻辑
npm run demo:2-5    # Persistence - 状态持久化
```

#### Phase 3: Deep Agents 高级

```bash
npm run demo:3-1    # Supervisor Pattern - 中心协调模式
npm run demo:3-2    # Hierarchical Teams - 层级团队
npm run demo:3-3    # Peer-to-Peer - 平等协作模式
npm run demo:3-4    # Debate Pattern - 辩论对抗模式
npm run demo:3-5    # Production Architecture - 生产级架构
```

## 学习路径

### Phase 1: LangChain 基础 (Week 1-2)

学习 LangChain 的核心概念和基础功能：

- **Prompts**: 掌握提示词模板和消息格式
- **Chains**: 学习 LCEL 和链式调用
- **Tools**: 实现函数调用和工具使用
- **Memory**: 管理对话历史和上下文
- **Basic Agent**: 构建第一个智能体

### Phase 2: LangGraph 进阶 (Week 3-4)

深入学习状态图和工作流管理：

- **StateGraph**: 定义和管理复杂状态
- **Nodes**: 实现不同类型的处理节点
- **Edges**: 掌握路由和条件分支
- **Conditional Logic**: 构建智能决策系统
- **Persistence**: 实现状态持久化和恢复

### Phase 3: Deep Agents 高级 (Week 5-6)

构建复杂的多智能体系统：

- **Supervisor Pattern**: 中心协调的多智能体协作
- **Hierarchical Teams**: 层级化的智能体组织
- **Peer-to-Peer**: 去中心化的平等协作
- **Debate Pattern**: 对抗式的优化系统
- **Production Architecture**: 生产级的完整架构

## 技术栈

- **TypeScript** - 类型安全的开发体验
- **LangChain** - AI 应用开发框架
- **LangGraph** - 状态图和智能体编排
- **Anthropic Claude** - 大语言模型

## 学习资源

- [LangChain JS 文档](https://js.langchain.com/)
- [LangGraph JS 文档](https://langchain-ai.github.io/langgraphjs/)
- [Anthropic API 文档](https://docs.anthropic.com/)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT
