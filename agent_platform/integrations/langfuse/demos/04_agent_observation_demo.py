"""
演示 04: agent（智能体）类型 observation。

agent observation 用于表示一个自主决策单元。其子 observation
通常包括 LLM 生成、工具调用、检索步骤和护栏检查，
这些都是 agent 在完成一项任务过程中执行的操作。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="agent",                              # observation 类型：agent
        name="support-triage-agent",                  # 名称：客服分诊智能体
        input={"ticket": "客户请求发票副本。"},          # 输入工单
        metadata={"agent_strategy": "classify-then-act"},  # 策略：先分类再执行
    ) as agent:
        # agent 内部的子 observation：规划阶段的 LLM 调用
        with langfuse.start_as_current_observation(
            as_type="generation",
            name="agent-planning-generation",          # agent 规划生成
            model="mock-planner",
            input="分类工单并选择下一步操作。",
        ) as generation:
            generation.update(output="意图: billing。操作: fetch_invoice_tool。")

        # 更新 agent 的最终输出
        agent.update(
            output={
                "intent": "billing",                   # 识别意图：账单类
                "selected_action": "fetch_invoice_tool", # 选中的操作
                "confidence": 0.91,                    # 置信度
            }
        )

    flush_and_print(langfuse, "agent-observation-demo")


if __name__ == "__main__":
    main()
