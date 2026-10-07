# ✈️ WoA 航線利潤與 XP 分析器 (桌面版)

這是一個專為 *World of Airports (WoA)* 玩家設計的離線桌面應用程式，旨在幫助玩家分析各機型在不同航線上的獲利能力、經驗值 (XP) 以及投資報酬率 (ROI)。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-1.2.3-orange.svg)

## ✨ 核心功能

*   **🌐 航線探索**：依據選定的機型，自動計算所有可用航線的淨利潤與 XP。
*   **✈️ 選購指南**：針對特定航線，橫向比較不同機型的獲利表現，找出最賺錢的飛機。
*   **👑 玩家分站**：指定玩家機場為目的地進行反向查詢，找出從哪個機場飛過來最賺錢。
*   **📈 ROI 計算**：結合飛機購置成本，自動計算投資報酬率 (ROI)，助您精準理財。
*   **⭐ 常用機型管理**：支援最愛機型設定，提供雙擊切換與快速篩選功能。
*   **📊 互動式排序**：表格標題支援點擊排序（利潤、距離、ROI、XP 等）。
*   **🔔 新版本提醒與手動下載**：啟動時在背景檢查 GitHub 最新版本，若有更新將在介面顯示顯眼的下載按鈕，由玩家主動點擊下載，不再強迫自動更新。

## 📋 更新日誌 (Changelog)

### v1.2.3
*   🚀 **更新機制調整 (非強制自動更新)**：
    *   取消啟動時彈出視窗強迫自動更新，改為在背景靜默檢查。
    *   當偵測到 GitHub 有新版本時，主介面頂端會顯示顯眼的橘色「🔔 發現新版本 (點此下載)」按鈕。
    *   點擊按鈕後於背景線程下載新版 EXE 並顯示進度，下載完成後給予提示，兼顧流暢度與版本自主權。

### v1.2.2
*   ✨ **新增玩家機場**：
    *   新增玩家可玩機場 **ZRH** (蘇黎世機場)。

### v1.2.0
*   🐛 **修復 CSV 讀取失敗問題**：
    *   支援帶有小數點的浮點數格式利潤轉換（如 `3239.63...` 自動四捨五入為整數），解決部分機型 CSV（如 `A21N.csv`）讀取失敗的問題。
    *   新增 `Destination` 欄位對應至目的地城市名稱。
    *   自動清理座位配置格式（去除 `.0` 尾數，如 `244.0` 格式化為 `244`）。
    *   強化試算表錯誤值過濾（如 `#Underload!`, `#DIV/0!`, `#VALUE!` 等）。

---

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
*   `Destination` / `Airport` (目的地城市名稱)
*   `Distance` (距離)
*   `Profit` / `Net Round Trip Profit` (淨利潤)
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
   python -m PyInstaller --clean --noconfirm WOA_Profit_Analyzer.spec
   ```

## 📝 授權
本專案採用 MIT 授權。