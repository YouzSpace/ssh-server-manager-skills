# SSH 超时保活配置

当用户反馈 SSH 连接频繁断开时，执行以下配置。

## 客户端配置

读取 `~/.ssh/config`，检查目标 Host 是否已包含保活参数。若未配置，追加：

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

## 服务器端配置

远程修改 `/etc/ssh/sshd_config`，确保以下配置已启用（未注释）：

```
TCPKeepAlive yes
ClientAliveInterval 30
ClientAliveCountMax 3
```

重启 SSH 服务：

```bash
ssh -i <私钥> <user>@<IP> "systemctl restart sshd"
```

## 验证

配置完成后，执行一个长时间命令（如 `top -b -n 1`），确认连接不再中途断开。
