"""
演示 05: tool（工具）类型 observation。

tool observation 用于 agent 调用的函数或外部系统：
- 搜索 API
- 计算器
- 数据库查询
- CRM 或工单系统操作
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    with langfuse.start_as_current_observation(
        as_type="tool",                               # observation 类型：tool
        name="lookup-invoice-tool",                   # 名称：发票查询工具
        input={"customer_id": "cust_123", "invoice_month": "2026-05"},  # 输入参数
        metadata={"system": "billing-api"},           # 来源系统
    ) as tool:
        # 工具输出应包含足够的结构信息以方便调试故障。
        # 避免存储密钥、原始凭据或不必要的个人身份信息（PII）。
        tool.update(
            output={
                "invoice_id": "inv_2026_05_123",      # 发票ID
                "status": "ready",                    # 状态：就绪
                "amount": 199.0,                      # 金额
            }
        )

    flush_and_print(langfuse, "tool-observation-demo")


if __name__ == "__main__":
    main()
