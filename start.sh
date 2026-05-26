#!/bin/bash
# 项目启动脚本

echo "GPT-Image2 文章发布系统 - 启动脚本"
echo "=================================="

# 检查并安装后端依赖
echo ""
echo "1. 安装后端依赖..."
cd backend
pip3 install -r requirements.txt

# 启动后端
echo ""
echo "2. 启动后端服务..."
python3 main.py &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"

# 安装并启动前端
echo ""
echo "3. 安装前端依赖..."
cd ../frontend
npm install

echo ""
echo "4. 启动前端服务..."
npm run dev

# 清理
trap "kill $BACKEND_PID 2>/dev/null" EXIT
