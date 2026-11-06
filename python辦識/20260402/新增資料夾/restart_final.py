#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO Extractor 完全重啟服務
不依賴模板檔案，內建HTML界面
"""
import os
import sys
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify

# 設置基本路徑
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# 創建Flask應用
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['SECRET_KEY'] = 'restart-key-2024'

# 確保目錄存在
os.makedirs('import_doc', exist_ok=True)
os.makedirs('output_doc', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# 嘗試載入功能
features_available = {}

try:
    from po_extractor.pipeline.step2_extract import extract_text_from_pdf
    from po_extractor.pipeline.step3_clean import clean_text_preserve_structure
    from po_extractor.pipeline.step4_classify import classify_vendor
    from po_extractor.extractors.registry import ExtractorRegistry
    features_available['basic_extraction'] = True
    print("✅ 基本提取功能已載入")
except Exception as e:
    features_available['basic_extraction'] = False
    print(f"❌ 基本功能載入失敗: {e}")

try:
    from po_extractor.pipeline.pipeline_orchestrator import process_po_document
    features_available['seven_step_pipeline'] = True
    print("✅ 七步管道功能已載入")
except Exception as e:
    features_available['seven_step_pipeline'] = False  
    print(f"⚠️  七步管道未載入: {e}")

try:
    from po_extractor.pipeline.step7_qwen_audit import QwenClient
    features_available['qwen_audit'] = True
    print("✅ Qwen審核功能已載入")
except Exception as e:
    features_available['qwen_audit'] = False
    print(f"⚠️  Qwen功能未載入: {e}")


@app.route('/')
def index():
    """主頁 - 內建HTML界面"""
    html = f'''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PO Extractor - 重啟服務</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; margin-bottom: 30px; }}
        .status-card {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .feature {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }}
        .feature-name {{ font-weight: 500; }}
        .status-ok {{ color: #27ae60; font-weight: bold; }}
        .status-error {{ color: #e74c3c; font-weight: bold; }}
        .upload-section {{ border: 2px dashed #bdc3c7; padding: 30px; text-align: center; margin: 20px 0; border-radius: 8px; }}
        .upload-section:hover {{ border-color: #3498db; }}
        .btn {{ background: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
        .btn:hover {{ background: #2980b9; }}
        .btn:disabled {{ background: #95a5a6; cursor: not-allowed; }}
        #results {{ margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 PO PDF Feature Extractor</h1>
        <h2>重啟服務 - v2.0 Enhanced</h2>
        
        <div class="status-card">
            <h3>📊 系統狀態</h3>
            <div class="feature">
                <span class="feature-name">基本提取功能</span>
                <span class="{'status-ok' if features_available.get('basic_extraction') else 'status-error'}">
                    {'✅ 可用' if features_available.get('basic_extraction') else '❌ 不可用'}
                </span>
            </div>
            <div class="feature">
                <span class="feature-name">七步管道</span>
                <span class="{'status-ok' if features_available.get('seven_step_pipeline') else 'status-error'}">
                    {'✅ 可用' if features_available.get('seven_step_pipeline') else '⚠️ 未載入'}
                </span>
            </div>
            <div class="feature">
                <span class="feature-name">Qwen審核</span>
                <span class="{'status-ok' if features_available.get('qwen_audit') else 'status-error'}">
                    {'✅ 可用' if features_available.get('qwen_audit') else '⚠️ 未載入'}
                </span>
            </div>
        </div>
        
        <div class="upload-section">
            <h3>📄 PDF 檔案處理</h3>
            <input type="file" id="pdfFile" accept=".pdf" multiple style="margin: 10px 0;">
            <br>
            <label style="margin: 10px 0; display: block;">
                <input type="checkbox" id="useEnhanced" {'checked' if features_available.get('seven_step_pipeline') else 'disabled'}>
                使用七步增強管道 {'(可用)' if features_available.get('seven_step_pipeline') else '(불가능)'}
            </label>
            <br>
            <button class="btn" onclick="uploadFile()" id="uploadBtn">開始處理</button>
            <div id="fileCount" style="margin-top: 10px; color: #666; font-size: 14px;"></div>
        </div>
        
        <div id="results"></div>
    </div>
    
    <script>
        // 檔案選擇監聽器
        document.getElementById('pdfFile').addEventListener('change', function(e) {{
            const fileCount = e.target.files.length;
            const countDiv = document.getElementById('fileCount');
            if (fileCount > 0) {{
                countDiv.textContent = `已選擇 ${{fileCount}} 個檔案`;
                countDiv.style.color = '#2c5aa0';
            }} else {{
                countDiv.textContent = '';
            }}
        }});

        async function uploadFile() {{
            const fileInput = document.getElementById('pdfFile');
            const useEnhanced = document.getElementById('useEnhanced').checked;
            const results = document.getElementById('results');
            const btn = document.getElementById('uploadBtn');
            
            if (!fileInput.files.length) {{
                alert('請選擇PDF檔案');
                return;
            }}
            
            btn.disabled = true;
            btn.textContent = '處理中...';
            results.style.display = 'block';
            
            const totalFiles = fileInput.files.length;
            results.innerHTML = `<h3>⏳ 正在處理 ${{totalFiles}} 個檔案...</h3><div id="progressArea"></div>`;
            
            const progressArea = document.getElementById('progressArea');
            let completedFiles = 0;
            const allResults = [];
            
            // 處理每個檔案
            for (let i = 0; i < fileInput.files.length; i++) {{
                const file = fileInput.files[i];
                progressArea.innerHTML += `<p>📄 正在處理: ${{file.name}}</p>`;
                
                const formData = new FormData();
                formData.append('file', file);
                formData.append('use_enhanced', useEnhanced);
                
                try {{
                    const response = await fetch('/process_pdf', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const data = await response.json();
                    allResults.push(data);
                    completedFiles++;
                    
                    if (data.status === 'success') {{
                        progressArea.innerHTML += `<p style="color: green;">✅ ${{file.name}} - 完成</p>`;
                    }} else {{
                        progressArea.innerHTML += `<p style="color: red;">❌ ${{file.name}} - 失敗: ${{data.error}}</p>`;
                    }}
                }} catch (error) {{
                    allResults.push({{
                        status: 'error',
                        filename: file.name,
                        error: error.message
                    }});
                    completedFiles++;
                    progressArea.innerHTML += `<p style="color: red;">❌ ${{file.name}} - 連接錯誤: ${{error.message}}</p>`;
                }}
                
                // 更新進度
                const progress = Math.round((completedFiles / totalFiles) * 100);
                btn.textContent = `處理中... (${{progress}}%)`;
            }}
            
            // 顯示總結果
            const successCount = allResults.filter(r => r.status === 'success').length;
            const failureCount = allResults.length - successCount;
            
            results.innerHTML = `
                <h3>📊 處理完成</h3>
                <p><strong>總計:</strong> ${{totalFiles}} 個檔案</p>
                <p><strong>成功:</strong> <span style="color: green;">${{successCount}}</span></p>
                <p><strong>失敗:</strong> <span style="color: red;">${{failureCount}}</span></p>
                <hr>
                <div id="detailedResults" style="max-height: 400px; overflow-y: auto;"></div>`;
            
            // 顯示詳細結果
            const detailedDiv = document.getElementById('detailedResults');
            allResults.forEach((result, index) => {{
                if (result.status === 'success') {{
                    detailedDiv.innerHTML += `
                        <div style="border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 5px;">
                            <h4>✅ ${{result.filename}}</h4>
                            <p><strong>處理時間:</strong> ${{result.processing_time || 'N/A'}}秒</p>
                            <p><strong>使用管道:</strong> ${{result.pipeline_used}}</p>
                            <details>
                                <summary>查看提取結果</summary>
                                <pre style="background: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow: auto; font-size: 12px;">
${{JSON.stringify(result.extraction, null, 2)}}
                                </pre>
                            </details>
                        </div>`;
                }} else {{
                    detailedDiv.innerHTML += `
                        <div style="border: 1px solid #ff4444; margin: 10px 0; padding: 10px; border-radius: 5px; background: #fff5f5;">
                            <h4>❌ ${{result.filename}}</h4>
                            <p style="color: red;"><strong>錯誤:</strong> ${{result.error}}</p>
                        </div>`;
                }}
            }});
            
            btn.disabled = false;
            btn.textContent = '開始處理';
        }}
    </script>
</body>
</html>
    '''
    return html


@app.route('/health')
def health():
    """健康檢查"""
    return jsonify({
        "status": "ok",
        "service": "po_extractor_restart",
        "version": "2.0-restart",
        "timestamp": datetime.now().isoformat(),
        "features": features_available
    })


@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    """處理PDF檔案"""
    if 'file' not in request.files:
        return jsonify({"status": "error", "error": "沒有選擇檔案"}), 400
    
    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({"status": "error", "error": "請選擇PDF檔案"}), 400
    
    use_enhanced = request.form.get('use_enhanced', 'false').lower() == 'true'
    
    # 儲存檔案
    filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    os.makedirs('uploads', exist_ok=True)
    filepath = os.path.join('uploads', filename)
    file.save(filepath)
    
    try:
        start_time = datetime.now()
        
        if use_enhanced and features_available.get('seven_step_pipeline'):
            # 使用七步管道
            result = process_po_document(filepath, enable_qwen_audit=False)
            extraction = result['final_extraction']
            pipeline_used = "七步增強管道"
        elif features_available.get('basic_extraction'):
            # 使用基本提取
            from po_extractor.main import process_single_pdf
            from po_extractor.config import DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR
            extraction = process_single_pdf(filepath, DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR)
            pipeline_used = "基本六步管道"
        else:
            # 模擬基本提取
            extraction = {
                "vendor_id": "unknown",
                "status": "processed_with_limited_features",
                "message": "基本功能未完全可用，僅做基本處理"
            }
            pipeline_used = "縮減功能模式"
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 清理檔案
        os.remove(filepath)
        
        return jsonify({
            "status": "success",
            "filename": file.filename,
            "processing_time": round(processing_time, 2),
            "pipeline_used": pipeline_used,
            "extraction": extraction
        })
        
    except Exception as e:
        # 清理檔案
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            "status": "error", 
            "error": str(e)
        }), 500


@app.route('/restart_info')
def restart_info():
    """重啟資訊"""
    return jsonify({
        "service": "po_extractor_restart",
        "restart_time": datetime.now().isoformat(),
        "workspace": WORKSPACE_DIR,
        "features_available": features_available,
        "directories_created": ["import_doc", "output_doc", "uploads"]
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  🔄 PO Extractor - 服務重啟完成")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  📂 工作目錄: {WORKSPACE_DIR}")
    print(f"  ⚡ 基本功能: {'✅' if features_available.get('basic_extraction') else '❌'}")
    print(f"  🚀 七步管道: {'✅' if features_available.get('seven_step_pipeline') else '⚠️'}")  
    print(f"  🤖 Qwen功能: {'✅' if features_available.get('qwen_audit') else '⚠️'}")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🌐 服務地址: http://127.0.0.1:5000")
    print("  📊 健康檢查: http://127.0.0.1:5000/health")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)