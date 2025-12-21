#!/bin/bash
# MaimWebBackend 启动脚本

# 设置数据库连接 URL
# 注意: MaimWebBackend 使用异步 SQLAlchemy，需要 sqlite+aiosqlite 驱动
# DATABASE_URL is now loaded from .env
# DATABASE_URL is now loaded from .env
export DATABASE_URL="sqlite+aiosqlite:////home/tcmofashi/proj/MaimWebBackend/maim_web.db"

echo "🚀 Starting MaimWebBackend..."
echo "📂 DATABASE_URL: $DATABASE_URL"
echo "🔌 Port: 8880"

# 使用 conda 环境启动 (假设环境名为 maibot)
# 如果已经在环境中，可以直接运行 python
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "maibot" ]; then
    echo "⚠️  Switching to 'maibot' conda environment..."
    eval "$(conda shell.bash hook)"
    conda activate maibot
fi

# 启动服务
python -m uvicorn src.main:app --host 0.0.0.0 --port 8880 --reload
