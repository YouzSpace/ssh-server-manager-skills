#!/bin/bash
# install.sh - SSH Server Manager Skill 安装/更新脚本
# 用法：curl -fsSL https://raw.githubusercontent.com/YouzSpace/ssh-server-manager-skills/main/install.sh | bash

set -e

REPO_URL="https://github.com/YouzSpace/ssh-server-manager-skills.git"
ZIP_URL="https://github.com/YouzSpace/ssh-server-manager-skills/archive/refs/heads/main.zip"
SKILL_NAME="ssh-server-manager"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "🔧 SSH Server Manager Skill 安装程序"
echo "======================================"
echo ""

# 0. 检测是否安装了 git
HAS_GIT=false
if command -v git &> /dev/null; then
    HAS_GIT=true
fi

# 1. 检测 Skill 目录
detect_install_dir() {
    # 优先 WorkBuddy
    if [ -d "$HOME/.workbuddy/skills" ]; then
        echo "$HOME/.workbuddy/skills/$SKILL_NAME"
        return
    fi
    # 其次 OpenClaw
    if [ -d "$HOME/.agents/skills" ]; then
        echo "$HOME/.agents/skills/$SKILL_NAME"
        return
    fi
    # 默认创建 WorkBuddy 目录
    mkdir -p "$HOME/.workbuddy/skills"
    echo "$HOME/.workbuddy/skills/$SKILL_NAME"
}

INSTALL_DIR=$(detect_install_dir)
echo -e "${GREEN}✅ 安装目录：${INSTALL_DIR}${NC}"

# 2. 判断是安装还是更新
if [ -d "$INSTALL_DIR/.git" ] && [ "$HAS_GIT" = true ]; then
    # 已安装且有 git → 更新
    echo ""
    echo -e "${YELLOW}📥 检测到已安装，正在更新...${NC}"
    cd "$INSTALL_DIR"

    # 保存本地修改（如有）
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  检测到本地修改，先暂存...${NC}"
        git stash
    fi

    # 拉取最新代码
    git pull origin main

    echo ""
    echo -e "${GREEN}✅ 更新完成！${NC}"
    echo ""
    echo "📋 最近更新："
    git log --oneline -5
    echo ""
else
    # 全新安装
    echo ""
    echo -e "${YELLOW}📥 正在安装...${NC}"

    # 创建父目录（如果不存在）
    mkdir -p "$(dirname "$INSTALL_DIR")"

    # 如果目标目录已存在（非 git 安装），先备份
    if [ -d "$INSTALL_DIR" ]; then
        BACKUP="${INSTALL_DIR}.bak.$(date +%Y%m%d%H%M%S)"
        echo -e "${YELLOW}⚠️  目录已存在，备份到：${BACKUP}${NC}"
        mv "$INSTALL_DIR" "$BACKUP"
    fi

    if [ "$HAS_GIT" = true ]; then
        # 有 git → git clone
        git clone "$REPO_URL" "$INSTALL_DIR"
    else
        # 没有 git → curl 下载 zip
        echo -e "${YELLOW}⚠️  未检测到 git，使用 zip 下载...${NC}"
        TMP_DIR=$(mktemp -d)
        curl -fsSL "$ZIP_URL" -o "$TMP_DIR/skill.zip"
        # 解压
        if command -v unzip &> /dev/null; then
            unzip -q "$TMP_DIR/skill.zip" -d "$TMP_DIR"
        elif command -v python3 &> /dev/null; then
            python3 -c "import zipfile; zipfile.ZipFile('$TMP_DIR/skill.zip').extractall('$TMP_DIR')"
        elif command -v python &> /dev/null; then
            python -c "import zipfile; zipfile.ZipFile('$TMP_DIR/skill.zip').extractall('$TMP_DIR')"
        else
            echo -e "${RED}❌ 需要安装 git 或 unzip 才能继续${NC}"
            rm -rf "$TMP_DIR"
            exit 1
        fi
        mv "$TMP_DIR/$SKILL_NAME-main" "$INSTALL_DIR"
        rm -rf "$TMP_DIR"
    fi

    echo ""
    echo -e "${GREEN}✅ 安装完成！${NC}"
fi

# 3. 显示下一步操作
echo ""
echo "======================================"
echo ""
echo "🚀 下一步："
echo ""
echo "   对你的 AI 助手说："
echo ""
echo "   \"连接我的服务器\""
echo ""
echo "   或者："
echo ""
echo "   \"查看服务器状态\""
echo ""
echo "======================================"
echo ""
echo "📖 项目地址：https://github.com/YouzSpace/ssh-server-manager-skills"
echo ""
