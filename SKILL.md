---
name: ssh-server-manager
description: >
  SSH 服务器远程操作管理 Skill。支持通过 SSH 密钥连接远程 Linux 服务器，
  执行命令、管理文件、安装软件、部署服务、查看状态等全方位服务器操作。
  当用户提到连接服务器、SSH、远程服务器、服务器操作、安装软件到服务器、
  查看服务器状态、管理服务器服务、部署到服务器等场景时触发此 Skill。
---

# SSH Server Manager Skill

通过 SSH 连接远程 Linux 服务器并执行操作的完整工作流。

---

## 初始化连接

第一次连接服务器时，按以下步骤操作：

1. **测试连通性**
   ```bash
   powershell -Command "Test-NetConnection -ComputerName <IP> -Port 22"
   ```
   端口通 → 继续；不通 → 提示用户检查防火墙/安全组。

2. **优先使用 SSH 密钥认证（推荐）**
   - 生成密钥对（如不存在）：
     ```bash
     ssh-keygen -t ed25519 -f <私钥路径> -N "" -C "workbuddy@agent"
     ```
   - 私钥保存在本地：`~/.ssh/`  (Windows: `%USERPROFILE%\.ssh\`)
   - 提示用户将公钥添加到服务器 `~/.ssh/authorized_keys`
   - 用户提供确认后，测试连接：
     ```bash
     ssh -i <私钥路径> -o StrictHostKeyChecking=no <user>@<IP> "echo ok"
     ```

3. **备选：密码认证（不推荐，仅在用户明确要求时使用）**
   - Windows 下 `sshpass` 不可用，需提示用户手动输入密码
   - 或建议用户改用密钥认证

---

## 连接参数管理

每次操作服务器时，从以下来源获取连接信息（按优先级）：

1. 用户本次对话中提供的 IP/域名/用户名/端口
2. 内存文件（`.workbuddy/memory/MEMORY.md` 或 `YYYY-MM-DD.md`）中已保存的服务器信息
3. 如果用户有多个服务器，询问用户选择哪一台

### 保存连接信息到内存

成功连接后，将以下信息写入内存文件：
- 服务器 IP / 域名
- SSH 端口（默认 22）
- 用户名
- 私钥路径
- 服务器系统信息（OS、架构、内存、磁盘）
- 已部署的重要服务（端口、密钥、域名等）

---

## SSH 超时保活配置

连接频繁断开时，需同时配置客户端和服务器端，双方互相发送心跳包保持连接。

### 客户端配置（Windows）

修改文件 `~/.ssh/config`，添加或更新 Host 配置：

```
Host <别名>
    HostName <服务器IP>
    User <用户名>
    IdentityFile ~/.ssh/<私钥文件>
    ServerAliveInterval 30      # 每30秒发送心跳包
    ServerAliveCountMax 3       # 最多允许3次无响应
    ConnectTimeout 15           # 连接超时15秒
    ConnectionAttempts 3        # 重试3次
```

### 服务器端配置（Linux）

修改文件 `/etc/ssh/sshd_config`：

```bash
TCPKeepAlive yes              # 启用TCP层心跳
ClientAliveInterval 30        # 服务器每30秒检测客户端
ClientAliveCountMax 3         # 最多允许3次无响应
```

重启 SSH 服务：
```bash
systemctl restart sshd
```

### 原理

```
客户端 ←────心跳包────→ 服务器
   ↑                      ↑
每30秒发送            每30秒检测
```

双方都在发送"我还活着"的信号，连接不会被中间网络设备（路由器、防火墙）断开。

| 对比项 | 配置前 | 配置后 |
|--------|--------|--------|
| 空闲超时 | 2-3分钟 | 90秒（可配置） |
| 自动重连 | 无 | 3次尝试 |
| 连接稳定性 | 容易断开 | 稳定保持 |

---

## 常用操作模板

### 查看服务器状态
```bash
ssh -i <私钥> <user>@<IP> "uptime && free -h && df -h && docker ps"
```

### 执行任意命令
```bash
ssh -i <私钥> <user>@<IP> "<command>"
```

### 上传文件到服务器
```bash
scp -i <私钥> <本地文件> <user>@<IP>:<远程路径>
```

### 从服务器下载文件
```bash
scp -i <私钥> <user>@<IP>:<远程文件> <本地路径>
```

### 在服务器上执行本地脚本
```bash
ssh -i <私钥> <user>@<IP> "bash -s" < <本地脚本文件>
```

---

## 安装 MTG (MTProto Proxy)

> 详细安装参考：[references/mtg-install.md](references/mtg-install.md)

**当前安装详情：**

| 项目 | 信息 |
|------|------|
| 安装路径 | /usr/local/bin/mtg |
| 配置文件 | /etc/mtg/config.toml |
| 服务文件 | /etc/systemd/system/mtg.service |
| 版本 | v2.2.8 |
| 安装方式 | 直接下载二进制文件 |

**安装工作流：**

1. 检查服务器环境（OS、架构）
2. 下载最新版本二进制文件（或使用 Docker 方式）
3. 安装到 `/usr/local/bin/mtg`
4. 生成 Secret：`mtg generate-secret example.com`
5. 创建配置文件 `/etc/mtg/config.toml`
6. 创建 systemd 服务并启动
7. 验证运行状态（`systemctl status mtg`）
8. 生成 Telegram 连接链接：
   ```
   https://t.me/proxy?server=<域名或IP>&port=443&secret=<SECRET>
   ```
9. 如有域名，提示用户设置 DNS A 记录指向服务器 IP
10. 提醒 Cloudflare 用户关闭代理（橙色云朵变灰色）

**常用管理命令：**
```bash
systemctl status mtg    # 查看状态
systemctl restart mtg   # 重启
systemctl stop mtg      # 停止
journalctl -u mtg -f    # 查看日志
```

---

## 其他常见操作参考

| 操作 | 说明 |
|------|------|
| 安装软件 | `apt-get install -y <包名>` 或 `yum install -y <包名>` |
| 管理 MTG 代理 | `systemctl status/restart/stop mtg`、`journalctl -u mtg -f` |
| 查看日志 | `journalctl -u <服务名>` 或直接读 log 文件 |
| 管理防火墙 | `ufw`、`firewalld`、`iptables` 根据系统选择 |
| 设置定时任务 | `crontab -e` 或通过 `automation_update` 工具 |
| 清理磁盘 | `docker system prune -f`、`apt-get clean` |
| 查看网络流量 | `vnstat`、`iftop`（需安装）|
| 管理 systemd 服务 | `systemctl status/enable/disable/restart <服务>` |

---

## 注意事项

- **内存小于 1GB 的服务器**：避免运行重型服务，注意磁盘空间
- **防火墙**：Docker 映射的端口需同时确保云安全组已放行
- **Cloudflare**：使用域名时，若用了 Cloudflare，需关闭代理（DNS only）
- **多用户分享代理**：提醒用户注意资源限制和安全风险
- **敏感信息**：Secret、密码等不直接显示在最终输出中（可提示用户保存）
