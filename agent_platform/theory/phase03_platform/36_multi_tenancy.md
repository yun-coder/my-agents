# 36 多租户权限 — Agent 平台安全架构

## 1. 概念概述

### 1.1 多租户架构

多租户（Multi-Tenancy）是指一个软件系统实例同时服务多个租户（组织、团队或用户），每个租户的数据和配置相互隔离。在 Agent 平台中，多租户架构确保不同团队/客户的 Agent、对话历史、知识库和配置不会相互泄漏。

多租户的三个核心目标：
- **数据隔离**：租户 A 的数据不能被租户 B 访问
- **性能隔离**：一个租户的负载不影响其他租户
- **可定制性**：每个租户可以独立配置 Agent 行为

### 1.2 隔离策略对比

| 策略 | 数据隔离度 | 成本 | 运维复杂度 | 适合场景 |
|------|-----------|------|-----------|---------|
| 数据库隔离 | 最高 | 高 | 高 | 金融、医疗等强合规场景 |
| Schema 隔离 | 高 | 中 | 中 | SaaS 平台企业版 |
| 行级隔离 (RLS) | 中 | 低 | 低 | 多租户 SaaS 标准方案 |
| 字段隔离 | 低 | 最低 | 低 | 低安全需求场景 |

### 1.3 权限模型

RBAC（基于角色的访问控制）是多租户平台最常用的权限模型，包含三个核心元素：

```
用户 (User) -> 角色 (Role) -> 权限 (Permission)
```

每个租户拥有独立的角色体系：
```
租户 A: Admin, Editor, Viewer
租户 B: Admin, Operator, Auditor
```

## 2. 核心原理

### 2.1 数据库隔离模式

**数据库隔离**：每个租户独立的数据库实例。
```
app-tenant-a (database)
app-tenant-b (database)
app-tenant-c (database)
```
优点：最强数据隔离，备份恢复互不影响。
缺点：维护成本高，连接数随租户增长而增长。

**Schema 隔离**：同一数据库，不同 Schema。
```
public_db.tenant_a.users
public_db.tenant_b.users
public_db.tenant_c.users
```
优点：隔离性好，共享数据库连接池。
缺点：Schema 变更需要同步到所有租户。

**行级隔离**：同一表，通过 tenant_id 列区分。
```
users 表:
| id | tenant_id | name  | email           |
|----|-----------|-------|-----------------|
| 1  | tenant_a  | 张三  | zhang@a.com     |
| 2  | tenant_b  | 李四  | li@b.com        |
```
优点：最简单，连接数最少。
缺点：应用层需要始终携带 tenant_id。

### 2.2 PostgreSQL 行级安全（RLS）

PostgreSQL RLS 在数据库层面强制执行行级隔离，即使应用层漏传 tenant_id 也无法越权：

```sql
-- 启用行级安全
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;

-- 创建隔离策略
CREATE POLICY tenant_isolation ON conversations
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON knowledge_bases
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- 策略类型
-- USING: SELECT, UPDATE, DELETE 的默认过滤
-- WITH CHECK: INSERT 和 UPDATE 的约束检查
```

### 2.3 JWT 认证与租户识别

多租户系统的身份认证流程：
1. 用户登录，服务端验证身份
2. 生成 JWT Token，包含 user_id 和 tenant_id
3. 客户端在后续请求中携带 Token
4. 中间件解析 Token，提取 tenant_id
5. 所有数据库操作携带 tenant_id

### 2.4 审计日志

审计日志记录所有敏感操作，满足合规要求：
```
timestamp | user_id | tenant_id | action      | resource_type | resource_id | detail
2025-06-08 10:00:00 | u001 | t001 | DELETE | knowledge_doc | doc_123 | {"name":"机密报告"}
2025-06-08 10:05:00 | u002 | t001 | EXPORT | conversation | conv_456 | {"count":100}
```

## 3. 实战指南

### 3.1 数据库模型设计

```python
# models.py — 多租户数据模型
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.schema import MetaData

Base = declarative_base()

# 租户模型
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(String(50), default="free")  # free, pro, enterprise
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    users = relationship("User", back_populates="tenant")
    conversations = relationship("Conversation", back_populates="tenant")
    knowledge_bases = relationship("KnowledgeBase", back_populates="tenant")

# 用户模型（跨租户）
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer")  # admin, editor, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")

# 对话模型（行级隔离）
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(500))
    messages = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="conversations")

# 知识库模型（行级隔离）
class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    document_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="knowledge_bases")
```

### 3.2 租户中间件

```python
# middleware.py — 多租户中间件
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional
import uuid

security = HTTPBearer()

class TenantContext:
    """租户上下文：每个请求的租户信息。"""

    def __init__(self):
        self.tenant_id: Optional[uuid.UUID] = None
        self.user_id: Optional[uuid.UUID] = None
        self.user_role: Optional[str] = None

    def set_tenant(self, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id

    def set_user(self, user_id: uuid.UUID, role: str):
        self.user_id = user_id
        self.user_role = role


# 全局单例，每个请求开始时重新初始化
tenant_context = TenantContext()


class TenantMiddleware:
    """FastAPI 多租户中间件。"""

    def __init__(self, app, jwt_secret: str):
        self.app = app
        self.jwt_secret = jwt_secret

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                tenant_context.set_tenant(uuid.UUID(payload["tenant_id"]))
                tenant_context.set_user(
                    uuid.UUID(payload["user_id"]),
                    payload.get("role", "viewer"),
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token 已过期")
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="无效的 Token")
        else:
            # 公开端点不需要认证
            pass

        await self.app(scope, receive, send)


def get_current_tenant() -> TenantContext:
    """获取当前请求的租户上下文。"""
    if not tenant_context.tenant_id:
        raise HTTPException(status_code=401, detail="未指定租户")
    return tenant_context


def require_role(required_role: str):
    """角色验证装饰器。"""
    def role_checker(ctx: TenantContext = Depends(get_current_tenant)):
        role_hierarchy = {"viewer": 1, "editor": 2, "admin": 3}
        if role_hierarchy.get(ctx.user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=403,
                detail=f"需要 {required_role} 角色，当前角色: {ctx.user_role}",
            )
        return ctx
    return role_checker
```

### 3.3 RBAC 权限系统

```python
# rbac.py — RBAC 权限实现
from enum import Enum
from typing import Optional
import uuid

class Permission(str, Enum):
    """系统权限定义。"""
    # Agent 权限
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_DEPLOY = "agent:deploy"

    # 知识库权限
    KB_CREATE = "knowledge_base:create"
    KB_READ = "knowledge_base:read"
    KB_UPDATE = "knowledge_base:update"
    KB_DELETE = "knowledge_base:delete"
    KB_UPLOAD = "knowledge_base:upload"

    # 对话权限
    CONVERSATION_READ = "conversation:read"
    CONVERSATION_DELETE = "conversation:delete"
    CONVERSATION_EXPORT = "conversation:export"

    # 用户管理
    USER_INVITE = "user:invite"
    USER_MANAGE = "user:manage"

    # 租户管理
    TENANT_SETTINGS = "tenant:settings"
    TENANT_BILLING = "tenant:billing"

    # 系统管理
    SYSTEM_ADMIN = "system:admin"


# 角色-权限映射
ROLE_PERMISSIONS = {
    "admin": [
        Permission.AGENT_CREATE, Permission.AGENT_READ,
        Permission.AGENT_UPDATE, Permission.AGENT_DELETE,
        Permission.AGENT_DEPLOY,
        Permission.KB_CREATE, Permission.KB_READ,
        Permission.KB_UPDATE, Permission.KB_DELETE,
        Permission.KB_UPLOAD,
        Permission.CONVERSATION_READ, Permission.CONVERSATION_DELETE,
        Permission.CONVERSATION_EXPORT,
        Permission.USER_INVITE, Permission.USER_MANAGE,
        Permission.TENANT_SETTINGS, Permission.TENANT_BILLING,
    ],
    "editor": [
        Permission.AGENT_CREATE, Permission.AGENT_READ,
        Permission.AGENT_UPDATE,
        Permission.KB_CREATE, Permission.KB_READ,
        Permission.KB_UPDATE, Permission.KB_UPLOAD,
        Permission.CONVERSATION_READ,
        Permission.USER_INVITE,
    ],
    "viewer": [
        Permission.AGENT_READ,
        Permission.KB_READ,
        Permission.CONVERSATION_READ,
    ],
}


class RBACChecker:
    """权限检查器。"""

    def __init__(self, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id

    def has_permission(self, user_role: str, permission: Permission) -> bool:
        """检查用户是否有指定权限。"""
        allowed = ROLE_PERMISSIONS.get(user_role, [])
        return permission in allowed

    def filter_by_permission(
        self,
        user_role: str,
        items: list,
        permission: Permission,
    ) -> list:
        """根据权限过滤列表。"""
        if self.has_permission(user_role, permission):
            return items
        return []


# FastAPI 依赖注入
async def check_permission(
    permission: Permission,
    ctx: TenantContext = Depends(get_current_tenant),
):
    """权限检查依赖。"""
    checker = RBACChecker(ctx.tenant_id)
    if not checker.has_permission(ctx.user_role, permission):
        raise HTTPException(
            status_code=403,
            detail=f"权限不足: 需要 {permission.value}",
        )
    return True
```

### 3.4 PostgreSQL RLS 实现

```python
# rls.py — PostgreSQL 行级安全
from sqlalchemy import event, DDL
from sqlalchemy.schema import DDLElement
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.engine import Connection

class SetTenantContext:
    """在每个数据库会话开始时设置租户上下文。"""

    def __init__(self, connection: Connection, tenant_id: uuid.UUID):
        self.connection = connection
        self.tenant_id = tenant_id

    def __enter__(self):
        self.connection.execute(
            DDL(f"SELECT set_config('app.tenant_id', '{self.tenant_id}', TRUE)")
        )
        return self

    def __exit__(self, *args):
        self.connection.execute(
            DDL("SELECT set_config('app.tenant_id', '', TRUE)")
        )


# 创建 RLS 迁移脚本
CREATE_RLS_POLICY = """
-- 启用 RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

-- 删除默认策略（如果存在）
DROP POLICY IF EXISTS tenant_isolation ON conversations;
DROP POLICY IF EXISTS tenant_isolation ON knowledge_bases;
DROP POLICY IF EXISTS tenant_isolation ON agents;

-- 创建隔离策略
CREATE POLICY tenant_isolation ON conversations
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON knowledge_bases
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON agents
    USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- 管理员可以查看所有（可选）
CREATE POLICY admin_access ON conversations
    USING (current_setting('app.user_role') = 'admin');
"""

# 执行 RLS 迁移
def apply_rls_policies(engine):
    with engine.begin() as conn:
        conn.execute(DDL(CREATE_RLS_POLICY))
    print("RLS 策略已应用")
```

### 3.5 数据加密

```python
# encryption.py — 租户数据加密
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional

class TenantDataEncryptor:
    """租户数据加密器：每个租户使用独立的加密密钥。"""

    def __init__(self, master_key: str):
        self.master_key = master_key.encode()

    def _derive_tenant_key(self, tenant_id: str) -> bytes:
        """从主密钥派生租户特定的密钥。"""
        salt = tenant_id.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return key

    def encrypt(self, tenant_id: str, data: str) -> str:
        """加密租户数据。"""
        key = self._derive_tenant_key(tenant_id)
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()

    def decrypt(self, tenant_id: str, encrypted_data: str) -> str:
        """解密租户数据。"""
        key = self._derive_tenant_key(tenant_id)
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()


# 使用示例
encryptor = TenantDataEncryptor("master-secret-key-xxxx")
tenant_id = "tenant-001"

# 加密敏感数据
encrypted = encryptor.encrypt(tenant_id, "用户的敏感信息")
print(f"加密后: {encrypted}")

# 解密
decrypted = encryptor.decrypt(tenant_id, encrypted)
print(f"解密后: {decrypted}")
```

### 3.6 审计日志实现

```python
# audit.py — 审计日志系统
from datetime import datetime
from typing import Optional
import json
import uuid

class AuditLogger:
    """审计日志记录器。"""

    def __init__(self, db_session):
        self.db = db_session

    def log(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        detail: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ):
        """记录审计事件。"""
        audit_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "detail": json.dumps(detail) if detail else None,
            "ip_address": ip_address,
        }
        # 写入审计表
        self.db.execute(
            "INSERT INTO audit_logs (id, timestamp, tenant_id, user_id, action, "
            "resource_type, resource_id, detail, ip_address) "
            "VALUES (:id, :timestamp, :tenant_id, :user_id, :action, "
            ":resource_type, :resource_id, :detail, :ip_address)",
            audit_entry,
        )
        self.db.commit()

    def query(
        self,
        tenant_id: uuid.UUID,
        action: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 100,
    ) -> list[dict]:
        """查询审计日志。"""
        query = "SELECT * FROM audit_logs WHERE tenant_id = :tenant_id"
        params = {"tenant_id": str(tenant_id)}

        if action:
            query += " AND action = :action"
            params["action"] = action
        if user_id:
            query += " AND user_id = :user_id"
            params["user_id"] = str(user_id)

        query += " ORDER BY timestamp DESC LIMIT :limit"
        params["limit"] = limit

        result = self.db.execute(query, params)
        return [dict(row) for row in result.fetchall()]
```

### 3.7 API 端点示例

```python
# routes.py — 多租户 API 端点
from fastapi import APIRouter, Depends, HTTPException
from typing import List
import uuid

router = APIRouter(prefix="/api/v1")

@router.get("/agents")
async def list_agents(
    ctx: TenantContext = Depends(get_current_tenant),
    _: bool = Depends(check_permission(Permission.AGENT_READ)),
):
    """列出当前租户的所有 Agent。"""
    agents = db.query(Agent).filter(Agent.tenant_id == ctx.tenant_id).all()
    return {"agents": agents, "tenant_id": str(ctx.tenant_id)}

@router.post("/agents")
async def create_agent(
    name: str,
    config: dict,
    ctx: TenantContext = Depends(get_current_tenant),
    _: bool = Depends(check_permission(Permission.AGENT_CREATE)),
):
    """创建 Agent（需要 editor 以上角色）。"""
    agent = Agent(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        name=name,
        config=config,
        created_by=ctx.user_id,
    )
    db.add(agent)
    db.commit()

    # 记录审计
    audit.log(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        action="AGENT_CREATE",
        resource_type="agent",
        resource_id=str(agent.id),
        detail={"name": name},
    )

    return {"agent": agent, "status": "created"}

@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: uuid.UUID,
    ctx: TenantContext = Depends(get_current_tenant),
    _: bool = Depends(check_permission(Permission.AGENT_DELETE)),
):
    """删除 Agent（需要 admin 角色）。"""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.tenant_id == ctx.tenant_id,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    db.delete(agent)
    db.commit()
    return {"status": "deleted"}
```

## 4. 最佳实践

### 4.1 隔离策略选择

1. **SaaS 标准方案**：行级隔离 + PostgreSQL RLS
2. **企业版客户**：Schema 隔离
3. **金融/医疗客户**：数据库隔离
4. **混合方案**：默认行级隔离，高级客户提供独立实例

### 4.2 性能优化

1. **tenant_id 索引**：所有带 tenant_id 的表建立复合索引
2. **连接池管理**：每个租户的连接池单独管理（数据库隔离模式）
3. **缓存隔离**：Redis 使用 key 前缀区分租户
4. **查询优化**：始终在 WHERE 子句中包含 tenant_id

### 4.3 安全加固

1. **API Key 轮转**：定期更换 API Key 和 JWT Secret
2. **传输加密**：全链路 HTTPS/TLS
3. **静态加密**：数据库存储加密
4. **最小权限**：默认只授予最少的必要权限

### 4.4 合规要求

1. **数据驻留**：某些地区要求数据存储在本地
2. **审计保留**：审计日志至少保留 90 天
3. **数据导出**：提供租户数据导出功能
4. **删除确认**：租户删除前要求多次确认

## 5. 常见陷阱

### 5.1 应用层漏传 tenant_id

最危险的多租户 Bug——应用层某个查询忘记加 tenant_id
过滤条件，导致数据泄漏。

### 5.2 缓存未隔离

使用 Redis 缓存时不添加 tenant_id 前缀，不同租户的缓存
互相覆盖。

### 5.3 Schema 迁移混乱

Schema 隔离模式下，数据库迁移需要为每个 Schema 执行，
容易遗漏。

### 5.4 连接数耗尽

每个租户独立连接池时，总连接数 = 租户数 * 连接池大小，
可能超过数据库上限。

### 5.5 备份恢复遗漏

数据库隔离模式下，忘记为新租户配置自动备份。

## 6. API Key 依赖

| 服务 | 需要 Key | 说明 |
|------|---------|------|
| Auth0 | 需要 | 第三方身份认证 |
| Ory Kratos | 需要 | 开源身份认证 |
| PostgreSQL | 不需要 | 数据库 |
| Redis | 不需要 | 缓存 |
| JWT | 不需要 | 本地生成 |
| Vault | 需要 | 密钥管理 |

## 7. 技术关系

- **上层**：业务 API -> 多租户 CRUD 操作
- **本层**：RBAC 权限系统 + RLS -> 数据隔离
- **下层**：PostgreSQL + Redis -> 数据存储
- **认证**：JWT / Auth0 / Ory -> 身份认证
- **审计**：审计日志 -> 操作追溯
- **加密**：Fernet / Vault -> 数据加密

## 8. 验收清单

- [ ] 理解三种隔离策略的优缺点和适用场景
- [ ] 掌握 PostgreSQL RLS 的配置方法
- [ ] 实现 JWT Token 中的租户上下文传递
- [ ] 设计完整的 RBAC 角色和权限体系
- [ ] 实现 FastAPI 租户中间件
- [ ] 完成数据库查询中的租户隔离
- [ ] 实现审计日志功能
- [ ] 配置数据加密机制
- [ ] 了解 Auth0 或 Ory 的集成方法
- [ ] 进行多租户安全性测试

## 9. 学习资源

- PostgreSQL RLS 文档：https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- Auth0 多租户指南：https://auth0.com/docs/architecture-scenarios/multitenant
- Ory Kratos 文档：https://www.ory.sh/docs/kratos
- RBAC 设计模式：https://en.wikipedia.org/wiki/Role-based_access_control
- 《多租户架构设计》O'Reilly
- SQLAlchemy 多租户指南：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
