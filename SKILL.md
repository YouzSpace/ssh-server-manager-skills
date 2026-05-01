---
name: ssh-server-manager
description: >
  SSH 服务器远程操作管理 Skill。通过 SSH 密钥连接远程 Linux 服务器，
  执行命令、管理文件、安装软件、部署服务、查看状态。
  当用户提到连接服务器、SSH、远程服务器、服务器操作、安装软件到服务器、
  查看服务器状态、管理服务器服务、部署到服务器等场景时触发此 Skill。
---

# SSH Server Manager Skill

通过 SSH 密钥认证连接远程 Linux 服务器，执行命令、管理服务、部署应用的完整工作流。

---

## 触发时执行流程

Skill 触发后，按以下顺序执行：

1. **确定目标服务器** — 获取连接参数（IP、用户名、私钥路径、端口），来源优先级：
   - 用户本次对话中明确提供的信息
   - 用户 `~/.ssh/config` 中已配置的 Host 别名
   - 若有多个服务器，询问用户选择
2. **测试连通性** — 确认 SSH 端口可达
3. **建立连接** — 使用密钥认证连接服务器
4. **连接成功后，展示选项菜单** — 让用户选择接下来要做什么
5. **执行任务** — 根据用户选择执行具体操作
6. **验证结果** — 确认操作成功，输出关键信息
7. **保存连接信息** — 更新用户 `~/.ssh/config`，方便后续快速连接

---

## 连接成功后的选项菜单

首次成功连接服务器时，向用户展示以下选项：

1. **安装服务** — 根据 `references/` 中的安装文档部署服务（如 3X-UI、MTG 等）
2. **管理服务** — 管理已部署的服务（启动/停止/重启/查看日志）
3. **查看状态** — 展示服务器整体状态概览
4. **自由操作** — 手动执行命令

用户选择后，跳转到对应操作执行。

---

## 初始化连接（首次连接新服务器）

### 1. 测试连通性

```bash
powershell -Command "Test-NetConnection -ComputerName <IP> -Port 22"
```

- 连通 → 继续下一步
- 不通 → 提示用户检查防火墙/安全组，等待用户确认后重试

### 2. 配置密钥认证

检查本地是否已有私钥文件，不存在则生成：

```bash
ssh-keygen -t ed25519 -f <私钥路径> -N "" -C "ssh-server-manager"
```

将公钥复制到服务器 `~/.ssh/authorized_keys`（提示用户操作或提供命令）。

### 3. 验证连接

```bash
ssh -i <私钥路径> -o StrictHostKeyChecking=no <user>@<IP> "echo ok"
```

返回 `ok` → 连接成功，继续执行任务。失败 → 排查密钥权限或防火墙问题。

### 4. 采集服务器信息（首次连接）

```bash
ssh -i <私钥> <user>@<IP> "uname -a && free -h && df -h / && cat /etc/os-release"
```

将结果记录下来，供后续操作参考。

---

## SSH 超时保活

当用户反馈 SSH 连接频繁断开时，执行以下配置：

### 客户端配置

读取 `~/.ssh/config`，检查目标 Host 是否已包含保活参数。若未配置，追加以下内容：

```
Host <别名>
    HostName <服务器IP>
    User <用户名>
    IdentityFile ~/.ssh/<私钥文件>
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ConnectTimeout 15
    ConnectionAttempts 3
```

### 服务器端配置

通过 SSH 远程修改 `/etc/ssh/sshd_config`，确保以下配置已启用（未注释）：

```
TCPKeepAlive yes
ClientAliveInterval 30
ClientAliveCountMax 3
```

然后重启 SSH 服务：

```bash
ssh -i <私钥> <user>@<IP> "systemctl restart sshd"
```

### 验证

配置完成后，执行一个长时间命令（如 `top -b -n 1`），确认连接不再中途断开。

---

## 执行服务器操作

### 查看服务器状态

```bash
ssh -i <私钥> <user>@<IP> "uptime && free -h && df -h / && docker ps 2>/dev/null"
```

输出关键指标：运行时间、内存使用、磁盘占用、运行中的容器。

### 执行任意命令

```bash
ssh -i <私钥> <user>@<IP> "<command>"
```

执行前向用户确认命令内容，执行后输出结果。

### 上传文件

```bash
scp -i <私钥> <本地文件> <user>@<IP>:<远程路径>
```

上传后验证文件存在：`ssh -i <私钥> <user>@<IP> "ls -lh <远程路径>"`

### 下载文件

```bash
scp -i <私钥> <user>@<IP>:<远程文件> <本地路径>
```

### 执行本地脚本

```bash
ssh -i <私钥> <user>@<IP> "bash -s" < <本地脚本文件>
```

---

## 服务部署

### 通用部署模式

安装任何服务时，遵循以下通用步骤：

1. 检查服务器架构：`uname -m`
2. 确认系统包管理器（apt/yum/dnf）
3. 检查所需依赖是否已安装
4. 下载/安装目标服务
5. 配置服务（配置文件、systemd 单元）
6. 启动并验证服务状态
7. 确认端口监听
8. 输出服务访问信息给用户

### 可用的安装参考文档

| 服务 | 参考文档 |
|------|----------|
| 3X-UI 面板 | [references/3x-ui-install.md](references/3x-ui-install.md) |
| MTG (MTProto Proxy) | [references/mtg-install.md](references/mtg-install.md) |

对于 `references/` 中未覆盖的服务，按通用部署模式执行，或提示用户参考服务官方文档。

### 管理已部署服务

通用的服务管理命令：

```bash
systemctl status <服务名>     # 查看状态
systemctl restart <服务名>    # 重启
systemctl stop <服务名>       # 停止
systemctl enable <服务名>     # 开机自启
journalctl -u <服务名> -f     # 实时查看日志
ss -tlnp | grep <端口>        # 检查端口监听
```

---

## 安全规则

- **敏感信息不输出**：Secret、密码、私钥内容不直接显示，提示用户自行保存
- **操作前确认**：执行破坏性命令（rm、stop、uninstall）前必须向用户确认
- **Cloudflare 提醒**：使用域名时，若配置了 Cloudflare，提醒用户关闭代理（DNS only）

---

## 故障排查

| 现象 | 排查步骤 |
|------|----------|
| SSH 连接超时 | 检查防火墙/安全组是否放行端口 22 |
| SSH 连接断开 | 执行 SSH 超时保活配置 |
| 密钥认证失败 | 检查私钥权限（600）、authorized_keys 内容 |
| 端口被占用 | `ss -tlnp \| grep <端口>` 查看占用进程 |
| 服务启动失败 | `journalctl -u <服务名> -n 50` 查看日志 |
| 面板无法访问 | 检查防火墙是否放行面板端口、确认服务运行中 |
