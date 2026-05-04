# 防火墙部署参考

> **性质**：通用防火墙部署手册，不绑定具体端口值。
> **用途**：部署防火墙、恢复配置。
> **核心原则**：默认全关，只开确实在用的端口。本地服务（127.0.0.1）禁止放行。部署前必须 `ss -tlnp` 确认监听端口。

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
├─ ⑫⑬⑭  HTTP 端口 <ACME_PORT> → 限速处理（域名证书 ACME 验证）
│     默认 80，具体端口取决于证书颁发机构和 Web 服务器配置
│     平时无服务监听，证书申请时临时放行，限速防滥用
│
├─ ⑮⑯  Xray 代理端口 <PROXY_PORT> → TCP + UDP 直接放行，不限速
│     代理每开一个网页就是新连接，限速会导致断连和卡顿
│     ⚠️ 必须在「所有 UDP 丢弃」规则之前，否则 UDP 被挡
│
├─ ⑰  ICMP（ping）→ 放行
│
├─ ⑱  无效状态包 → 丢弃
│
├─ ⑲  所有 UDP → 丢弃
│     服务器没有 UDP 服务（代理端口已在前面放过），全丢防 UDP 反射攻击
│
├─ ⑳  IP 分片包 → 丢弃
│
├─ ㉑  XMAS 扫描包 → 丢弃
│
├─ ㉒  NULL 扫描包 → 丢弃
│
└─ 兜底：默认策略 DROP
      以上规则都没匹配到的，全部丢弃
      白名单模式：没说能进的，都不让进
```

> ⚠️ **禁止**添加通用 SYN 限速规则（`tcp --syn -m limit`），会绕过白名单。默认 DROP 已天然防 SYN 洪水。特定端口限速用 `recent` 模块（见第二节）。

**IPv6 防火墙**（必须与 IPv4 白名单完全对应，限速+放行+高级防护全部同步）：

```
① 已建立连接 → 放行
② 本地回环 → 放行
③④⑤  SSH <SSH_PORT> → 限速处理（与 IPv4 参数一致）
⑥⑦⑧  管理面板 <ADMIN_PORT> → 限速处理
⑨⑩⑪  订阅端口 <SUBSCRIPTION_PORT> → 限速处理
⑫⑬⑭  HTTP <ACME_PORT> → 限速处理（域名证书 ACME 验证，默认 80）
⑮⑯  Xray 代理端口 <PROXY_PORT> TCP+UDP → 放行（不限速）
⑰ ICMPv6 → 放行（IPv6 地址分配、邻居发现依赖它）
⑱  无效状态包 → 丢弃
⑲  所有 UDP → 丢弃
⑳  XMAS 扫描包 → 丢弃
㉑  NULL 扫描包 → 丢弃
兜底 默认 DROP
```

> ⚠️ IPv6 规则必须与 IPv4 完全对应。新增 IPv4 白名单端口时，必须同步添加 IPv6 规则。限速端口的 `recent` 记录表名加 `6` 后缀（`ssh6`/`admin6`/`sub6`/`http6`）避免与 IPv4 冲突。

---

## 二、限速原理

限速**不是**限制网速，而是限制「**新建连接**」的速度。用 iptables 的 `recent` 模块实现，每组 3 条规则配合：

```bash
# SET → 记录这个 IP 刚访问了端口
iptables -A INPUT -p tcp --dport <PORT> -m recent --set --name <NAME> --rsource
# DROP → 指定时间内超过指定次数就丢弃
iptables -A INPUT -p tcp --dport <PORT> -m recent --update --seconds <TIME> --hitcount <COUNT> --name <NAME> --rsource -j DROP
# ACCEPT → 没超限放行
iptables -A INPUT -p tcp --dport <PORT> -j ACCEPT
```

**关键理解**：
- ✅ 限速只针对「新建连接」，已建立的连接不受影响
- ❌ **代理端口不能限速**，每开一个网页就是新连接，限速会断连
- 参数参考 → **第六节 端口放行决策表**

---

## 三、部署脚本（占位符模板）

### IPv4 防火墙

```bash
#!/bin/bash
# IPv4 防火墙部署脚本（替换占位符为实际端口值）

# 端口配置
SSH_PORT=<SSH_PORT>                     # 通常 22
ADMIN_PORT=<ADMIN_PORT>                 # x-ui 管理面板
SUBSCRIPTION_PORT=<SUBSCRIPTION_PORT>   # x-ui 订阅
PROXY_PORT=<PROXY_PORT>                 # Xray 代理
ACME_PORT=<ACME_PORT>                   # 域名证书验证（通常 80）

# 限速参数
SSH_RATE="10"; SSH_TIME="60"
ADMIN_RATE="20"; ADMIN_TIME="60"
SUB_RATE="20"; SUB_TIME="60"
ACME_RATE="20"; ACME_TIME="60"

# ========== 开始部署 ==========

# 1. 清空规则
iptables -F; iptables -X; iptables -Z

# 2. 默认策略（白名单模式）
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 3. 基础规则（必须最先）
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT

# 4. SSH 限速（3 条：SET → DROP → ACCEPT）
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

# 7. HTTP 限速（域名证书验证，平时无服务监听）
iptables -A INPUT -p tcp --dport $ACME_PORT -m recent --set --name http --rsource
iptables -A INPUT -p tcp --dport $ACME_PORT -m recent --update --seconds $ACME_TIME --hitcount $ACME_RATE --name http --rsource -j DROP
iptables -A INPUT -p tcp --dport $ACME_PORT -j ACCEPT

# 8. 代理端口（TCP+UDP 完全放行）← 必须在 UDP 丢弃之前！
iptables -A INPUT -p tcp --dport $PROXY_PORT -j ACCEPT
iptables -A INPUT -p udp --dport $PROXY_PORT -j ACCEPT

# 9. ICMP
iptables -A INPUT -p icmp -j ACCEPT

# 10. 高级防护
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
iptables -A INPUT -p udp -j DROP
iptables -A INPUT -f -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP

# 11. 保存（必须！否则重启后丢失）
iptables-save > /etc/iptables/rules.v4

echo "IPv4 防火墙部署完成"
iptables -L INPUT -n --line-numbers
```

### IPv6 防火墙

与 IPv4 脚本结构完全一致，仅需替换：

| 差异项 | IPv4 | IPv6 |
|--------|------|------|
| 命令 | `iptables` | `ip6tables` |
| 清空 | `-F -X -Z` | `-F -X`（无 `-Z`） |
| ICMP | `-p icmp` | `-p icmpv6` |
| 限速表名 | `ssh`/`admin`/`sub`/`http` | `ssh6`/`admin6`/`sub6`/`http6` |
| 保存 | `iptables-save > rules.v4` | `ip6tables-save > rules.v6` |

> ⚠️ ICMPv6 必须放行——IPv6 地址分配（SLAAC）和邻居发现（NDP）依赖它。

---

## 四、规则持久化

iptables 规则默认存在内存中，**重启后全部消失**。部署后必须安装持久化工具：

```bash
echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
apt install -y iptables-persistent
systemctl enable netfilter-persistent

# 手动保存（每次修改规则后必须执行）
iptables-save > /etc/iptables/rules.v4
ip6tables-save > /etc/iptables/rules.v6
```

---

## 五、常用命令速查

| 操作 | 命令 |
|------|------|
| 查看规则 | `iptables -L INPUT -n --line-numbers`（IPv6 用 `ip6tables`） |
| 保存规则 | `iptables-save > /etc/iptables/rules.v4`（IPv6 用 `ip6tables-save > rules.v6`） |
| 恢复规则 | `iptables-restore < /etc/iptables/rules.v4`（IPv6 用 `ip6tables-restore`） |
| 清理旧连接 | `ss -K sport = :<端口>` + `conntrack -D -p tcp --dport <端口>` |
| 临时关闭（危险） | `iptables -P INPUT ACCEPT && iptables -F INPUT` |

---

## 六、端口放行决策表

| 服务类型 | 放行方式 | 为什么 | 举例 |
|----------|----------|--------|------|
| SSH | TCP 限速（60s/10次） | 登录只需 1 次连接 | 端口 22 |
| 管理面板 | TCP 限速（60s/20次） | 有登录页面，限速防暴力破解 | x-ui 12362 |
| 订阅服务 | TCP 限速（60s/20次） | 客户端定期拉取，频率低 | x-ui 订阅端口 |
| 域名证书验证 | TCP 限速（60s/20次） | ACME HTTP 验证，平时无服务监听，默认 80 | 80 / 443 等 |
| 代理 / VPN | TCP+UDP 完全放行 | 每开一个网页就是新连接，限速会断连 | xray 代理端口 |
| 游戏服务器 | TCP+UDP 完全放行 | 游戏需要高频通信，限速导致延迟高 | MC、Palworld |
| 本地端口 | **不放行** | 绑定 127.0.0.1，外部不可达 | xray 11111/62789 |

---

## 七、新增或删除端口规则

> **信息不全时禁止执行，先向用户确认。**

### 新增端口

| # | 步骤 | 说明 | 完成 |
|---|------|------|------|
| 1 | 确认需求 | 端口号、协议（TCP/UDP/TCP+UDP）、服务类型（参考第六节决策表） | ☐ |
| 2 | 确认服务监听 | `ss -tlnp \| grep <端口>` | ☐ |
| 3 | 检查当前规则 | `iptables -L INPUT -n --line-numbers` + `ip6tables`，找到插入位置 | ☐ |
| 4 | 添加 IPv4 规则 | 限速端口插入 3 条（SET→DROP→ACCEPT），完全放行插入 TCP+UDP 各 1 条 | ☐ |
| 5 | 添加 IPv6 规则 | 必须同步！表名加 `6` 后缀 | ☐ |
| 6 | 持久化保存 | `iptables-save > /etc/iptables/rules.v4` + `ip6tables-save > /etc/iptables/rules.v6` | ☐ |
| 7 | 验证规则 | `iptables -L INPUT -n --line-numbers` + `ip6tables`，确认规则存在且位置正确 | ☐ |
| 8 | 验证连通 | 从外部测试端口可达（`telnet` / `nc`） | ☐ |

### 删除端口

| # | 步骤 | 说明 | 完成 |
|---|------|------|------|
| 1 | 确认需求 | 端口号、规则类型（限速 3 条 / 完全放行 2 条） | ☐ |
| 2 | 检查当前规则 | `iptables -L INPUT -n --line-numbers \| grep <端口>` + `ip6tables`，记录行号 | ☐ |
| 3 | 删除规则 | 从大行号往小行号删（防止行号前移），IPv4 + IPv6 同步删除 | ☐ |
| 4 | 清理旧连接 | `ss -K sport = :<端口>` + `conntrack -D -p tcp --dport <端口>`，验证 ESTAB 归零 | ☐ |
| 5 | 持久化保存 | `iptables-save > /etc/iptables/rules.v4` + `ip6tables-save > /etc/iptables/rules.v6` | ☐ |
| 6 | 验证移除 | `iptables/ip6tables -L INPUT -n \| grep <端口>`，应无输出 | ☐ |

### 命令示例

**新增限速端口**（以 8080 为例）：

```bash
iptables -I INPUT <行号> -p tcp --dport 8080 -m recent --set --name web8080 --rsource
iptables -I INPUT <行号+1> -p tcp --dport 8080 -m recent --update --seconds 60 --hitcount 20 --name web8080 --rsource -j DROP
iptables -I INPUT <行号+2> -p tcp --dport 8080 -j ACCEPT
ip6tables -I INPUT <行号> -p tcp --dport 8080 -m recent --set --name web8080_6 --rsource
ip6tables -I INPUT <行号+1> -p tcp --dport 8080 -m recent --update --seconds 60 --hitcount 20 --name web8080_6 --rsource -j DROP
ip6tables -I INPUT <行号+2> -p tcp --dport 8080 -j ACCEPT
```

**新增完全放行端口**（以 443 为例）：

```bash
iptables -I INPUT <行号> -p tcp --dport 443 -j ACCEPT
iptables -I INPUT <行号+1> -p udp --dport 443 -j ACCEPT
ip6tables -I INPUT <行号> -p tcp --dport 443 -j ACCEPT
ip6tables -I INPUT <行号+1> -p udp --dport 443 -j ACCEPT
```

**删除端口规则**：

```bash
iptables -D INPUT <大行号>          # 从大往小删
iptables -D INPUT <小行号>
ip6tables -D INPUT <对应行号>       # 同步 IPv6
ss -K sport = :<端口>               # 清理旧连接
conntrack -D -p tcp --dport <端口>  # 清理连接跟踪
```

**持久化**（每次变更后必须执行）：

```bash
iptables-save > /etc/iptables/rules.v4
ip6tables-save > /etc/iptables/rules.v6
```

---

*最后更新：2026-05-04*
