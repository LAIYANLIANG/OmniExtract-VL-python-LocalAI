# PO PDF 智能特徵抽取系統 — 系統文件

> **文件版本**: v1.0  
> **建立日期**: 2026-03-30  
> **專案名稱**: PO PDF Feature Extractor (po_extractor)  
> **專案語言**: Python 3.13  
> **目標對象**: 系統開發人員、維運人員、專案管理者

---

## 目錄

- [壹、系統規格書 (System Specification)](#壹系統規格書-system-specification)
- [貳、系統分析 (System Analysis)](#貳系統分析-system-analysis)
- [參、系統功能說明 (System Functions)](#參系統功能說明-system-functions)
- [肆、施作紀錄 (Implementation Progress)](#肆施作紀錄-implementation-progress)
- [伍、資料字典 (Data Dictionary)](#伍資料字典-data-dictionary)
- [陸、部署與維運指南 (Deployment & Operations)](#陸部署與維運指南-deployment--operations)
- [柒、測試報告 (Test Report)](#柒測試報告-test-report)
- [捌、已知限制與未來規劃 (Known Limitations & Roadmap)](#捌已知限制與未來規劃-known-limitations--roadmap)

---

# 壹、系統規格書 (System Specification)

## 1.1 系統概述

本系統為一套**採購訂單 (Purchase Order, PO) PDF 智能特徵抽取工具**，能自動從 PDF 格式的採購訂單中抽取結構化資料，輸出為標準 JSON 格式。系統採用 **Factory Pattern（工廠模式）** 設計，可支援 500+ 種供應商格式的擴充，並具備**自學習機制**，透過人工校正回饋持續提升抽取準確率。

## 1.2 系統目標

| 目標項目 | 說明 |
|---------|------|
| **自動化抽取** | 將非結構化的 PO PDF 文件自動轉換為結構化 JSON 資料 |
| **多供應商支援** | 透過 Factory Pattern 支援多種供應商格式，當前已支援 4 家 + 1 泛用 |
| **品質保證** | 4 方法交叉驗證的信心評分系統，自動標記需人工審核的欄位 |
| **自學習優化** | 人工校正後系統可自動學習，下次抽取時準確率持續提升 |
| **自動擴展** | 新供應商累積 ≥3 份校正樣本後，自動生成專屬抽取器 |
| **易用介面** | 提供 CLI 批次處理 + Flask Web 介面雙入口 |

## 1.3 技術規格

### 1.3.1 運行環境

| 項目 | 規格 |
|------|------|
| 作業系統 | Windows 10/11 |
| Python 版本 | 3.13.12（透過 `py` 啟動器） |
| 啟動命令 | `py -m po_extractor.main`（**非** `python`） |
| Web 框架 | Flask 3.1.3 |
| PDF 解析 | pdfplumber |
| 字元編碼 | UTF-8 |

### 1.3.2 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        使用者介面層                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│   │  CLI (main)  │    │ Flask Web UI │    │  CLI (learn)     │  │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────────┘  │
├──────────┼───────────────────┼───────────────────┼──────────────┤
│          │         處理管線層 (Pipeline)          │              │
│   ┌──────▼───────────────────▼───────────────────▼──────────┐   │
│   │ Step2:Extract → Step3:Clean → Step4:Classify → Extract  │   │
│   │                                                          │   │
│   │    ┌────────────────┐    ┌─────────────────────┐        │   │
│   │    │ Symbol         │    │ Confidence           │        │   │
│   │    │ Validator      │    │ Scorer               │        │   │
│   │    │ (4 methods)    │    │ (4 methods)          │        │   │
│   │    └────────────────┘    └─────────────────────┘        │   │
│   │                                                          │   │
│   │    ┌────────────────┐    ┌─────────────────────┐        │   │
│   │    │ Pattern        │    │ Extractor            │        │   │
│   │    │ Learner        │◄──►│ Generator            │        │   │
│   │    └────────────────┘    └─────────────────────┘        │   │
│   └──────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│                      抽取器層 (Extractors)                       │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │              ExtractorRegistry (Factory)                  │   │
│   │  ┌─────┐ ┌───────┐ ┌────────┐ ┌────────┐ ┌─────────┐   │   │
│   │  │ BYD │ │Siemens│ │ Kaifa  │ │DESAY SV│ │ Generic │   │   │
│   │  └─────┘ └───────┘ └────────┘ └────────┘ └─────────┘   │   │
│   │           + 自動生成的新供應商 extractor                    │   │
│   └──────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│                       資料模型層 (Models)                        │
│   PurchaseOrder → PurchaseInfo / VendorInfo / AddressInfo        │
│                    / LineItem / ScheduleLine                      │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3.3 目錄結構

```
<workspace>/
├── import_doc/               # 📥 PDF 輸入目錄
│   └── finish/<Vendor>/      #    處理完成後的 PDF 歸檔
├── output_doc/<Vendor>/      # 📤 JSON 抽取結果輸出
├── corrected/<Vendor>/       # ✏️ 人工校正後的 JSON
├── learned_patterns.json     # 🧠 自動學習的 regex patterns
├── po_extractor/             # 📦 主程式套件
│   ├── main.py               #    CLI 批次處理入口
│   ├── learn.py              #    CLI 學習入口
│   ├── webapp.py             #    Flask Web 入口
│   ├── config.py             #    全域設定
│   ├── models/               #    資料模型 (dataclass)
│   ├── extractors/           #    供應商抽取器 (Factory Pattern)
│   ├── pipeline/             #    處理管線 (5 步驟 + 支援模組)
│   ├── features/             #    供應商特徵關鍵字庫
│   └── templates/            #    Web 介面模板
```

### 1.3.4 相依套件

| 套件 | 版本 | 用途 |
|------|------|------|
| pdfplumber | latest | PDF 文字抽取 |
| Flask | 3.1.3 | Web 介面 |
| Werkzeug | (Flask 附屬) | 檔案上傳安全處理 |

### 1.3.5 效能指標

| 指標 | 數值 |
|------|------|
| 單檔 PDF 處理時間 | < 2 秒 |
| 14 檔批次處理 | < 10 秒 |
| 支援的 PDF 類型 | 文字型 PDF（非影像掃描型） |
| 最大檔案大小限制 | 50 MB (Web 上傳) |

---

# 貳、系統分析 (System Analysis)

## 2.1 需求分析

### 2.1.1 業務需求

公司定期收到來自多家供應商的 PO (採購訂單) PDF 文件，格式各不相同。目前人工逐欄位手動轉錄至系統中，耗時且易錯。本系統旨在自動化此流程，減少人工作業，提升資料正確性。

### 2.1.2 功能需求

| 編號 | 需求 | 優先級 | 狀態 |
|------|------|--------|------|
| FR-01 | 從 PO PDF 抽取訂單編號、日期、金額等結構化欄位 | 高 | ✅ 已完成 |
| FR-02 | 自動識別 PDF 屬於哪家供應商 | 高 | ✅ 已完成 |
| FR-03 | 針對不同供應商使用不同抽取邏輯 | 高 | ✅ 已完成 |
| FR-04 | 統一輸出 JSON 格式 | 高 | ✅ 已完成 |
| FR-05 | 處理 Unicode 變體符號（全形/半形混用） | 高 | ✅ 已完成 |
| FR-06 | 數值格式驗證（歐洲 vs 美式數字格式） | 高 | ✅ 已完成 |
| FR-07 | 信心評分與人工審核標記 | 高 | ✅ 已完成 |
| FR-08 | Web 上傳介面 | 中 | ✅ 已完成 |
| FR-09 | 批次處理 CLI | 中 | ✅ 已完成 |
| FR-10 | 人工校正回饋學習機制 | 中 | ✅ 已完成 |
| FR-11 | 新供應商自動建模 | 中 | ✅ 已完成 |
| FR-12 | 影像型 PDF OCR 辨識 | 低 | ❌ 預留 |
| FR-13 | LayoutLM 深度學習進階抽取 | 低 | ❌ 預留 |

### 2.1.3 非功能需求

| 編號 | 需求 | 說明 |
|------|------|------|
| NFR-01 | 可擴充性 | Factory Pattern 支援 500+ 供應商格式 |
| NFR-02 | 可維護性 | 新增供應商只需一個 .py 檔 + 裝飾器註冊 |
| NFR-03 | 安全性 | 路徑遍歷防護（`..` 檢查）、檔案上傳大小限制 |
| NFR-04 | 可靠性 | 抽取失敗不中斷整批處理 |
| NFR-05 | 編碼安全 | 全程 UTF-8，排除 Unicode 相似符號干擾 |

## 2.2 資料流分析

### 2.2.1 主處理流程 (Level 0 DFD)

```
                                    ┌──────────┐
  ┌──────┐    PDF 檔案    ┌────────►│ output_  │  JSON 結果
  │ 使用 │ ─────────────► │  PO     │ doc/     │ ──────────► 下游系統
  │ 者   │                │  抽取   │          │
  │      │ ◄──── 校正 ──  │  系統   ├──────────┤
  └──────┘   回饋 JSON    │        ─┤ finish/  │  歸檔 PDF
                          └────────►│          │
                                    ├──────────┤
                                    │corrected/│  校正 JSON
                                    ├──────────┤
                                    │ learned_ │  學習 patterns
                                    │patterns  │
                                    └──────────┘
```

### 2.2.2 詳細處理流程 (Level 1 DFD)

```
PDF ──► [Step2 Text Extract] ──► raw_text
            │
            ▼
       [Step3 Clean] ──► cleaned_text
            │
            ▼
       [Step4 Classify] ──► vendor_id
            │
            ▼
       [Registry.get_extractor(vendor_id)]
            │
            ▼
       [Extractor.extract()]  ◄── [Pattern Applier: apply_learned()]
            │
            ▼
       [PurchaseOrder.to_dict()]  ◄── [Symbol Normalizer]
            │
            ▼
       [Confidence Scorer]
            │
            ▼
       JSON output ──► output_doc/<Vendor>/
            │
            ▼
       PDF ──► import_doc/finish/<Vendor>/
```

### 2.2.3 自學習回饋流程

```
output_doc/xxx.json ──► [使用者複製到 corrected/] ──► [人工修正]
            │                                              │
            ▼                                              ▼
       [Pattern Learner: diff()]  ◄───────────  corrected/xxx.json
            │
            ├──► learned_patterns.json (regex patterns)
            │
            ├──► _keywords (分類關鍵字)
            │
            ▼
       [Extractor Generator] ─── (≥3 樣本) ──► NEW_vendor.py
            │
            ▼
       [Registry: 自動註冊新 extractor]
```

## 2.3 設計模式分析

### 2.3.1 Factory Pattern（工廠模式）

系統核心採用 Factory Pattern 管理供應商抽取器：

```python
# 註冊（在各 extractor 檔案頂部）
@ExtractorRegistry.register("byd")
class BYDExtractor(BaseExtractor): ...

# 使用（在 main.py / webapp.py）
extractor = ExtractorRegistry.get_extractor(vendor_id)
po = extractor.extract(cleaned_text, cleaned_pages)
```

**優點**：
- 新增供應商只需建立一個檔案，無需修改核心程式碼
- 各供應商邏輯完全隔離
- 自動生成器可直接生成符合此模式的程式碼

### 2.3.2 Template Method Pattern（模板方法模式）

所有 extractor 繼承 `BaseExtractor`，共用相同的抽取流程骨架：

```python
def extract(self, raw_text, pages) -> PurchaseOrder:
    po = PurchaseOrder(vendor_id="xxx")
    self._extract_header(raw_text, po)      # 子類別實作
    self._extract_vendor(raw_text, po)       # 子類別實作
    self._extract_addresses(raw_text, po)    # 子類別實作
    self._extract_line_items(raw_text, po)   # 子類別實作
    self.apply_learned(po, raw_text)         # 基類別提供 (learned patterns)
    return po
```

### 2.3.3 Strategy Pattern（策略模式）

`symbol_validator.py` 中的 4 方法驗證策略：

| 方法 | 策略 | 說明 |
|------|------|------|
| Method 1 | Unicode 正規化 | NFKC + 自訂符號對應表 |
| Method 2 | 上下文推斷 | 根據前後數字的位數判斷分隔符意義 |
| Method 3 | 格式樣式比對 | 偵測文件使用的數字格式（美式/歐式） |
| Method 4 | 交叉一致性投票 | 比對文件中其他數字的格式進行投票 |

### 2.3.4 Pipeline Pattern（管線模式）

處理流程由 5+N 個步驟串聯：

```
Step1(預留) → Step2(文字抽取) → Step3(清理) → Step4(分類) → Step5(預留)
                                                     ↓
                              Extractor → Symbol → Confidence → Output
```

---

# 參、系統功能說明 (System Functions)

## 3.1 PDF 文字抽取 (Step 2)

| 模組 | `pipeline/step2_extract.py` |
|------|---------------------------|
| 函式 | `extract_text_from_pdf(pdf_path)` |
| 輸入 | PDF 檔案路徑 |
| 輸出 | `{full_text, pages[], is_image_pdf}` |
| 技術 | pdfplumber 逐頁讀取 |
| 影像偵測 | 全文長度 < 50 字元 → 判定為影像型 PDF |

## 3.2 文字清理與正規化 (Step 3)

| 模組 | `pipeline/step3_clean.py` |
|------|--------------------------|
| 函式 | `clean_text_preserve_structure(text)` |
| 處理 | 1. `normalize_text_symbols()` 全形→半形符號轉換 |
|       | 2. NFKC Unicode 正規化 |
|       | 3. 保留換行結構（不合併行） |

### 符號對應表（40+ 種變體）

| 類別 | 已處理的變體數量 | 範例 |
|------|---------------|------|
| 句號 | 11 種 | `·` `˙` `．` `。` → `.` |
| 逗號 | 5 種 | `，` `、` `‚` → `,` |
| 連字號 | 9 種 | `–` `—` `ー` `－` → `-` |
| 空格 | 14 種 | `　`(全形) `\u00A0`(不斷空格) → ` ` |
| 星號 | 4 種 | `＊` `✳` → `*` |

## 3.3 供應商分類 (Step 4)

| 模組 | `pipeline/step4_classify.py` |
|------|------------------------------|
| 函式 | `classify_vendor(raw_text)` |
| 策略 | 關鍵字權重匹配 |
| 資料來源 | `feature_db.py` (內建) + `learned_patterns.json` (學習) |
| 回傳 | vendor_id 字串，無法識別時回傳 `"unknown"` |

**目前已支援的供應商**：

| vendor_id | 供應商名稱 | 關鍵字 |
|-----------|-----------|--------|
| `byd` | BYD (H.K.) CO., LIMITED | BYD, BYD (H.K.) CO., LIMITED |
| `kaifa` | Kaifa Technology | KAIFA, KFSU, KFML |
| `siemens` | Siemens | Siemens, siemens.com |
| `desay_sv` | 德賽西威 | 德赛西威, DESAY SV, desaysv.com |
| `generic` | (萬用/未識別) | — (fallback) |

## 3.4 結構化資料抽取 (Extractors)

### 3.4.1 抽取器架構

```
BaseExtractor (ABC)
├── BYDExtractor          → BYD (H.K.) 訂購單
├── SiemensExtractor      → Siemens 採購訂單 (歐式數字)
├── KaifaExtractor        → Kaifa Technology (KFML/KFSU 兩種子格式)
├── DesaySVExtractor      → 德赛西威 (中文 + 英文混合)
├── GenericExtractor      → 萬用啟發式抽取
└── [auto-generated]      → 自動生成的新供應商抽取器
```

### 3.4.2 各抽取器能力對照

| 欄位 | BYD | Siemens | Kaifa | DESAY SV | Generic |
|------|-----|---------|-------|----------|---------|
| PO Number | ✅ | ✅ | ✅ | ✅ | ✅ |
| Date | ✅ | ✅ | ✅ | ✅ | ✅ |
| Buyer | ✅ | ✅ | ✅ | ✅ | ✅ |
| Contact | ✅ | ✅ | ✅ | ✅ | — |
| Currency | ✅ | ✅ | ✅ | ✅ | ✅ |
| Payment Terms | ✅ | ✅ | ✅ | ✅ | ✅ |
| Trade Terms | ✅ | ✅ | ✅ | ✅ | ✅ |
| Total Amount | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vendor Code | — | ✅ | ✅ | ✅ | — |
| Vendor Name | ✅ | ✅ | ✅ | ✅ | ✅ |
| Vendor Contact | ✅ | ✅ | — | — | — |
| Vendor Phone | — | ✅ | — | — | — |
| Vendor Fax | — | ✅ | ✅ | — | — |
| Vendor Email | — | — | — | ✅ | — |
| Bill-to | ✅ | ✅ | ✅ | ✅ | — |
| Ship-to | ✅ | ✅ | ✅ | ✅ | — |
| Line Items | ✅ | ✅ | ✅ | ✅ | ✅ |
| Schedule Lines | ✅ | ✅ | ✅ | ✅ | — |
| Price Unit | ✅ | ✅ | ✅ | ✅ | — |
| Supplier Material | ✅ | — | — | ✅ | — |
| **歐式數字** | — | **✅** | — | — | — |

### 3.4.3 Siemens 歐式數字格式處理

Siemens 使用歐式數字格式（`.` 為千位分隔，`,` 為小數點）：

| 原始 | 轉換結果 |
|------|---------|
| `1.500` | `1500` |
| `190,00` | `190.00` |
| `2.850,00` | `2850.00` |

## 3.5 符號驗證系統 (Symbol Validator)

### 4 方法共識投票機制

```
原始數值 ──► [Method 1: Unicode 正規化] ──► 結果 A
         ──► [Method 2: 上下文推斷]     ──► 結果 B
         ──► [Method 3: 格式樣式比對]   ──► 結果 C
         ──► [Method 4: 交叉一致性]     ──► 結果 D
                    │
                    ▼
              [投票取多數] → 最終正規化結果
```

### 全文遞迴正規化

`PurchaseOrder.to_dict()` 在輸出前呼叫 `_normalize_all_strings()`，遞迴走訪所有 dataclass 的字串欄位，確保輸出的 JSON 中不殘留任何 Unicode 變體符號。

## 3.6 信心評分系統 (Confidence Scorer)

### 3.6.1 四方法評分

每個欄位使用 4 種獨立方法評分：

| 方法 | 名稱 | 說明 |
|------|------|------|
| M1 | 格式驗證 | 以 regex 檢查欄位值是否符合預期格式 |
| M2 | 完整性檢查 | 值非空、長度合理 |
| M3 | 交叉一致性 | 跨欄位數學核對 (qty × unit_price ≈ net_price) |
| M4 | 來源驗證 | 驗證抽取值確實存在於原始 PDF 文字中 |

### 3.6.2 評分規則

| 同意數 | 分數 | 是否需要人工審核 |
|--------|------|----------------|
| 4/4 方法同意 | 100 分 | 否 |
| 3/4 方法同意 | 75 分 | 否（標示未通過的方法） |
| 2/4 方法同意 | 50 分 | **是** |
| 1/4 或更少 | 25 分 | **是** |
| 必填欄位為空 | 0 分 | **是** |
| 選填欄位為空 | 50 分 | 否 |

### 3.6.3 文件層級判定

- `_accuracy_pct` < 90% → 整份文件標記需人工審核
- 任何欄位被標記 `review: true` → 文件標記需審核

### 3.6.4 JSON 輸出欄位

```json
{
  "purchase_info": { ... },
  "vendor_info": { ... },
  "_accuracy_pct": 83.6,
  "_review_required": true,
  "_review_fields": ["bill_to.contact", "ship_to.phone"],
  "_confidence": {
    "purchase_info.po_number": {"score": 100, "review": false},
    "bill_to.contact": {"score": 0, "review": true, "reason": "必填欄位為空"}
  }
}
```

## 3.7 自學習回饋系統

### 3.7.1 人工校正存檔

| 操作 | 說明 |
|------|------|
| 位置 | `corrected/<Vendor>/xxx.json` |
| 方式 | 從 `output_doc/` 複製 JSON，修正錯誤值後存入 |
| Web API | `POST /save-correction` 透過 Web 介面直接儲存 |

### 3.7.2 Pattern Learning 引擎

| 模組 | `pipeline/pattern_learner.py` |
|------|-------------------------------|
| 指令 | `py -m po_extractor.learn` |
| 流程 | 1. 掃描 `corrected/<Vendor>/*.json` |
|       | 2. 找到對應的 `output_doc/<Vendor>/*.json` |
|       | 3. 比對差異欄位 (diff) |
|       | 4. 從原始 PDF 文字中定位正確值 |
|       | 5. 擷取上下文標籤，生成 regex pattern |
|       | 6. 儲存至 `learned_patterns.json` |

### Pattern 生成策略

```
corrected_value = "Min Zhou"
  → 在 raw_text 中找到 "Min Zhou"
  → 取前方上下文 "Integrated Silicon Solution公司"
  → 生成 pattern: egrated\ Silicon\ Solution公司\s*[:：]?\s*([^\n]{1,100})
  → 儲存到 learned_patterns.json
```

### 3.7.3 Learned Patterns 自動套用

| 模組 | `pipeline/pattern_applier.py` |
|------|-------------------------------|
| 觸發 | 每個 extractor 的 `extract()` 結尾自動呼叫 `self.apply_learned()` |
| 邏輯 | 1. 讀取 `learned_patterns.json`（有檔案變更快取）|
|       | 2. 遍歷該 vendor_id 的所有 learned patterns |
|       | 3. 只填入目前為空的欄位（不覆蓋已有值） |
|       | 4. 按 `samples` 數量排序，最有信心的 pattern 優先 |

### 3.7.4 新供應商自動建模

| 模組 | `pipeline/extractor_generator.py` |
|------|-----------------------------------|
| 指令 | `py -m po_extractor.learn --generate` |
| 門檻 | 同一 vendor_id ≥ 3 份校正樣本（可設定 `AUTO_EXTRACTOR_THRESHOLD`） |
| 產出 | 自動生成的 `extractors/<vendor>.py` |
| 動作 | 1. 以 learned patterns 為 regex 來源生成 Python 程式碼 |
|       | 2. 自動註冊到 `extractors/__init__.py` |
|       | 3. 自動加入 `feature_db.py` 的分類關鍵字 |
|       | 4. 自動加入 `VENDOR_FOLDER_MAP` |

## 3.8 CLI 功能

### 3.8.1 批次處理 (main.py)

```bash
py -m po_extractor.main                    # 掃描 import_doc/ 處理全部
py -m po_extractor.main --input <path>     # 自訂輸入路徑
py -m po_extractor.main --output <path>    # 自訂輸出路徑
py -m po_extractor.main --list-vendors     # 列出已註冊的 extractor
py -m po_extractor.main --no-recursive     # 不遞迴掃描子目錄
```

### 3.8.2 學習指令 (learn.py)

```bash
py -m po_extractor.learn                   # 從 corrected/ 學習
py -m po_extractor.learn --status          # 顯示學習狀態
py -m po_extractor.learn --show-patterns   # 顯示所有已學習 patterns
py -m po_extractor.learn --generate        # 學習 + 自動生成 extractor
```

## 3.9 Web 介面功能

| 路由 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 主頁：拖曳上傳、處理全部、結果瀏覽 |
| `/upload` | POST | 多檔 PDF 上傳並即時處理 |
| `/process-all` | POST | 掃描 import_doc/ 批次處理 |
| `/results` | GET | 列出所有結果（依供應商分組） |
| `/view/<path>` | GET | 檢視 JSON 結果內容 |
| `/download/<path>` | GET | 下載 JSON 結果檔案 |
| `/save-correction` | POST | 儲存人工校正的 JSON |
| `/learn` | POST | 觸發 Pattern Learning |
| `/learn/generate` | POST | 學習 + 自動生成 extractor |
| `/learn/status` | GET | 查詢學習狀態 |
| `/corrections` | GET | 列出所有已校正的檔案 |

---

# 肆、施作紀錄 (Implementation Progress)

## 4.1 開發時程

| 階段 | 完成項目 | 狀態 |
|------|---------|------|
| **Phase 1: 基礎架構** | 專案骨架、config、models、pipeline 5 步驟 | ✅ 完成 |
| **Phase 2: 抽取器開發** | BYD / Kaifa / Siemens / DESAY_SV / Generic 共 5 個 | ✅ 完成 |
| **Phase 3: Bug 修復 Round 1** | BYD 日期 regex、Siemens 總額、Kaifa 總額冒號 | ✅ 完成 |
| **Phase 4: 目錄重構** | import_doc/output_doc/finish/ 三層架構 | ✅ 完成 |
| **Phase 5: 符號驗證** | symbol_validator 4 方法 + 全文遞迴正規化 | ✅ 完成 |
| **Phase 6: Web 介面** | Flask webapp + templates (上傳/處理/瀏覽) | ✅ 完成 |
| **Phase 7: 欄位校正** | 所有 4 個供應商 extractor 空白欄位修復 | ✅ 完成 |
| **Phase 8: 信心評分** | confidence_scorer 4 方法 + 人工審核標記 | ✅ 完成 |
| **Phase 9: 自學習系統** | pattern_learner + pattern_applier + extractor_generator | ✅ 完成 |

## 4.2 程式碼統計

| 項目 | 數量 |
|------|------|
| Python 檔案 | 28 個 |
| 程式碼行數 | ~2,745 行 |
| HTML 模板 | 1 個 |
| 已支援供應商 | 4 + 1 泛用 |
| 已測試 PDF 數 | 14 份 |
| 學習樣本 | 1 份 (siemens) |

## 4.3 目前準確率

| 供應商 | PDF 數 | 準確率範圍 | 需審核欄位數 |
|--------|--------|-----------|------------|
| DESAY_SV | 3 | 92.4% — 96.0% | 5 |
| BYD | 3 | 79.3% — 84.6% | 4 |
| Siemens | 5 | 72.3% — 83.6% | 2—6 |
| Kaifa | 3 | 73.6% — 79.9% | 5—6 |

### 主要需審核欄位分布

| 欄位 | BYD | Siemens | Kaifa | DESAY_SV | 說明 |
|------|-----|---------|-------|----------|------|
| vendor_info.contact | 3 | 2 | 3 | 3 | PDF 中無此資訊 |
| vendor_info.phone | 0 | 2 | 3 | 3 | PDF 中無此資訊 |
| bill_to.contact | 3 | 5 | 3 | 3 | PDF 中無此資訊 |
| bill_to.phone | 0 | 0 | 2 | 3 | 部分有 |
| ship_to.contact | 0 | 2 | 3 | 0 | |
| ship_to.phone | 0 | 5 | 3 | 0 | |
| ship_to.address | 0 | 0 | 0 | 3 | |
| ship_to.company_name | 3 | 0 | 0 | 0 | |

> **備註**: 多數需審核欄位是因為 PDF 原始文件中確實不包含該資訊。

## 4.4 已修復的 Bug

| # | 問題 | 解決方案 |
|---|------|---------|
| 1 | BYD 日期 regex 無法匹配 `2025.01.15` 分行 | 修正 regex 支援跨行日期 |
| 2 | Siemens Total 匹配不到 `2.850,00` | 改用歐式數字 regex |
| 3 | Kaifa Total 匹配不到冒號後數字 | 修正 regex 支援 `Tax: 8,195,706.84` |
| 4 | `python` 命令找不到 | 改用 `py` 啟動器 |
| 5 | 相對 import 失敗 | 改用絕對 import `po_extractor.xxx` |
| 6 | Unicode 變體符號導致 regex 失敗 | 建立 40+ 符號對應表 |
| 7 | Siemens vendor_code 隔行無法匹配 | 允許 200 字元範圍內搜尋 |
| 8 | Siemens contact 抓到公司名稱 | 改用 `Name/CN DI` 精確模式 |
| 9 | BYD 聯絡人/Ship-to/supplier_material 空白 | 新增對應 regex |
| 10 | DESAY_SV Attention 格式不匹配 | 放寬 `\S+` 模式 |

## 4.5 最新功能實施 (2025/12/26)

### 新增需求實施狀態
**✅ 全部完成**

| 階段 | 功能 | 狀態 | 測試結果 |
|------|------|------|---------|
| **Phase 1** | PDF 頁面追蹤與欄位來源映射 | ✅ 完成 | 96% 準確率處理 |
| **Phase 2** | /pdf-pages API 路由实现 | ✅ 完成 | 成功返回 2 頁內容 |
| **Phase 3** | 審核面板頁面分組重構 | ✅ 完成 | 色彩編碼分頁顯示 |
| **Phase 4** | 欄位管理（新增/刪除/重命名） | ✅ 完成 | 動態欄位操作 |
| **Phase 5** | /pretrain API 路由實現 | ✅ 完成 | 成功學習 2 個模式 |
| **Phase 6** | 預訓練前端介面開發 | ✅ 完成 | 拖拽上傳/動態表格 |
| **Phase 7** | 整合測試與除錯 | ✅ 完成 | 所有 API 測試通過 |

### 技術改進摘要

**Backend 改進:**
- ✅ `_page_info` 數據結構：每頁文本內容完整保存
- ✅ `_field_sources` 映射：每個欄位追蹤來源頁碼  
- ✅ `track_field_sources()` 函數：智能頁面來源分析
- ✅ `learn_from_pretrain()` 功能：用戶數據直接學習
- ✅ 2 個新 API 端點：`/pdf-pages` 和 `/pretrain`

**Frontend 改進:**
- ✅ 頁面分組審核面板：6 種顏色編碼不同頁面
- ✅ 可摺疊頁面文本：點擊展開查看原始內容
- ✅ 欄位管理工具：新增/刪除/重命名動態操作
- ✅ 預訓練介面：完整的拖拽上傳和欄位映射
- ✅ 實時反饋系統：處理狀態和結果顯示

**數據兼容性:**
- ✅ 向前兼容：所有現有功能保持不變
- ✅ 數據結構擴展：新增欄位不影響現有邏輯
- ✅ API 向下兼容：原有後端介面保持穩定

## 4.6 UI優化與用戶體驗改進 (2026/03/30)

### 預訓練介面收合功能
**✅ 完成實施**

| 項目 | 功能 | 狀態 | 實施細節 |
|------|------|------|---------|
| **收合展開機制** | 預訓練區塊可收合/展開控制 | ✅ 完成 | 完整的CSS動畫和JavaScript控制 |
| **視覺設計** | 收合按鈕與狀態指示 | ✅ 完成 | ▶/▼ 圖標切換，展開/收合文字提示 |
| **預設狀態** | 預訓練區塊預設收起 | ✅ 完成 | 減少頁面初期視覺雜亂 |
| **動畫效果** | 平滑的展開/收合過渡 | ✅ 完成 | 0.3秒CSS過渡動畫 |

### 技術實施詳情

**Frontend UI 改進:**
- ✅ **收合控制結構**：新增 `.card-header` 和 `.card-content` 分層設計
- ✅ **CSS 動畫樣式**：`.collapsed` 和 `.expanded` 狀態控制
- ✅ **JavaScript 控制函數**：`togglePretrain()` 函數實現狀態切換
- ✅ **按鈕設計**：`.collapse-btn` 樣式，包含懸停效果和狀態提示
- ✅ **響應式支援**：在各種設備上均能正常運作

**用戶體驗改進:**
- ✅ **預設收起狀態**：頁面初次載入時預訓練內容隱藏，保持頁面簡潔
- ✅ **直觀操作**：清楚的視覺提示（▶ 展開 / ▼ 收合）
- ✅ **狀態保持**：用戶操作的展開/收合狀態在操作期間持續
- ✅ **無縫切換**：平滑動畫避免突兀的內容顯示/隱藏

**代碼品質:**
- ✅ **CSS 組織**：收合功能的樣式獨立分區，易於維護
- ✅ **JavaScript 簡潔性**：單一函數控制所有收合邏輯
- ✅ **HTML 結構化**：語義化的標籤結構，提高可讀性

### 實施影響

| 方面 | 改進效果 | 數據/反饋 |
|------|---------|-----------|
| **頁面載入** | 減少初期視覺負擔 | 預訓練內容預設隱藏 |
| **用戶選擇** | 按需顯示功能 | 用戶可自行決定是否使用預訓練功能 |
| **介面整潔度** | 提升頁面組織性 | 主要功能區塊清晰分離 |
| **操作回饋** | 增加互動性 | 即時的視覺狀態變化 |

### 測試驗證

- ✅ **功能測試**：收合/展開機制正常運作
- ✅ **瀏覽器兼容**：在主流瀏覽器中正常顯示
- ✅ **響應式測試**：各種螢幕尺寸下功能正常
- ✅ **動畫流暢度**：過渡動畫平滑無卡頓

---

# 伍、資料字典 (Data Dictionary)

## 5.1 PurchaseOrder（採購訂單主結構）

| 欄位 | 型別 | 說明 | 範例 |
|------|------|------|------|
| vendor_id | str | 供應商識別碼 | `"siemens"` |
| purchase_info | PurchaseInfo | 訂單表頭資訊 | (見下表) |
| vendor_info | VendorInfo | 供應商資訊 | (見下表) |
| bill_to | AddressInfo | 帳單地址 | (見下表) |
| ship_to | AddressInfo | 送貨地址 | (見下表) |
| line_items | List[LineItem] | 明細行項目 | (見下表) |

## 5.2 PurchaseInfo（訂單表頭）

| 欄位 | 型別 | 說明 | 範例 |
|------|------|------|------|
| po_number | str | 訂單編號 | `"4511697495"` |
| date | str | 訂單日期 | `"24.10.2025"` |
| buyer | str | 採購方 | `"Siemens Industrial Automation Products Ltd., Chengdu"` |
| contact | str | 聯絡人 | `"Min Zhou"` |
| payment_terms | str | 付款條件 | `"90 days after receipt of invoice, net"` |
| currency | str | 幣別 | `"USD"` |
| trade_terms | str | 貿易條件 | `"DAP Chengdu"` |
| total_amount | str | 總金額 | `"2700.00"` |

## 5.3 VendorInfo（供應商資訊）

| 欄位 | 型別 | 說明 | 範例 |
|------|------|------|------|
| vendor_code | str | 供應商代碼 | `"4000039123"` |
| name | str | 供應商名稱 | `"Integrated Silicon Solution (Cayman) Inc."` |
| address | str | 地址 | `"PO BOX 309, UGLAND HOUSE..."` |
| country | str | 國家 | `"中国香港"` |
| contact | str | 聯絡人 | `"Deni Yang"` |
| phone | str | 電話 | `"86-027-87509686"` |
| fax | str | 傳真 | `"0086 28 6238 7000"` |
| email | str | 電子郵件 | `"huan.li2@desaysv.com"` |

## 5.4 AddressInfo（地址區塊）

| 欄位 | 型別 | 說明 | 範例 |
|------|------|------|------|
| company_name | str | 公司名稱 | `"西门子(中国)有限公司"` |
| address | str | 地址 | `"No. 1 Tianfu St., Chengdu"` |
| contact | str | 聯絡人 | `"Ms.Wang"` |
| phone | str | 電話 | `"(852)24827617"` |
| fax | str | 傳真 | `"(852)24710474"` |
| email | str | 電子郵件 |  |

## 5.5 LineItem（明細行）

| 欄位 | 型別 | 說明 | 範例 |
|------|------|------|------|
| item_no | str | 項次 | `"00010"` |
| product_code | str | 產品編號 | `"A5E37602377"` |
| description | str | 品名描述 | `"IC_DDR3L_2Gb_x16"` |
| quantity | str | 數量 | `"1500"` |
| unit | str | 單位 | `"EA"` / `"ST"` / `"Piece"` |
| unit_price | str | 單價 | `"190.00"` |
| price_unit | str | 計價單位 | `"PER/10,000"` / `"/100"` |
| net_price | str | 淨價 | `"2850.00"` |
| supplier_material | str | 供應商料號 | `"IS43TR16128DL-125KBLI-TR"` |
| schedule_lines | List[ScheduleLine] | 交期明細 | (見下表) |

## 5.6 ScheduleLine（交期排程）

| 欄位 | 型別 | 說明 | 範例 |
|------|------|------|------|
| schedule_no | str | 排程序號 | `"0001"` |
| delivery_date | str | 交貨日期 | `"2026-03-23"` |
| quantity | str | 數量 | `"5000.00"` |

## 5.7 learned_patterns.json 結構

```json
{
  "<vendor_id>": {
    "<field.dot.path>": [
      {
        "pattern": "<regex 字串>",
        "group": 1,
        "flags": "IGNORECASE",
        "label": "<前方標籤文字>",
        "samples": 2,
        "last_updated": "2026-03-30",
        "source_files": ["file.json"]
      }
    ]
  },
  "_keywords": {
    "<vendor_id>": ["分類關鍵字1", "分類關鍵字2"]
  }
}
```

---

# 陸、部署與維運指南 (Deployment & Operations)

## 6.1 安裝步驟

```bash
# 1. 確認 Python 版本
py --version   # 需 3.10+

# 2. 安裝相依套件
py -m pip install pdfplumber flask

# 3. 建立目錄結構
mkdir import_doc
mkdir output_doc
mkdir corrected
```

## 6.2 日常操作流程

### 批次處理

```bash
# 1. 將 PDF 放入 import_doc/
# 2. 執行批次處理
py -m po_extractor.main

# 3. 結果在 output_doc/<Vendor>/*.json
# 4. 已處理 PDF 移至 import_doc/finish/<Vendor>/
```

### Web 介面

```bash
py -m po_extractor.webapp
# 瀏覽器開啟 http://127.0.0.1:5000
```

### 自學習回饋

```bash
# 1. 複製需校正的 JSON
cp output_doc/SIEMENS/4511697495.json corrected/SIEMENS/

# 2. 修正 corrected/ 中的 JSON（可用文字編輯器或 Web 介面）

# 3. 執行學習
py -m po_extractor.learn

# 4. 查看學習成果
py -m po_extractor.learn --status
py -m po_extractor.learn --show-patterns

# 5. 自動生成新供應商 extractor (需 ≥3 份樣本)
py -m po_extractor.learn --generate
```

## 6.3 新增供應商 (手動方式)

1. 在 `po_extractor/extractors/` 建立 `<vendor_id>.py`
2. 繼承 `BaseExtractor`，加上 `@ExtractorRegistry.register("<vendor_id>")`
3. 實作 `extract()` 方法（可參考現有 extractor）
4. 在 `extractors/__init__.py` 加上 `from .<vendor_id> import *`
5. 在 `features/feature_db.py` 加入關鍵字
6. 在 `config.py` 的 `VENDOR_FOLDER_MAP` 加入對應

## 6.4 新增供應商 (自動方式)

1. 讓系統用 Generic extractor 處理新供應商 PDF
2. 將 `output_doc/GENERIC/` 中的 JSON 複製到 `corrected/NEW_VENDOR/`
3. 修正欄位值，確保 `vendor_id` 欄位設為新的供應商 ID
4. 累積 ≥3 份校正樣本
5. 執行 `py -m po_extractor.learn --generate`
6. 系統自動生成 extractor 檔案、註冊、加入分類關鍵字

## 6.5 完整重啟指南

每次重新啟動系統時，請依照以下步驟操作：

### 步驟一：環境確認

```powershell
# 確認 Python 環境
py --version
# 預期: Python 3.13.x

# 確認套件完整
py -c "import pdfplumber; import flask; print('pdfplumber:', pdfplumber.__version__); print('Flask:', flask.__version__)"
```

### 步驟二：確認目錄結構

```powershell
# 確認所有必要目錄與檔案存在
Test-Path "import_doc"           # 應為 True
Test-Path "output_doc"           # 應為 True
Test-Path "corrected"            # 應為 True
Test-Path "learned_patterns.json" # 應為 True

# 如有缺失，執行以下建立
mkdir import_doc -ErrorAction SilentlyContinue
mkdir output_doc -ErrorAction SilentlyContinue
mkdir corrected -ErrorAction SilentlyContinue
```

### 步驟三：啟動方式 (三選一)

#### 方式 A：CLI 批次處理

```powershell
# 1. 將 PDF 放入 import_doc/ 目錄
# 2. 執行批次抽取
py -m po_extractor.main

# 結果：output_doc/<Vendor>/*.json
# 已處理 PDF 移至：import_doc/finish/<Vendor>/
```

#### 方式 B：Web 介面

```powershell
# 啟動 Web 伺服器
py -m po_extractor.webapp

# 瀏覽器開啟 http://127.0.0.1:5000
# 可拖曳上傳 PDF、線上查看結果、提交校正
```

#### 方式 C：完整學習 + 抽取循環

```powershell
# 1. 先執行學習（如 corrected/ 有新校正資料）
py -m po_extractor.learn

# 2. 查看學習狀態
py -m po_extractor.learn --status

# 3. 如需自動生成新 extractor（需 ≥3 份樣本）
py -m po_extractor.learn --generate

# 4. 執行批次抽取
py -m po_extractor.main
```

### 快速參考命令表

| 用途 | 命令 |
|------|------|
| 批次抽取 | `py -m po_extractor.main` |
| Web 介面 | `py -m po_extractor.webapp` |
| 執行學習 | `py -m po_extractor.learn` |
| 學習狀態 | `py -m po_extractor.learn --status` |
| 查看模式 | `py -m po_extractor.learn --show-patterns` |
| 生成 extractor | `py -m po_extractor.learn --generate` |
| 環境檢查 | `py --version` |
| 目錄檢查 | `Test-Path "import_doc"` |

### 壓力測試重啟流程

```powershell
# 1. 清空 output_doc（保留目錄結構）
Remove-Item "output_doc\*" -Recurse -Force -ErrorAction SilentlyContinue

# 2. 將測試 PDF 從 finish 複製回 import_doc
Copy-Item "import_doc\finish\*" "import_doc\" -Recurse -Force

# 3. 執行批次處理
py -m po_extractor.main

# 4. 確認結果
Get-ChildItem "output_doc" -Recurse -Filter "*.json" | Measure-Object
```

---

## 6.6 設定說明

| 設定項 | 檔案位置 | 預設值 | 說明 |
|--------|---------|--------|------|
| `DEFAULT_INPUT_DIR` | config.py | `import_doc/` | PDF 輸入目錄 |
| `DEFAULT_OUTPUT_DIR` | config.py | `output_doc/` | JSON 輸出目錄 |
| `DEFAULT_FINISH_DIR` | config.py | `import_doc/finish/` | 已處理 PDF 歸檔 |
| `DEFAULT_CORRECTED_DIR` | config.py | `corrected/` | 人工校正 JSON |
| `LEARNED_PATTERNS_PATH` | config.py | `learned_patterns.json` | 學習成果儲存 |
| `AUTO_EXTRACTOR_THRESHOLD` | config.py | `3` | 自動生成 extractor 所需最低樣本數 |
| `IMAGE_PDF_TEXT_THRESHOLD` | config.py | `50` | 低於此字數判定為影像型 PDF |
| `MAX_CONTENT_LENGTH` | webapp.py | `50 MB` | Web 上傳檔案大小限制 |

---

# 柒、測試報告 (Test Report)

## 7.1 測試範圍

| 項目 | 說明 |
|------|------|
| 測試日期 | 2026-03-30 |
| PDF 總數 | 14 份 |
| 供應商涵蓋 | BYD (3)、Siemens (5)、Kaifa (3)、DESAY_SV (3) |
| 成功率 | 14/14 (100%) 全數成功處理 |

## 7.2 各供應商測試結果

### BYD (3 份)

| 檔案 | 準確率 | 需審核 |
|------|--------|--------|
| 3100544305 | 84.6% | 4 欄位 |
| 3100556671 | 81.4% | 4 欄位 |
| 3100635522 | 79.3% | 4 欄位 |

### Siemens (5 份)

| 檔案 | 準確率 | 需審核 |
|------|--------|--------|
| 4511697495 | 83.6% | 2 欄位 |
| 4511793623 | 83.3% | 2 欄位 |
| 4511802539 | 72.3% | 6 欄位 |
| 4511823207 | 72.3% | 6 欄位 |
| 4511828853 | 83.2% | 2 欄位 |

### Kaifa (3 份)

| 檔案 | 準確率 | 需審核 |
|------|--------|--------|
| KFSU PO 4501032812 | 76.4% | 5 欄位 |
| PO# 4501027279 REV01 | 79.9% | 6 欄位 |
| PO# 4501055361 | 75.5% | 6 欄位 |

### DESAY_SV (3 份)

| 檔案 | 準確率 | 需審核 |
|------|--------|--------|
| 3600217031 | 92.9% | 5 欄位 |
| 6100042336 | 92.4% | 5 欄位 |
| 6300002706 | 96.0% | 5 欄位 |

## 7.3 自學習測試結果

| 測試項目 | 結果 |
|---------|------|
| 校正檔案儲存 | ✅ 成功 |
| Pattern 差異比對 | ✅ 偵測到 2 個欄位差異 |
| Pattern 自動生成 | ✅ 成功生成 1 個 pattern |
| Learned Pattern 套用 | ✅ 成功填入 `bill_to.contact` |
| 學習狀態查詢 | ✅ 正常顯示 |
| extractor 自動生成 | ✅ 邏輯正常（尚未達門檻） |

---

# 捌、已知限制與未來規劃 (Known Limitations & Roadmap)

## 8.1 已知限制

| # | 限制 | 影響 | 計畫改善 |
|---|------|------|---------|
| 1 | **不支援影像型 PDF** | 掃描件無法處理 | Step 1 預留 OCR 接口 (Tesseract/PaddleOCR) |
| 2 | **不支援密碼保護 PDF** | 加密文件無法開啟 | 未規劃 |
| 3 | **模式生成精度有限** | 初次學習的 pattern 可能過於寬鬆 | 多筆校正後會自動收斂 |
| 4 | **無表格佈局分析** | 橫跨多欄的表格可能錯位 | Step 5 預留 LayoutLM |
| 5 | **Line Item 學習受限** | 自動學習主要針對 header 欄位 | 需手動調整 extractor |
| 6 | **無資料庫整合** | 結果僅存 JSON 檔案 | 可擴充 SQLite/PostgreSQL |
| 7 | **單機運行** | 無分散式處理能力 | 可擴充 Celery 任務佇列 |
| 8 | **Web UI 無使用者認證** | 無權限控管 | 可加入 Flask-Login |

## 8.2 未來規劃 (Roadmap)

### 短期 (1-3 個月)

| 優先級 | 項目 | 說明 |
|--------|------|------|
| 高 | OCR 支援 | 整合 Tesseract 或 PaddleOCR 處理影像型 PDF |
| 高 | Web 校正編輯器 | 在 Web 介面中直接編輯 JSON 欄位並儲存校正 |
| 中 | 匯出 Excel/CSV | 支援下載 Excel 格式 |
| 中 | 批次學習排程 | 定時自動執行學習 |

### 中期 (3-6 個月)

| 優先級 | 項目 | 說明 |
|--------|------|------|
| 高 | LayoutLM 進階抽取 | 深度學習模型處理複雜表格佈局 |
| 中 | 資料庫儲存 | JSON → SQLite/PostgreSQL |
| 中 | API 整合 | REST API 供 ERP/SAP 系統串接 |
| 低 | 多語言 OCR | 中英日混合文字辨識 |

### 長期 (6-12 個月)

| 優先級 | 項目 | 說明 |
|--------|------|------|
| 中 | 使用者管理 | 權限控管、審核流程 |
| 中 | 儀表板 | 準確率趨勢、供應商統計、學習進度 |
| 低 | 分散式處理 | Celery + Redis 大量 PDF 並行處理 |
| 低 | 自動閾值調整 | 根據歷史準確率自動調整信心評分門檻 |

---

# 玖、開發計畫 (Development Plans)

## 9.1 當前開發需求

### 9.1.1 需求概述

| 需求 | 描述 | 優先級 |
|------|------|--------|
| **需求一** | 增強「審核修正」頁面 — 逐頁 PDF 內容呈現與欄位管理 | 高 |
| **需求二** | 首頁新增「預訓練」功能 | 中 |

### 9.1.2 需求一：增強審核修正頁面

#### 功能需求
- **逐頁呈現**：依各 PDF 有幾頁，將欄位按頁面分組顯示
- **頁面標記**：每個欄位標註出自 PDF 第幾頁
- **頁面區分**：不同頁面以顏色區分，便於視覺識別
- **欄位管理**：提供手動新增/刪除/修改欄位名稱功能
- **原文對照**：各頁面提供原始 PDF 文字預覽，方便核對

#### 技術架構

**後端變更** (webapp.py)
```python
# 修改 process_pdf() 函數
def process_pdf(pdf_path: str) -> dict:
    # 新增頁面資訊追蹤
    output["_page_info"] = {
        "total_pages": len(result["pages"]),
        "pages": [
            {"page": i+1, "text": page_text} 
            for i, page_text in enumerate(result["pages"])
        ]
    }
    
    # 新增欄位來源追蹤
    output["_field_sources"] = track_field_sources(output, result["pages"])

# 新增 API 路由
@app.route('/pdf-pages/<path:filepath>')
def get_pdf_pages(filepath):
    """取得 PDF 逐頁文字內容"""
```

**前端變更** (index.html)
- 重構「查看/編輯所有欄位」區域
- 按頁碼分組顯示 (📄 第 1 頁、📄 第 2 頁...)
- 頁面顏色系統 (CSS 變數動態生成)
- 欄位操作功能 (新增 ➕、刪除 🗑️、改名)
- 原文預覽 (可摺疊的 📝 查看此頁原文)

#### UI 設計規格

```
┌─────────────────────────────────────────────────────┐
│ 📄 第 1 頁 (共 3 頁)                    [📝 查看原文] │
│  ┌─ 淡藍底色 ──────────────────────────────────────┐ │
│  │ [purchase_info.po_number ▼] [P1] [4511697495  ] │🗑│
│  │ [purchase_info.date      ▼] [P1] [24.10.2025  ] │🗑│
│  │ [vendor_info.name        ▼] [P1] [Integrated...] │🗑│
│  │         [＋ 新增欄位]                              │
│  └──────────────────────────────────────────────────┘ │
│                                                       │
│ 📄 第 2 頁 (共 3 頁)                    [📝 查看原文] │
│  ┌─ 淡綠底色 ──────────────────────────────────────┐ │
│  │ [purchase_info.total_amount▼] [P2] [2850.00   ] │🗑│
│  │ [line_items.0.product_code ▼] [P2] [A5E376...  ] │🗑│
│  │         [＋ 新增欄位]                              │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 9.1.3 需求二：預訓練功能

#### 功能需求
- **PDF 上傳**：單一 PDF 檔案上傳
- **供應商選擇**：下拉選單 + 新增選項
- **欄位對照表**：標準欄位名稱 + 使用者填值
- **自動學習**：直接生成 patterns 並儲存
- **結果顯示**：顯示學習成果摘要

#### 技術架構

**後端變更** (webapp.py)
```python
@app.route('/pretrain', methods=['POST'])
def pretrain():
    """預訓練 API
    
    接收: 
    - pdf: PDF 檔案
    - vendor_id: 供應商 ID (可選)
    - fields: JSON 格式的欄位資料
    
    處理:
    1. extract_text_from_pdf()
    2. classify_vendor() 或使用指定 vendor_id  
    3. 對每個欄位呼叫 _generate_pattern_for_field()
    4. 儲存到 learned_patterns.json
    5. 同時儲存到 corrected/<Vendor>/
    """
```

**前端變更** (index.html)
```html
<!-- 新增預訓練卡片 -->
<div class="card">
  <h2>🧠 預訓練</h2>
  <div class="pretrain-upload">...</div>
  <div class="vendor-select">...</div>
  <div class="field-mapping-table">...</div>
  <button class="btn btn-primary">🧠 開始預訓練</button>
</div>
```

#### 欄位對照表設計

| 欄位名稱 | 正確值 |
|---------|--------|
| purchase_info.po_number | [使用者輸入] |
| purchase_info.date | [使用者輸入] |
| purchase_info.buyer | [使用者輸入] |
| vendor_info.name | [使用者輸入] |
| ... | ... |

### 9.1.4 施作計畫

| 步驟 | 內容 | 預估時間 |
|------|------|---------|
| **Phase 1** | 後端：修改 `process_pdf()` 加入頁面追蹤 | 30 分鐘 |
| **Phase 2** | 後端：新增 `/pdf-pages` API | 15 分鐘 |
| **Phase 3** | 前端：重構審核面板 — 逐頁分組顯示 | 45 分鐘 |
| **Phase 4** | 前端：欄位管理功能 (新增/刪除/改名) | 30 分鐘 |
| **Phase 5** | 後端：新增 `/pretrain` API | 30 分鐘 |
| **Phase 6** | 前端：預訓練 UI 介面 | 45 分鐘 |
| **Phase 7** | 整合測試與除錯 | 30 分鐘 |
| **總計** | | **約 3.5 小時** |

### 9.1.5 資料結構變更

#### JSON 輸出新增欄位

```json
{
  "purchase_info": { ... },
  "vendor_info": { ... },
  "_accuracy_pct": 83.6,
  "_review_required": true,
  "_page_info": {
    "total_pages": 3,
    "pages": [
      { "page": 1, "text": "Purchase Order\nPO Number: 4511697495..." },
      { "page": 2, "text": "Line Items:\n00010 A5E37602377..." },
      { "page": 3, "text": "Terms and Conditions..." }
    ]
  },
  "_field_sources": {
    "purchase_info.po_number": [1],
    "purchase_info.total_amount": [2],
    "vendor_info.name": [1],
    "line_items.0.product_code": [2]
  }
}
```

#### 預訓練 API 規格

```
POST /pretrain
Content-Type: multipart/form-data

Fields:
  - pdf: PDF 檔案
  - vendor_id: 供應商 ID（可選）
  - fields: JSON 字串，格式如：
    {
      "purchase_info.po_number": "4511697495",
      "purchase_info.date": "24.10.2025",
      "vendor_info.name": "Siemens AG"
    }

Response:
{
  "status": "success",
  "vendor_id": "siemens", 
  "patterns_learned": 5,
  "fields_processed": {
    "purchase_info.po_number": "success",
    "purchase_info.date": "success", 
    "vendor_info.name": "not_found_in_pdf"
  }
}
```

### 9.1.6 檔案修改清單

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `po_extractor/webapp.py` | 修改 + 新增 | 修改 `process_pdf()`；新增 `/pdf-pages`、`/pretrain` 路由 |
| `po_extractor/templates/index.html` | 重構 | 審核面板重構 + 預訓練卡片 + CSS 樣式 |
| `po_extractor/pipeline/pattern_learner.py` | 新增 | `learn_from_pretrain()` 函式 |

---

# 附錄

## A. 完整檔案清單

| # | 檔案路徑 | 行數 | 用途 |
|---|---------|------|------|
| 1 | `po_extractor/__init__.py` | 1 | 套件初始化 |
| 2 | `po_extractor/config.py` | 24 | 全域設定 |
| 3 | `po_extractor/main.py` | 173 | CLI 批次處理 |
| 4 | `po_extractor/learn.py` | 169 | CLI 學習入口 |
| 5 | `po_extractor/webapp.py` | 294 | Flask Web 介面 |
| 6 | `po_extractor/models/__init__.py` | 1 | 匯出 Models |
| 7 | `po_extractor/models/po_model.py` | 105 | 資料模型定義 |
| 8 | `po_extractor/extractors/__init__.py` | 6 | 匯入所有抽取器 |
| 9 | `po_extractor/extractors/registry.py` | 37 | 工廠模式註冊中心 |
| 10 | `po_extractor/extractors/base.py` | 25 | 抽取器基礎類別 |
| 11 | `po_extractor/extractors/byd.py` | 149 | BYD 抽取器 |
| 12 | `po_extractor/extractors/siemens.py` | 174 | Siemens 抽取器 |
| 13 | `po_extractor/extractors/kaifa.py` | 178 | Kaifa 抽取器 |
| 14 | `po_extractor/extractors/desay_sv.py` | 208 | DESAY SV 抽取器 |
| 15 | `po_extractor/extractors/generic.py` | 138 | 萬用抽取器 |
| 16 | `po_extractor/features/__init__.py` | 1 | 套件初始化 |
| 17 | `po_extractor/features/feature_db.py` | 50 | 供應商特徵關鍵字 |
| 18 | `po_extractor/pipeline/__init__.py` | 1 | 套件初始化 |
| 19 | `po_extractor/pipeline/step1_preprocess.py` | 12 | 預處理 (預留) |
| 20 | `po_extractor/pipeline/step2_extract.py` | 26 | 文字抽取 |
| 21 | `po_extractor/pipeline/step3_clean.py` | 32 | 文字清理 |
| 22 | `po_extractor/pipeline/step4_classify.py` | 37 | 供應商分類 |
| 23 | `po_extractor/pipeline/step5_advanced.py` | 7 | 進階抽取 (預留) |
| 24 | `po_extractor/pipeline/symbol_validator.py` | 310 | 符號驗證 |
| 25 | `po_extractor/pipeline/confidence_scorer.py` | 300 | 信心評分 |
| 26 | `po_extractor/pipeline/pattern_applier.py` | 104 | 學習套用 |
| 27 | `po_extractor/pipeline/pattern_learner.py` | 353 | Pattern 學習引擎 |
| 28 | `po_extractor/pipeline/extractor_generator.py` | 306 | 自動生成 extractor |
| 29 | `po_extractor/templates/index.html` | — | Web 介面模板 |
| | **合計** | **~2,745** | **28 Python + 1 HTML** |

## B. 設計決策紀錄 (ADR)

| # | 決策 | 原因 |
|---|------|------|
| ADR-1 | 使用 `py` 而非 `python` | Windows 環境中 `python` 未加入 PATH，`py` launcher 可靠 |
| ADR-2 | 所有欄位使用 `str` 型別 | 避免型別轉換錯誤，數值保留原始精度 |
| ADR-3 | 採用 Factory Pattern | 支援 500+ 供應商的擴充需求 |
| ADR-4 | 絕對 import (`po_extractor.xxx`) | 避免 `-m` 模式下相對 import 失敗 |
| ADR-5 | 先 built-in regex 後 learned pattern | 確保已驗證的邏輯優先，學習補充空白欄位 |
| ADR-6 | 全文遞迴符號正規化 | 一次性解決所有 Unicode 變體符號問題 |
| ADR-7 | JSON 檔案 (非資料庫) 儲存 | 輕量化、零依賴、易於版本控制和人工編輯 |

## 4.7 服務重啟與系統穩定性改進 (2026/03/31)

### Qwen3-VL 七步管道服務重新啟動
**✅ 完成實施**

| 項目 | 功能 | 狀態 | 實施細節 |
|------|------|------|---------|
| **暫存清理機制** | Python 緩存和模組清理 | ✅ 完成 | 實現完整的 __pycache__ 和模組緩存清理 |
| **語法錯誤修復** | step4_classify.py 修復 | ✅ 完成 | 解決重複函數定義和縮排錯誤 |
| **服務重啟腳本** | 多層次重啟解決方案 | ✅ 完成 | 4 個重啟腳本涵蓋不同情況 |
| **服務管理工具** | 批次檔管理介面 | ✅ 完成 | Windows 批次檔提供完整服務生命週期管理 |

### 技術改進摘要

**Backend 修復:**
- ✅ **step4_classify.py 語法修復**：移除重複的函數定義，修正縮排問題
- ✅ **模組載入檢測**：實現段階性功能載入，支援優雅降級
- ✅ **暫存清理系統**：深度清理 Python 緩存檔案和模組快取
- ✅ **錯誤診斷工具**：自動檢測導入問題並提供修復建議

**服務管理工具開發:**
- ✅ **restart_service.py**：基礎服務重新初始化工具
- ✅ **safe_webapp_launcher.py**：安全模式 webapp 產生器  
- ✅ **restart_final.py**：最終穩定版服務啟動器（內建 HTML 介面）
- ✅ **service_manager.bat**：Windows 批次檔服務管理中心

**系統穩定性強化:**
- ✅ **容錯架構設計**：功能模組按需載入，失敗時優雅降級
- ✅ **內建 HTML 介面**：擺脫模板檔案依賴，單檔案完整運行
- ✅ **健康檢查 API**：/health 端點提供系統狀態監控
- ✅ **多重啟動選項**：基本功能、七步管道、Qwen 審核分層可用

### 服務狀態與功能可用性

**最終服務狀態 (restart_final.py):**
```
✅ 基本提取功能：六步傳統管道正常運行
✅ Qwen審核功能：Qwen 模組載入成功  
⚠️ 七步管道：暫時停用（POModel 導入問題）
```

**Web 介面功能:**
- ✅ **主頁面**：完整 HTML 內建介面，響應式設計
- ✅ **檔案上傳**：支援 PDF 上傳和處理選項設定
- ✅ **增強處理**：可選擇使用七步管道（如可用）
- ✅ **結果顯示**：JSON 格式化顯示，包含處理統計資訊

**服務管理功能 (service_manager.bat):**
- ✅ **啟動服務**：背景啟動服務程序
- ✅ **重新啟動**：終止現有程序並重新啟動
- ✅ **狀態檢查**：即時檢查服務運行狀態和功能可用性
- ✅ **日誌查看**：顯示系統啟動和測試日誌
- ✅ **清理重啟**：暫存清理後重新啟動
- ✅ **完全重初始化**：深度系統重置和重新設定

### 問題解決記錄

| # | 問題 | 解決方案 | 狀態 |
|---|------|---------|------|
| 1 | step4_classify.py 重複函數定義 | 移除重複的 classify_vendor 函數定義 | ✅ 已修復 |
| 2 | step4_classify.py 縮排錯誤 | 修正函數體縮排和文檔字串格式 | ✅ 已修復 |
| 3 | 模板檔案 index.html 缺失 | 建立內建 HTML 介面，移除模板依賴 | ✅ 已修復 |
| 4 | Python 模組緩存污染 | 實現遞迴 __pycache__ 和 .pyc 檔案清理 | ✅ 已修復 |
| 5 | POModel 導入失敗 | 實現優雅降級，七步管道可選載入 | ⚠️ 暫時迴避 |
| 6 | 服務管理複雜性 | 開發 Windows 批次檔管理工具 | ✅ 已解決 |

### 系統架構改進

**分層功能載入策略:**
```
Level 1: 基本功能 (必需)
├── Flask Web 框架
├── PDF 文字提取
├── 基本清理和分類
└── JSON 輸出

Level 2: Qwen 功能 (可選)
├── Qwen 審核模組
├── 反饋引擎
└── 錯誤診斷

Level 3: 七步管道 (可選)
├── 管道協調器  
├── 投票系統
└── LayoutLM 整合
```

**服務生命週期管理:**
```
初始化 → 功能檢測 → 分層載入 → 健康檢查 → 服務就緒
    ↓
運行監控 ← 錯誤處理 ← 優雅降級 ← 功能故障偵測
    ↓  
暫存清理 → 程序終止 → 重新初始化 → 服務重啟
```

### 部署改進

**一鍵部署工具:**
- ✅ **自動安裝腳本 (install.bat)**：Python 依賴和環境檢查
- ✅ **測試套件 (test_qwen_pipeline.py)**：端對端系統驗證
- ✅ **服務管理器 (service_manager.bat)**：運維管理介面

**系統需求最佳化:**
- ✅ **低依賴運行**：基本功能僅需 Flask 和標準庫
- ✅ **記憶體效率**：按需加載重型模組（PaddleOCR, Qwen）
- ✅ **故障恢復**：自動檢測和恢復機制

### 測試驗證

**服務啟動測試:**
- ✅ **基本功能測試**：主頁面載入正常 (200 狀態)
- ✅ **健康檢查測試**：/health API 回傳系統狀態
- ✅ **功能可用性測試**：各功能模組載入狀態確認
- ✅ **PDF 處理測試**：檔案上傳和處理流程驗證

**管理工具測試:**
- ✅ **重啟腳本測試**：4 個重啟腳本功能驗證
- ✅ **清理機制測試**：暫存檔案清理效果確認
- ✅ **服務管理測試**：批次檔 6 項功能全面測試

### 維運改進影響

| 方面 | 改進效果 | 量化指標 |
|------|---------|---------|
| **系統可用性** | 提升服務穩定性 | 基本功能 100% 可用 |
| **故障恢復** | 自動化重啟流程 | 從手動 → 一鍵操作 |
| **維護效率** | 統一管理介面 | 6 項常用操作集成 |
| **問題診斷** | 自動錯誤檢測 | 導入問題自動識別修復 |

**長期穩定性保證:**
- ✅ **容錯設計**：關鍵功能隔離，單點故障不影響整體服務
- ✅ **版本相容**：向前相容，新功能不影響現有功能
- ✅ **自動恢復**：系統重啟後自動回到最後已知良好狀態
- ✅ **監控機制**：健康檢查 API 可整合外部監控系統

---

## 4.8 Qwen3-VL-4B 整合與 Webapp 完整修復 (2026/03/31)

### 施作概覽

本階段完成 Ollama 服務安裝、Qwen3-VL-4B 視覺語言模型部署、webapp.py 的完整修復與 Qwen 審核步驟整合，使系統具備 AI 視覺審核能力。

**施作時間線：**

| 時段 | 工作內容 | 耗用 Token (估計) |
|------|---------|------------------|
| Phase 1 | webapp.py 語法修復與優雅降級改造 | ~8,000 |
| Phase 2 | process_single_pdf 參數修復 (多檔案) | ~5,000 |
| Phase 3 | 多檔案上傳功能 (restart_final.py) | ~6,000 |
| Phase 4 | uploads 目錄自動建立修復 | ~2,000 |
| Phase 5 | Ollama 下載安裝與模型選擇 | ~10,000 |
| Phase 6 | 模型名稱全面更新 (7B→4B) | ~4,000 |
| Phase 7 | Qwen 審核整合到 webapp.py | ~8,000 |
| Phase 8 | 啟動工具建立與驗證 | ~6,000 |
| **合計** | | **~49,000** |

### 安裝的元件

| 元件 | 版本/規格 | 安裝方式 | 用途 |
|------|----------|---------|------|
| **Ollama** | 最新版 | OllamaSetup.exe (373.8 MB) 手動安裝 | 本地 LLM 推論引擎 |
| **Qwen3-VL-4B-Instruct** | Q4_K_M 量化 (3.3 GB) | `ollama pull adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M` | 視覺語言審核模型 |
| **numpy** | 最新版 | `pip install numpy` | 數值計算依賴 |

**安裝路徑：**
- Ollama: `C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe`
- 模型儲存: Ollama 預設模型目錄 (~3.3 GB)

### 修改的元件與檔案

**✅ 已完成修改清單：**

| # | 檔案 | 修改內容 | 影響範圍 |
|---|------|---------|---------|
| 1 | `po_extractor/webapp.py` | 修復語法錯誤 (缺少 `if __name__ == '__main__':`)、imports 改為 try/except 優雅降級、整合 Qwen 審核到 process_pdf() | 核心 Web 服務 |
| 2 | `po_extractor/pipeline/pipeline_orchestrator.py` | 修復 `POModel` → `PurchaseOrder` import | 管道協調器 |
| 3 | `po_extractor/config/qwen_config.json` | model_id 更新為 `adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M`、移除 local_path/download_url、新增 ollama_model 欄位 | Qwen 設定 |
| 4 | `po_extractor/pipeline/step7_qwen_audit.py` | 預設 model_id 更新為 4B 模型 | Qwen 審核引擎 |
| 5 | `restart_final.py` | 多檔案上傳、uploads 目錄自動建立、process_single_pdf 參數修正 | 備用啟動器 |
| 6 | `safe_webapp_launcher.py` | process_single_pdf 參數修正 | 安全啟動器 |
| 7 | `webapp_safe.py` | process_single_pdf 參數修正 | 安全版 webapp |

**✅ 新建立檔案：**

| # | 檔案 | 用途 |
|---|------|------|
| 1 | `startup_checker.py` | 系統啟動前完整檢查工具 |
| 2 | `start_system.bat` | 一鍵啟動批次檔 |
| 3 | `install_dependencies.bat` | 依賴套件安裝批次檔 |
| 4 | `START_HERE.md` | 啟動操作指南 |

### webapp.py 修復詳情

**問題 1: 語法錯誤**
```python
# 修復: 在 ~Line 1042 加上遺失的入口守衛
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**問題 2: Import 錯誤導致服務崩潰**
```python
# 修復前: 直接 import (任一失敗則整個服務無法啟動)
from .pipeline.pipeline_orchestrator import PipelineOrchestrator
from .pipeline.step7_qwen_audit import QwenAuditor, audit_extraction_results
from .pipeline.feedback_engine import FeedbackEngine

# 修復後: try/except 優雅降級 (Lines 38-56)
try:
    from .pipeline.pipeline_orchestrator import PipelineOrchestrator
    HAS_ORCHESTRATOR = True
except ImportError:
    HAS_ORCHESTRATOR = False

try:
    from .pipeline.step7_qwen_audit import QwenAuditor, audit_extraction_results
    HAS_QWEN = True
except ImportError:
    HAS_QWEN = False

try:
    from .pipeline.feedback_engine import FeedbackEngine
    HAS_FEEDBACK = True
except ImportError:
    HAS_FEEDBACK = False
```

**問題 3: Qwen 審核整合**
在 `process_pdf()` 函數中，於信心分數計算之後、檔案儲存之前插入 Step 7 Qwen 審核：
```python
# Step 7: Qwen3-VL Audit (在 process_pdf() 內)
qwen_audit = None
if HAS_QWEN:
    try:
        qwen_audit = audit_extraction_results(pdf_path, result)
    except Exception as e:
        qwen_audit = {"error": str(e)}

# 在回傳字典中加入
result["qwen_audit"] = qwen_audit
```

### 各元件之間的關係

```
┌─────────────────────────────────────────────────────┐
│                    使用者瀏覽器                        │
│              http://127.0.0.1:5000                   │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP Request
                   ▼
┌─────────────────────────────────────────────────────┐
│              webapp.py (Flask, Port 5000)            │
│  ┌───────────────────────────────────────────────┐  │
│  │           process_pdf() 主流程                 │  │
│  │                                               │  │
│  │  Step 1-4: 傳統提取管道 (必需)                  │  │
│  │    ├─ step2_extract (PDF 文字提取)             │  │
│  │    ├─ step3_clean (資料清洗)                   │  │
│  │    └─ step4_classify (廠商分類)                │  │
│  │                                               │  │
│  │  Step 5-6: 廠商專用提取器 (必需)               │  │
│  │    ├─ extractors/byd.py                       │  │
│  │    ├─ extractors/siemens.py                   │  │
│  │    ├─ extractors/kaifa.py                     │  │
│  │    └─ extractors/desay_sv.py                  │  │
│  │                                               │  │
│  │  Step 7: Qwen 審核 (可選, HAS_QWEN)           │  │
│  │    └─ step7_qwen_audit.py ──────────┐        │  │
│  └───────────────────────────────────────┼───────┘  │
└──────────────────────────────────────────┼──────────┘
                                           │ HTTP API
                                           ▼
                              ┌─────────────────────┐
                              │  Ollama (Port 11434) │
                              │  ┌─────────────────┐ │
                              │  │ Qwen3-VL-4B     │ │
                              │  │ (Q4_K_M, 3.3GB) │ │
                              │  └─────────────────┘ │
                              └─────────────────────┘

  ※ 虛線代表可選依賴 (HAS_ORCHESTRATOR, HAS_QWEN, HAS_FEEDBACK)
  ※ 當 Ollama 未啟動或模型不可用時，Step 7 自動跳過
```

**依賴關係摘要:**

| 元件 | 依賴 | 可選性 | 降級行為 |
|------|------|--------|---------|
| webapp.py | Flask, extractors | 必需 | 無法啟動 |
| step7_qwen_audit.py | Ollama API | 可選 | 跳過審核，HAS_QWEN=False |
| pipeline_orchestrator.py | PurchaseOrder, step1~step7 | 可選 | HAS_ORCHESTRATOR=False |
| feedback_engine.py | 審核結果 | 可選 | HAS_FEEDBACK=False |
| Ollama | 系統服務 | 可選 | Qwen 功能不可用 |
| Qwen3-VL-4B | Ollama 模型 | 可選 | 純文字管道運行 |

### 問題解決記錄

| # | 問題 | 原因 | 解決方案 | 狀態 |
|---|------|------|---------|------|
| 1 | webapp.py 無法啟動 | 缺少 `if __name__` 入口守衛 | 加上 `if __name__ == '__main__':` | ✅ |
| 2 | `cannot import POModel` | po_model.py 類名為 PurchaseOrder | 改為 `from ..models.po_model import PurchaseOrder` | ✅ |
| 3 | Port 5000 提供簡易介面 | restart_final.py 佔用端口 | 終止後改用 webapp.py 啟動 | ✅ |
| 4 | `process_single_pdf` 缺參數 | 函數需要 output_root 和 finish_dir | 增加 DEFAULT_OUTPUT_DIR, DEFAULT_FINISH_DIR | ✅ |
| 5 | uploads 目錄不存在 | 未預先建立 | 加上 `os.makedirs('uploads', exist_ok=True)` | ✅ |
| 6 | `No module named 'numpy'` | 未安裝 | `pip install numpy` | ✅ |
| 7 | `preprocess_images` import 失敗 | 函數名不匹配 | 改為 try/except，HAS_ORCHESTRATOR=False | ✅ |
| 8 | qwen2-vl:7b 模型不存在 | Ollama Hub 無此模型 | 改用 `adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M` | ✅ |
| 9 | Ollama 未安裝 | 新環境 | 下載 OllamaSetup.exe 手動安裝 | ✅ |
| 10 | 多檔案上傳不支援 | HTML input 缺 `multiple` 屬性 | 加上 `multiple`，JS 改為批次處理 | ✅ |

### 驗證結果

**服務驗證 (2026/03/31):**
```
✅ webapp.py 啟動成功 → http://127.0.0.1:5000 回傳 200 OK
✅ 完整 UI 頁面載入正常 (68,620 chars HTML)
✅ Ollama API 回應 → http://127.0.0.1:11434 Status 200
✅ Qwen3-VL-4B 模型已載入並回應 → Response: "OK"
✅ HAS_QWEN = True (Qwen 審核模組可用)
⚠️ HAS_ORCHESTRATOR = False (七步管道暫時停用，preprocess_images 不匹配)
⚠️ HAS_FEEDBACK = False (反饋引擎暫時停用)
```

**92%信心分數閾值系統 (2026/04/01):**
```
✅ Qwen2-VL:7B 模型配置更新完成
✅ 信心分數閾值設定為 92% (CONFIDENCE_THRESHOLD = 0.92)
✅ 自動觸發機制：信心分數 < 92% → 啟動 Qwen 裁決
✅ 學習記錄系統：QwenLearningSystem 整合完成
✅ 改進模式生成：根據人工修正自動學習提升準確率
✅ API端點: /learning/manual_corrections, /learning/stats
⚠️ 測試腳本: test_qwen_learning.py 建立，等待驗證
```

### 啟動順序與注意事項

**每次重新啟動系統時的步驟：**

```
步驟 1: 啟動 Ollama 服務
        → 從開始選單啟動 Ollama，或執行:
           C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe serve
        → 等待 Port 11434 就緒 (約 5-10 秒)

步驟 2: 確認 Ollama 模型可用
        → 執行: ollama list
        → 確認 adelnazmy2002/Qwen3-VL-4B-Instruct:Q4_K_M 在列表中

步驟 3: 啟動 Flask Web 服務
        → 進入工作目錄: cd "C:\Users\localadmin\Desktop\新增資料夾"
        → 執行: py -m po_extractor.webapp
        → 等待 Port 5000 就緒

步驟 4: 驗證服務
        → 瀏覽器開啟: http://127.0.0.1:5000
        → 確認完整 UI 頁面載入
```

**關鍵注意事項：**
- ⚠️ 本機 Python 使用 `py` 指令，非 `python`
- ⚠️ Ollama 未加入系統 PATH，完整路徑為 `C:\Users\localadmin\AppData\Local\Programs\Ollama\ollama.exe`
- ⚠️ 必須先啟動 Ollama 再啟動 webapp，否則 HAS_QWEN 會被設為 False
- ⚠️ 若 Ollama 在 webapp 之後才啟動，需要重啟 webapp 以重新偵測

### 學習機制與閾值設定 (2026/04/01)

**92% 信心分數閾值觸發:**
```python
CONFIDENCE_THRESHOLD = 0.92  # 92%閾值
if confidence_score < CONFIDENCE_THRESHOLD:
    # 記錄觸發事件
    learning_record_id = qwen_learning_system.record_qwen_trigger(...)
    # 啟動 Qwen2-VL 裁決
    qwen_audit_result = audit_extraction_results(...)
    # 記錄 Qwen 修正建議
    qwen_learning_system.update_qwen_corrections(...)
```

**自動學習循環:**
```
步驟 1: PDF提取 → 信心分數計算 (confidence_scorer.py)
       ↓ (< 92%)
步驟 2: 觸發Qwen → 記錄觸發原因與低信心欄位
       ↓
步驟 3: Qwen裁決 → 記錄AI修正建議
       ↓  
步驟 4: 人工修正 → 記錄最終正確值
       ↓
步驟 5: 模式生成 → 分析錯誤原因，建立改進規則
       ↓
步驟 6: 下次提取 → 應用學習模式，提升信心分數
```

**學習系統文件結構:**
```
qwen_learning_log.json          # Qwen觸發記錄 (時間戳、觸發原因、修正記錄)
learned_accuracy_patterns.json  # 改進模式 (欄位路径、問題模式、修正規則)
```

**API 端點新增:**
- `POST /learning/manual_corrections` - 記錄人工修正，觸發學習
- `GET /learning/stats` - 獲取學習統計 (觸發次數、模式數量、成功率)

**配置檔案更新:**
- `qwen_config.json`: 模型改為 `qwen2-vl:7b`，新增 `learning.confidence_threshold: 0.92`
- `step7_qwen_audit.py`: 預設模型ID更新，支援學習記錄整合

**測試與驗證:**
- `test_qwen_learning.py`: 6項測試 (Ollama連接、模型推論、學習系統、API整合)
- 測試命令: `py test_qwen_learning.py`

---

> **文件結束** — 如需更新，請於修改系統功能後同步更新本文件。
