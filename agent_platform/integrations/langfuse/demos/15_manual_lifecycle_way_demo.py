"""
演示 15: 手动 start/end 生命周期方式。

当 observation 无法用简单的 with 代码块表达时，使用
start_observation(...) 手动管理。例如后台任务、回调、消息队列，
或在一个函数中开始、在另一个函数中结束的场景。
你必须自己调用 end() 来结束 observation。
"""

from __future__ import annotations

from _common import flush_and_print, get_configured_langfuse


def main() -> None:
    langfuse = get_configured_langfuse()

    # 手动开始一个 observation（不使用 with 语句）
    job = langfuse.start_observation(
        as_type="span",
        name="manual-background-job",                # 名称：手动管理的后台任务
        input={"job_id": "job_123", "kind": "daily-eval"},
    )

    try:
        result = {"processed_rows": 1500, "failed_rows": 0}
        job.update(output=result, level="DEFAULT")
    except Exception as exc:
        # 在重新抛出异常之前将 observation 标记为错误状态。
        # 这样即使异常在上游被处理，失败的作业也能在 Langfuse 中可见。
        job.update(level="ERROR", status_message=str(exc))
        raise
    finally:
        # 确保无论如何都要结束 observation
        job.end()

    flush_and_print(langfuse, "manual-lifecycle-way-demo")


if __name__ == "__main__":
    main()
