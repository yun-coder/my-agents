# 26 Guardrails 安全护栏

## 概念概述

Guardrails（安全护栏）是指在 LLM 应用输入和输出两端设置的安全检查机制，确保模型的行为在可控范围内。随着 LLM 被广泛应用于客服、内容生成、代码辅助等场景，模型可能产生有害内容、泄露敏感信息或被恶意利用。Guardrails 系统作为 AI 应用的安全边界，承担着输入过滤、输出审核、行为约束等多重职责。

当前主流的 Guardrails 框架主要有两个方向：NeMo Guardrails 和 Guardrails AI。NeMo Guardrails 由 NVIDIA 开发，侧重于对话流程控制，通过定义对话轨道（Colang 语言）来约束 LLM 的行为边界。Guardrails AI 则更关注输入输出的内容安全检查，提供丰富的预置校验器和灵活的规则配置。

安全护栏的运行贯穿 LLM 应用的完整调用链路：

```
用户输入 -> 输入护栏 -> LLM 处理 -> 输出护栏 -> 用户响应
                 |                    |
           注入检测、PII、        有害内容、合规检查
           越权指令                PII 泄露
```

## 核心原理

### 护栏类型与层级

**输入护栏（Input Rails）**：在用户请求进入 LLM 之前进行安全检查。

| 检查类型 | 检测目标 | 处理策略 |
|---------|---------|---------|
| Prompt 注入 | 越权指令、角色扮演 | 拦截 / 净化 |
| 内容安全 | 仇恨言论、暴力内容 | 拦截 |
| PII 泄露 | 用户输入的敏感信息 | 脱敏 / 警告 |
| 业务规则 | 超出范围的查询 | 重定向 |
| 频率控制 | 异常高频请求 | 限流 |

**输出护栏（Output Rails）**：在 LLM 响应返回给用户之前进行安全检查。

| 检查类型 | 检测目标 | 处理策略 |
|---------|---------|---------|
| 有害内容 | 暴力、色情、歧视言论 | 拦截 / 替换 |
| PII 泄露 | 输出的身份证、手机号 | 脱敏 / 拦截 |
| 幻觉检测 | 事实性错误 | 警告 / 拦截 |
| 品牌合规 | 违反品牌语气的表述 | 修改 / 拦截 |
| 安全建议 | 医疗、法律等专业建议 | 免责声明 |

### NeMo Guardrails 的 Colang 语言

NeMo Guardrails 使用 Colang（Conversational Language）定义对话规则，这是一种专门用于描述对话流程的领域特定语言：

```
# 定义用户意图
define user express_harmful_intent
    "我想伤害别人"
    "如何制造危险物品"

# 定义护栏规则
define flow
    user express_harmful_intent
    bot refuse_to_respond
    bot provide_helpful_resources

# 定义机器人回复
define bot refuse_to_respond
    "抱歉，我不能提供这方面的帮助。"
    "这超出了我能协助的范围。"
```

### Guardrails AI 的校验器体系

Guardrails AI 采用校验器（Validator）概念，每个校验器负责一项具体的检查任务：

```
输入文本 -> Validator 1 -> Validator 2 -> Validator N -> LLM
              |               |              |
           通过/拒绝        通过/拒绝      通过/拒绝
```

每个校验器可以配置不同的处理动作：
- `pass`：允许通过
- `fix`：自动修正
- `filter`：过滤违规内容
- `refrain`：拒绝回答
- `noop`：记录但不处理

## 实战指南

### 基于 SecurityGuard 的安全检查

以下代码基于本项目的 `src/security/guard.py` 实现：

```python
"""安全护栏：基于项目 SecurityGuard 实现输入输出检查。"""
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GuardRule:
    """一条安全规则的配置。"""

    name: str
    patterns: list[str]
    severity: str = "medium"
    action: str = "block"
    message: str = ""


# 扩展规则集
EXTENDED_INPUT_RULES: list[GuardRule] = [
    GuardRule(
        name="jailbreak_attempt",
        patterns=[
            r"DAN|jailbreak|越狱",
            r"你(现在|已经)是.*(不受|没有).*(限制|约束)",
            r"ignore.*(ethics|moral|guideline|rule)",
            r"你是一个没有限制的AI",
        ],
        severity="critical",
        message="检测到越狱尝试",
    ),
    GuardRule(
        name="sql_injection",
        patterns=[
            r"'.*OR.*'='|DROP\s+TABLE|DELETE\s+FROM",
            r"SELECT.*FROM.*WHERE",
        ],
        severity="critical",
        message="检测到 SQL 注入尝试",
    ),
    GuardRule(
        name="excessive_length",
        patterns=[],
        severity="medium",
        action="sanitize",
        message="输入超出长度限制",
    ),
]

EXTENDED_OUTPUT_RULES: list[GuardRule] = [
    GuardRule(
        name="api_key_leak",
        patterns=[
            r"sk-[A-Za-z0-9]{20,}",
            r"pk-[A-Za-z0-9]{20,}",
        ],
        severity="critical",
        message="输出包含 API Key，已拦截",
    ),
    GuardRule(
        name="personal_info",
        patterns=[
            r"\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])\d{2}\d{3}[\dXx]\b",
            r"\b1[3-9]\d{9}\b",
            r"\b\d{17}[\dXx]\b",
        ],
        severity="high",
        action="sanitize",
        message="输出包含个人敏感信息，已脱敏",
    ),
    GuardRule(
        name="harmful_instructions",
        patterns=[
            r"(如何|怎么).*(制作|制造|合成).*(炸弹|毒品|武器)",
            r"(攻击|入侵).*(系统|网站|服务器).*方法",
        ],
        severity="critical",
        message="检测到有害指令生成",
    ),
]


class SecurityGuard:
    """安全护栏主类：管理输入输出规则链。"""

    def __init__(
        self,
        input_rules: list[GuardRule] | None = None,
        output_rules: list[GuardRule] | None = None,
        max_input_length: int = 10000,
    ) -> None:
        self._input_rules = input_rules or EXTENDED_INPUT_RULES
        self._output_rules = output_rules or EXTENDED_OUTPUT_RULES
        self._max_input_length = max_input_length

    def _check_text(
        self, text: str, rules: list[GuardRule]
    ) -> list[dict[str, Any]]:
        """对文本执行规则检查，返回所有违规记录。"""
        violations: list[dict[str, Any]] = []
        text_lower = text.lower()

        for rule in rules:
            if not rule.patterns:
                if rule.name == "excessive_length" and len(text) > self._max_input_length:
                    violations.append({
                        "rule": rule.name,
                        "severity": rule.severity,
                        "action": rule.action,
                        "message": rule.message or f"输入长度 {len(text)} 超过限制 {self._max_input_length}",
                        "matched": f"length={len(text)}",
                    })
                continue

            for pattern in rule.patterns:
                try:
                    if re.search(pattern, text_lower):
                        violations.append({
                            "rule": rule.name,
                            "severity": rule.severity,
                            "action": rule.action,
                            "message": rule.message or f"匹配模式: {pattern[:60]}",
                            "matched": pattern[:80],
                        })
                except re.error as exc:
                    logger.warning("正则表达式错误 %s: %s", pattern, exc)

        return violations

    def check_input(self, text: str) -> list[dict[str, Any]]:
        """检查用户输入。返回违规列表，空列表表示安全。"""
        return self._check_text(text, self._input_rules)

    def check_output(self, text: str) -> list[dict[str, Any]]:
        """检查模型输出。返回违规列表，空列表表示安全。"""
        return self._check_text(text, self._output_rules)

    def sanitize_output(self, text: str) -> str:
        """净化输出文本：对违规内容进行脱敏处理。"""
        result = text
        result = re.sub(
            r"\b(\d{6})\d{8}(\d{4}[\dXx])\b",
            r"\1********\2",
            result,
        )
        result = re.sub(
            r"\b(1[3-9]\d)\d{4}(\d{4})\b",
            r"\1****\2",
            result,
        )
        result = re.sub(
            r"(sk-[A-Za-z0-9]{8})[A-Za-z0-9]+([A-Za-z0-9]{4})",
            r"\1...\2",
            result,
        )
        return result

    def validate_request(
        self, user_input: str
    ) -> tuple[bool, str, list[dict[str, Any]]]:
        """完整校验一次请求。返回 (是否通过, 提示消息, 违规详情)。"""
        violations = self.check_input(user_input)

        critical = [v for v in violations if v["severity"] == "critical"]
        if critical:
            return False, "您的请求包含不安全内容，已被系统拦截。", violations

        high = [v for v in violations if v["severity"] == "high"]
        if high:
            return False, "您的请求包含潜在风险，请修改后重试。", violations

        return True, "", violations


# 全局护栏实例
_default_guard = SecurityGuard()


def check_input(text: str) -> list[dict[str, Any]]:
    """便捷函数：检查输入。"""
    return _default_guard.check_input(text)


def check_output(text: str) -> list[dict[str, Any]]:
    """便捷函数：检查输出。"""
    return _default_guard.check_output(text)


def sanitize(text: str) -> str:
    """便捷函数：净化文本。"""
    return _default_guard.sanitize_output(text)
```

### 集成 Guardrails AI 框架

```python
"""使用 Guardrails AI 框架创建结构化的输出护栏。"""
from typing import Any

import guardrails as gd
from guardrails.hub import (
    BanCompetitors,
    DetectPII,
    FactualConsistency,
    ToxicLanguage,
    RegexMatch,
)


def create_content_guardrail() -> gd.Guard:
    """创建内容安全护栏。"""
    from guardrails import Guard

    guard = Guard().use(
        ToxicLanguage(threshold=0.7, validation_method="sentence"),
        on_fail="exception",
    ).use(
        DetectPII(
            pii_entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "CREDIT_CARD"],
            on_fail="fix",
        ),
    ).use(
        FactualConsistency(
            validation_method="percentage",
            min_percentage=0.8,
            on_fail="warn",
        ),
    )

    return guard


def guard_llm_response(
    response: str, guard: gd.Guard
) -> tuple[bool, str, dict[str, Any]]:
    """使用护栏验证 LLM 响应。"""
    try:
        result = guard.validate(response)
        return True, result.validated_output or response, result.metadata
    except Exception as exc:
        return False, str(exc), {}
```

### 自定义校验器

```python
"""创建自定义校验器以满足特定业务规则。"""
import json
import re
from typing import Any


class BusinessRuleValidator:
    """业务规则校验器：执行领域特定的安全检查。"""

    def __init__(self, config_path: str | None = None) -> None:
        self.rules: list[dict[str, Any]] = []
        if config_path:
            self.load_rules(config_path)

    def load_rules(self, path: str) -> None:
        """从 JSON 文件加载业务规则。"""
        with open(path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def add_rule(
        self,
        name: str,
        check_type: str,
        pattern: str | None = None,
        keywords: list[str] | None = None,
        action: str = "block",
    ) -> None:
        """动态添加一条业务规则。"""
        self.rules.append({
            "name": name,
            "check_type": check_type,
            "pattern": pattern,
            "keywords": keywords or [],
            "action": action,
        })

    def validate(self, text: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """执行业务规则验证。"""
        violations: list[dict[str, Any]] = []
        text_lower = text.lower()

        for rule in self.rules:
            if rule["check_type"] == "keyword_ban":
                for kw in rule.get("keywords", []):
                    if kw.lower() in text_lower:
                        violations.append({
                            "rule": rule["name"],
                            "type": "keyword_ban",
                            "detail": f"包含禁止关键词: {kw}",
                            "action": rule.get("action", "block"),
                        })

            elif rule["check_type"] == "regex_block":
                if rule.get("pattern"):
                    if re.search(rule["pattern"], text_lower):
                        violations.append({
                            "rule": rule["name"],
                            "type": "regex_block",
                            "detail": f"匹配禁止模式",
                            "action": rule.get("action", "block"),
                        })

            elif rule["check_type"] == "context_check":
                if context:
                    violation = self._check_context(rule, context)
                    if violation:
                        violations.append(violation)

        return violations

    def _check_context(
        self, rule: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any] | None:
        """执行上下文检查。"""
        field = rule.get("context_field", "")
        expected = rule.get("expected_value", "")
        actual = context.get(field)

        if actual != expected:
            return {
                "rule": rule["name"],
                "type": "context_check",
                "detail": f"上下文检查失败: {field} 期望 {expected} 实际 {actual}",
                "action": rule.get("action", "block"),
            }
        return None


def demo_business_rules() -> None:
    """演示业务规则校验器的使用。"""
    validator = BusinessRuleValidator()

    validator.add_rule(
        name="no_price_discussion",
        check_type="keyword_ban",
        keywords=["折扣", "优惠券代码", "优惠码", "内部价"],
        action="block",
    )
    validator.add_rule(
        name="no_competitor_mention",
        check_type="regex_block",
        pattern=r"\b(竞品A|竞品B|竞品C)\b",
        action="warn",
    )

    test_text = "请问有什么优惠码可以使用吗？"
    violations = validator.validate(test_text)
    if violations:
        for v in violations:
            print(f"违规: [{v['action']}] {v['rule']} - {v['detail']}")
```

### 生产级护栏集成

```python
"""生产级护栏集成：将安全检查嵌入 LLM 请求处理流程。"""
import logging
import time
from functools import wraps
from typing import Any, Callable

from .guard import SecurityGuard

logger = logging.getLogger(__name__)


class GuardedLLM:
    """带安全护栏的 LLM 客户端。"""

    def __init__(
        self,
        guard: SecurityGuard | None = None,
        llm_client: Any | None = None,
    ) -> None:
        self.guard = guard or SecurityGuard()
        self.llm = llm_client

    def generate(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """安全的 LLM 生成：带输入输出检查。"""
        start = time.perf_counter()

        # 第一阶段：输入检查
        input_violations = self.guard.check_input(prompt)
        if any(v["severity"] == "critical" for v in input_violations):
            return {
                "success": False,
                "error": "INPUT_BLOCKED",
                "message": "输入被安全护栏拦截",
                "violations": input_violations,
                "latency_ms": (time.perf_counter() - start) * 1000,
            }

        # 第二阶段：LLM 调用
        try:
            response = self.llm.chat.completions.create(
                model=kwargs.get("model", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
            )
            output_text = response.choices[0].message.content or ""
        except Exception as exc:
            return {
                "success": False,
                "error": "LLM_ERROR",
                "message": str(exc),
                "latency_ms": (time.perf_counter() - start) * 1000,
            }

        # 第三阶段：输出检查
        output_violations = self.guard.check_output(output_text)
        critical_output = [
            v for v in output_violations if v["severity"] == "critical"
        ]
        if critical_output:
            logger.warning("输出被护栏拦截: %s", critical_output)
            return {
                "success": False,
                "error": "OUTPUT_BLOCKED",
                "message": "生成内容被安全护栏拦截",
                "violations": output_violations,
                "latency_ms": (time.perf_counter() - start) * 1000,
            }

        # 第四阶段：如果需要，净化输出
        sanitized = output_text
        warn_violations = [
            v for v in output_violations if v["action"] == "sanitize"
        ]
        if warn_violations:
            sanitized = self.guard.sanitize_output(output_text)
            logger.info("输出已净化: %s", [v["rule"] for v in warn_violations])

        return {
            "success": True,
            "output": sanitized,
            "original_output": output_text if warn_violations else None,
            "violations": input_violations + output_violations,
            "latency_ms": (time.perf_counter() - start) * 1000,
        }


def with_guardrail(func: Callable) -> Callable:
    """装饰器：为函数添加安全检查。"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        for arg in args:
            if isinstance(arg, str):
                violations = check_input(arg)
                if violations:
                    logger.warning("安全检查拦截参数: %s", violations)
                    return {"error": "输入被安全护栏拦截", "violations": violations}

        result = func(*args, **kwargs)

        if isinstance(result, str):
            violations = check_output(result)
            if violations:
                logger.warning("输出安全检查失败: %s", violations)
                return {"error": "输出被安全护栏拦截", "violations": violations}

        return result

    return wrapper
```

## 最佳实践

1. **分层防护**：不要依赖单一检测手段。结合正则匹配、语义分析、LLM-as-Judge 多种方式构建纵深防御。

2. **误报处理**：安全护栏可能产生误报（False Positive）。提供人工审核和申诉机制，避免过度拦截影响用户体验。

3. **性能影响**：每个安全检查都会增加延迟。对性能敏感的生产环境，设置超时时间（如 500ms）并支持异步检查。

4. **规则动态更新**：攻击模式在不断演变。设计规则热加载机制，无需重启服务即可更新规则。

5. **日志审计**：所有拦截事件记录完整上下文（用户 ID、时间、拦截原因），用于安全审计和规则优化。

## 常见陷阱

1. **过度拦截**：规则过于严格导致大量正常请求被拦截，严重影响用户体验。通过 A/B 测试逐步收紧规则。

2. **规则绕过**：攻击者可以通过大小写变换、编码绕过、分段输入等方式规避正则检测。使用语义检测作为补充。

3. **输出护栏绕过**：LLM 可能通过 Base64 编码、凯撒密码等方式隐藏有害输出。对编码内容也需要检查。

4. **性能瓶颈**：在 LLM 调用链路中同步执行多个重量级校验器可能导致显著延迟增加。考虑异步化或预检查策略。

## API Key 依赖

Guardrails 框架的 API Key 需求：

- **SecurityGuard（本实现）**：完全本地运行，不需要 API Key
- **Guardrails AI**：Hub 校验器部分免费，部分需要 API Key（如 FactualConsistency 需要 OpenAI Key）
- **NeMo Guardrails**：基础功能不需要 API Key，但使用 LLM 做语义检查时需要 LLM API Key
- **PII 检测**：基于正则的检测不需要 Key，云端 API 检测（如 Microsoft Presidio）需要 Key

## 技术关系

安全护栏与 LLM 应用的其他安全组件紧密协作：

- **[Prompt Injection Defense](../phase02_production/27_prompt_injection.md)**：安全护栏是 Prompt 注入防御的第一道防线
- **[Input Sanitizer (sanitizer.py)](../phase02_production/27_prompt_injection.md)**：护栏检测到危险内容后，调用净化器进行处理
- **[LLM 可观测性](../phase02_production/25_observability.md)**：拦截事件需要被记录到观测平台，用于安全分析
- **[代码执行沙箱](../phase02_production/29_code_sandbox.md)**：护栏拦截不可信代码执行请求

## 验收清单

- [ ] 实现了输入护栏（Prompt 注入检测）
- [ ] 实现了输出护栏（PII/有害内容检测）
- [ ] 支持自定义规则扩展
- [ ] 支持规则热加载
- [ ] 实现了分级处理策略（拦截/警告/净化）
- [ ] 所有拦截事件记录审计日志
- [ ] 护栏性能指标（P95 延迟小于 200ms）
- [ ] 建立了误报处理机制
- [ ] 通过了红队测试
- [ ] 集成了主 LLM 调用管道

## 学习资源

- [NeMo Guardrails 文档](https://github.com/NVIDIA/NeMo-Guardrails)
- [Guardrails AI 文档](https://docs.guardrailsai.com/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-llm-applications/)
- [Microsoft Presidio PII 检测](https://github.com/microsoft/presidio)
