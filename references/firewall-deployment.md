# 防火墙部署参考

> **性质**：通用防火墙部署手册，不绑定具体端口值。
> **用途**：部署防火墙、恢复配置。
> **端口配置**：见具体设备的配置备份文档（重装后恢复用）。
> ⚠️ **核心原则**：默认全关，只开确实在用的端口，多开一个端口多一份风险。本地服务（127.0.0.1）禁止放行。部署前必须 `ss -tlnp` 确认哪些端口在监听。

---

## 一、防火墙架构（数据包处理流程）

防火墙按照**规则列表从上到下**逐条检查数据包，匹配到就执行动作，不再看后面的规则。

```
数据包到达服务器
│
├─ ① 已建立的连接（正在用的 SSH、正在传的数据）→ 直接放行
│     如果没有这条，SSH 连上后后续数据包被丢弃，连接立刻断开
│
├─ ② 本地回环（127.0.0.1，服务之间内部通信）→ 放行
│     xray 的 metrics/API 通过 127.0.0.1 通信，不放行会断
│
├─ ③④⑤  SSH 端口 <SSH_PORT> → 限速处理
│     记录连接 → 指定时间内超过指定次数就丢弃 → 没超限放行
│     攻击者的扫描器每秒尝试几十次，会被限速卡住
│     你自己登录只用 1 次连接，完全不受影响
│
├─ ⑥⑦⑧  管理面板 <ADMIN_PORT> → 限速处理（防暴力破解）
│
├─ ⑨⑩⑪  订阅端口 <SUBSCRIPTION_PORT> → 限速处理
│
├─ ⑫⑬  Xray 代理端口 <PROXY_PORT> → TCP + UDP 直接放行，不限速
│     代理每开一个网页就是新连接，限速会导致断连和卡顿
│     ⚠️ 必须在「所有 UDP 丢弃」规则之前，否则 UDP 被挡
│
├─ ⑭  ICMP（ping）→ 放行
│
├─ ⑮  无效状态包 → 丢弃
│
├─ ⑯  所有 UDP → 丢弃
│     服务器没有 UDP 服务（代理端口已在前面放过），全丢防 UDP 反射攻击
│
├─ ⑰  IP 分片包 → 丢弃
│
├─ ⑱  XMAS 扫描包 → 丢弃
│
├─ ⑲  NULL 扫描包 → 丢弃
│
└─ 兜底：默认策略 DROP
      以上规则都没匹配到的，全部丢弃
      白名单模式：没说能进的，都不让进
```

> ⚠️ **SYN 洪水防护**：不要添加通用 SYN 限速规则（`tcp --syn -m limit --limit 50/s`）。该规则没有端口限制，会 ACCEPT 所有 TCP 端口的 SYN 包，导致白名单形同虚设。默认 DROP 策略已经足够——不在白名单中的端口的 SYN 包会被 DROP，天然防 SYN 洪水。如果需要对特定端口做连接限速，使用 `recent` 模块（见第三节）。

**IPv6 防火墙**（必须与 IPv4 白名单完全对应）：

```
① 已建立连接 → 放行
② 本地回环 → 放行
③④  Xray 代理端口 <PROXY_PORT> TCP+UDP → 放行（不限速）
⑤ SSH <SSH_PORT> → 放行
⑥ 管理面板 <ADMIN_PORT> → 放行
⑦ 订阅端口 <SUBSCRIPTION_PORT> → 放行
⑧ ICMPv6 → 放行（IPv6 地址分配、邻居发现依赖它）
兜底 默认 DROP
```

> ⚠️ IPv6 规则必须与 IPv4 完全对应。新增 IPv4 白名单端口时，必须同步添加 IPv6 规则。

---

## 二、限速原理（防暴力破解的核心）

限速**不是**限制网速，而是限制「**新建连接**」的速度。用 iptables 的 `recent` 模块实现，每组 3 条规则配合：

```bash
# 第 1 条：记录 — "这个 IP 刚访问了端口 <SSH_PORT>"
iptables -A INPUT -p tcp --dport <SSH_PORT> -m recent --set --name ssh --rsource

# 第 2 条：检查 — "这个 IP 在指定时间内访问了几次"，超过指定次数就丢弃
iptables -A INPUT -p tcp --dport <SSH_PORT> -m recent --update --seconds <TIME_WINDOW> --hitcount <MAX_CONNECTIONS> --name ssh --rsource -j DROP

# 第 3 条：没超限 → 放行
iptables -A INPUT -p tcp --dport <SSH_PORT> -j ACCEPT
```

**关键理解**：
- ✅ 限速只针对「新建连接」，已经连上的连接完全不受影响
- ✅ 你 SSH 登录只需 **1 次连接**，10 次/60秒绰绰有余
- ✅ 攻击者每秒尝试几十次，会被限速卡住
- ❌ **代理端口不能限速**，每开一个网页就是新连接，限速会断连

### 推荐限速参数

| 服务 | 参数 | 为什么 |
|------|------|--------|
| SSH | 60秒/10次 | 登录只需 1 次连接，10 次绰绰有余 |
| 管理面板 | 60秒/20次 | 浏览器加载页面会建立几个连接 |
| 订阅接口 | 60秒/20次 | 客户端定期拉取，频率低 |
| 代理端口 | **不限速** | 每开一个网页就是新连接，限速会断连 |

---

## 三、完整部署命令（带占位符）

### IPv4 防火墙

```bash
#!/bin/bash
# 防火墙部署脚本（需要替换为实际端口值）

# 端口配置（根据实际情况修改）
SSH_PORT=<SSH_PORT>           # 通常 22
ADMIN_PORT=<ADMIN_PORT>       # x-ui 管理面板端口
SUBSCRIPTION_PORT=<SUBSCRIPTION_PORT>  # x-ui 订阅端口
PROXY_PORT=<PROXY_PORT>       # Xray 代理端口

# 限速参数（可根据需要调整）
SSH_RATE="10"           # SSH 最大连接数
SSH_TIME="60"           # SSH 时间窗口（秒）
ADMIN_RATE="20"         # 管理面板最大连接数
ADMIN_TIME="60"         # 管理面板时间窗口
SUB_RATE="20"           # 订阅端口最大连接数
SUB_TIME="60"           # 订阅端口时间窗口

# ========== 开始部署 ==========

# 1. 清空现有规则
iptables -F  # 清空所有规则
iptables -X  # 删除所有自定义链
iptables -Z  # 清零所有计数器

# 2. 设置默认策略（白名单模式）
iptables -P INPUT DROP      # 入站默认丢弃
iptables -P FORWARD DROP    # 转发默认丢弃
iptables -P OUTPUT ACCEPT   # 出站默认放行

# 3. 基础规则（必须最先）
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT

# 4. SSH 限速（3 条）
iptables -A INPUT -p tcp --dport $SSH_PORT -m recent --set --name ssh --rsource
iptables -A INPUT -p tcp --dport $SSH_PORT -m recent --update --seconds $SSH_TIME --hitcount $SSH_RATE --name ssh --rsource -j DROP
iptables -A INPUT -p tcp --dport $SSH_PORT -j ACCEPT

# 5. 管理面板限速（3 条）
iptables -A INPUT -p tcp --dport $ADMIN_PORT -m recent --set --name admin --rsource
iptables -A INPUT -p tcp --dport $ADMIN_PORT -m recent --update --seconds $ADMIN_TIME --hitcount $ADMIN_RATE --name admin --rsource -j DROP
iptables -A INPUT -p tcp --dport $ADMIN_PORT -j ACCEPT

# 6. 订阅端口限速（3 条）
iptables -A INPUT -p tcp --dport $SUBSCRIPTION_PORT -m recent --set --name sub --rsource
iptables -A INPUT -p tcp --dport $SUBSCRIPTION_PORT -m recent --update --seconds $SUB_TIME --hitcount $SUB_RATE --name sub --rsource -j DROP
iptables -A INPUT -p tcp --dport $SUBSCRIPTION_PORT -j ACCEPT

# 7. 代理端口（TCP + UDP 完全放行，不限速）← 必须在"所有 UDP 丢弃"之前！
iptables -A INPUT -p tcp --dport $PROXY_PORT -j ACCEPT
iptables -A INPUT -p udp --dport $PROXY_PORT -j ACCEPT

# 8. ICMP 放行（允许 ping）
iptables -A INPUT -p icmp -j ACCEPT

# 9. 高级防护
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP  # 无效状态包
iptables -A INPUT -p udp -j DROP                         # 所有 UDP 丢弃（代理 UDP 已在前方放行）
iptables -A INPUT -f -j DROP                             # IP 分片包
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP      # XMAS 扫描
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP     # NULL 扫描

# 10. 保存规则（必须！否则重启后丢失）
iptables-save > /etc/iptables/rules.v4

echo "IPv4 防火墙部署完成"
iptables -L INPUT -n --line-numbers
```

### IPv6 防火墙

```bash
#!/bin/bash
# IPv6 防火墙部署脚本（需要替换为实际端口值）

# 端口配置（与 IPv4 一致）
SSH_PORT=<SSH_PORT>
ADMIN_PORT=<ADMIN_PORT>
SUBSCRIPTION_PORT=<SUBSCRIPTION_PORT>
PROXY_PORT=<PROXY_PORT>

# ========== 开始部署 ==========

# 1. 清空现有规则
ip6tables -F
ip6tables -X

# 2. 设置默认策略
ip6tables -P INPUT DROP
ip6tables -P FORWARD DROP
ip6tables -P OUTPUT ACCEPT

# 3. 基础规则
ip6tables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
ip6tables -A INPUT -i lo -j ACCEPT

# 4. 代理端口（TCP + UDP，不限速）← 必须在其他端口之前，与 IPv4 对应
ip6tables -A INPUT -p tcp --dport $PROXY_PORT -j ACCEPT
ip6tables -A INPUT -p udp --dport $PROXY_PORT -j ACCEPT

# 5. 端口放行（IPv6 不做限速，直接放行）
ip6tables -A INPUT -p tcp --dport $SSH_PORT -j ACCEPT
ip6tables -A INPUT -p tcp --dport $ADMIN_PORT -j ACCEPT
ip6tables -A INPUT -p tcp --dport $SUBSCRIPTION_PORT -j ACCEPT

# 6. ICMPv6 放行（必须！IPv6 地址分配、邻居发现依赖它）
ip6tables -A INPUT -p icmpv6 -j ACCEPT

# 7. 保存规则
ip6tables-save > /etc/iptables/rules.v6

echo "IPv6 防火墙部署完成"
ip6tables -L INPUT -n --line-numbers  # 验证规则
```

---

## 四、规则持久化（重启后不丢失）

iptables 规则默认存在内存中，**服务器重启后规则全部消失**。必须安装持久化工具：

```bash
# 安装持久化工具（预设 debconf 选项避免交互提示）
echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
apt install -y iptables-persistent

# 确保开机自启
systemctl enable netfilter-persistent

# 手动保存当前规则（每次修改后必须执行！）
iptables-save > /etc/iptables/rules.v4
ip6tables-save > /etc/iptables/rules.v6
```

> **重要**：每次修改 iptables/ip6tables 规则后，必须执行 `iptables-save > /etc/iptables/rules.v4` 保存，否则重启后规则丢失。

---

## 五、常用命令速查

| 操作 | 命令 |
|------|------|
| 查看规则（带行号） | `iptables -L INPUT -n --line-numbers` |
| 查看规则 + 命中统计 | `iptables -L INPUT -n -v` |
| 保存 IPv4 规则 | `iptables-save > /etc/iptables/rules.v4` |
| 保存 IPv6 规则 | `ip6tables-save > /etc/iptables/rules.v6` |
| 恢复 IPv4 规则 | `iptables-restore < /etc/iptables/rules.v4` |
| 临时关闭防火墙（危险！） | `iptables -P INPUT ACCEPT && iptables -F INPUT` |

---

## 六、端口放行决策表

| 服务类型 | 放行方式 | 为什么 | 举例 |
|----------|----------|--------|------|
| SSH | TCP 限速（60s/10次） | 登录只需 1 次连接 | 端口 22 |
| 管理面板 | TCP 限速（60s/20次） | 有登录页面，限速防暴力破解 | x-ui 12362 |
| 订阅服务 | TCP 限速（60s/20次） | 客户端定期拉取，频率低 | x-ui 订阅端口 |
| 代理 / VPN | TCP+UDP 完全放行 | 每开一个网页就是新连接，限速会断连 | xray 代理端口 |
| 游戏服务器 | TCP+UDP 完全放行 | 游戏需要高频通信，限速导致延迟高 | MC、Palworld |
| 本地端口 | **不放行** | 绑定 127.0.0.1，外部不可达 | xray 11111/62789 |

---

## 七、新增或删除端口规则

### 新增限速端口（以 8080 为例）

```bash
# 1. 查看当前规则，找到「所有 UDP 丢弃」规则的行号
iptables -L INPUT -n --line-numbers

# 2. 在「所有 UDP 丢弃」之前插入 3 条限速规则
iptables -I INPUT <行号> -p tcp --dport 8080 -m recent --set --name web8080 --rsource
iptables -I INPUT <行号+1> -p tcp --dport 8080 -m recent --update --seconds 60 --hitcount 20 --name web8080 --rsource -j DROP
iptables -I INPUT <行号+2> -p tcp --dport 8080 -j ACCEPT

# 3. 保存（必须！）
iptables-save > /etc/iptables/rules.v4
```

### 新增完全放行端口（以 443 为例）

```bash
# 1. 查看当前规则，找到"所有 UDP 丢弃"的行号
iptables -L INPUT -n --line-numbers

# 2. 在"所有 UDP 丢弃"之前插入
iptables -I INPUT <行号> -p tcp --dport 443 -j ACCEPT
iptables -I INPUT <行号+1> -p udp --dport 443 -j ACCEPT

# 3. 保存
iptables-save > /etc/iptables/rules.v4
```

> **注意**：代理端口必须同时放行 TCP 和 UDP，少一个协议代理可能连不上。

### 删除端口规则

```bash
# 1. 查看行号
iptables -L INPUT -n --line-numbers

# 2. 从大往小删！删小号会导致后面行号前移
iptables -D INPUT <大行号>
iptables -D INPUT <小行号>

# 3. 保存
iptables-save > /etc/iptables/rules.v4
```

> **注意**：限速端口要删 3 条（SET + DROP + ACCEPT），完全放行端口删 1-2 条。

---

*最后更新：2026-05-04*
