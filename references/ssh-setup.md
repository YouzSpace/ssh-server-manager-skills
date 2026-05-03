# SSH 密钥配置

## 检查已有密钥

```bash
ls ~/.ssh/*.pub
```

若已有 ed25519 密钥，直接使用。

## 生成新密钥

```bash
ssh-keygen -t ed25519 -f <私钥路径> -N "" -C "ssh-server-manager"
```

## 部署公钥到服务器

将公钥复制到服务器 `~/.ssh/authorized_keys`，可使用 ssh-copy-id 或手动追加：

```bash
ssh-copy-id -i <私钥> <user>@<IP>
```

## 验证连接

```bash
ssh -i <私钥> -o StrictHostKeyChecking=no <user>@<IP> "echo ok"
```

返回 `ok` → 连接成功。失败 → 检查私钥权限（600）和 authorized_keys 内容。

## 首次连接采集服务器信息

```bash
ssh -i <私钥> <user>@<IP> "uname -a && free -h && df -h / && cat /etc/os-release"
```
