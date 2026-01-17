# StockSelection - A股 RSI 智能筛选系统

基于 Python 的股票筛选工具，使用 Akshare 数据源和多线程技术，实时分析股票 RSI 指标。

## 功能特性

- **实时数据获取**：使用 Akshare 获取沪深 A 股实时行情
- **RSI 智能筛选**：基于同花顺算法的 RSI(14) 指标计算
- **多线程处理**：使用线程池加速数据分析
- **可视化界面**：基于 Tkinter 和 ttkbootstrap 的现代化 GUI
- **数据缓存**：LRU 缓存优化，减少重复请求

## 使用方法

### 环境要求
- Python 3.12+
- pandas
- akshare
- ttkbootstrap

### 安装依赖
```bash
pip install pandas akshare ttkbootstrap
```

### 运行程序
```bash
python SelectionFunction.py
```

### 打包为 EXE
```bash
pyinstaller SelectionFunction.spec
```

## 筛选条件

程序筛选指定天数内 RSI(14) 值持续低于 30 的股票：
- 支持 3-30 天连续筛选
- 按成交量排序，优先分析活跃股票
- 实时显示分析进度和结果

## 技术栈

- Python 3.12
- Tkinter (GUI)
- ttkbootstrap (UI 美化)
- Akshare (数据源)
- Pandas (数据处理)
- Threading (并发处理)

## 许可证

MIT License

## 作者

Qisong (小天)
