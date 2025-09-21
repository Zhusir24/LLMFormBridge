#!/bin/bash

# LLMFormBridge 启动脚本
# 用于同时启动前端和后端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖环境..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装 Python 3.12+"
        exit 1
    fi

    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js 18+"
        exit 1
    fi

    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi

    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        log_warning "Python虚拟环境未找到，正在创建..."
        python3 -m venv .venv
        log_success "虚拟环境创建完成"
    fi

    log_success "依赖检查完成"
}

# 安装后端依赖
install_backend_deps() {
    log_info "安装后端依赖..."
    cd backend

    # 激活虚拟环境并安装依赖
    source ../.venv/bin/activate
    pip install -r requirements.txt

    cd ..
    log_success "后端依赖安装完成"
}

# 安装前端依赖
install_frontend_deps() {
    log_info "安装前端依赖..."
    cd frontend

    if [ ! -d "node_modules" ]; then
        npm install
    else
        log_info "前端依赖已存在，跳过安装"
    fi

    cd ..
    log_success "前端依赖安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    cd backend

    source ../.venv/bin/activate

    # 检查是否已经有迁移
    if [ ! -f "llmbridge.db" ]; then
        log_info "应用数据库迁移..."
        ../.venv/bin/alembic upgrade head
        log_success "数据库初始化完成"
    else
        log_info "数据库已存在，跳过初始化"
    fi

    cd ..
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    cd backend

    # 设置环境变量
    export PYTHONPATH=.

    # 启动后端服务
    ../.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!

    cd ..

    # 等待后端启动
    log_info "等待后端服务启动..."
    sleep 5

    # 检查后端是否启动成功
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "后端服务启动成功 (PID: $BACKEND_PID)"
        log_info "后端服务地址: http://localhost:8000"
        log_info "API文档地址: http://localhost:8000/docs"
    else
        log_error "后端服务启动失败"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    cd frontend

    # 启动前端开发服务器
    npm run dev &
    FRONTEND_PID=$!

    cd ..

    # 等待前端启动
    log_info "等待前端服务启动..."
    sleep 8

    log_success "前端服务启动成功 (PID: $FRONTEND_PID)"
    log_info "前端服务地址: http://localhost:3000"
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."

    # 停止所有相关进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true

    log_success "所有服务已停止"
}

# 显示使用说明
show_usage() {
    echo "LLMFormBridge 启动脚本"
    echo ""
    echo "用法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start    启动前后端服务 (默认)"
    echo "  stop     停止所有服务"
    echo "  restart  重启所有服务"
    echo "  install  只安装依赖"
    echo "  backend  只启动后端"
    echo "  frontend 只启动前端"
    echo "  help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start     # 启动完整服务"
    echo "  $0 backend   # 只启动后端API服务"
    echo "  $0 stop      # 停止所有服务"
}

# 主函数
main() {
    local command=${1:-start}

    case $command in
        "start")
            log_info "=== LLMFormBridge 启动 ==="
            check_dependencies
            install_backend_deps
            install_frontend_deps
            init_database
            start_backend
            start_frontend

            log_success "=== 所有服务启动完成 ==="
            log_info "前端地址: http://localhost:3000"
            log_info "后端地址: http://localhost:8000"
            log_info "API文档: http://localhost:8000/docs"
            log_info ""
            log_info "按 Ctrl+C 停止所有服务"

            # 等待用户中断
            trap stop_services SIGINT SIGTERM
            wait
            ;;

        "stop")
            stop_services
            ;;

        "restart")
            stop_services
            sleep 2
            main start
            ;;

        "install")
            check_dependencies
            install_backend_deps
            install_frontend_deps
            init_database
            log_success "=== 依赖安装完成 ==="
            ;;

        "backend")
            log_info "=== 启动后端服务 ==="
            check_dependencies
            install_backend_deps
            init_database
            start_backend

            log_success "=== 后端服务启动完成 ==="
            log_info "后端地址: http://localhost:8000"
            log_info "API文档: http://localhost:8000/docs"
            log_info ""
            log_info "按 Ctrl+C 停止服务"

            trap stop_services SIGINT SIGTERM
            wait
            ;;

        "frontend")
            log_info "=== 启动前端服务 ==="
            if ! command -v node &> /dev/null; then
                log_error "Node.js 未安装"
                exit 1
            fi
            install_frontend_deps
            start_frontend

            log_success "=== 前端服务启动完成 ==="
            log_info "前端地址: http://localhost:3000"
            log_info ""
            log_info "按 Ctrl+C 停止服务"

            trap stop_services SIGINT SIGTERM
            wait
            ;;

        "help"|"-h"|"--help")
            show_usage
            ;;

        *)
            log_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"