#!/bin/bash
# 部署脚本

echo "===== Mephisto Streamlit 部署脚本 ====="
echo ""

# 检查是否配置了 GitHub 用户名
if [ -z "$1" ]; then
    echo "用法: ./deploy.sh YOUR_GITHUB_USERNAME"
    echo "例如: ./deploy.sh duanmanni"
    exit 1
fi

GITHUB_USER=$1
REPO_NAME="mephisto-streamlit"

echo "步骤 1: 设置 Git 远程仓库..."
git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git 2>/dev/null || git remote set-url origin https://github.com/$GITHUB_USER/$REPO_NAME.git

echo "步骤 2: 推送到 GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "===== 完成 ====="
echo ""
echo "请在浏览器中访问: https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "接下来:"
echo "1. 访问 https://streamlit.io/cloud"
echo "2. 使用 GitHub 账号登录"
echo "3. 点击 'New app'"
echo "4. 选择 Repository: $GITHUB_USER/$REPO_NAME"
echo "5. 点击 Deploy"
