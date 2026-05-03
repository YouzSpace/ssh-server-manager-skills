---
name: ssh-server-manager
description: >
  SSH 服务器远程操作管理 Skill。通过 SSH 密钥连接远程 Linux 服务器，
  执行命令、管理文件、安装软件、部署服务、查看状态。
  当用户提到连接服务器、SSH、远程服务器、服务器操作、安装软件到服务器、
  查看服务器状态、管理服务器服务、部署到服务器等场景时触发此 Skill。
---

# SSH Server Manager Skill

通过 SSH 密钥认证连接远程 Linux 服务器，执行命令、管理服务、部署应用。

---

## 核心工作流

Skill 触发后，按顺序执行：

1. **读取记忆** — 检查本地记忆文件中是否已有该服务器的信息（IP、用户名、密钥路径、密码等），有则直接使用
2. **确定目标服务器** — 优先级：用户本次提供 > 已记忆的服务器 > `~/.ssh/config` > 询问用户
3. **测试连通性** — `ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no <user>@<IP> "echo ok"`
4. **建立连接** — 使用密钥认证；若密钥未配置，读取 `references/ssh-setup.md` 执行配置流程
5. **记录信息** — 将服务器 IP、用户名、密钥路径、密码等关键信息写入本地记忆（见下方记忆管理规则），下次直接使用
6. **展示菜单** — 让用户选择操作

### 菜单选项

连接成功后展示：

1. **安装服务** — 读取 `references/` 中对应安装文档执行
2. **管理服务** — 启动/停止/重启/查看日志
3. **查看状态** — CPU、内存、磁盘、运行中的服务
4. **自由操作** — 手动执行命令

---

## 记忆管理规则

**核心原则：记住用户输入的一切关键信息，下次对话自动使用，不让用户重复输入。**

### 文件结构

```
.workbuddy/memory/
├── MEMORY.md           # 长期记忆（覆写更新，只保留最新状态）
├── YYYY-MM-DD.md       # 当日操作日志（追加）
└── ...                 # 7天以上的旧日志自动清理
```

### 读取时机

每次 Skill 触发时，读取以下文件恢复上下文：
- `MEMORY.md` — 服务器信息、服务部署状态、密码凭证
- 今日日志 — 今天已执行的操作
- 昨日日志 — 昨天的操作（可选，按需读取）

### 写入时机

**必须写记忆的操作（完成一个实质任务后立即写入）：**
- 连接了新服务器（记录 IP、用户名、密钥路径、SSH 端口）
- 安装了服务（记录服务名、版本、端口、密码）
- 卸载了服务（删除对应记录）
- 修改了配置（面板密码、端口、SSL 证书等）
- 服务状态变更（重启、停止、启动）
- 用户说"记住这个"或"保存"

**不需要写记忆的操作：**
- 查看服务器状态（临时信息，不记录）
- 纯问答（没改变任何东西）
- 操作失败（记录失败原因即可，不记操作细节）

### MEMORY.md 格式（长期记忆）

每次更新时**覆写旧内容**，只保留最新状态：

```markdown
# 服务器信息

## <服务器别名或域名>
- IP: <IP地址>
- 用户: <用户名>
- 密钥: <私钥路径>
- SSH端口: <端口>
- 系统: <操作系统信息>

### 已部署服务
- <服务名>: <版本>, 端口 <端口>, 密码 <密码>
- <服务名>: <版本>, 端口 <端口>

### 上次操作
- <日期>: <简要描述>
```

### 每日日志格式（当日操作）

在当天的日志文件中**追加**记录：

```markdown
# YYYY-MM-DD

## HH:MM - <操作标题>
- <步骤1>
- <步骤2>
- 结果: <成功/失败>
```

### 清理规则

| 日志年龄 | 处理方式 |
|---------|---------|
| 0-1 天 | 保留原样，每次 Skill 触发时读取 |
| 2-7 天 | 保留原样，用户询问时读取 |
| 7 天以上 | 压缩摘要写入 MEMORY.md，删除原日志 |

压缩示例：

7天前日志（5条记录）→ 压缩为 MEMORY.md 中的一句话：
```markdown
- 04-26: 安装并配置 3X-UI（端口 2053，已配 SSL）
```

---

## 服务部署

### 安装步骤

1. 检查架构：`uname -m`
2. 确认包管理器（apt/yum/dnf）
3. 检查依赖
4. 下载/安装服务
5. 配置服务（配置文件、systemd）
6. 启动并验证
7. 输出访问信息给用户，同时写入本地记忆

### 可用的安装参考文档

| 服务 | 文档 | 按需读取 |
|------|------|----------|
| 3X-UI 面板 | [references/3x-ui-install.md](references/3x-ui-install.md) | 用户选择安装时读取 |
| MTG (MTProto Proxy) | [references/mtg-install.md](references/mtg-install.md) | 用户选择安装时读取 |
| 防火墙部署 | [references/firewall-deployment.md](references/firewall-deployment.md) | 部署防火墙时读取 |
| conntrack 调优 | [references/conntrack-tuning.md](references/conntrack-tuning.md) | 连接追踪问题时读取 |

未覆盖的服务，按通用步骤安装，或参考官方文档。

### 管理服务

```bash
systemctl status|restart|stop|enable <服务名>
journalctl -u <服务名> -f    # 日志
ss -tlnp | grep <端口>       # 端口检查
```

---

## 按需读取的参考文档

以下文档**不要预先加载**，仅在对应场景触发时读取：

| 场景 | 文档 |
|------|------|
| SSH 连接断开/超时 | [references/ssh-keepalive.md](references/ssh-keepalive.md) |
| 首次配置密钥认证 | [references/ssh-setup.md](references/ssh-setup.md) |
| 服务器操作（执行命令/上传下载文件/运行脚本） | [references/ssh-operations.md](references/ssh-operations.md) |
| 3X-UI 安装 | [references/3x-ui-install.md](references/3x-ui-install.md) |
| MTG 安装 | [references/mtg-install.md](references/mtg-install.md) |
| 防火墙部署 | [references/firewall-deployment.md](references/firewall-deployment.md) |
| conntrack 表满/连接追踪问题 | [references/conntrack-tuning.md](references/conntrack-tuning.md) |

---

## 安全规则

- 执行破坏性命令（rm、stop、uninstall）前必须向用户确认
- 密码、Token 不在对话中直接重复显示
- 使用 Cloudflare 域名时，提醒用户关闭代理（DNS only）

---

## 故障排查

| 现象 | 排查 |
|------|------|
| SSH 超时 | 检查防火墙/安全组是否放行端口 22 |
| SSH 断开 | 读取 `references/ssh-keepalive.md` 配置保活 |
| 密钥认证失败 | 检查私钥权限（600）、authorized_keys |
| 端口被占用 | `ss -tlnp \| grep <端口>` |
| 服务启动失败 | `journalctl -u <服务名> -n 50` |
| 面板无法访问 | 检查防火墙是否放行面板端口、确认服务运行中 |

详细排查步骤，读取 [references/troubleshooting.md](references/troubleshooting.md)（若存在）。

---

## 安装与更新 Skill

### 用户请求更新时的执行流程

当用户说"更新 Skill"、"更新一下"、"升级 Skill"等类似表述时：

1. 检测 Skill 安装目录，按以下优先级查找：
   - WorkBuddy：`~/.workbuddy/skills/ssh-server-manager`
   - OpenClaw 个人级：`~/.agents/skills/ssh-server-manager`
   - OpenClaw 工作区级：`<workspace>/skills/ssh-server-manager`
   - 找到哪个目录有 `.git` 文件夹就用哪个
2. 执行更新命令：
   ```bash
   cd <Skill安装目录> && git pull origin main
   ```
3. 若 git pull 失败（本地有修改冲突），执行：
   ```bash
   git stash && git pull origin main
   ```
4. 向用户确认更新完成，简要说明本次更新内容

### 一键安装/更新（用户手动执行）

```bash
curl -fsSL https://raw.githubusercontent.com/YouzSpace/ssh-server-manager-skills/main/install.sh | bash
```
