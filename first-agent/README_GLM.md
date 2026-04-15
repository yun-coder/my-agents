# LangChain + GLM 模型示例

基于 LangChain 新版 API（v1.0+）和智谱 AI GLM 模型的 TypeScript 示例项目。

## ✨ 特性

- ✅ 使用 LangChain 最新 API（`createAgent`、`tool` 等）
- ✅ 集成智谱 AI GLM 模型（GLM-4）
- ✅ TypeScript 类型支持
- ✅ 多工具支持（天气查询、计算器、时间获取）
- ✅ 多轮对话记忆功能

## 📦 安装

```bash
npm install
```

## 🔑 配置 API Key

1. 获取智谱 AI API Key: https://open.bigmodel.cn/usercenter/apikeys
2. 在 `.env` 文件中设置：

```env
GLM_API_KEY=your_glm_api_key_here
```

## 🚀 运行

```bash
# 开发模式（直接运行 TypeScript）
npm run dev

# 编译 TypeScript
npm run build

# 运行编译后的代码
npm start
```

## 📖 代码结构

```
src/
  └── index.ts        # 主程序文件
```

## 🛠️ 可用的 GLM 模型

| 模型名称 | 说明 |
|---------|------|
| `glm-4` | GLM-4 基础模型 |
| `glm-4-plus` | GLM-4 增强版 |
| `glm-4-0520` | GLM-4 特定版本 |
| `glm-4-flash` | GLM-4 快速版 |

在 `src/index.ts` 中修改 `createGLMModel()` 的参数即可切换模型：

```typescript
const model = createGLMModel("glm-4-plus");
```

## 📚 核心概念

### 1. Agent（智能体）

Agent 是 LangChain 的核心概念，它可以根据用户需求自动选择合适的工具来完成任务。

### 2. Tool（工具）

工具是 Agent 可以调用的函数，本示例包含：

- `get_weather`: 获取天气信息
- `calculator`: 数学计算
- `get_current_time`: 获取当前时间

### 3. Memory（记忆）

使用 `MemorySaver` 实现多轮对话记忆，Agent 可以记住之前的对话内容。

## 🔧 自定义工具

```typescript
import { tool } from "langchain";
import * as z from "zod";

const myTool = tool(
  ({ param1 }) => {
    // 处理逻辑
    return "结果";
  },
  {
    name: "my_tool",
    description: "工具描述",
    schema: z.object({
      param1: z.string().describe("参数描述"),
    }),
  }
);
```

## 📖 参考文档

- [LangChain 官方文档](https://docs.langchain.com/oss/javascript/langchain/quickstart)
- [智谱 AI 开放平台](https://open.bigmodel.cn/)
- [GLM API 文档](https://open.bigmodel.cn/dev/api)

## ❓ 常见问题

### Q: 如何切换到其他模型？

A: 修改 `createGLMModel()` 的参数：

```typescript
// 切换到 GLM-4 Plus
const model = createGLMModel("glm-4-plus");
```

### Q: 如何添加更多工具？

A: 使用 `tool()` 函数定义新工具，然后添加到 `createAgent` 的 `tools` 数组中。

### Q: 如何持久化对话记忆？

A: 将 `MemorySaver` 替换为数据库 checkpointer（如 PostgresSaver）。

## 📄 License

ISC
