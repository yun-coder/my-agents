"""
演示 10: guardrail（护栏）类型 observation。

guardrail observation 用于安全、合规、策略或模式检查。
它在 LLM 调用之前以及在向用户返回答案之前都很有用。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="guardrail",                          # observation 类型：guardrail
        name="pii-output-check",                      # 名称：PII（个人身份信息）输出检查
        input={"answer": "您的发票已在账单门户中准备好。"},
        metadata={"policy": "no-sensitive-identifiers"},  # 策略：禁止敏感标识符
        version="guardrail-1.0.0",                    # 版本号
    ) as guardrail:
        passed = True                                  # 检查是否通过
        guardrail.update(
            output={"passed": passed, "violations": []},  # 输出：通过状态和违规列表
            level="DEFAULT" if passed else "WARNING",     # 级别：通过=DEFAULT，未通过=WARNING
        )

    flush_and_print(langfuse, "guardrail-observation-demo")


if __name__ == "__main__":
    main()
