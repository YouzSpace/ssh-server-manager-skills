# SSH Server Manager Skill

完善的服务器远程操作管理Skill，支持通过SSH密钥连接Linux服务器，执行命令、管理文件、安装软件、部署服务、查看状态等全方位服务器操作。

## ✨ 功能特性

- 🔐 **SSH密钥认证** - 自动管理SSH密钥，支持ed25519加密算法
- 🚀 **服务部署** - 一键安装Docker、MTProto代理、x-ui面板等
- 📦 **软件管理** - 安装、卸载、更新服务器软件包
- 📊 **状态监控** - 实时查看CPU、内存、磁盘使用情况
- 📁 **文件操作** - 上传、下载、编辑服务器文件
- 🔧 **服务管理** - systemctl服务启停、状态查询
- 🌐 **域名绑定** - 配合DNS配置实现域名访问
- 🛠️ **故障修复** - 自动诊断和修复常见问题

## 📋 前置要求

### 必需工具

#### Windows用户

1. **Git Bash** (推荐) 或 WSL2
   - 下载：https://git-scm.com/download/win
   - 安装时选择"Use Git and optional Unix tools from the Command Prompt"
   - 提供ssh、scp、bash等命令

2. **OpenSSH Client** (Windows 10/11自带)
   - 设置 → 应用 → 可选功能 → OpenSSH客户端
   - 或PowerShell执行：`Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0`

3. **Python 3.8+**
   - 下载：https://www.python.org/downloads/
   - 安装时勾选"Add Python to PATH"

#### macOS用户

```bash
# 安装Xcode命令行工具（包含ssh）
xcode-select --install

# 安装Python（如未安装）
brew install python
```

#### Linux用户

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install -y openssh-client python3 python3-pip

# CentOS/RHEL
sudo yum install -y openssh-clients python3 python3-pip
```

### 可选工具（增强功能）

- **Visual Studio Code** - 远程SSH编辑文件
- **PuTTY** (Windows) - 备选SSH客户端
- **WinSCP** (Windows) - 图形化文件传输

## 🚀 安装方法

### 方法一：从GitHub安装（推荐）

```bash
# 克隆到WorkBuddy skills目录
cd ~/.workbuddy/skills/
git clone git@github.com:YouzSpace/ssh-server-manager-skills.git ssh-server-manager

# 或使用HTTPS
git clone https://github.com/YouzSpace/ssh-server-manager-skills.git ssh-server-manager
```

### 方法二：手动安装

1. 下载 `SKILL.md` 和 `scripts/ssh_helper.py`
2. 放置到 `~/.workbuddy/skills/ssh-server-manager/` 目录
3. 确保 `ssh_helper.py` 有执行权限：`chmod +x scripts/ssh_helper.py`

## 🔧 配置说明

### 1. 生成SSH密钥

Skill会自动生成SSH密钥，或手动生成：

```bash
# 生成ed25519密钥（推荐）
ssh-keygen -t ed25519 -C "workbuddy@agent" -f ~/.ssh/id_ed25519_workbuddy

# 生成RSA密钥（兼容旧系统）
ssh-keygen -t rsa -b 4096 -C "workbuddy@agent" -f ~/.ssh/id_rsa_workbuddy
```

### 2. 配置SSH快捷访问

编辑 `~/.ssh/config` 添加服务器：

```
Host myserver
    HostName 192.168.1.100
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519_workbuddy
    ServerAliveInterval 60
```

### 3. 上传公钥到服务器

```bash
# 方法一：自动上传（推荐）
ssh-copy-id -i ~/.ssh/id_ed25519_workbuddy.pub root@192.168.1.100

# 方法二：手动上传
cat ~/.ssh/id_ed25519_workbuddy.pub | ssh root@192.168.1.100 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

## 📖 使用指南

### 基本连接

对WorkBuddy说：

```
连接到我的服务器 192.168.1.100，用户root
```

WorkBuddy会：
1. 检查SSH密钥是否存在
2. 如不存在则自动生成
3. 提示你上传公钥到服务器
4. 测试连接是否成功

### 常用操作示例

#### 1. 查看服务器状态

```
查看服务器状态
查看CPU和内存使用情况
查看磁盘空间
```

#### 2. 安装软件

```
安装Docker
安装MTProto代理
安装x-ui面板
```

#### 3. 管理服务

```
启动nginx服务
停止microsocks服务
查看x-ui服务状态
```

#### 4. 文件操作

```
查看 /etc/x-ui/ 目录
编辑 /etc/x-ui/x-ui.db 配置文件
下载服务器日志到本地
```

#### 5. 部署应用

```
部署MTProto代理，端口443
绑定域名 example.com
配置SSL证书
```

### 高级功能

#### 批量服务器管理

在 `~/.workbuddy/skills/ssh-server-manager/SKILL.md` 中配置多个服务器：

```yaml
servers:
  hk-server:
    host: 192.168.1.100
    user: root
    key: ~/.ssh/id_ed25519_workbuddy
  
  jp-server:
    host: 192.168.2.100
    user: ubuntu
    key: ~/.ssh/id_ed25519_workbuddy
```

然后可以说：

```
在hk-server和jp-server上同时安装Docker
```

#### 自动化脚本

创建自定义部署脚本放到 `scripts/` 目录：

```bash
#!/bin/bash
# scripts/deploy_mtproto.sh

docker run -d \
  --name mtproto-proxy \
  -p 443:443 \
  -e SECRET=$(head -c 16 /dev/urandom | xxd -p) \
  telegrammessenger/proxy:latest
```

## 🛠️ 常见问题修复

### 问题1：SSH连接被拒绝

```bash
# 检查SSH服务是否运行
sudo systemctl status sshd

# 检查防火墙
sudo ufw status
sudo firewall-cmd --list-all
```

### 问题2：密钥权限过高

```bash
# 修复密钥权限
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519_workbuddy
chmod 644 ~/.ssh/id_ed25519_workbuddy.pub
```

### 问题3：x-ui节点无法连接

```
修复x-ui面板节点连接问题
重新生成privateKey
重启xray-core服务
```

### 问题4：Docker容器无法启动

```
查看Docker日志
增加系统文件描述符限制
检查端口占用情况
```

## 📊 技术架构

```
┌─────────────────┐
│  WorkBuddy AI   │
│  (对话界面)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SSH Server      │
│ Manager Skill   │
│ - SKILL.md      │
│ - ssh_helper.py │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SSH Protocol  │
│ (ssh, scp, sftp)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Remote Server  │
│ (Linux/Docker)  │
└─────────────────┘
```

## 🔐 安全建议

1. **使用SSH密钥认证**，禁用密码登录
2. **定期更换密钥**，建议使用ed25519算法
3. **配置防火墙**，仅开放必要端口
4. **启用fail2ban**，防止暴力破解
5. **定期更新系统**，修补安全漏洞
6. **备份重要数据**，包括SSH密钥和配置文件

## 📝 更新日志

### v1.0.0 (2026-04-30)

- ✅ 初始版本发布
- ✅ 支持SSH密钥自动生成和管理
- ✅ 支持MTProto代理一键部署
- ✅ 支持x-ui面板故障自动修复
- ✅ 支持服务状态监控和管理
- ✅ 支持文件上传下载

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 提交Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [WorkBuddy](https://workbuddy.ai) - AI助手平台
- [x-ui](https://github.com/vaxilu/x-ui) - xray面板
- [MTProto](https://core.telegram.org/mtproto) - Telegram代理协议

## 📧 联系方式

- 作者：YouzSpace
- GitHub：[YouzSpace](https://github.com/YouzSpace)
- 仓库：[ssh-server-manager-skills](https://github.com/YouzSpace/ssh-server-manager-skills)

---

**⭐ 如果这个Skill对你有帮助，请给个Star！**
