import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import re
import io
import os
import sys
import glob
import urllib.request
import subprocess
import time

# ==========================================
# 0. 自動更新配置
# ==========================================
CURRENT_VERSION = "1.1.0"
VERSION_URL = "https://raw.githubusercontent.com/F1026120/WOA-Profit-Analyzer/refs/heads/main/version.txt"
EXE_URL = f"https://github.com/F1026120/WOA-Profit-Analyzer/releases/download/v{CURRENT_VERSION}/WOA_Profit_Analyzer.exe"

# ==========================================
# 1. 預載資料與常數
# ==========================================
PLAYABLE_AIRPORTS = {
    'INN', 'BRI', 'PRG', 'IAD', 'NGO', 'SAN', 'MCT', 'LEJ', 
    'SXM', 'LHR', 'SYD', 'BKK', 'MSY', 'GRU', 'SCL', 'CNN', 'HKG'
}

INITIAL_DATA = [
    {'hub': 'PRG', 'dest': 'HND', 'aircraft': 'A388', 'dist': 4908, 'profit': 9053, 'e': '600', 'b': '10', 'f': '30'},
    {'hub': 'PRG', 'dest': 'CKG', 'aircraft': 'A388', 'dist': 4145, 'profit': 8856, 'e': '598', 'b': '30', 'f': '20'},
    {'hub': 'PRG', 'dest': 'BKK', 'aircraft': 'B748', 'dist': 4639, 'profit': 8673, 'e': '424', 'b': '10', 'f': '20'},
    {'hub': 'BRI', 'dest': 'HND', 'aircraft': 'B77W', 'dist': 5233, 'profit': 7129, 'e': '406', 'b': '0', 'f': '20'},
    {'hub': 'BRI', 'dest': 'HND', 'aircraft': 'A35K', 'dist': 5233, 'profit': 6132, 'e': '336', 'b': '0', 'f': '20'}
]

INITIAL_DEST_INFO = {
    'HND': {'city': 'Tokyo Haneda', 'country': 'Japan'},
    'CKG': {'city': 'Chongqing', 'country': 'China'},
    'BKK': {'city': 'Bangkok', 'country': 'Thailand'},
    'PRG': {'city': '布拉格', 'country': '捷克'},
    'BRI': {'city': '巴里', 'country': '義大利'}
}

INITIAL_PRICE_INFO = {
    'A388': 380000000,
    'B748': 350000000,
    'B77W': 300000000,
    'A35K': 320000000
}

# ==========================================
# 2. 輔助函數
# ==========================================
def clean_profit_value(val):
    if pd.isna(val):
        return None
    val_str = str(val)
    if '#DIV/0!' in val_str or '#VALUE!' in val_str:
        return None
    cleaned = re.sub(r'[^0-9.-]', '', val_str)
    try:
        return int(cleaned)
    except ValueError:
        return None

# ==========================================
# 3. 桌面應用程式主體 (Tkinter)
# ==========================================
class ProfitAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"✈️ WoA 航線利潤與 XP 分析器 (v{CURRENT_VERSION})")
        self.root.geometry("1150x780")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        style.configure("Treeview", rowheight=25)
        
        # 資料庫
        self.db = pd.DataFrame(INITIAL_DATA)
        self.dest_info = INITIAL_DEST_INFO.copy()
        self.xp_dict = {} # 存放機型對應的 XP 資料
        self.price_dict = INITIAL_PRICE_INFO.copy() # 存放機型對應的 Unit Price
        self.favorites = set() # 存放最愛的機型代碼
        self.fav_file = "favorites.txt"
        self.load_favorites()
        
        self.create_widgets()
        self.update_filters()
        
        self.apply_filters()
        self.apply_tab2_filters()

        # 使用 after 延遲執行自動載入，讓主視窗先畫出來，進度視窗才能正確顯示在上方
        self.root.after(200, self.auto_load_csv_folder)
        
        # 啟動檢查更新 (延遲 1 秒執行以免卡住啟動)
        self.root.after(1000, self.check_for_updates)

    def create_widgets(self):
        # --- 頂部控制區 ---
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        
        upload_btn = tk.Button(top_frame, text="📂 手動上傳 CSV", bg="#2563eb", fg="white", font=("Helvetica", 11, "bold"), command=self.upload_csv)
        upload_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(top_frame, text="🗑️ 清空資料庫", bg="#dc2626", fg="white", font=("Helvetica", 11, "bold"), command=self.clear_db)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.lbl_record_count = tk.Label(top_frame, text=f"航線: {len(self.db)} 筆 | 機型資料: {len(self.price_dict)} 筆", fg="gray")
        self.lbl_record_count.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(top_frame, text=f"Version: {CURRENT_VERSION}", fg="#94a3b8", font=("Helvetica", 9)).pack(side=tk.RIGHT, padx=5)

        # --- 分頁管理區 ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab4 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="🌐 航線探索 (依機型找航線)")
        self.notebook.add(self.tab2, text="✈️ 選購指南 (依航線比機型)")
        self.notebook.add(self.tab4, text="👑 玩家分站 (依目的地找航線)")
        self.notebook.add(self.tab3, text="⭐ 常用機型 (管理最愛)")

        self.create_tab1()
        self.create_tab2()
        self.create_tab4()
        self.create_tab3()

    def create_tab1(self):
        # ================= Tab 1: 航線探索 =================
        filter_frame = tk.LabelFrame(self.tab1, text="篩選條件", padx=10, pady=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(filter_frame, text="🌍 出發機場:").grid(row=0, column=0, padx=5, pady=5)
        self.hub_var = tk.StringVar()
        self.hub_cb = ttk.Combobox(filter_frame, textvariable=self.hub_var, state="readonly", width=12)
        self.hub_cb.grid(row=0, column=1, padx=5, pady=5)
        self.hub_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        tk.Label(filter_frame, text="✈️ 機型:").grid(row=0, column=2, padx=5, pady=5)
        self.aircraft_var = tk.StringVar()
        self.aircraft_cb = ttk.Combobox(filter_frame, textvariable=self.aircraft_var, state="readonly", width=12)
        self.aircraft_cb.grid(row=0, column=3, padx=5, pady=5)
        self.aircraft_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())
        
        tk.Label(filter_frame, text="🔍 搜尋:").grid(row=0, column=4, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda n, i, m: self.apply_filters())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=15)
        search_entry.grid(row=0, column=5, padx=5, pady=5)
        
        self.tab1_playable_var = tk.BooleanVar(value=False)
        self.tab1_playable_cb = ttk.Checkbutton(filter_frame, text="👑 玩家機場", variable=self.tab1_playable_var, command=self.apply_filters)
        self.tab1_playable_cb.grid(row=0, column=6, padx=5, pady=5)
        
        self.tab1_fav_only_var = tk.BooleanVar(value=False)
        self.tab1_fav_only_cb = ttk.Checkbutton(filter_frame, text="⭐ 只看常用機型", variable=self.tab1_fav_only_var, command=self.update_filters)
        self.tab1_fav_only_cb.grid(row=0, column=7, padx=5, pady=5)

        stats_frame = tk.Frame(self.tab1, padx=10, pady=5)
        stats_frame.pack(fill=tk.X)
        
        self.lbl_top_route = tk.Label(stats_frame, text="🏆 最高利潤: 無", font=("Helvetica", 14, "bold"), fg="#1e40af")
        self.lbl_top_route.pack(side=tk.LEFT, padx=10)
        
        self.lbl_top_profit = tk.Label(stats_frame, text="💰 淨利: $0", font=("Helvetica", 14, "bold"), fg="#059669")
        self.lbl_top_profit.pack(side=tk.LEFT, padx=10)
        
        self.lbl_top_seat = tk.Label(stats_frame, text="💺 座位: -/-/-", font=("Helvetica", 14, "bold"), fg="#b45309")
        self.lbl_top_seat.pack(side=tk.LEFT, padx=10)
        
        self.lbl_top_xp = tk.Label(stats_frame, text="✨ T10 XP: -", font=("Helvetica", 14, "bold"), fg="#7c3aed")
        self.lbl_top_xp.pack(side=tk.LEFT, padx=10)

        self.lbl_top_roi = tk.Label(stats_frame, text="📈 ROI: -", font=("Helvetica", 14, "bold"), fg="#0891b2")
        self.lbl_top_roi.pack(side=tk.LEFT, padx=10)

        table_frame = tk.Frame(self.tab1, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("rank", "dest", "dist", "seat", "xp", "profit", "roi")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        tab1_headings = {
            "rank": "排名", 
            "dest": "目的地 (城市, 國家)", 
            "dist": "距離(NM)", 
            "seat": "推薦座位(E/B/F)", 
            "xp": "Lv.10 XP", 
            "profit": "淨利潤 ($)", 
            "roi": "報酬率 (ROI)"
        }
        
        for col, text in tab1_headings.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(self.tree, c, False))
            
        self.tree.column("rank", width=50, anchor=tk.CENTER)
        self.tree.column("dest", width=300, anchor=tk.W)
        self.tree.column("dist", width=80, anchor=tk.CENTER)
        self.tree.column("seat", width=130, anchor=tk.CENTER)
        self.tree.column("xp", width=80, anchor=tk.CENTER)
        self.tree.column("profit", width=120, anchor=tk.E)
        self.tree.column("roi", width=120, anchor=tk.E)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_tab2(self):
        # ================= Tab 2: 選購指南 =================
        filter_frame = tk.LabelFrame(self.tab2, text="指定航線比較", padx=10, pady=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(filter_frame, text="🌍 出發機場:").grid(row=0, column=0, padx=5, pady=5)
        self.tab2_hub_var = tk.StringVar()
        self.tab2_hub_cb = ttk.Combobox(filter_frame, textvariable=self.tab2_hub_var, state="readonly", width=12)
        self.tab2_hub_cb.grid(row=0, column=1, padx=5, pady=5)
        self.tab2_hub_cb.bind("<<ComboboxSelected>>", self.on_tab2_hub_change)
        
        self.tab2_playable_var = tk.BooleanVar(value=False)
        self.tab2_playable_cb = ttk.Checkbutton(filter_frame, text="👑 玩家機場", variable=self.tab2_playable_var, command=self.on_tab2_hub_change)
        self.tab2_playable_cb.grid(row=0, column=2, padx=5, pady=5)
        
        self.tab2_fav_only_var = tk.BooleanVar(value=False)
        self.tab2_fav_only_cb = ttk.Checkbutton(filter_frame, text="⭐ 只看常用機型", variable=self.tab2_fav_only_var, command=self.apply_tab2_filters)
        self.tab2_fav_only_cb.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(filter_frame, text="📍 目的地:").grid(row=0, column=3, padx=5, pady=5)
        self.tab2_dest_var = tk.StringVar()
        self.tab2_dest_cb = ttk.Combobox(filter_frame, textvariable=self.tab2_dest_var, state="readonly", width=30)
        self.tab2_dest_cb.grid(row=0, column=4, padx=5, pady=5)
        self.tab2_dest_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_tab2_filters())

        stats_frame = tk.Frame(self.tab2, padx=10, pady=5)
        stats_frame.pack(fill=tk.X)
        
        self.lbl_tab2_top = tk.Label(stats_frame, text="🏆 最賺錢機型: 無", font=("Helvetica", 14, "bold"), fg="#1e40af")
        self.lbl_tab2_top.pack(side=tk.LEFT, padx=10)

        table_frame = tk.Frame(self.tab2, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("rank", "aircraft", "dist", "seat", "xp", "profit", "roi")
        self.tree2 = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        tab2_headings = {
            "rank": "排名", 
            "aircraft": "機型 (Aircraft)", 
            "dist": "距離(NM)", 
            "seat": "推薦座位(E/B/F)", 
            "xp": "Lv.10 XP", 
            "profit": "淨利潤 ($)", 
            "roi": "報酬率 (ROI)"
        }
        
        for col, text in tab2_headings.items():
            self.tree2.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(self.tree2, c, False))
            
        self.tree2.column("rank", width=50, anchor=tk.CENTER)
        self.tree2.column("aircraft", width=180, anchor=tk.W)
        self.tree2.column("dist", width=80, anchor=tk.CENTER)
        self.tree2.column("seat", width=120, anchor=tk.CENTER)
        self.tree2.column("xp", width=80, anchor=tk.CENTER)
        self.tree2.column("profit", width=120, anchor=tk.E)
        self.tree2.column("roi", width=120, anchor=tk.E)
        
        scrollbar2 = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree2.yview)
        self.tree2.configure(yscroll=scrollbar2.set)
        self.tree2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

    def create_tab4(self):
        # ================= Tab 4: 玩家分站 =================
        filter_frame = tk.LabelFrame(self.tab4, text="篩選條件", padx=10, pady=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(filter_frame, text="📍 玩家機場 (目的地):").grid(row=0, column=0, padx=5, pady=5)
        self.tab4_dest_var = tk.StringVar()
        self.tab4_dest_cb = ttk.Combobox(filter_frame, textvariable=self.tab4_dest_var, state="readonly", width=15)
        self.tab4_dest_cb.grid(row=0, column=1, padx=5, pady=5)
        self.tab4_dest_cb.bind("<<ComboboxSelected>>", lambda e: self.apply_tab4_filters())
        
        self.tab4_fav_only_var = tk.BooleanVar(value=False)
        self.tab4_fav_only_cb = ttk.Checkbutton(filter_frame, text="⭐ 只看常用機型", variable=self.tab4_fav_only_var, command=self.apply_tab4_filters)
        self.tab4_fav_only_cb.grid(row=0, column=2, padx=20, pady=5)

        stats_frame = tk.Frame(self.tab4, padx=10, pady=5)
        stats_frame.pack(fill=tk.X)
        
        self.lbl_tab4_top = tk.Label(stats_frame, text="🏆 最佳航線: 無", font=("Helvetica", 14, "bold"), fg="#1e40af")
        self.lbl_tab4_top.pack(side=tk.LEFT, padx=10)

        table_frame = tk.Frame(self.tab4, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("rank", "hub", "aircraft", "dist", "seat", "xp", "profit", "roi")
        self.tree4 = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        tab4_headings = {
            "rank": "排名", 
            "hub": "出發地 (Hub)",
            "aircraft": "機型 (Aircraft)", 
            "dist": "距離(NM)", 
            "seat": "推薦座位(E/B/F)", 
            "xp": "Lv.10 XP", 
            "profit": "淨利潤 ($)", 
            "roi": "報酬率 (ROI)"
        }
        
        for col, text in tab4_headings.items():
            self.tree4.heading(col, text=text, command=lambda c=col: self.treeview_sort_column(self.tree4, c, False))
            
        self.tree4.column("rank", width=50, anchor=tk.CENTER)
        self.tree4.column("hub", width=120, anchor=tk.CENTER)
        self.tree4.column("aircraft", width=150, anchor=tk.W)
        self.tree4.column("dist", width=80, anchor=tk.CENTER)
        self.tree4.column("seat", width=120, anchor=tk.CENTER)
        self.tree4.column("xp", width=80, anchor=tk.CENTER)
        self.tree4.column("profit", width=120, anchor=tk.E)
        self.tree4.column("roi", width=120, anchor=tk.E)
        
        scrollbar4 = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree4.yview)
        self.tree4.configure(yscroll=scrollbar4.set)
        self.tree4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar4.pack(side=tk.RIGHT, fill=tk.Y)

    def create_tab3(self):
        # ================= Tab 3: 常用機型管理 =================
        main_frame = tk.Frame(self.tab3, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(main_frame, text="💡 在此管理您常用的機型，設定後可在「航線探索」中快速篩選。", fg="gray").pack(pady=(0, 2))
        tk.Label(main_frame, text="✨ 提示：您可以「雙擊」表格中的機型來快速切換最愛狀態。", fg="#0891b2", font=("Helvetica", 10, "italic")).pack(pady=(0, 10))
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="⭐ 切換最愛狀態", command=self.toggle_favorite, bg="#f59e0b", fg="white", font=("Helvetica", 11, "bold")).pack(side=tk.LEFT, padx=5)
        
        table_frame = tk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.fav_tree = ttk.Treeview(table_frame, columns=("code", "status"), show="headings", height=15)
        self.fav_tree.heading("code", text="機型代碼", command=lambda: self.treeview_sort_column(self.fav_tree, "code", False))
        self.fav_tree.heading("status", text="狀態", command=lambda: self.treeview_sort_column(self.fav_tree, "status", False))
        
        self.fav_tree.column("code", width=200, anchor=tk.W)
        self.fav_tree.column("status", width=150, anchor=tk.CENTER)
        
        # 綁定雙擊事件
        self.fav_tree.bind("<Double-1>", lambda e: self.toggle_favorite())
        
        fav_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.fav_tree.yview)
        self.fav_tree.configure(yscroll=fav_scroll.set)
        self.fav_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_fav_table()

    def update_fav_table(self):
        """更新常用機型管理表格"""
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)
            
        if self.db.empty: return
        
        all_acs = sorted(self.db['aircraft'].unique().tolist())
        for ac in all_acs:
            status = "★ 常用" if ac in self.favorites else "☆ -"
            self.fav_tree.insert("", tk.END, values=(ac, status))

    def toggle_favorite(self):
        """切換選中機型的最愛狀態"""
        selected = self.fav_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請先從表格中選擇一個機型")
            return
            
        for item in selected:
            ac_code = self.fav_tree.item(item, "values")[0]
            if ac_code in self.favorites:
                self.favorites.remove(ac_code)
            else:
                self.favorites.add(ac_code)
        
        self.update_fav_table()
        self.update_filters()
        self.save_favorites() # 儲存到檔案

    def load_favorites(self):
        """從檔案讀取最愛機型"""
        if os.path.exists(self.fav_file):
            try:
                with open(self.fav_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    self.favorites = {line.strip() for line in lines if line.strip()}
            except Exception as e:
                print(f"載入最愛機型失敗: {e}")

    def save_favorites(self):
        """將最愛機型儲存到檔案"""
        try:
            with open(self.fav_file, "w", encoding="utf-8") as f:
                for ac in sorted(list(self.favorites)):
                    f.write(f"{ac}\n")
        except Exception as e:
            print(f"儲存最愛機型失敗: {e}")

    def auto_load_csv_folder(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        csv_folder = os.path.join(base_path, "CSV")
        if os.path.exists(csv_folder) and os.path.isdir(csv_folder):
            csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
            if csv_files:
                self.load_csv_files(csv_files, silent=True)

    def upload_csv(self):
        file_paths = filedialog.askopenfilenames(title="選擇 CSV 檔案", filetypes=[("CSV files", "*.csv")])
        if file_paths:
            self.load_csv_files(file_paths, silent=False)
            
    def load_csv_files(self, file_paths, silent=False):
        if not file_paths: return
            
        total_files = len(file_paths)
        new_records = []
        
        # --- 建立動態進度條視窗 ---
        prog_win = tk.Toplevel(self.root)
        prog_win.title("讀取進度")
        prog_win.geometry("400x150")
        prog_win.resizable(False, False)
        prog_win.transient(self.root)  # 將其附著於主視窗
        prog_win.grab_set()            # 鎖定主視窗，防止載入時被點擊

        # 讓進度視窗置中顯示
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        prog_win.geometry(f"+{x}+{y}")

        tk.Label(prog_win, text="正在匯入資料庫...", font=("Helvetica", 12, "bold")).pack(pady=10)
        lbl_status = tk.Label(prog_win, text="準備讀取...", font=("Helvetica", 10), fg="#4b5563")
        lbl_status.pack(pady=5)
        
        progress = ttk.Progressbar(prog_win, orient=tk.HORIZONTAL, length=320, mode='determinate', maximum=total_files)
        progress.pack(pady=10)
        # -----------------------------

        try:
            for idx, path in enumerate(file_paths):
                filename = os.path.basename(path)
                # 更新進度視窗的文字與進度條
                lbl_status.config(text=f"({idx+1}/{total_files}) 正在解析: {filename}")
                progress['value'] = idx
                prog_win.update()  # 強制更新視窗畫面

                try:
                    try:
                        with open(path, 'r', encoding='utf-8-sig') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(path, 'r', encoding='cp1252') as f:
                            content = f.read()
                            
                    lines = content.split('\n')
                    if len(lines) < 2: continue
                        
                    aircraft_code = "預設機型"
                    skip_rows = 0
                    
                    if "Route Information" in lines[0]:
                        aircraft_code = lines[0].split(',')[0].strip()
                        skip_rows = 1
                    elif "Capacity" in lines[0] or "Basic" in lines[0]:
                        skip_rows = 1
                        
                    df_csv = pd.read_csv(io.StringIO(content), skiprows=skip_rows)
                    df_csv.columns = [str(c).replace(' ', '').replace('\n', '').lower() for c in df_csv.columns]
                    
                    # ==== 檢查這是不是一份包含飛機資訊的資料表 (找 XP 與 價格) ====
                    col_code_xp = next((c for c in df_csv.columns if 'icaocode' in c or '機型代碼' in c), None)
                    col_xp_val = next((c for c in df_csv.columns if 'lv.10' in c or 'xp' in c), None)
                    col_price_val = next((c for c in df_csv.columns if 'unitprice' in c or '飛機的價格' in c), None)
                    
                    if col_code_xp and (col_xp_val or col_price_val):
                        for _, row in df_csv.iterrows():
                            ac_code = str(row[col_code_xp]).strip()
                            # 儲存 XP
                            if col_xp_val:
                                try:
                                    self.xp_dict[ac_code] = int(float(row[col_xp_val]))
                                except:
                                    pass
                            # 儲存 飛機價格 Unit Price
                            if col_price_val:
                                price_str = str(row[col_price_val])
                                price_cleaned = re.sub(r'[^0-9]', '', price_str)
                                if price_cleaned:
                                    self.price_dict[ac_code] = int(price_cleaned)
                        continue # 處理完後跳過，不當作航線處理
                    
                    # ==== 檢查這是不是一般的航線利潤表 ====
                    col_map = {}
                    for col in df_csv.columns:
                        if col == 'from': col_map['hub'] = col
                        elif col == 'to': col_map['dest'] = col
                        elif col == 'airport': col_map['city'] = col
                        elif col == 'country': col_map['country'] = col
                        elif col in ['distance', 'dist']: col_map['dist'] = col
                        elif col in ['e', 'economy']: col_map['e'] = col
                        elif col in ['b', 'business']: col_map['b'] = col
                        elif col in ['f', 'first']: col_map['f'] = col
                        elif 'adjustednetroundtripprofit' in col: col_map['profit'] = col
                        elif 'netroundtripprofit' in col and 'profit' not in col_map: col_map['profit'] = col
                        elif 'profit' in col and 'profit' not in col_map: col_map['profit'] = col

                    if 'hub' not in col_map or 'dest' not in col_map or 'profit' not in col_map:
                        if not silent: messagebox.showwarning("警告", f"檔案缺少必要欄位: {filename}")
                        continue
                        
                    for _, row in df_csv.iterrows():
                        hub = str(row[col_map['hub']]).strip()
                        dest = str(row[col_map['dest']]).strip()
                        if not hub or not dest or pd.isna(row[col_map['hub']]): continue
                            
                        profit = clean_profit_value(row[col_map['profit']])
                        if profit is None: continue

                        if 'city' in col_map and 'country' in col_map:
                            self.dest_info[dest] = {
                                'city': str(row[col_map['city']]).strip(),
                                'country': str(row[col_map['country']]).strip()
                            }
                            
                        dist = row[col_map['dist']] if 'dist' in col_map else 0
                        dist = int(re.sub(r'[^0-9]', '', str(dist))) if pd.notna(dist) else 0
                        
                        e_seats = str(row[col_map['e']]).strip() if 'e' in col_map and pd.notna(row[col_map['e']]) else ''
                        b_seats = str(row[col_map['b']]).strip() if 'b' in col_map and pd.notna(row[col_map['b']]) else ''
                        f_seats = str(row[col_map['f']]).strip() if 'f' in col_map and pd.notna(row[col_map['f']]) else ''

                        new_records.append({
                            'hub': hub, 'dest': dest, 'aircraft': aircraft_code,
                            'dist': dist, 'profit': profit,
                            'e': e_seats, 'b': b_seats, 'f': f_seats
                        })
                except Exception as e:
                    if not silent: messagebox.showerror("錯誤", f"讀取 {filename} 發生錯誤:\n{e}")

        finally:
            # 確保檔案迴圈結束後，進度條跑滿並關閉視窗
            progress['value'] = total_files
            prog_win.update()
            prog_win.destroy()

        if new_records:
            df_new = pd.DataFrame(new_records)
            self.db = pd.concat([self.db, df_new], ignore_index=True)
            
        self.update_filters()
        self.apply_filters()
        self.apply_tab2_filters()
        self.lbl_record_count.config(text=f"航線: {len(self.db)} 筆 | 機型資料: {len(self.price_dict)} 筆")
        
        if not silent and (new_records or len(self.xp_dict) > 0 or len(self.price_dict) > 0):
            messagebox.showinfo("成功", "資料成功匯入並更新完畢！")

    def clear_db(self):
        if messagebox.askyesno("確認", "確定要清空所有資料嗎？"):
            self.db = pd.DataFrame(columns=['hub', 'dest', 'aircraft', 'dist', 'profit', 'e', 'b', 'f'])
            self.xp_dict = {}
            self.price_dict = {}
            self.update_filters()
            self.apply_filters()
            self.apply_tab2_filters()
            self.lbl_record_count.config(text="航線: 0 筆 | 機型資料: 0 筆")

    def update_filters(self):
        if self.db.empty:
            self.hub_cb['values'] = []
            self.aircraft_cb['values'] = []
            self.hub_var.set('')
            self.aircraft_var.set('')
            
            self.tab2_hub_cb['values'] = []
            self.tab2_hub_var.set('')
            self.on_tab2_hub_change()
            return
            
        hubs = sorted(self.db['hub'].unique().tolist())
        aircrafts = sorted(self.db['aircraft'].unique().tolist())
        
        # 處理常用機型過濾
        if self.tab1_fav_only_var.get():
            display_acs = [ac for ac in aircrafts if ac in self.favorites]
            # 如果勾選了但沒半個最愛，還是顯示全部以免空掉，或給提示
            if not display_acs:
                display_acs = aircrafts
        else:
            display_acs = aircrafts

        self.hub_cb['values'] = hubs
        self.aircraft_cb['values'] = display_acs
        
        if self.hub_var.get() not in hubs and hubs:
            self.hub_var.set(hubs[0])
            
        if display_acs:
            if self.aircraft_var.get() not in display_acs:
                self.aircraft_var.set(display_acs[0])
        else:
            self.aircraft_var.set('')

        self.tab2_hub_cb['values'] = hubs
        if self.tab2_hub_var.get() not in hubs and hubs:
            self.tab2_hub_var.set(hubs[0])
        self.on_tab2_hub_change()
        
        # 更新 Tab 4 玩家分站選單
        p_dests = sorted([d for d in self.db['dest'].unique().tolist() if d in PLAYABLE_AIRPORTS])
        self.tab4_dest_cb['values'] = p_dests
        if p_dests:
            if self.tab4_dest_var.get() not in p_dests:
                self.tab4_dest_var.set(p_dests[0])
        else:
            self.tab4_dest_var.set('')
        self.apply_tab4_filters()
        
        # 同步更新常用機型管理介面的表格
        if hasattr(self, 'fav_tree'):
            self.update_fav_table()

    # ================= 更新邏輯 =================
    def check_for_updates(self):
        """檢查 GitHub 上是否有新版本"""
        try:
            # 使用 urllib 抓取遠端版本號
            with urllib.request.urlopen(VERSION_URL, timeout=5) as response:
                latest_version = response.read().decode('utf-8').strip()
            
            # 比較版本號 (簡單的字串比較，若更複雜可使用 packaging.version)
            if latest_version > CURRENT_VERSION:
                if messagebox.askyesno("更新提醒", f"發現新版本 {latest_version}！\n目前版本: {CURRENT_VERSION}\n是否立即下載更新？"):
                    self.perform_update(latest_version)
        except Exception as e:
            # 靜默失敗，不干擾使用者正常使用
            print(f"檢查更新失敗: {e}")

    def perform_update(self, latest_version):
        """執行更新流程：下載新版本並以版本號命名"""
        try:
            # 以版本號命名新檔案
            new_exe_name = f"WOA_Profit_Analyzer_v{latest_version}.exe"
            
            # 下載進度提示
            prog_win = tk.Toplevel(self.root)
            prog_win.title("正在下載更新")
            prog_win.geometry("350x120")
            tk.Label(prog_win, text=f"正在下載新版本 v{latest_version}...\n下載完成後請手動開啟新程式。", 
                     font=("Helvetica", 10)).pack(pady=20)
            prog_win.update()

            # 執行下載
            urllib.request.urlretrieve(EXE_URL, new_exe_name)
            prog_win.destroy()

            messagebox.showinfo("下載完成", f"新版本已下載完成！\n\n檔名：{new_exe_name}\n\n請關閉目前視窗並手動啟動新版本即可。")
            
        except Exception as e:
            messagebox.showerror("下載失敗", f"下載過程中發生錯誤:\n{e}")
        
    def treeview_sort_column(self, tv, col, reverse):
        """點擊標題進行排序"""
        # 獲取所有項目的資料與 ID
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        
        # 轉換數值以便正確排序
        def convert_val(val):
            if col == "roi":
                try: return float(val.replace('%', ''))
                except: return 0.0
            if col == "profit":
                try: return int(re.sub(r'[^\d-]', '', val))
                except: return 0
            if col in ["dist", "rank", "xp"]:
                try: return int(val)
                except: return 0
            return val.lower()

        l.sort(key=lambda t: convert_val(t[0]), reverse=reverse)

        # 重新排列項目
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # 反轉下次排序的方向
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    # ================= Tab 1 邏輯 =================
    def apply_filters(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if self.db.empty:
            self.lbl_top_route.config(text="🏆 最高利潤: 無")
            self.lbl_top_profit.config(text="💰 淨利: $0")
            self.lbl_top_seat.config(text="💺 座位: -/-/-")
            self.lbl_top_xp.config(text="✨ T10 XP: -")
            self.lbl_top_roi.config(text="📈 ROI: -")
            return

        selected_hub = self.hub_var.get()
        selected_ac = self.aircraft_var.get()
        search_kw = self.search_var.get().lower()

        df_filtered = self.db[(self.db['hub'] == selected_hub) & (self.db['aircraft'] == selected_ac)].copy()
        
        if self.tab1_playable_var.get():
            df_filtered = df_filtered[df_filtered['dest'].isin(PLAYABLE_AIRPORTS)]
        
        df_filtered['city'] = df_filtered['dest'].apply(lambda x: self.dest_info.get(x, {}).get('city', '未知'))
        df_filtered['country'] = df_filtered['dest'].apply(lambda x: self.dest_info.get(x, {}).get('country', 'N/A'))
        
        if search_kw:
            mask = df_filtered['dest'].str.lower().str.contains(search_kw) | df_filtered['city'].str.lower().str.contains(search_kw)
            df_filtered = df_filtered[mask]

        df_filtered = df_filtered.sort_values(by='profit', ascending=False).reset_index(drop=True)

        ac_xp = self.xp_dict.get(selected_ac, '-')

        if df_filtered.empty:
            self.lbl_top_route.config(text="🏆 最高利潤: 無資料")
            self.lbl_top_profit.config(text="💰 淨利: $0")
            self.lbl_top_seat.config(text="💺 座位: -/-/-")
            self.lbl_top_xp.config(text=f"✨ T10 XP: {ac_xp}")
            self.lbl_top_roi.config(text="📈 ROI: -")
            return

        best = df_filtered.iloc[0]
        self.lbl_top_route.config(text=f"🏆 最高利潤: {selected_hub} ✈ {best['dest']}")
        self.lbl_top_profit.config(text=f"💰 淨利: ${int(best['profit']):,}")
        self.lbl_top_seat.config(text=f"💺 座位: {best['e'] or 0} / {best['b'] or 0} / {best['f'] or 0}")
        self.lbl_top_xp.config(text=f"✨ T10 XP: {ac_xp}")
        
        # 計算 ROI 並更新頂部標籤
        price = self.price_dict.get(selected_ac)
        if price and price > 0:
            best_roi = (best['profit'] / price) * 100
            self.lbl_top_roi.config(text=f"📈 ROI: {best_roi:.4f}%")
        else:
            self.lbl_top_roi.config(text="📈 ROI: -")

        for i, row in df_filtered.iterrows():
            dest_str = f"{row['dest']} - {row['city']} ({row['country']})"
            seat_str = f"{row['e'] or 0} / {row['b'] or 0} / {row['f'] or 0}"
            profit_str = f"${int(row['profit']):,}"
            
            # 計算該列的 ROI
            if price and price > 0:
                roi_val = (row['profit'] / price) * 100
                roi_str = f"{roi_val:.4f}%"
            else:
                roi_str = "-"
            
            self.tree.insert("", tk.END, values=(i + 1, dest_str, row['dist'], seat_str, ac_xp, profit_str, roi_str))

    # ================= Tab 2 邏輯 =================
    def on_tab2_hub_change(self, event=None):
        selected_hub = self.tab2_hub_var.get()
        if not selected_hub or self.db.empty:
            self.tab2_dest_cb['values'] = []
            self.tab2_dest_var.set('')
            self.apply_tab2_filters()
            return
            
        dests = self.db[self.db['hub'] == selected_hub]['dest'].unique().tolist()
        
        if self.tab2_playable_var.get():
            dests = [d for d in dests if d in PLAYABLE_AIRPORTS]
        
        formatted_dests = []
        for d in dests:
            city = self.dest_info.get(d, {}).get('city', '未知')
            country = self.dest_info.get(d, {}).get('country', 'N/A')
            formatted_dests.append(f"{d} - {city} ({country})")
            
        sorted_dests = sorted(formatted_dests)
        self.tab2_dest_cb['values'] = sorted_dests
        
        if sorted_dests:
            if self.tab2_dest_var.get() not in sorted_dests:
                self.tab2_dest_var.set(sorted_dests[0])
        else:
            self.tab2_dest_var.set('')
            
        self.apply_tab2_filters()

    def apply_tab2_filters(self):
        for item in self.tree2.get_children():
            self.tree2.delete(item)
            
        selected_hub = self.tab2_hub_var.get()
        selected_dest_full = self.tab2_dest_var.get()
        
        if not selected_hub or not selected_dest_full or self.db.empty:
            self.lbl_tab2_top.config(text="🏆 最賺錢機型: 無")
            return
            
        selected_dest = selected_dest_full.split(" - ")[0]
        
        df_filtered = self.db[(self.db['hub'] == selected_hub) & (self.db['dest'] == selected_dest)].copy()
        
        # 處理常用機型過濾
        if self.tab2_fav_only_var.get():
            df_filtered = df_filtered[df_filtered['aircraft'].isin(self.favorites)]
            
        df_filtered = df_filtered.sort_values(by='profit', ascending=False).reset_index(drop=True)

        if df_filtered.empty:
            self.lbl_tab2_top.config(text="🏆 最賺錢機型: 無資料")
            return

        best = df_filtered.iloc[0]
        self.lbl_tab2_top.config(text=f"🏆 此航線最賺錢機型: {best['aircraft']} (淨利 ${int(best['profit']):,})")

        for i, row in df_filtered.iterrows():
            ac = row['aircraft']
            profit_val = row['profit']
            
            seat_str = f"{row['e'] or 0} / {row['b'] or 0} / {row['f'] or 0}"
            profit_str = f"${int(profit_val):,}"
            xp_val = self.xp_dict.get(ac, '-')
            
            # 計算報酬率 (ROI = 淨利潤 / 飛機價格 * 100)
            price = self.price_dict.get(ac)
            if price and price > 0:
                roi_val = (profit_val / price) * 100
                roi_str = f"{roi_val:.4f}%" # 顯示到小數點後四位
            else:
                roi_str = "-"
            
            self.tree2.insert("", tk.END, values=(i + 1, ac, row['dist'], seat_str, xp_val, profit_str, roi_str))

    # ================= Tab 4 邏輯 =================
    def apply_tab4_filters(self):
        for item in self.tree4.get_children():
            self.tree4.delete(item)
            
        selected_dest = self.tab4_dest_var.get()
        if not selected_dest or self.db.empty:
            self.lbl_tab4_top.config(text="🏆 最佳航線: 無")
            return
            
        df_filtered = self.db[self.db['dest'] == selected_dest].copy()
        
        # 處理常用機型過濾
        if self.tab4_fav_only_var.get():
            df_filtered = df_filtered[df_filtered['aircraft'].isin(self.favorites)]
            
        df_filtered = df_filtered.sort_values(by='profit', ascending=False).reset_index(drop=True)

        if df_filtered.empty:
            self.lbl_tab4_top.config(text="🏆 最佳航線: 無資料")
            return

        best = df_filtered.iloc[0]
        self.lbl_tab4_top.config(text=f"🏆 最佳出發點: {best['hub']} (${int(best['profit']):,})")

        for i, row in df_filtered.iterrows():
            ac = row['aircraft']
            profit_val = row['profit']
            seat_str = f"{row['e'] or 0} / {row['b'] or 0} / {row['f'] or 0}"
            profit_str = f"${int(profit_val):,}"
            xp_val = self.xp_dict.get(ac, '-')
            
            # 計算報酬率 (ROI)
            price = self.price_dict.get(ac)
            if price and price > 0:
                roi_val = (profit_val / price) * 100
                roi_str = f"{roi_val:.4f}%"
            else:
                roi_str = "-"
            
            self.tree4.insert("", tk.END, values=(i + 1, row['hub'], ac, row['dist'], seat_str, xp_val, profit_str, roi_str))

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfitAnalyzerApp(root)
    root.mainloop()