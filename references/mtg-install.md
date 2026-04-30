# MTG (MTProto Proxy) 安装参考

## 当前安装详情

| 项目 | 信息 |
|------|------|
| 安装路径 | /usr/local/bin/mtg |
| 配置文件 | /etc/mtg/config.toml |
| 服务文件 | /etc/systemd/system/mtg.service |
| 版本 | v2.2.8 (MTProto proxy) |
| 安装方式 | 直接下载二进制文件 |

---

## 安装方式一：官方推荐（使用 release 二进制）

```bash
# 1. 下载最新版本
cd /tmp
wget https://github.com/9seconds/mtg/releases/latest/download/mtg-linux-amd64.tar.gz

# 2. 解压
tar -xzf mtg-linux-amd64.tar.gz

# 3. 移动到系统目录
mv mtg /usr/local/bin/
chmod +x /usr/local/bin/mtg

# 4. 验证安装
mtg --version
```

## 安装方式二：Docker 安装

```bash
# 运行 MTG 容器
docker run -d \
  --name mtg \
  --restart always \
  -p 443:443 \
  -e MTG_SECRET="your-secret-here" \
  9seconds/mtg:latest
```

## 完整安装脚本（一键安装）

```bash
#!/bin/bash

# 安装 MTG
wget -qO- https://github.com/9seconds/mtg/releases/latest/download/mtg-linux-amd64.tar.gz | tar -xz -C /tmp
mv /tmp/mtg /usr/local/bin/
chmod +x /usr/local/bin/mtg

# 创建配置目录
mkdir -p /etc/mtg

# 生成 secret
SECRET=$(mtg generate-secret example.com | head -1)

# 创建配置文件
cat > /etc/mtg/config.toml << EOF
secret = "$SECRET"
bind-to = "0.0.0.0:443"
EOF

# 创建 systemd 服务
cat > /etc/systemd/system/mtg.service << 'EOF'
[Unit]
Description=MTG MTProto Proxy
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mtg run /etc/mtg/config.toml
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable mtg
systemctl start mtg

echo "MTG 安装完成！"
echo "Secret: $SECRET"
echo "链接: https://t.me/proxy?server=YOUR_IP&port=443&secret=$SECRET"
```

---

## 配置文件说明

配置文件路径：`/etc/mtg/config.toml`

```toml
secret = "<生成的 secret>"
bind-to = "0.0.0.0:443"
```

- `secret`：通过 `mtg generate-secret example.com` 生成
- `bind-to`：监听地址和端口

---

## 常用管理命令

```bash
# 查看服务状态
systemctl status mtg

# 重启服务
systemctl restart mtg

# 停止服务
systemctl stop mtg

# 查看日志
journalctl -u mtg -f

# 检查版本
mtg --version
```

---

## 生成 Telegram 连接链接

安装完成后，生成客户端连接链接：

```
https://t.me/proxy?server=<服务器IP>&port=443&secret=<SECRET>
```

或使用 `tg://` 协议：

```
tg://proxy?server=<服务器IP>&port=443&secret=<SECRET>
```
