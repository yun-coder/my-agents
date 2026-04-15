# 🚀 快速开始指南

## 1. 获取 GLM API Key

1. 访问智谱 AI 开放平台: https://open.bigmodel.cn/usercenter/apikeys
2. 注册/登录账号
3. 创建 API Key
4. 复制 API Key（格式类似: `xxxxxxxx.xxxxxxxx`）

## 2. 配置环境变量

在项目根目录的 `.env` 文件中设置：

```env
GLM_API_KEY=your_actual_api_key_here
```

替换 `your_actual_api_key_here` 为你实际的 API Key。

## 3. 运行示例

### 基础示例

```bash
# 运行 GLM 对话示例
npm run glm

# 或者
npx tsx src/glm-chat.ts
```

### 进阶示例

基于 LangChain 官方教程的进阶示例：

```bash
# RAG Agent（检索增强生成）
npm run rag

# 语义搜索和向量存储
npm run semantic

# 多 Agent 协作
npm run multi-agent

# Memory 持久化
npm run memory

# LangGraph 工作流
npm run workflow
```

## 📖 示例说明

### 基础示例

#### `src/glm-chat.ts` - 推荐使用
简化稳定版，包含：
- 基础对话
- 系统提示
- 多轮对话
- 结构化输出

### 进阶示例

#### `src/rag-agent.ts` - RAG 检索增强生成
基于 LangChain 官方教程的 RAG 实现：
- 文档加载和预处理
- 文本分割和向量化
- 向量存储和语义搜索
- RAG 检索增强生成
- 自定义文档问答

**学习资源**: https://docs.langchain.com/oss/javascript/tutorials/rag

```bash
npm run rag
```

#### `src/semantic-search.ts` - 语义搜索和向量存储
基于 LangChain 官方教程的语义搜索：
- 文档向量化
- 语义相似度搜索
- 混合搜索（语义+关键词）
- 向量存储管理
- 基于 GLM 的智能推荐

**学习资源**: https://docs.langchain.com/oss/javascript/tutorials/semantic_search

```bash
npm run semantic
```

#### `src/multi-agent.ts` - 多 Agent 协作
基于 LangChain 官方教程的多 Agent 系统：
- 多个专业 Agent 协作（研究员、分析师、策划师、审核员）
- Agent 任务分配和协调
- 结果聚合和验证
- 协调器工作流
- Agent 能力展示

**学习资源**: https://docs.langchain.com/oss/javascript/tutorials/multi_agent

```bash
npm run multi-agent
```

#### `src/memory-persistence.ts` - Memory 持久化
基于 LangChain 官方教程的 Memory 管理：
- 对话历史管理
- 跨会话记忆持久化
- 本地文件存储
- 记忆检索和总结
- 多用户场景支持

**学习资源**: https://docs.langchain.com/oss/javascript/concepts/memory

```bash
npm run memory
```

#### `src/langgraph-workflow.ts` - LangGraph 工作流
基于 LangChain 官方教程的工作流：
- 状态机工作流
- 条件路由
- 循环和迭代
- 内容审核工作流
- 自定义文章生成流程

**学习资源**: https://docs.langchain.com/oss/javascript/tutorials/graph

```bash
npm run workflow
```

## 📖 可用的 GLM 模型

| 模型名称 | 说明 | 推荐用途 |
|---------|------|---------|
| `glm-4` | GLM-4 基础模型 | 通用对话 |
| `glm-4-plus` | GLM-4 增强版 | 复杂任务 |
| `glm-4-flash` | GLM-4 快速版 | 快速响应 |
| `glm-4-air` | GLM-4 轻量版 | 成本优化 |

### 切换模型

编辑对应的源文件，修改 `createGLMModel()` 调用：

```typescript
// 使用 GLM-4 Plus
const model = createGLMModel("glm-4-plus");

// 使用 GLM-4 Flash（快速）
const model = createGLMModel("glm-4-flash");
```

## 📝 代码说明

### 文件结构

```
src/
  ├── index.ts          # 完整 Agent 示例
  ├── demo.ts           # 多功能演示（包含流式输出）
  ├── glm-chat.ts       # ✅ 推荐使用：简化稳定版
  ├── rag-agent.ts      # RAG 检索增强生成
  ├── semantic-search.ts # 语义搜索和向量存储
  ├── multi-agent.ts    # 多 Agent 协作
  ├── memory-persistence.ts # Memory 持久化
  └── langgraph-workflow.ts # LangGraph 工作流
```

### 核心 API

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";

// 创建模型
const model = new ChatOpenAI({
  modelName: "glm-4",
  openAIApiKey: process.env.GLM_API_KEY,
  configuration: {
    baseURL: "https://open.bigmodel.cn/api/coding/paas/v4",
  },
});

// 发送消息
const response = await model.invoke([
  new HumanMessage("你好"),
]);

console.log(response.content);
```

## 🔧 常见问题

### 1. 401 认证错误

```
❌ 执行出错: 401 令牌已过期或验证不正确
```

**解决方案:**
- 检查 `.env` 文件中 `GLM_API_KEY` 是否正确
- 确认 API Key 没有过期
- 检查智谱 AI 账户余额是否充足

### 2. 网络连接错误

**解决方案:**
- 确保能访问 `https://open.bigmodel.cn`
- 如果在国内，通常不需要代理
- 如果仍无法连接，可设置代理环境变量

### 3. TypeScript 编译错误

**解决方案:**
- 使用 `tsx` 直接运行，无需编译：
  ```bash
  npx tsx src/glm-chat.ts
  ```

### 4. Memory 存储文件

运行 `memory-persistence.ts` 后会生成 `memory_storage` 目录，包含对话历史文件。

**清理存储:**
```bash
# 删除存储目录
rm -rf memory_storage
```

## 📚 参考资源

- [LangChain 官方文档](https://docs.langchain.com/oss/javascript)
- [LangChain 学习资源](https://docs.langchain.com/oss/javascript/learn)
- [智谱 AI 开放平台](https://open.bigmodel.cn/)
- [GLM API 文档](https://open.bigmodel.cn/dev/api)

## 🎓 LangChain 学习路径

基于 LangChain 官方学习资源，推荐的进阶路径：

1. **基础概念**
   - 运行 `glm-chat.ts` 了解基本对话
   - 学习 LangChain 核心 API

2. **RAG（检索增强生成）**
   - 运行 `rag-agent.ts`
   - 理解文档检索和生成

3. **语义搜索**
   - 运行 `semantic-search.ts`
   - 学习向量存储和相似度搜索

4. **多 Agent 系统**
   - 运行 `multi-agent.ts`
   - 理解 Agent 协作模式

5. **Memory 管理**
   - 运行 `memory-persistence.ts`
   - 学习对话状态管理

6. **工作流设计**
   - 运行 `langgraph-workflow.ts`
   - 掌握复杂流程编排

## ✨ 示例输出

运行成功后，你会看到类似以下输出：

```
🚀 LangChain + GLM 模型示例

使用模型: GLM-4
API 地址: https://open.bigmodel.cn/api/coding/paas/v4

📌 基础对话示例
━━━━━━━━━━━━━━━━━━━━━━━━━━━

用户: 你好，请用一句话介绍一下你自己。
GLM 回复: 你好！我是智谱AI开发的GLM（General Language Model）系列的语言模型...

✅ 所有示例执行完成!
```

## 🔄 更新日志

### v1.1.0 (2026-04-15)
- ✅ 添加 RAG Agent demo
- ✅ 添加语义搜索和向量存储 demo
- ✅ 添加多 Agent 协作 demo
- ✅ 添加 Memory 持久化 demo
- ✅ 添加 LangGraph 工作流 demo
- ✅ 基于 LangChain 官方教程实现
- ✅ 支持本地文件存储 Memory
- ✅ 完整的 TypeScript 类型支持
