# ✈️ WoA 航線利潤與 XP 分析器 (桌面版)

這是一個專為 *World of Airports (WoA)* 玩家設計的離線桌面應用程式，旨在幫助玩家分析各機型在不同航線上的獲利能力、經驗值 (XP) 以及投資報酬率 (ROI)。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-1.0.1-orange.svg)

## ✨ 核心功能

*   **🌐 航線探索**：依據選定的機型，自動計算所有可用航線的淨利潤與 XP。
*   **✈️ 選購指南**：針對特定航線，橫向比較不同機型的获利表現，找出最賺錢的飛機。
*   **📈 ROI 計算**：結合飛機購置成本，自動計算投資報酬率 (ROI)，助您精準理財。
*   **⭐ 常用機型管理**：支援最愛機型設定，並提供快速篩選功能，專注於您擁有的飛機。
*   **📊 互動式排序**：所有數據表格皆支援點擊標題排序（利潤、距離、ROI 等）。
*   **🔄 自動更新**：程式啟動時自動檢查新版本，確保您始終擁有最新功能。

## 🚀 如何開始

### 1. 下載程式
前往 [Releases](https://github.com/F1026120/WOA-Profit-Analyzer/releases) 頁面下載最新的 `WOA_Profit_Analyzer.exe`。

### 2. 資料準備
*   將您的航線資料 (CSV 格式) 放入程式同目錄下的 `CSV` 資料夾中。
*   程式啟動時會自動偵測並匯入該資料夾內的所有 CSV 檔案。

### 3. 最愛設定
在「常用機型」分頁中，雙擊機型即可將其加入最愛，之後可在分析頁面中快速過濾。

## 📁 CSV 資料格式說明

程式支援 WoA 社群常用的 CSV 導出格式，請確保 CSV 包含以下關鍵欄位：
*   `From`, `To` (出發與目的地)
*   `Distance` (距離)
*   `Net Round Trip Profit` (淨利潤)
*   `Capacity (E/B/F)` (座位配置)

## 🛠️ 開發與建置

如果您想從原始碼執行或自行打包：

1. 安裝依賴項目：
   ```bash
   pip install pandas
   ```
2. 執行程式：
   ```bash
   python WOA_plane.py
   ```
3. 打包為 EXE：
   ```bash
   pyinstaller --onefile --noconsole --name "WOA_Profit_Analyzer" WOA_plane.py
   ```

## 📝 授權
本專案採用 MIT 授權。