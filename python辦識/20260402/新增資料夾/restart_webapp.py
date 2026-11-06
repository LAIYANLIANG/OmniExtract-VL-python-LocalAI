
import os
import sys
from flask import Flask

# 確保工作目錄正確
app = Flask(__name__)
app.config['SECRET_KEY'] = 'temp-key-for-restart'

@app.route('/')
def health_check():
    return """
    <h1>🚀 PO Extractor Service</h1>
    <p><strong>狀態:</strong> 服務正常運行</p>
    <p><strong>時間:</strong> """ + str(__import__('datetime').datetime.now()) + """</p>
    <p><strong>版本:</strong> Qwen3-VL Enhanced v2.0</p>
    <hr>
    <p>✅ 基礎服務已啟動</p>
    <p>🔄 完整功能載入中...</p>
    """

@app.route('/health')
def health():
    return {"status": "ok", "service": "po_extractor", "version": "2.0"}

if __name__ == '__main__':
    print("="*60)
    print("  🚀 PO Extractor - 緊急重啟模式")
    print("  服務地址: http://127.0.0.1:5000")
    print("="*60)
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
