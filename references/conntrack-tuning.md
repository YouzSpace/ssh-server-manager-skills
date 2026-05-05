# conntrack 连接追踪调优

> **性质**：Linux 内核连接追踪模块调优参考。
> **用途**：防止 conntrack 表满导致新连接被丢弃。

---

## 一、什么是 conntrack

conntrack 是 Linux 内核的连接追踪模块，iptables 的状态检测（`ESTABLISHED,RELATED`）和 `recent` 模块都依赖它。

**如果追踪表满了，新连接会被直接丢弃**，症状是：
- SSH 能连，但代理突然连不上
- 部分网站打不开，或连接超时
- 防火墙规则没问题，ss -tlnp 显示服务在监听
- 重启后恢复正常，但不久又出现

---

## 二、核心参数（加入 `/etc/sysctl.d/99-security.conf`）

```bash
# 最大追踪连接数（最重要）
# 默认 2048，代理服务器很容易满
# 计算建议：每 1GB 内存 ≈ 16384
# 977MB 内存 → 16384
# 2GB 内存 → 32768
net.netfilter.nf_conntrack_max = 16384

# 已建立连接超时（很重要）
# 默认 432000 = 5 天，太长了！
# 缩短为 24 小时，让连接更快释放
net.netfilter.nf_conntrack_tcp_timeout_established = 86400

# UDP 连接超时（代理服务器重要）
# 默认 30，代理 UDP 流量需要更长
net.netfilter.nf_conntrack_udp_timeout = 60
net.netfilter.nf_conntrack_udp_timeout_stream = 120
```

---

## 三、应用配置

```bash
# 写入 /etc/sysctl.d/99-security.conf 后执行
sysctl --system

# 验证
sysctl net.netfilter.nf_conntrack_max
sysctl net.netfilter.nf_conntrack_tcp_timeout_established
```

---

## 四、模块持久化（关键 ⚠️）

**踩坑记录**：配置文件内容正确，但 `nf_conntrack_max` 等参数重启后不生效。根因是 `nf_conntrack` 模块未在开机时自动加载，`systemd-sysctl` 应用配置时 conntrack 参数不存在被**静默跳过**。

### 必须执行的两步

**第 1 步**：确保模块开机自动加载

```bash
echo "nf_conntrack" > /etc/modules-load.d/conntrack.conf
```

**第 2 步**：创建 systemd oneshot 服务，在 `systemd-sysctl` 之前先加载模块再应用配置

```bash
cat > /etc/systemd/system/conntrack-sysctl.service << 'EOF'
[Unit]
Description=Load nf_conntrack and apply sysctl
Before=systemd-sysctl.service
After=modules-load.service

[Service]
Type=oneshot
ExecStart=/sbin/modprobe nf_conntrack
ExecStart=/sbin/sysctl -p /etc/sysctl.d/99-security.conf
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl enable conntrack-sysctl.service
```

### 验证

```bash
# 重启后验证（必须重启才算真正验证）
sysctl net.netfilter.nf_conntrack_max    # 必须返回 16384
sysctl net.netfilter.nf_conntrack_tcp_timeout_established  # 必须返回 86400
```

### 为什么需要两层保障？

| 机制 | 作用 |
|------|------|
| `/etc/modules-load.d/conntrack.conf` | 内核层面：开机时加载 `nf_conntrack` 模块 |
| `conntrack-sysctl.service` | 确保在 `systemd-sysctl` 读取配置之前，模块已就绪 |

> **重装系统后恢复 checklist**：除了执行 `modprobe nf_conntrack && sysctl -p`，**必须**创建上述两个文件，否则重启后参数又会丢失。

---

## 五、查看当前状态

```bash
# 当前已追踪连接数
cat /proc/sys/net/netfilter/nf_conntrack_count

# 最大追踪数
cat /proc/sys/net/netfilter/nf_conntrack_max

# 使用率
awk "BEGIN {printf \"%.2f%%\", $(cat /proc/sys/net/netfilter/nf_conntrack_count) / $(cat /proc/sys/net/netfilter/nf_conntrack_max) * 100}"
```

---

## 六、为什么代理服务器特别容易满？

- 默认 `nf_conntrack_max=2048`，太少了
- 已建立连接超时默认 **5 天**，连接释放极慢
- 每开一个网页 = 多个新连接

**解决**：调大 `nf_conntrack_max` + 缩短 `nf_conntrack_tcp_timeout_established`

---

*最后更新：2026-05-05*
