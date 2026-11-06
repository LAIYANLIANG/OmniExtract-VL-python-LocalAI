#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO 提取系統啟動與檢查工具
======================

這個檔案會自動檢查系統依賴、安裝缺失的套件，並啟動系統。
使用方式: python startup_checker.py

作者: GitHub Copilot
日期: 2026-03-31
"""

import os
import sys
import subprocess
import importlib
import time
import requests
import json
from pathlib import Path

class SystemChecker:
    def __init__(self):
        self.workspace_path = Path(__file__).parent
        self.required_packages = [
            'flask', 'requests', 'pillow', 'opencv-python', 
            'paddlepaddle', 'paddleocr', 'transformers', 
            'torch', 'numpy', 'pandas', 'matplotlib'
        ]
        self.optional_packages = [
            'layoutlm', 'layoutlmv2', 'layoutlmv3'
        ]
        self.ollama_models = ['adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M']
        self.status = {}
        
    def print_header(self, message):
        """印出標題"""
        print("\n" + "="*60)
        print(f" {message}")
        print("="*60)
        
    def print_step(self, step_num, message):
        """印出步驟"""
        print(f"\n🔧 步驟 {step_num}: {message}")
        print("-" * 50)
        
    def check_python_version(self):
        """檢查 Python 版本"""
        self.print_step(1, "檢查 Python 版本")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"✅ Python 版本: {sys.version}")
            self.status['python'] = True
            return True
        else:
            print(f"❌ Python 版本過舊: {sys.version}")
            print("請升級到 Python 3.8 或更新版本")
            self.status['python'] = False
            return False
            
    def check_package(self, package_name):
        """檢查單個套件"""
        try:
            importlib.import_module(package_name.replace('-', '_'))
            return True
        except ImportError:
            return False
            
    def install_package(self, package_name):
        """安裝套件"""
        try:
            print(f"   正在安裝 {package_name}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package_name
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"   ✅ {package_name} 安裝成功")
                return True
            else:
                print(f"   ❌ {package_name} 安裝失敗: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"   ❌ {package_name} 安裝超時")
            return False
        except Exception as e:
            print(f"   ❌ {package_name} 安裝錯誤: {e}")
            return False
            
    def check_required_packages(self):
        """檢查必要套件"""
        self.print_step(2, "檢查必要的 Python 套件")
        
        missing_packages = []
        installed_packages = []
        
        for package in self.required_packages:
            if self.check_package(package):
                print(f"✅ {package}")
                installed_packages.append(package)
            else:
                print(f"❌ {package} (缺失)")
                missing_packages.append(package)
                
        if missing_packages:
            print(f"\n需要安裝 {len(missing_packages)} 個套件...")
            for package in missing_packages:
                success = self.install_package(package)
                if success:
                    installed_packages.append(package)
                    
        self.status['required_packages'] = len(installed_packages) == len(self.required_packages)
        return self.status['required_packages']
        
    def check_optional_packages(self):
        """檢查選用套件"""
        self.print_step(3, "檢查選用套件")
        
        for package in self.optional_packages:
            if self.check_package(package):
                print(f"✅ {package}")
            else:
                print(f"⚠️  {package} (選用，未安裝)")
                
    def check_ollama_service(self):
        """檢查 Ollama 服務"""
        self.print_step(4, "檢查 Ollama 服務")
        
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                print("✅ Ollama 服務正在運行")
                
                # 檢查模型
                models = response.json().get('models', [])
                model_names = [model.get('name', '') for model in models]
                
                print(f"📋 已安裝的模型: {len(model_names)} 個")
                for model_name in model_names:
                    print(f"   - {model_name}")
                    
                # 檢查所需模型
                required_models_available = []
                for required_model in self.ollama_models:
                    found = any(required_model in model_name for model_name in model_names)
                    if found:
                        print(f"✅ 所需模型: {required_model}")
                        required_models_available.append(required_model)
                    else:
                        print(f"❌ 缺失模型: {required_model}")
                        
                self.status['ollama'] = len(required_models_available) > 0
                return True
            else:
                print(f"❌ Ollama 服務回應異常: {response.status_code}")
                self.status['ollama'] = False
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Ollama 服務未運行")
            print("請先啟動 Ollama 服務:")
            print("   方法1: 從開始選單啟動 Ollama")
            print("   方法2: 命令列執行 'ollama serve'")
            self.status['ollama'] = False
            return False
        except Exception as e:
            print(f"❌ Ollama 檢查失敗: {e}")
            self.status['ollama'] = False
            return False
            
    def install_ollama_model(self):
        """安裝 Ollama 模型"""
        if not self.status.get('ollama', False):
            print("❌ Ollama 服務未運行，跳過模型安裝")
            return False
            
        print(f"\n要安裝 Qwen3-VL 模型嗎? 這可能需要較長時間...")
        choice = input("輸入 'y' 繼續安裝，或按 Enter 跳過: ").lower().strip()
        
        if choice == 'y':
            try:
                print("正在下載模型，請耐心等候...")
                result = subprocess.run([
                    'ollama', 'pull', 'adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M'
                ], capture_output=True, text=True, timeout=3600)  # 1小時超時
                
                if result.returncode == 0:
                    print("✅ Qwen3-VL 模型安裝成功")
                    return True
                else:
                    print(f"❌ 模型安裝失敗: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                print("❌ 模型下載超時")
                return False
            except FileNotFoundError:
                print("❌ 找不到 ollama 命令，請檢查 Ollama 安裝")
                return False
        else:
            print("跳過模型安裝")
            return False
            
    def check_workspace_structure(self):
        """檢查工作區結構"""
        self.print_step(5, "檢查工作區結構")
        
        required_dirs = [
            'po_extractor',
            'po_extractor/pipeline', 
            'po_extractor/extractors',
            'po_extractor/models',
            'po_extractor/features',
            'output_doc',
            'results'
        ]
        
        required_files = [
            'po_extractor/__init__.py',
            'po_extractor/webapp.py',
            'po_extractor/main.py',
            'po_extractor/config.py',
            'package.json',
            'requirements.txt'
        ]
        
        missing_items = []
        
        # 檢查目錄
        for dir_path in required_dirs:
            full_path = self.workspace_path / dir_path
            if full_path.exists():
                print(f"✅ 目錄: {dir_path}")
            else:
                print(f"❌ 缺失目錄: {dir_path}")
                missing_items.append(dir_path)
                
        # 檢查檔案
        for file_path in required_files:
            full_path = self.workspace_path / file_path
            if full_path.exists():
                print(f"✅ 檔案: {file_path}")
            else:
                print(f"❌ 缺失檔案: {file_path}")
                missing_items.append(file_path)
                
        self.status['workspace'] = len(missing_items) == 0
        
        if missing_items:
            print(f"\n⚠️  發現 {len(missing_items)} 個缺失項目")
            print("請確認工作區完整性")
            
        return self.status['workspace']
        
    def clear_cache(self):
        """清理 Python 快取"""
        self.print_step(6, "清理系統快取")
        
        try:
            # 刪除 __pycache__ 目錄
            pycache_dirs = list(self.workspace_path.rglob('__pycache__'))
            for cache_dir in pycache_dirs:
                if cache_dir.is_dir():
                    subprocess.run(['rmdir', '/s', '/q', str(cache_dir)], 
                                 shell=True, check=False)
                    print(f"✅ 清理快取: {cache_dir.relative_to(self.workspace_path)}")
                    
            # 刪除 .pyc 檔案
            pyc_files = list(self.workspace_path.rglob('*.pyc'))
            for pyc_file in pyc_files:
                try:
                    pyc_file.unlink()
                    print(f"✅ 刪除緩存檔: {pyc_file.relative_to(self.workspace_path)}")
                except:
                    pass
                    
            print("✅ 快取清理完成")
            return True
        except Exception as e:
            print(f"⚠️  快取清理部分失敗: {e}")
            return True  # 不影響主要功能
            
    def start_webapp(self):
        """啟動網站服務"""
        self.print_step(7, "啟動 Web 應用程式")
        
        try:
            # 先檢查端口是否被佔用
            try:
                response = requests.get('http://127.0.0.1:5000', timeout=2)
                print("⚠️  端口 5000 已被使用，嘗試停止現有服務...")
                # 可以在這裡加入停止服務的邏輯
            except:
                pass  # 端口空閒，正常
                
            print("正在啟動 Flask 應用程式...")
            
            # 使用 restart_final.py 如果存在
            restart_final_path = self.workspace_path / 'restart_final.py'
            if restart_final_path.exists():
                print("使用 restart_final.py 啟動...")
                subprocess.Popen([sys.executable, 'restart_final.py'], 
                               cwd=self.workspace_path)
            else:
                # 直接啟動webapp
                print("直接啟動 webapp...")
                subprocess.Popen([sys.executable, '-m', 'po_extractor.webapp'],
                               cwd=self.workspace_path)
                
            # 等待服務啟動
            print("等待服務啟動...")
            for i in range(10):
                time.sleep(2)
                try:
                    response = requests.get('http://127.0.0.1:5000', timeout=5)
                    if response.status_code == 200:
                        print("✅ Web 應用程式啟動成功!")
                        print(f"🌐 訪問地址: http://127.0.0.1:5000")
                        self.status['webapp'] = True
                        return True
                except:
                    print(f"   等待中... ({i+1}/10)")
                    
            print("❌ Web 應用程式啟動超時")
            self.status['webapp'] = False
            return False
            
        except Exception as e:
            print(f"❌ Web 應用程式啟動失敗: {e}")
            self.status['webapp'] = False
            return False
            
    def run_health_check(self):
        """運行健康檢查"""
        self.print_step(8, "系統健康檢查")
        
        if not self.status.get('webapp', False):
            print("❌ Web 服務未啟動，跳過健康檢查")
            return False
            
        try:
            # 檢查主頁
            response = requests.get('http://127.0.0.1:5000', timeout=10)
            print(f"✅ 主頁訪問: {response.status_code}")
            
            # 檢查健康端點
            try:
                health_response = requests.get('http://127.0.0.1:5000/health', timeout=5)
                print(f"✅ 健康檢查端點: {health_response.status_code}")
            except:
                print("⚠️  健康檢查端點不可用 (正常，可能未實作)")
                
            # 檢查基本功能
            if 'PO提取系統' in response.text or 'PO Extraction' in response.text:
                print("✅ 系統界面正常載入")
            else:
                print("⚠️  系統界面可能有問題")
                
            print("✅ 健康檢查完成")
            return True
            
        except Exception as e:
            print(f"❌ 健康檢查失敗: {e}")
            return False
            
    def generate_status_report(self):
        """生成狀態報告"""
        self.print_header("系統狀態報告")
        
        components = [
            ('Python 版本', self.status.get('python', False)),
            ('必要套件', self.status.get('required_packages', False)),
            ('Ollama 服務', self.status.get('ollama', False)),
            ('工作區結構', self.status.get('workspace', False)),
            ('Web 應用程式', self.status.get('webapp', False))
        ]
        
        print("\n📊 各組件狀態:")
        for name, status in components:
            icon = "✅" if status else "❌"
            print(f"   {icon} {name}")
            
        success_count = sum(1 for _, status in components if status)
        total_count = len(components)
        
        print(f"\n🎯 系統整體狀態: {success_count}/{total_count} 組件正常")
        
        if success_count == total_count:
            print("🎉 系統完全就緒！")
            print("🌐 請訪問: http://127.0.0.1:5000")
        elif success_count >= 4:
            print("⚠️  系統基本可用，但某些功能可能受限")
            print("🌐 請訪問: http://127.0.0.1:5000")
        else:
            print("❌ 系統存在重大問題，請檢查上述錯誤")
            
    def run_full_check(self):
        """運行完整檢查"""
        self.print_header("PO 提取系統啟動檢查工具")
        print("正在進行系統檢查與啟動...")
        
        try:
            # 各項檢查
            self.check_python_version()
            self.check_required_packages()
            self.check_optional_packages()
            self.check_ollama_service()
            self.check_workspace_structure()
            self.clear_cache()
            
            # 如果基本檢查通過，嘗試啟動服務
            if all([
                self.status.get('python', False),
                self.status.get('required_packages', False),
                self.status.get('workspace', False)
            ]):
                self.start_webapp()
                time.sleep(3)  # 給應用程式更多啟動時間
                self.run_health_check()
            else:
                print("\n⚠️  基本檢查未完全通過，跳過服務啟動")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  用戶中斷操作")
        except Exception as e:
            print(f"\n❌ 檢查過程發生錯誤: {e}")
        finally:
            self.generate_status_report()


def main():
    """主函數"""
    try:
        checker = SystemChecker()
        checker.run_full_check()
    except Exception as e:
        print(f"啟動檢查工具發生錯誤: {e}")
        input("按 Enter 結束...")


if __name__ == "__main__":
    main()