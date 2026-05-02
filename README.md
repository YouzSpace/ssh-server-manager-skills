# SSH Server Manager Skill

通过 SSH 密钥认证连接远程 Linux 服务器，执行命令、管理服务、部署应用的通用 Agent Skill。

兼容 [AgentSkills.io](https://agentskills.io) 开放标准，支持 [WorkBuddy](https://www.codebuddy.cn/docs/workbuddy/Overview)、[OpenClaw](https://docs.openclaw.ai) 等平台。

## 功能特性

- **SSH 密钥认证** — 自动生成和管理 ed25519 密钥
- **服务部署** — 可扩展的服务安装框架（含 3X-UI、MTG 参考文档）
- **文件操作** — 上传、下载服务器文件
- **状态监控** — 查看 CPU、内存、磁盘、运行中的服务
- **超时保活** — SSH 心跳配置，防止连接断开
- **故障排查** — 内置常见问题诊断流程

## 兼容平台

| 平台 | 安装路径 |
|------|----------|
| WorkBuddy | `~/.workbuddy/skills/ssh-server-manager/` |
| OpenClaw | `~/.agents/skills/ssh-server-manager/` 或 `<workspace>/skills/ssh-server-manager/` |
| 其他 AgentSkills 兼容平台 | 对应 skills 目录 |

## 前置要求

- **SSH 客户端** — Windows 自带 OpenSSH Client，macOS/Linux 自带
- **bash** — Git Bash (Windows) 或系统自带 (macOS/Linux)
- **Python 3.8+** — 可选，用于 `scripts/ssh_helper.py` 辅助工具

## 安装

### 一键安装（推荐）

复制以下命令到终端，回车即可：

```bash
curl -fsSL https://raw.githubusercontent.com/YouzSpace/ssh-server-manager-skills/main/install.sh | bash
```

脚本自动检测平台（WorkBuddy / OpenClaw），自动创建目录，自动完成安装。

### 手动安装

```bash
# WorkBuddy:
git clone https://github.com/YouzSpace/ssh-server-manager-skills.git ~/.workbuddy/skills/ssh-server-manager

# OpenClaw:
git clone https://github.com/YouzSpace/ssh-server-manager-skills.git ~/.agents/skills/ssh-server-manager
```

## 更新

运行和安装相同的命令，脚本会自动判断是安装还是更新：

```bash
curl -fsSL https://raw.githubusercontent.com/YouzSpace/ssh-server-manager-skills/main/install.sh | bash
```

或手动更新：

```bash
cd ~/.workbuddy/skills/ssh-server-manager && git pull origin main
```

也可以对 AI 助手说"更新 Skill"，助手会自动执行更新。

## 使用方式

### 触发 Skill

在支持 AgentSkills 的平台中，使用自然语言触发：

```
连接到我的服务器 192.168.1.100
查看服务器状态
在服务器上安装 Docker
```

### 首次连接流程

1. Skill 自动测试 SSH 连通性
2. 检查/生成 SSH 密钥
3. 提示用户将公钥添加到服务器
4. 验证连接成功
5. 展示选项菜单（安装服务 / 管理服务 / 查看状态 / 自由操作）

### 使用辅助脚本

```bash
# 测试连接
python3 scripts/ssh_helper.py test --host 192.168.1.100 --user root --key ~/.ssh/id_ed25519

# 执行命令
python3 scripts/ssh_helper.py exec --host 192.168.1.100 --user root --key ~/.ssh/id_ed25519 --cmd "uptime"

# 采集服务器信息
python3 scripts/ssh_helper.py info --host 192.168.1.100 --user root --key ~/.ssh/id_ed25519

# 上传文件
python3 scripts/ssh_helper.py upload --host 192.168.1.100 --user root --key ~/.ssh/id_ed25519 --local ./file.txt --remote /tmp/file.txt

# 下载文件
python3 scripts/ssh_helper.py download --host 192.168.1.100 --user root --key ~/.ssh/id_ed25519 --remote /var/log/syslog --local ./syslog.txt
```

## 目录结构

```
ssh-server-manager/
├── SKILL.md                    # Skill 定义（AgentSkills 标准）
├── README.md                   # 本文件
├── install.sh                  # 一键安装/更新脚本
├── LICENSE                     # MIT 许可证
├── .gitignore
├── references/                 # 服务安装参考文档
│   ├── 3x-ui-install.md        # 3X-UI 面板安装指南
│   └── mtg-install.md          # MTG (MTProto Proxy) 安装指南
└── scripts/
    └── ssh_helper.py           # SSH 辅助工具
```

## 扩展

在 `references/` 目录中添加新的安装参考文档，SKILL.md 会自动引导用户使用。

## 许可证

MIT License — 详见 [LICENSE](LICENSE) 文件。
