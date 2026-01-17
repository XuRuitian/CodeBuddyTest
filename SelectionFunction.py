# 自动安装缺失的库
import subprocess
import sys

# 需要安装的库列表
required_libraries = [
    "pandas",
    "akshare",
    "ttkbootstrap"
]

# 安装缺失的库
def install_missing_libraries():
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            print(f"正在安装缺失的库: {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# 执行安装
install_missing_libraries()

# 导入所需库
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import akshare as ak
import concurrent.futures
import threading
from functools import lru_cache
import time
from datetime import datetime

# 尝试导入美化库，如果没有则使用原生
try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
    ROOT_CLASS = tb.Window
except ImportError:
    ROOT_CLASS = tk.Tk

class StockScreenerApp:
    def __init__(self):
        # 初始化主窗口
        if ROOT_CLASS == tk.Tk:
            self.root = tk.Tk()
        else:
            self.root = ROOT_CLASS(themename="superhero")
            
        self.root.title("A股 RSI 智能筛选系统 (Akshare + Multi-threading)")
        self.root.geometry("1000x700")

        # 全局变量
        self.is_analyzing = False
        self.stop_event = threading.Event()
        
        # 缓存锁
        self.data_lock = threading.Lock()

        # 布局初始化
        self.setup_ui()

    def setup_ui(self):
        # --- 顶部控制区 ---
        control_frame = ttk.LabelFrame(self.root, text="筛选控制面板", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 板块选择
        ttk.Label(control_frame, text="选择市场/板块:").pack(side=tk.LEFT, padx=5)
        self.market_combo = ttk.Combobox(control_frame, state="readonly", width=15)
        self.market_combo['values'] = ("沪深A股", "上证主板", "深证主板") # 示例，可扩展港股
        self.market_combo.current(0)
        self.market_combo.pack(side=tk.LEFT, padx=5)

        # 天数输入
        ttk.Label(control_frame, text=" |  连续天数:").pack(side=tk.LEFT, padx=5)
        self.days_var = tk.IntVar(value=5) # 默认5天
        self.days_entry = ttk.Entry(control_frame, textvariable=self.days_var, width=5)
        self.days_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, text="天 RSI < 30 |").pack(side=tk.LEFT, padx=5)

        # 参数说明
        ttk.Label(control_frame, text=" 筛选条件: 指定天数内所有RSI(14) < 30  ").pack(side=tk.LEFT, padx=10)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # 按钮
        self.btn_start = ttk.Button(control_frame, text="开始筛选", command=self.start_analysis_thread)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(self.root, text="就绪", font=("Arial", 10))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # --- 数据展示区 ---
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("code", "name", "price", "rsi", "change_pct", "industry")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # 定义表头
        self.tree.heading("code", text="股票代码")
        self.tree.heading("name", text="股票名称")
        self.tree.heading("price", text="当前价格")
        self.tree.heading("rsi", text="RSI(14)数值")
        self.tree.heading("change_pct", text="涨跌幅(%)")
        self.tree.heading("industry", text="所属行业")
        
        # 定义列宽和对齐
        for col in columns:
            self.tree.column(col, anchor="center", width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # --- 核心算法逻辑 ---

    @staticmethod
    def calculate_ths_rsi(series_close, N=14, days=None):
        """
        同花顺 RSI 算法翻译
        LC := REF(C,1);
        RSI:SMA(MAX(C-LC,0),14,1)/SMA(ABS(C-LC),14,1)*100;
        
        参数:
        - series_close: 收盘价序列
        - N: RSI计算周期
        - days: 返回最近多少天的RSI值，None则只返回最新值
        
        返回:
        - days=None: 最新的RSI值
        - days>0: 最近days天的RSI值列表
        """
        if len(series_close) < N + 1:
            return None


        # 计算涨跌幅 C - LC
        delta = series_close.diff()
        
        # MAX(C-LC, 0) -> 上涨部分
        up = delta.clip(lower=0)
        
        # ABS(C-LC) -> 绝对值变化
        abs_diff = delta.abs()

        # SMA(X, 14, 1) 在 Pandas 中等同于 ewm(alpha=1/14, adjust=False)
        alpha = 1 / N
        
        sma_up = up.ewm(alpha=alpha, adjust=False).mean()
        sma_abs = abs_diff.ewm(alpha=alpha, adjust=False).mean()

        # 计算 RSI
        rsi = (sma_up / sma_abs) * 100
        
        if days is None:
            return rsi.iloc[-1] # 返回最新的 RSI 值
        else:
            # 返回最近days天的RSI值
            return rsi.iloc[-days:].tolist() if len(rsi) >= days else None


    # --- 数据获取与缓存 ---

    @lru_cache(maxsize=100) # 数据缓存优化：内存中缓存最近请求的100只股票数据
    def fetch_stock_history_cached(self, symbol):
        """
        获取单只股票历史数据（带缓存）
        """
        try:
            # 获取日线数据，用于计算RSI
            # 注意：akshare 接口可能会变动，这里使用较稳定的 stock_zh_a_hist
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            return df
        except Exception:
            return None

    def get_market_stocks(self, market_type):
        """获取市场实时行情列表"""
        self.update_status("正在获取全市场实时数据...")
        try:
            # 获取沪深A股实时行情
            df = ak.stock_zh_a_spot_em()
            
            # 根据下拉框筛选 (简单示例)
            if market_type == "上证主板":
                df = df[df['代码'].str.startswith('60')]
            elif market_type == "深证主板":
                df = df[df['代码'].str.startswith('00')]
            
            # 过滤掉退市或停牌的（成交量为0）
            df = df[df['最新价'].notnull()]
            return df
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("网络错误", f"无法获取市场数据: {str(e)}"))
            return pd.DataFrame()

    # --- 多线程控制 ---

    def start_analysis_thread(self):
        if self.is_analyzing:
            return
        
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.is_analyzing = True
        self.btn_start.configure(state="disabled", text="正在分析...")
        self.progress_var.set(0)
        
        # 开启后台线程
        threading.Thread(target=self.run_analysis_logic, daemon=True).start()

    def run_analysis_logic(self):
        market_type = self.market_combo.get()
        check_days = self.days_var.get()  # 获取用户输入的天数
        all_stocks = self.get_market_stocks(market_type)
        
        if all_stocks.empty:
            self.finish_analysis()
            return

        # 限制数量用于演示（避免请求数千次接口太慢），实际使用可去掉 head()
        # 注意：为了演示效果，这里只取前 50 只股票，或者成交量大的前 100 只
        # 实际生产中建议分批处理或使用付费的量化本地数据库
        target_stocks = all_stocks.sort_values(by="成交量", ascending=False).head(100) 
        total_stocks = len(target_stocks)
        
        results = []
        completed_count = 0

        # 线程池配置
        # max_workers 不宜过大，防止触发反爬虫限制
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_stock = {}
            
            for index, row in target_stocks.iterrows():
                code = row['代码']
                future = executor.submit(self.process_single_stock, code, row, check_days)
                future_to_stock[future] = code


            for future in concurrent.futures.as_completed(future_to_stock):
                data = future.result()
                if data:
                    results.append(data)
                    # 实时插入数据到 Treeview（需要回到主线程）
                    self.root.after(0, self.insert_tree_row, data)
                
                completed_count += 1
                progress = (completed_count / total_stocks) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda c=completed_count, t=total_stocks: self.update_status(f"正在分析: {c}/{t}"))

        self.root.after(0, self.finish_analysis)

    def process_single_stock(self, code, row_data, check_days):
        """
        单个股票的处理逻辑（将在子线程运行）
        
        参数:
        - code: 股票代码
        - row_data: 股票实时数据
        - check_days: 检查连续多少天RSI < 30
        """
        try:
            # 1. 获取历史数据
            hist_df = self.fetch_stock_history_cached(code)
            
            # 需要确保有足够的数据来计算RSI和检查指定天数
            if hist_df is None or len(hist_df) < 20 + check_days:
                return None


            # 2. 计算最近check_days天的RSI值
            rsi_values = self.calculate_ths_rsi(hist_df['收盘'], N=14, days=check_days)
            
            if rsi_values is None or len(rsi_values) < check_days:
                return None


            # 3. 筛选条件：所有RSI值 < 30
            if all(rsi < 30 for rsi in rsi_values):
                return {
                    "code": code,
                    "name": row_data['名称'],
                    "price": row_data['最新价'],
                    "rsi": round(rsi_values[-1], 2),  # 显示最新的RSI值
                    "change_pct": row_data['涨跌幅'],
                    "industry": row_data.get('行业', '未知') # akshare 某些接口可能不含行业字段
                }
            return None

        except Exception as e:
            # 这里的错误最好记录日志，不要弹窗打断
            return None

    # --- GUI 更新回调 ---

    def insert_tree_row(self, data):
        # 根据 RSI 值设置颜色标签（可选）
        self.tree.insert("", "end", values=(
            data['code'],
            data['name'],
            data['price'],
            data['rsi'],
            data['change_pct'],
            data['industry']
        ))

    def update_status(self, text):
        self.status_label.config(text=text)

    def finish_analysis(self):
        self.is_analyzing = False
        self.btn_start.configure(state="normal", text="开始筛选")
        self.update_status("筛选完成")
        messagebox.showinfo("完成", "筛选任务已结束！")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    import traceback
    try:
        app = StockScreenerApp()
        app.run()
    except Exception as e:
        print("程序发生错误:", str(e))
        traceback.print_exc()
        with open("error_log.txt", "w") as f:
            f.write(str(e))
            f.write("\n")
            traceback.print_exc(file=f)
        input("按回车键退出...")