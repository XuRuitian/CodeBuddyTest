# -*- coding: utf-8 -*-
"""
A股市场RSI筛选工具
基于AKshare库获取股票数据，按照同花顺平台RSI计算公式筛选RSI值低于30的股票
支持并发处理、图形界面、数据可视化等功能
"""

import sys
import subprocess
import importlib.util
import logging
import threading
import queue
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rsi_scanner.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DependencyChecker:
    """依赖包检测和自动安装类"""
    
    REQUIRED_PACKAGES = {
        'akshare': 'akshare',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'tqdm': 'tqdm'
    }
    
    def __init__(self, root=None):
        self.root = root
        self.missing_packages = []
        self.install_queue = queue.Queue()
        
    def check_package(self, package_name: str) -> bool:
        """检查单个包是否已安装"""
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    
    def check_all_dependencies(self) -> Tuple[bool, List[str]]:
        """检查所有必需的依赖包"""
        self.missing_packages = []
        
        for package, install_name in self.REQUIRED_PACKAGES.items():
            if not self.check_package(package):
                self.missing_packages.append(install_name)
                logger.warning(f"未找到必需包：{install_name}")
        
        if self.missing_packages:
            logger.warning(f"缺少 {len(self.missing_packages)} 个必需包")
            return False, self.missing_packages
        else:
            logger.info("所有依赖包已就绪")
            return True, []
    
    def install_package(self, package_name: str, progress_callback=None) -> bool:
        """安装单个包"""
        try:
            cmd = [sys.executable, "-m", "pip", "install", package_name, "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    logger.info(f"安装 {package_name}: {line}")
                    if progress_callback:
                        progress_callback(line)
            
            process.wait()
            
            if process.returncode == 0:
                logger.info(f"包 {package_name} 安装成功")
                return True
            else:
                logger.error(f"包 {package_name} 安装失败")
                return False
                
        except Exception as e:
            logger.error(f"安装 {package_name} 时出错：{str(e)}")
            return False
    
    def install_all_missing(self, progress_callback=None) -> bool:
        """安装所有缺失的包"""
        if not self.missing_packages:
            return True
        
        success_count = 0
        for package in self.missing_packages:
            if self.install_package(package, progress_callback):
                success_count += 1
            else:
                return False
        
        return success_count == len(self.missing_packages)


class StockDataFetcher:
    """股票数据获取和RSI计算类"""
    
    def __init__(self):
        self.data_cache = {}
        
    def get_stock_list(self) -> List[Dict]:
        """获取A股市场股票列表"""
        try:
            import akshare as ak
            import pandas as pd
            
            logger.info("正在获取A股股票列表...")
            stock_list = ak.stock_info_a_code_name()
            
            if isinstance(stock_list, pd.DataFrame):
                stocks = []
                for _, row in stock_list.iterrows():
                    stocks.append({
                        'code': row['code'],
                        'name': row['name']
                    })
                logger.info(f"获取到 {len(stocks)} 只股票")
                return stocks
            else:
                logger.error("获取股票列表失败")
                return []
                
        except Exception as e:
            logger.error(f"获取股票列表时出错：{str(e)}")
            return []
    
    def calculate_rsi(self, close_prices: List[float], period: int = 14) -> Optional[float]:
        """
        按照同花顺平台RSI计算公式计算RSI值
        LC:=REF(C,1);
        RSI:SMA(MAX(C-LC,0),14,1)/SMA(ABS(C-LC),14,1)*100
        """
        import numpy as np
        
        if len(close_prices) < period + 1:
            return None
        
        close_array = np.array(close_prices)
        lc = np.roll(close_array, 1)  # LC:=REF(C,1)
        
        diff = close_array - lc
        gain = np.where(diff > 0, diff, 0)  # MAX(C-LC,0)
        loss = np.where(diff < 0, -diff, 0)  # ABS(C-LC)
        
        # 计算SMA（简单移动平均）
        # 同花顺使用的是SMA，不是EMA
        # SMA(X,N,M) = (M*X + (N-M)*Prev)/N
        # 这里M=1
        
        def sma_calculate(values: np.ndarray, n: int, m: int = 1) -> np.ndarray:
            """计算SMA"""
            result = np.zeros(len(values))
            result[0] = values[0]
            
            for i in range(1, len(values)):
                result[i] = (m * values[i] + (n - m) * result[i-1]) / n
            
            return result
        
        gain_sma = sma_calculate(gain, period)
        loss_sma = sma_calculate(loss, period)
        
        # 避免除以0
        if loss_sma[-1] == 0:
            return 100.0
        
        rsi = (gain_sma[-1] / loss_sma[-1]) * 100
        
        return rsi
    
    def get_stock_data(self, stock_code: str) -> Optional[Dict]:
        """获取单只股票的RSI数据"""
        try:
            import akshare as ak
            
            # 获取历史行情数据
            stock_df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=100)).strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq"
            )
            
            if stock_df is None or len(stock_df) < 15:
                return None
            
            close_prices = stock_df['收盘'].tolist()
            rsi = self.calculate_rsi(close_prices)
            
            if rsi is not None:
                return {
                    'code': stock_code,
                    'name': '',  # 名称会在后续填充
                    'close': close_prices[-1],
                    'rsi': rsi,
                    'date': datetime.now().strftime('%Y-%m-%d')
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"获取股票 {stock_code} 数据失败：{str(e)}")
            return None
    
    def fetch_stocks_parallel(self, stocks: List[Dict], max_workers: int = 10, 
                             progress_callback=None) -> List[Dict]:
        """并发获取股票数据"""
        import concurrent.futures
        
        results = []
        total = len(stocks)
        completed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_stock = {
                executor.submit(self.get_stock_data, stock['code']): stock 
                for stock in stocks
            }
            
            for future in concurrent.futures.as_completed(future_to_stock):
                stock = future_to_stock[future]
                try:
                    data = future.result()
                    if data:
                        data['name'] = stock['name']
                        results.append(data)
                except Exception as e:
                    logger.error(f"处理股票 {stock['code']} 时出错：{str(e)}")
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, results)
        
        return results


class RSIApplication:
    """主应用程序类"""
    
    def __init__(self):
        self.root = None
        self.fetcher = StockDataFetcher()
        self.filtered_results = []
        self.is_running = False
        
    def start(self):
        """启动应用程序"""
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext
        
        self.root = tk.Tk()
        self.root.title("A股市场RSI筛选工具")
        self.root.geometry("1000x700")
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="A股市场RSI筛选工具", 
            font=('微软雅黑', 16, 'bold')
        )
        title_label.grid(row=0, column=0, pady=10)
        
        # 参数设置区域
        param_frame = ttk.LabelFrame(main_frame, text="筛选参数设置", padding="10")
        param_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        param_frame.columnconfigure(1, weight=1)
        
        # RSI阈值
        ttk.Label(param_frame, text="RSI阈值:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.rsi_threshold = tk.IntVar(value=30)
        rsi_spinbox = ttk.Spinbox(
            param_frame, 
            from_=0, 
            to=100, 
            textvariable=self.rsi_threshold,
            width=10
        )
        rsi_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 并发线程数
        ttk.Label(param_frame, text="并发线程数:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.max_workers = tk.IntVar(value=10)
        workers_spinbox = ttk.Spinbox(
            param_frame, 
            from_=1, 
            to=50, 
            textvariable=self.max_workers,
            width=10
        )
        workers_spinbox.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="开始筛选", 
            command=self.start_screening
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="停止", 
            command=self.stop_screening,
            state='disabled'
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.export_button = ttk.Button(
            button_frame, 
            text="导出结果", 
            command=self.export_results,
            state='disabled'
        )
        self.export_button.grid(row=0, column=2, padx=5)
        
        self.visualize_button = ttk.Button(
            button_frame, 
            text="可视化", 
            command=self.visualize_results,
            state='disabled'
        )
        self.visualize_button.grid(row=0, column=3, padx=5)
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            mode='determinate'
        )
        progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.grid(row=0, column=1, padx=10)
        
        # 结果统计
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.total_label = ttk.Label(stats_frame, text="总计：0")
        self.total_label.grid(row=0, column=0, padx=10)
        
        self.filtered_label = ttk.Label(stats_frame, text="符合条件：0")
        self.filtered_label.grid(row=0, column=1, padx=10)
        
        self.current_rsi_label = ttk.Label(stats_frame, text="当前最低RSI: -")
        self.current_rsi_label.grid(row=0, column=2, padx=10)
        
        # 结果展示区域
        result_frame = ttk.LabelFrame(main_frame, text="筛选结果", padding="10")
        result_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview显示结果
        columns = ('代码', '名称', '收盘价', 'RSI值', '日期')
        self.result_tree = ttk.Treeview(
            result_frame, 
            columns=columns, 
            show='headings',
            height=15
        )
        
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=120, anchor='center')
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=5)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=8, 
            wrap=tk.WORD,
            state='disabled'
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 重定向日志输出
        self.setup_log_redirect()
        
        # 启动时检查依赖
        self.check_dependencies_on_startup()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def setup_log_redirect(self):
        """重定向日志输出到GUI"""
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.configure(state='disabled')
                self.text_widget.after(0, append)
        
        gui_handler = TextHandler(self.log_text)
        gui_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)
    
    def check_dependencies_on_startup(self):
        """启动时检查依赖"""
        def check_thread():
            checker = DependencyChecker(self.root)
            all_ok, missing = checker.check_all_dependencies()
            
            if not all_ok:
                self.root.after(0, lambda: self.show_dependency_dialog(checker, missing))
            else:
                self.root.after(0, lambda: self.log_text.configure(state='normal'))
        
        thread = threading.Thread(target=check_thread)
        thread.daemon = True
        thread.start()
    
    def show_dependency_dialog(self, checker, missing_packages):
        """显示依赖安装对话框"""
        from tkinter import messagebox
        
        packages_str = '\n'.join(missing_packages)
        msg = f"发现以下缺失的依赖包：\n\n{packages_str}\n\n是否自动安装？"
        
        if messagebox.askyesno("依赖包检测", msg):
            # 创建安装进度窗口
            install_window = tk.Toplevel(self.root)
            install_window.title("安装依赖包")
            install_window.geometry("500x300")
            install_window.transient(self.root)
            install_window.grab_set()
            
            ttk.Label(
                install_window, 
                text="正在安装依赖包，请稍候...", 
                font=('微软雅黑', 12)
            ).pack(pady=20)
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(
                install_window, 
                variable=progress_var, 
                maximum=len(missing_packages),
                mode='determinate'
            )
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            
            status_label = ttk.Label(install_window, text="")
            status_label.pack(pady=10)
            
            log_text = scrolledtext.ScrolledText(install_window, height=10, wrap=tk.WORD)
            log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            def progress_callback(msg):
                log_text.insert(tk.END, msg + '\n')
                log_text.see(tk.END)
            
            def install_thread():
                success = checker.install_all_missing(progress_callback)
                
                def finish_install():
                    if success:
                        messagebox.showinfo("安装成功", "所有依赖包安装成功！")
                        install_window.destroy()
                        self.log_text.configure(state='normal')
                    else:
                        messagebox.showerror("安装失败", "部分依赖包安装失败，请手动安装。")
                        install_window.destroy()
                
                install_window.after(0, finish_install)
            
            def install_packages():
                current = 0
                for package in missing_packages:
                    status_label.config(text=f"正在安装 {package}...")
                    progress_var.set(current)
                    checker.install_package(package, progress_callback)
                    current += 1
                progress_var.set(len(missing_packages))
            
            thread = threading.Thread(target=install_thread)
            thread.daemon = True
            thread.start()
        else:
            messagebox.showwarning("提示", "缺少必要的依赖包，程序可能无法正常运行。")
            self.log_text.configure(state='normal')
    
    def start_screening(self):
        """开始筛选"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.export_button.configure(state='disabled')
        self.visualize_button.configure(state='disabled')
        self.result_tree.delete(*self.result_tree.get_children())
        self.filtered_results = []
        
        def screening_thread():
            try:
                # 获取股票列表
                self.root.after(0, lambda: self.status_label.config(text="正在获取股票列表..."))
                stocks = self.fetcher.get_stock_list()
                
                if not stocks:
                    self.root.after(0, lambda: messagebox.showerror("错误", "获取股票列表失败"))
                    return
                
                self.root.after(0, lambda: self.total_label.config(text=f"总计：{len(stocks)}"))
                
                # 并发获取数据
                def progress_callback(completed, total, results):
                    progress = (completed / total) * 100
                    self.root.after(0, lambda: self.progress_var.set(progress))
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"进度：{completed}/{total}"
                    ))
                    
                    # 更新符合条件的股票
                    threshold = self.rsi_threshold.get()
                    filtered = [r for r in results if r['rsi'] < threshold]
                    self.root.after(0, lambda: self.filtered_label.config(
                        text=f"符合条件：{len(filtered)}"
                    ))
                    
                    # 更新最低RSI
                    if filtered:
                        min_rsi = min(r['rsi'] for r in filtered)
                        self.root.after(0, lambda: self.current_rsi_label.config(
                            text=f"当前最低RSI: {min_rsi:.2f}"
                        ))
                
                self.root.after(0, lambda: self.status_label.config(text="正在获取股票数据..."))
                workers = self.max_workers.get()
                results = self.fetcher.fetch_stocks_parallel(
                    stocks, 
                    max_workers=workers,
                    progress_callback=progress_callback
                )
                
                # 筛选RSI低于阈值的股票
                threshold = self.rsi_threshold.get()
                self.filtered_results = [r for r in results if r['rsi'] < threshold]
                
                # 按RSI排序
                self.filtered_results.sort(key=lambda x: x['rsi'])
                
                # 更新UI
                def update_ui():
                    self.progress_var.set(100)
                    self.status_label.config(text="筛选完成")
                    self.filtered_label.config(text=f"符合条件：{len(self.filtered_results)}")
                    
                    # 填充结果
                    for stock in self.filtered_results[:100]:  # 只显示前100条
                        self.result_tree.insert('', tk.END, values=(
                            stock['code'],
                            stock['name'],
                            f"{stock['close']:.2f}",
                            f"{stock['rsi']:.2f}",
                            stock['date']
                        ))
                    
                    if self.filtered_results:
                        self.export_button.configure(state='normal')
                        self.visualize_button.configure(state='normal')
                    
                    self.start_button.configure(state='normal')
                    self.stop_button.configure(state='disabled')
                    self.is_running = False
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                logger.error(f"筛选过程中出错：{str(e)}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"筛选失败：{str(e)}"))
                self.root.after(0, lambda: self.start_button.configure(state='normal'))
                self.root.after(0, lambda: self.stop_button.configure(state='disabled'))
                self.is_running = False
        
        thread = threading.Thread(target=screening_thread)
        thread.daemon = True
        thread.start()
    
    def stop_screening(self):
        """停止筛选"""
        self.is_running = False
        self.status_label.config(text="正在停止...")
    
    def export_results(self):
        """导出结果"""
        if not self.filtered_results:
            return
        
        from tkinter import filedialog
        import pandas as pd
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx")],
            title="保存筛选结果"
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.filtered_results)
                
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(file_path, index=False)
                
                messagebox.showinfo("成功", f"结果已保存到：{file_path}")
                logger.info(f"结果导出到：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def visualize_results(self):
        """可视化结果"""
        if not self.filtered_results:
            return
        
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.font_manager import FontProperties
        
        # 创建可视化窗口
        viz_window = tk.Toplevel(self.root)
        viz_window.title("RSI可视化")
        viz_window.geometry("800x600")
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # RSI分布直方图
        rsi_values = [r['rsi'] for r in self.filtered_results]
        ax1.hist(rsi_values, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
        ax1.axvline(x=self.rsi_threshold.get(), color='red', linestyle='--', label=f'阈值：{self.rsi_threshold.get()}')
        ax1.set_xlabel('RSI值')
        ax1.set_ylabel('股票数量')
        ax1.set_title('RSI分布直方图')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # RSI前10的股票
        top_10 = self.filtered_results[:10]
        if top_10:
            names = [r['name'] for r in top_10]
            rsi_top = [r['rsi'] for r in top_10]
            
            colors = plt.cm.RdYlGn_r([r/100 for r in rsi_top])
            bars = ax2.barh(range(len(names)), rsi_top, color=colors)
            ax2.set_yticks(range(len(names)))
            ax2.set_yticklabels(names)
            ax2.set_xlabel('RSI值')
            ax2.set_title('RSI最低的10只股票')
            ax2.invert_yaxis()
            
            # 添加数值标签
            for i, (bar, val) in enumerate(zip(bars, rsi_top)):
                ax2.text(val + 0.5, i, f'{val:.2f}', va='center', fontsize=9)
        
        ax2.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 嵌入到Tkinter
        canvas = FigureCanvasTkAgg(fig, master=viz_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 保存按钮
        def save_figure():
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG图片", "*.png"), ("PDF文件", "*.pdf")],
                title="保存图表"
            )
            if file_path:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("成功", f"图表已保存到：{file_path}")
        
        ttk.Button(viz_window, text="保存图表", command=save_figure).pack(pady=10)
    
    def on_closing(self):
        """关闭窗口处理"""
        if self.is_running:
            from tkinter import messagebox
            if messagebox.askokcancel("退出", "筛选正在进行中，确定要退出吗？"):
                self.is_running = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("A股市场RSI筛选工具启动")
    logger.info("=" * 50)
    
    try:
        app = RSIApplication()
        app.start()
    except Exception as e:
        logger.error(f"程序启动失败：{str(e)}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    main()
