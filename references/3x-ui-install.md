# 3X-UI 面板安装参考

## 概述

3X-UI 是一个基于 Xray 的多协议代理管理面板，支持 VLESS、VMess、Trojan、Shadowsocks 等协议，提供 Web 管理界面。

项目地址：https://github.com/MHSanaei/3x-ui

---

## 安装步骤

### 1. 执行官方安装脚本

```bash
bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
```

若安装脚本无法访问，参考 https://github.com/MHSanaei/3x-ui 获取最新安装方式。

### 2. 安装配置

安装脚本是交互式的，按以下策略选择：

| 选项 | 选择 |
|------|------|
| 端口 | 随机生成 |
| 账号 | 随机生成 |
| 密码 | 随机生成 |
| 其他 | 全部默认 |

### 3. 记录面板信息

安装完成后，脚本会输出以下信息，**务必保存**：

- 面板地址：`http://<服务器IP>:<端口>`
- 登录账号
- 登录密码
- 面板路径（如 `/path`）

---

## 创建入站

安装完成后需要在面板中创建入站才能使用：

1. 登录面板 → 左侧菜单 **入站列表** → **添加入站**
2. 常用协议推荐：
   - **VLESS + WebSocket**：适合配合 Cloudflare CDN
   - **Trojan**：伪装 HTTPS 流量，隐蔽性好
3. 设置端口、用户、流量限制后保存
4. 客户端可通过面板生成的链接/二维码导入配置

---

## 域名绑定

### 步骤

1. 在域名 DNS 添加 A 记录，指向服务器 IP
2. 等待 DNS 生效（通常几分钟）
3. 在 3X-UI 面板中设置域名，或通过命令行配置
4. 配置 SSL 证书（通过 x-ui CLI）：

   ```bash
   x-ui  # 进入管理菜单
   # 选择 SSL Certificate Management → Get SSL (Domain)
   # 输入域名，端口默认回车
   # ACME 选 n（首次申请）
   # 是否为面板设置此证书？选 y
   ```

   > 也可通过面板 Web 界面申请，或手动配置 Nginx 反向代理 + SSL

### 域名 + Cloudflare 配置

1. **购买域名**：推荐 [Spaceship](https://www.spaceship.com/zh/)，选择便宜后缀（如六位数字 xyz），注册地选非大陆
2. **托管到 Cloudflare**：添加域名 → 免费套餐 → 添加 A 记录（名称填前缀或 `@`，IPv4 填服务器 IP，代理关闭）→ 激活
3. **替换 Nameserver**：回到域名注册商，将 DNS 服务器替换为 Cloudflare 提供的 Nameserver

> ⚠️ Cloudflare 代理必须关闭（DNS only / 灰色云朵），否则 WebSocket 等协议无法正常连接

---

## BBR 优化

BBR（Bottleneck Bandwidth and RTT）是 Google 开发的 TCP 拥塞控制算法，可显著提升网络传输性能。

### 启用 BBR

```bash
echo 'net.core.default_qdisc=fq' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_congestion_control=bbr' >> /etc/sysctl.conf
sysctl -p
```

### 验证 BBR

```bash
sysctl net.ipv4.tcp_congestion_control
```

输出 `net.ipv4.tcp_congestion_control = bbr` 即为成功。

---

## 常用管理命令

```bash
# 查看面板状态
systemctl status x-ui

# 启动面板
x-ui start

# 停止面板
x-ui stop

# 重启面板
x-ui restart

# 查看面板状态
x-ui status

# 查看面板日志
journalctl -u x-ui -f

# 更新面板
x-ui update

# 卸载面板
x-ui uninstall
```

---

## 验证安装

1. 确认面板服务运行中：`systemctl status x-ui`
2. 确认端口监听：`ss -tlnp | grep x-ui`
3. 浏览器访问面板地址，确认能正常登录
4. 创建节点并测试连接

---

## 故障排查

| 现象 | 排查步骤 |
|------|----------|
| 面板无法访问 | 检查防火墙/安全组是否放行面板端口。若使用 https 无法访问，尝试去掉 `s` 改用 http |
| 面板无法访问 | 确认 x-ui 服务运行中：`systemctl status x-ui` |
| 登录失败 | 确认账号密码正确，可重置：`x-ui reset` |
| 节点无法连接 | 检查节点端口是否在防火墙中放行 |
| 节点无法连接 | 查看 xray 日志：面板 → 日志 → 查看错误信息 |
| SSL 证书申请失败 | 确认域名 DNS 已正确指向服务器 IP |
| WebSocket 连接失败 | Cloudflare 用户确认已关闭代理（DNS only） |

---

## 安全建议

1. **修改默认端口**：避免使用常见端口（如 80、443）作为面板端口
2. **强密码**：使用随机生成的强密码
3. **定期更新**：通过 `x-ui update` 保持面板版本最新
4. **防火墙**：仅开放必要端口，面板端口可限制 IP 访问
5. **HTTPS**：生产环境务必配置 SSL 证书
