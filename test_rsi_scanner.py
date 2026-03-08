# -*- coding: utf-8 -*-
"""
RSI 筛选工具功能测试脚本
"""

import sys

def test_imports():
    """测试必要的包是否已安装"""
    print("=" * 60)
    print("测试 Python 包导入")
    print("=" * 60)
    
    packages = {
        'akshare': 'AKShare 财经数据',
        'pandas': 'Pandas 数据处理',
        'numpy': 'NumPy 数值计算',
        'matplotlib': 'Matplotlib 绘图',
        'tkinter': 'Tkinter GUI 界面',
        'concurrent.futures': '并发处理',
        'logging': '日志记录'
    }
    
    failed = []
    for package, desc in packages.items():
        try:
            __import__(package)
            print(f"✓ {package:20s} - {desc}")
        except ImportError as e:
            print(f"✗ {package:20s} - {desc} [失败：{str(e)}]")
            failed.append(package)
    
    print()
    if failed:
        print(f"有 {len(failed)} 个包导入失败：{', '.join(failed)}")
        return False
    else:
        print("所有包导入成功！")
        return True

def test_rsi_calculation():
    """测试 RSI 计算功能"""
    print()
    print("=" * 60)
    print("测试 RSI 计算功能")
    print("=" * 60)
    
    try:
        import numpy as np
        
        # 模拟收盘价数据
        close_prices = [10.0, 10.2, 10.1, 10.5, 10.8, 10.6, 10.9, 11.2, 11.0, 11.3,
                       11.5, 11.8, 12.0, 11.7, 11.9, 12.2, 12.5, 12.3, 12.6, 12.8]
        
        def calculate_rsi(close_prices, period=14):
            """按照同花顺公式计算 RSI"""
            if len(close_prices) < period + 1:
                return None
            
            close_array = np.array(close_prices)
            lc = np.roll(close_array, 1)
            
            diff = close_array - lc
            gain = np.where(diff > 0, diff, 0)
            loss = np.where(diff < 0, -diff, 0)
            
            def sma_calculate(values, n, m=1):
                result = np.zeros(len(values))
                result[0] = values[0]
                for i in range(1, len(values)):
                    result[i] = (m * values[i] + (n - m) * result[i-1]) / n
                return result
            
            gain_sma = sma_calculate(gain, period)
            loss_sma = sma_calculate(loss, period)
            
            if loss_sma[-1] == 0:
                return 100.0
            
            rsi = (gain_sma[-1] / loss_sma[-1]) * 100
            return rsi
        
        rsi = calculate_rsi(close_prices)
        print(f"测试数据 RSI 值：{rsi:.2f}")
        
        if 0 <= rsi <= 100:
            print("✓ RSI 计算结果正常")
            return True
        else:
            print("✗ RSI 计算结果异常")
            return False
            
    except Exception as e:
        print(f"✗ RSI 计算测试失败：{str(e)}")
        return False

def test_akshare():
    """测试 AKshare 数据获取"""
    print()
    print("=" * 60)
    print("测试 AKshare 数据获取")
    print("=" * 60)
    
    try:
        import akshare as ak
        from datetime import datetime, timedelta
        
        # 测试获取股票列表
        print("正在获取 A 股股票列表...")
        stock_list = ak.stock_info_a_code_name()
        
        if stock_list is not None and len(stock_list) > 0:
            print(f"✓ 成功获取 {len(stock_list)} 只股票信息")
            print(f"  示例：{stock_list.iloc[0].tolist()}")
            return True
        else:
            print("✗ 获取股票列表失败")
            return False
            
    except Exception as e:
        print(f"✗ AKshare 测试失败：{str(e)}")
        return False

def test_concurrent():
    """测试并发处理"""
    print()
    print("=" * 60)
    print("测试并发处理功能")
    print("=" * 60)
    
    try:
        import concurrent.futures
        import time
        
        def test_task(n):
            time.sleep(0.1)
            return n * n
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(test_task, range(10)))
        elapsed = time.time() - start_time
        
        print(f"✓ 并发测试完成，耗时：{elapsed:.2f}秒")
        print(f"  结果：{results[:5]}...")
        return True
        
    except Exception as e:
        print(f"✗ 并发测试失败：{str(e)}")
        return False

def test_gui():
    """测试 GUI 组件"""
    print()
    print("=" * 60)
    print("测试 Tkinter GUI")
    print("=" * 60)
    
    try:
        import tkinter as tk
        
        # 创建测试窗口
        root = tk.Tk()
        root.title("RSI 筛选工具 - 测试窗口")
        root.geometry("400x300")
        
        label = tk.Label(root, text="Tkinter GUI 测试成功！", font=('Arial', 16))
        label.pack(expand=True)
        
        button = tk.Button(root, text="关闭", command=root.destroy)
        button.pack(pady=20)
        
        print("✓ Tkinter GUI 初始化成功")
        print("  测试窗口已打开，请点击关闭按钮继续测试...")
        
        root.mainloop()
        print("✓ GUI 测试完成")
        return True
        
    except Exception as e:
        print(f"✗ GUI 测试失败：{str(e)}")
        return False

def main():
    """运行所有测试"""
    print("\nRSI 筛选工具 - 功能测试\n")
    
    results = {
        '包导入测试': test_imports(),
        'RSI 计算测试': test_rsi_calculation(),
        'AKshare 测试': test_akshare(),
        '并发处理测试': test_concurrent(),
        'GUI 测试': test_gui()
    }
    
    print()
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20s} - {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print()
    print(f"总计：{passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n✓ 所有测试通过！程序可以正常运行。")
        print("\n现在可以运行主程序：python rsi_scanner.py")
    else:
        print("\n✗ 部分测试失败，请检查相关依赖包。")
    
    print()
    input("按回车键退出...")

if __name__ == "__main__":
    main()
