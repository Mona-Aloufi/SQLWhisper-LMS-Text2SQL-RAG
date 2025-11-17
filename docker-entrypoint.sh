#!/bin/bash
set -e

echo "🚀 Starting SQLWhisper..."

# تشغيل Streamlit في الخلفية
echo "📱 Starting Streamlit frontend..."
streamlit run streamlit_app/streamlitapp.py --server.port=8501 --server.address=0.0.0.0 &

# تأخير بسيط للتأكد إنه بدأ
sleep 2

# تشغيل FastAPI backend
echo "🔧 Starting FastAPI backend..."
python -m uvicorn app:app --host 0.0.0.0 --port 8000
