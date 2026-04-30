---
name: ssh-server-manager
agent_created: true
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

1. **确定目标服务器** — 从内存文件或用户输入中获取连接参数（IP、用户名、私钥路径、端口）
2. **测试连通性** — 确认 SSH 端口可达
3. **建立连接** — 使用密钥认证连接服务器
4. **连接成功后，展示选项菜单** — 让用户选择接下来要做什么
5. **执行任务** — 根据用户选择执行具体操作
6. **验证结果** — 确认操作成功，输出关键信息
7. **保存信息** — 将新的服务器信息写入内存文件（仅首次连接或信息变更时）

### 连接成功后的选项菜单

首次成功连接服务器时，向用户展示以下选项：

1. **安装 3X-UI 面板** — 一键部署 Xray 管理面板（含节点配置、域名绑定、BBR 优化）
2. **安装 MTG 服务** — 部署 MTProto Proxy 代理服务
3. **自由操作** — 手动执行命令或查看服务器状态

用户选择后，跳转到对应章节执行。

---

## 获取连接参数

按以下优先级获取服务器连接信息：

1. 用户本次对话中明确提供的 IP/域名/用户名/端口
2. 内存文件 `MEMORY.md` 中已保存的服务器信息
3. 用户有多个服务器时，询问用户选择哪一台

**首次连接成功后，立即保存以下信息到 `MEMORY.md`：**
- 服务器 IP / 域名、SSH 端口、用户名、私钥路径
- 服务器系统信息（OS、架构、内存、磁盘）
- 已部署的重要服务（名称、端口、版本等）

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
ssh-keygen -t ed25519 -f <私钥路径> -N "" -C "workbuddy@agent"
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

将结果保存到内存文件。

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

## 安装 3X-UI 面板

### 执行安装

1. 在服务器上运行官方安装脚本：
   ```bash
   ssh -i <私钥> <user>@<IP> "bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)"
   ```
   - 安装脚本是交互式的，端口、账号、密码均选择**随机生成**，其他选项保持默认
   - 若安装脚本无法访问，参考 https://github.com/MHSanaei/3x-ui 获取最新安装方式

2. 安装完成后，脚本会输出面板访问信息，**将这些信息保存到内存文件**：
   - 面板地址（IP + 端口）
   - 登录账号和密码
   - 面板路径（如 `/path`）

3. 向用户确认面板信息，提醒用户保存账号密码

### 域名绑定

安装完成后，询问用户是否需要绑定域名：

- **绑定**：让用户输入域名，执行以下步骤：
  1. 提醒用户在域名 DNS 添加 A 记录指向服务器 IP
  2. 确认 DNS 生效后，在 3X-UI 面板中设置域名（或通过命令行配置）
  3. 配置 SSL 证书（推荐使用面板内置的 ACME 申请 Let's Encrypt 证书）
  4. 若使用 Cloudflare，提醒关闭代理（DNS only / 灰色云朵）

- **不绑定**：跳过此步骤，继续下一步

### BBR 优化

域名配置完成后（或跳过绑定后），询问用户是否开启 BBR：

- **开启**：执行以下命令启用 BBR 拥塞控制算法：
  ```bash
  ssh -i <私钥> <user>@<IP> "echo 'net.core.default_qdisc=fq' >> /etc/sysctl.conf && echo 'net.ipv4.tcp_congestion_control=bbr' >> /etc/sysctl.conf && sysctl -p && sysctl net.ipv4.tcp_congestion_control"
  ```
  - 验证输出包含 `bbr` 即为成功

- **不开**：跳过此步骤

### 验证安装

1. 确认面板服务运行中：`systemctl status x-ui`
2. 确认端口监听：`ss -tlnp | grep x-ui`
3. 提供面板访问链接给用户

---

## 管理 MTG (MTProto Proxy)

> 详细安装步骤参考：[references/mtg-install.md](references/mtg-install.md)

### 检查 MTG 状态

```bash
ssh -i <私钥> <user>@<IP> "systemctl status mtg && mtg --version"
```

### 安装 MTG（新服务器）

1. 检查服务器架构：`uname -m`
2. 下载对应版本二进制文件（参考 `references/mtg-install.md`）
3. 安装到 `/usr/local/bin/mtg` 并赋权
4. 生成 Secret：`mtg generate-secret example.com`
5. 创建配置文件 `/etc/mtg/config.toml`
6. 创建 systemd 服务文件（参考 `references/mtg-install.md`）
7. 启动并验证：`systemctl enable mtg && systemctl start mtg && systemctl status mtg`
8. 确认端口监听：`ss -tlnp | grep 443`
9. 生成 Telegram 连接链接提供给用户

### 管理 MTG 服务

```bash
systemctl status mtg    # 查看状态
systemctl restart mtg   # 重启
systemctl stop mtg      # 停止
journalctl -u mtg -f    # 实时查看日志
```

---

## 安全规则

- **敏感信息不输出**：Secret、密码、私钥内容不直接显示，提示用户自行保存
- **操作前确认**：执行破坏性命令（rm、stop、uninstall）前必须向用户确认
- **不推送内部文件**：`.workbuddy/` 目录仅用于本地内存，不提交到 Git
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
| 3X-UI 面板无法访问 | 检查防火墙是否放行面板端口、确认 x-ui 服务运行中 |
