# 29 代码执行沙箱

## 概念概述

代码执行沙箱（Code Sandbox）是一种安全隔离环境，用于在受控条件下运行不可信或不可预知的代码。在 AI Agent 场景中，当 LLM 生成需要实际执行的代码时（如数据分析、文件处理、系统操作），沙箱提供了必要的安全保障，防止恶意代码或错误代码对宿主系统造成损害。

沙箱的核心目标是在"给 AI 执行能力"和"防止 AI 造成破坏"之间取得平衡。一个完善的代码执行沙箱需要解决以下安全问题：

- **文件系统隔离**：沙箱内的代码不能访问宿主系统的敏感文件
- **网络访问控制**：限制沙箱代码可以访问的网络资源
- **资源限制**：限制 CPU、内存、磁盘、执行时间，防止资源耗尽攻击
- **系统调用过滤**：阻止危险系统调用（如 fork、mount、reboot）
- **进程隔离**：沙箱内的进程不能影响宿主或其他沙箱进程

当前主流的代码沙箱方案包括：

| 方案 | 安全级别 | 启动速度 | 适用场景 |
|------|---------|---------|---------|
| E2B Sandbox | 高（虚机级） | 中等 | 生产环境，需要高安全性 |
| Modal | 高（容器级） | 快 | Serverless 执行 |
| Docker 容器 | 中高 | 快 | 自托管，灵活可控 |
| subprocess（裸进程） | 低 | 极快 | 内部工具，信任环境 |
| Pyodide（浏览器） | 高（浏览器隔离） | 慢 | 前端执行 Python |

## 核心原理

### 安全隔离级别

| 层级 | 隔离技术 | 安全程度 | 性能开销 |
|------|---------|---------|---------|
| L0 | 语言级隔离（如 Python sandbox） | 低 | 无 |
| L1 | OS 进程级隔离（subprocess） | 低 | 低 |
| L2 | 容器级隔离（Docker） | 中 | 中 |
| L3 | 虚拟机级隔离（gVisor, Firecracker） | 高 | 中高 |
| L4 | 硬件级隔离（KVM, Hyper-V） | 最高 | 高 |

### E2B Sandbox

E2B 提供云端托管的沙箱环境，每个沙箱是一个轻量级虚拟机：

```
用户代码 -> API 请求 -> E2B 云端 -> 隔离 VM -> 执行代码
                                     |
                             文件系统 / 网络 / 资源限制
```

E2B 的核心特性：
- 基于 Firecracker 微虚拟机，提供硬件级隔离
- 支持 Python、Node.js、Bash 等多种执行环境
- 可自定义沙箱模板（预装依赖）
- 文件上传/下载支持
- 执行超时自动终止

### Modal

Modal 提供 Serverless 的函数即服务（FaaS）平台，每个函数在独立的容器环境中运行：

```
用户代码 -> Modal 部署 -> 容器镜像 -> 按需执行 -> 自动扩缩容
```

Modal 的核心特性：
- 基于容器的隔离，秒级冷启动
- 自动扩缩容，按用量付费
- GPU 支持
- 文件挂载和网络配置
- 调度器优先级管理

### Docker 容器沙箱

自托管的 Docker 容器方案，通过配置容器的安全策略实现隔离：

```
Docker run --rm \
  --network none \
  --read-only \
  --memory 512m \
  --cpus 1 \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  sandbox-image python code.py
```

## 实战指南

### 基于 subprocess 的轻量沙箱

```python
"""轻量级代码沙箱：使用 subprocess 在隔离进程中执行代码。"""
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


class SubprocessSandbox:
    """基于 subprocess 的轻量级代码执行沙箱。

    警告：此沙箱提供基本的进程级隔离，不适用于高安全场景。
    对于不可信代码，应使用 Docker 或 E2B 等更严格的方案。
    """

    def __init__(
        self,
        work_dir: str | None = None,
        timeout: int = 30,
        max_memory_mb: int = 256,
    ) -> None:
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    def execute_python(
        self, code: str, env_vars: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """执行 Python 代码并返回结果。"""
        # 将代码写入临时文件
        script_path = self.work_dir / "temp_script.py"
        with script_path.open("w", encoding="utf-8") as f:
            f.write(code)

        # 准备执行环境
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if env_vars:
            env.update(env_vars)

        # 移除危险环境变量
        for dangerous in ["OPENAI_API_KEY", "AWS_SECRET_ACCESS_KEY"]:
            env.pop(dangerous, None)

        start = time.perf_counter()

        try:
            result = subprocess.run(
                [
                    "python", str(script_path),
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=str(self.work_dir),
            )

            elapsed = (time.perf_counter() - start) * 1000

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "elapsed_ms": round(elapsed, 2),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（{self.timeout}秒）",
                "return_code": -1,
                "elapsed_ms": self.timeout * 1000,
            }

        except Exception as exc:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行错误: {exc}",
                "return_code": -1,
                "elapsed_ms": (time.perf_counter() - start) * 1000,
            }

        finally:
            # 清理临时文件
            if script_path.exists():
                script_path.unlink()

    def execute_bash(
        self, command: str, env_vars: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """执行 Bash 命令并返回结果。"""
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # 限制危险命令
        dangerous_commands = [
            "rm -rf /", "mkfs", "dd if=",
            "reboot", "shutdown", "halt",
        ]
        for dangerous in dangerous_commands:
            if dangerous in command:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"危险命令被拦截: {dangerous}",
                    "return_code": -1,
                    "elapsed_ms": 0,
                }

        start = time.perf_counter()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=str(self.work_dir),
            )

            elapsed = (time.perf_counter() - start) * 1000

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "elapsed_ms": round(elapsed, 2),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（{self.timeout}秒）",
                "return_code": -1,
                "elapsed_ms": self.timeout * 1000,
            }

    def cleanup(self) -> None:
        """清理工作目录。"""
        import shutil

        shutil.rmtree(self.work_dir, ignore_errors=True)
```

### 基于 Docker 的沙箱执行

```python
"""Docker 容器沙箱：提供容器级隔离的代码执行环境。"""
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


class DockerSandbox:
    """基于 Docker 的代码执行沙箱，提供容器级隔离。

    要求：宿主机已安装 Docker 并配置了正确的权限。
    """

    SANDBOX_IMAGE = "python:3.11-slim"

    def __init__(
        self,
        image: str = SANDBOX_IMAGE,
        timeout: int = 30,
        memory_limit: str = "256m",
        cpu_limit: float = 1.0,
        network_enabled: bool = False,
    ) -> None:
        self.image = image
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = str(cpu_limit)
        self.network_enabled = network_enabled
        self.container_name = self._generate_container_name()

    def _generate_container_name(self) -> str:
        """生成唯一的容器名称。"""
        import uuid

        return f"sandbox-{uuid.uuid4().hex[:8]}"

    def _build_docker_run_args(self, script_path: str) -> list[str]:
        """构建 docker run 命令参数。"""
        args = [
            "docker", "run",
            "--rm",
            "--name", self.container_name,
            "--memory", self.memory_limit,
            "--cpus", self.cpu_limit,
            "--network", "none" if not self.network_enabled else "bridge",
            "--read-only",
            "--security-opt", "no-new-privileges:true",
            "--cap-drop", "ALL",
            "--pids-limit", "50",
            "--ulimit", "nofile=1024:1024",
            "--stop-timeout", str(self.timeout),
        ]

        # 文件系统：只读挂载脚本文件
        host_path = Path(script_path).resolve()
        args.extend(["-v", f"{host_path}:/app/script.py:ro"])

        # 设置工作目录
        args.extend(["-w", "/app"])

        # 设置环境变量
        args.extend(["-e", "PYTHONUNBUFFERED=1"])
        args.extend(["-e", "PYTHONDONTWRITEBYTECODE=1"])

        args.extend([self.image, "python", "/app/script.py"])

        return args

    def execute_code(
        self,
        code: str,
        env_vars: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """在 Docker 沙箱中执行代码。"""
        # 将代码写入临时文件
        temp_dir = Path(tempfile.mkdtemp())
        script_path = temp_dir / "script.py"

        with script_path.open("w", encoding="utf-8") as f:
            f.write(code)

        cmd = self._build_docker_run_args(str(script_path))

        start = time.perf_counter()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 5,  # 额外给 Docker 一些时间
            )

            elapsed = (time.perf_counter() - start) * 1000

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "elapsed_ms": round(elapsed, 2),
            }

        except subprocess.TimeoutExpired:
            self._force_remove_container()
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（{self.timeout}秒）",
                "return_code": -1,
                "elapsed_ms": self.timeout * 1000,
            }

        except Exception as exc:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Docker 执行错误: {exc}",
                "return_code": -1,
                "elapsed_ms": (time.perf_counter() - start) * 1000,
            }

        finally:
            # 清理
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def _force_remove_container(self) -> None:
        """强制移除超时的容器。"""
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            capture_output=True,
        )

    def execute_with_dependencies(
        self,
        code: str,
        pip_packages: list[str] | None = None,
    ) -> dict[str, Any]:
        """在安装了额外依赖的 Docker 沙箱中执行代码。"""
        if pip_packages:
            install_script = (
                f"import subprocess; "
                f"subprocess.run(['pip', 'install', '--no-cache-dir'] + {pip_packages!r}, "
                f"check=True, capture_output=True)\n"
                f"{code}"
            )
        else:
            install_script = code

        return self.execute_code(install_script)

    def list_installed_packages(self) -> list[str]:
        """列出沙箱镜像中已安装的 Python 包。"""
        result = self.execute_code(
            "import pkg_resources; "
            "print([d.project_name for d in pkg_resources.working_set])"
        )
        if result["success"]:
            import ast

            return ast.literal_eval(result["stdout"].strip())
        return []
```

### 代码安全审查

```python
"""代码执行前的安全审查模块。"""
import ast
import re
from typing import Any


class CodeSecurityReviewer:
    """在代码执行前进行安全审查，检测危险操作。"""

    # 禁止的模块列表
    BLOCKED_MODULES = {
        "os", "subprocess", "shutil", "signal",
        "ctypes", "socket", "multiprocessing",
        "threading", "requests", "urllib",
        "http", "ftplib", "telnetlib",
        "smtplib", "poplib", "imaplib",
        "paramiko", "fabric", "invoke",
    }

    # 禁止的内置函数
    BLOCKED_BUILTINS = {
        "exec", "eval", "compile",
        "open", "__import__", "input",
        "breakpoint", "exit", "quit",
    }

    # 禁止的 AST 节点类型
    DANGEROUS_PATTERNS = [
        (ast.Call, "函数调用"),
        (ast.Import, "import 语句"),
        (ast.ImportFrom, "from import 语句"),
        (ast.Attribute, "属性访问"),
    ]

    def __init__(self) -> None:
        self.findings: list[dict[str, Any]] = []

    def review_code(self, code: str) -> dict[str, Any]:
        """审查代码安全性，返回审查结果。"""
        self.findings = []

        # 1. 静态 AST 分析
        self._analyze_ast(code)

        # 2. 危险模式匹配
        self._scan_dangerous_patterns(code)

        # 3. 资源使用评估
        self._evaluate_resource_usage(code)

        is_safe = len([f for f in self.findings if f["severity"] == "critical"]) == 0

        return {
            "is_safe": is_safe,
            "findings": self.findings,
            "risk_level": self._calculate_risk_level(),
            "summary": self._generate_summary(),
        }

    def _analyze_ast(self, code: str) -> None:
        """使用 AST 分析代码。"""
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            self.findings.append({
                "type": "syntax_error",
                "severity": "critical",
                "detail": f"语法错误: {exc}",
                "line": exc.lineno or 0,
            })
            return

        for node in ast.walk(tree):
            # 检测 import 黑名单
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.BLOCKED_MODULES:
                        self.findings.append({
                            "type": "blocked_import",
                            "severity": "critical",
                            "detail": f"禁止导入模块: {alias.name}",
                            "line": node.lineno,
                        })

            if isinstance(node, ast.ImportFrom):
                if node.module in self.BLOCKED_MODULES:
                    self.findings.append({
                        "type": "blocked_import_from",
                        "severity": "critical",
                        "detail": f"禁止导入模块: {node.module}",
                        "line": node.lineno,
                    })

            # 检测危险内置函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BLOCKED_BUILTINS:
                        self.findings.append({
                            "type": "blocked_builtin",
                            "severity": "critical",
                            "detail": f"禁止使用内置函数: {node.func.id}",
                            "line": node.lineno,
                        })

            # 检测文件操作
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("write", "remove", "unlink", "rmdir"):
                        self.findings.append({
                            "type": "file_operation",
                            "severity": "high",
                            "detail": f"检测到文件操作: {node.func.attr}",
                            "line": node.lineno,
                        })

    def _scan_dangerous_patterns(self, code: str) -> None:
        """扫描危险文本模式。"""
        dangerous_patterns = [
            (r"__import__\s*\(", "动态导入"),
            (r"open\s*\(", "文件打开操作"),
            (r"while\s+True", "无限循环"),
            (r"os\.system", "系统命令执行"),
            (r"os\.popen", "管道执行"),
            (r"base64\.b64decode", "编码解码"),
            (r"pickle\.loads", "反序列化操作"),
        ]

        for pattern, desc in dangerous_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count("\n") + 1
                self.findings.append({
                    "type": "dangerous_pattern",
                    "severity": "medium",
                    "detail": f"{desc}: {match.group()[:50]}",
                    "line": line_num,
                })

    def _evaluate_resource_usage(self, code: str) -> None:
        """评估资源使用风险。"""
        # 检查大循环
        for_loops = len(re.findall(r"\bfor\s+\w+\s+in\s+range\(", code))
        if for_loops > 3:
            self.findings.append({
                "type": "resource_risk",
                "severity": "medium",
                "detail": f"检测到大量循环（{for_loops}个），可能导致 CPU 占用过高",
                "line": 0,
            })

        # 检查递归
        if re.search(r"def\s+\w+.*:\s*\n\s+.*\1\(", code):
            self.findings.append({
                "type": "resource_risk",
                "severity": "high",
                "detail": "检测到递归调用，可能导致栈溢出",
                "line": 0,
            })

        # 检查大内存分配
        large_lists = len(re.findall(r"\[\s*0\s*\]\s*\*\s*\d{5,}", code))
        if large_lists > 0:
            self.findings.append({
                "type": "resource_risk",
                "severity": "high",
                "detail": "检测到大量内存分配操作",
                "line": 0,
            })

    def _calculate_risk_level(self) -> str:
        """计算总体风险等级。"""
        severities = [f["severity"] for f in self.findings]
        if "critical" in severities:
            return "critical"
        if "high" in severities:
            return "high"
        if "medium" in severities:
            return "medium"
        return "low"

    def _generate_summary(self) -> str:
        """生成审查摘要。"""
        total = len(self.findings)
        critical = sum(1 for f in self.findings if f["severity"] == "critical")
        high = sum(1 for f in self.findings if f["severity"] == "high")
        medium = sum(1 for f in self.findings if f["severity"] == "medium")

        return (
            f"共发现 {total} 个安全问题: "
            f"{critical} 个严重, {high} 个高危, {medium} 个中危"
        )


def safe_execute(code: str, sandbox: Any = None) -> dict[str, Any]:
    """安全的代码执行入口：先审查，后执行。"""
    reviewer = CodeSecurityReviewer()
    review_result = reviewer.review_code(code)

    if not review_result["is_safe"]:
        return {
            "success": False,
            "error": "代码安全审查未通过",
            "review": review_result,
        }

    if sandbox is None:
        sandbox = DockerSandbox(timeout=30)

    execution_result = sandbox.execute_code(code)
    execution_result["review"] = review_result

    return execution_result
```

### E2B Sandbox 集成

```python
"""E2B Sandbox 集成：使用云端沙箱执行不可信代码。

注意：使用 E2B 需要设置 E2B_API_KEY 环境变量。
"""
import os
from typing import Any


class E2BSandboxExecutor:
    """基于 E2B 的代码执行沙箱。"""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("E2B_API_KEY", "")
        assert self.api_key, "请设置 E2B_API_KEY 环境变量"

    def execute_python(self, code: str) -> dict[str, Any]:
        """在 E2B 沙箱中执行 Python 代码。"""
        from e2b import Sandbox

        sandbox = Sandbox(api_key=self.api_key)

        try:
            result = sandbox.run_code(code)
            return {
                "success": result.error is None,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": str(result.error) if result.error else None,
            }
        finally:
            sandbox.close()

    def execute_with_files(
        self, code: str, files: dict[str, str]
    ) -> dict[str, Any]:
        """上传文件并执行 Python 代码。"""
        from e2b import Sandbox

        sandbox = Sandbox(api_key=self.api_key)

        try:
            # 上传文件到沙箱
            for file_path, content in files.items():
                sandbox.filesystem.write(file_path, content)

            # 执行代码
            result = sandbox.run_code(code)
            return {
                "success": result.error is None,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": str(result.error) if result.error else None,
            }
        finally:
            sandbox.close()
```

## 最佳实践

1. **最小权限原则**：沙箱只给予代码完成任务所需的最小权限。默认禁用网络，只在必要时开放。

2. **资源限制**：始终设置 CPU、内存、执行时间的上限，防止代码失控消耗资源。

3. **先审查后执行**：在执行任何代码之前，先进行静态安全检查。对于高风险代码，即使沙箱提供隔离，也应该拒绝执行。

4. **清理环境**：每次执行后清理沙箱环境，防止状态残留影响后续执行。

5. **审计日志**：记录所有代码执行记录，包括代码内容、执行者、执行时间、执行结果。

## 常见陷阱

1. **轻量级方案的安全幻觉**：subprocess 和 exec 不提供真正的安全隔离。对于不可信代码，必须使用容器或虚拟机级隔离。

2. **Docker 逃逸**：默认的 Docker 配置可能存在逃逸风险。使用 `--security-opt no-new-privileges`、`--cap-drop ALL` 等加固配置。

3. **网络访问未限制**：默认情况下 Docker 容器可以访问网络。对不需要网络的代码设置 `--network none`。

4. **依赖安装风险**：安装软件包时可能执行恶意安装脚本。使用预构建镜像而非动态安装。

5. **临时文件残留**：沙箱执行后未清理临时文件可能导致磁盘空间耗尽或信息泄露。

## API Key 依赖

代码沙箱的 API Key 需求：

- **subprocess 沙箱**：不需要 API Key
- **Docker 沙箱**：不需要 API Key（但需要 Docker 守护进程权限）
- **E2B Sandbox**：需要 `E2B_API_KEY`
- **Modal**：需要 `MODAL_TOKEN_ID` 和 `MODAL_TOKEN_SECRET`
- **执行环境**：沙箱内的代码不应访问宿主机的 API Key，环境变量需要显式过滤

## 技术关系

代码执行沙箱在 AI Agent 架构中的位置：

- **[Guardrails 安全护栏](../phase02_production/26_guardrails.md)**：在代码进入沙箱之前进行安全审查
- **[Prompt Injection Defense](../phase02_production/27_prompt_injection.md)**：防止提示注入生成恶意代码
- **[LLM 可观测性](../phase02_production/25_observability.md)**：记录代码执行事件用于审计
- **[Docker 部署](../phase02_production/30_docker_compose.md)**：沙箱基于 Docker 容器技术实现
- **[浏览器自动化](../phase02_production/28_browser_automation.md)**：自动化脚本可在沙箱中安全执行

## 验收清单

- [ ] 实现了代码执行前的安全审查
- [ ] 集成了 Docker 容器沙箱
- [ ] 配置了资源限制（CPU / 内存 / 超时）
- [ ] 默认禁用网络访问
- [ ] 实现了文件系统隔离（只读挂载）
- [ ] 集成了 E2B 或 Modal 云端沙箱
- [ ] 代码执行有完整的审计日志
- [ ] 沙箱环境每次执行后自动清理
- [ ] 阻止了危险系统调用
- [ ] 通过了安全审查测试用例

## 学习资源

- [E2B Sandbox 文档](https://e2b.dev/docs)
- [Modal 文档](https://modal.com/docs)
- [Docker 安全最佳实践](https://docs.docker.com/engine/security/)
- [Firecracker 微虚拟机](https://firecracker-microvm.github.io/)
- [gVisor 沙箱运行时](https://gvisor.dev/)
