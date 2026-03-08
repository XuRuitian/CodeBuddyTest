# A 股市场 RSI 筛选工具

基于 AKshare 库获取 A 股市场股票数据，按照同花顺平台的 RSI 计算公式筛选 RSI 值低于指定阈值（RSI<30）的股票。

## 功能特点

- ✅ **自动依赖检测**：程序启动时自动检测必需的 Python 包，并提供自动安装功能
- ✅ **并发数据处理**：使用多线程并发获取股票数据，大幅提升处理效率
- ✅ **图形化界面**：基于 Python Tkinter 的友好 GUI，支持参数设置、进度显示
- ✅ **RSI 计算**：严格按照同花顺平台公式计算 RSI 值
- ✅ **数据可视化**：提供 RSI 分布直方图和低 RSI 股票排行
- ✅ **结果导出**：支持导出 CSV 和 Excel 格式
- ✅ **错误处理**：完善的异常处理和日志记录功能

## 系统要求

- Windows 7/8/10/11
- Python 3.8 或更高版本
- 网络连接（用于获取股票数据）

## 安装步骤

### 方法一：使用安装脚本（推荐）

1. 双击运行 `install_dependencies.bat` 文件
2. 等待所有依赖包安装完成
3. 运行 `python rsi_scanner.py` 启动程序

### 方法二：手动安装

```bash
# 升级 pip
python -m pip install --upgrade pip

# 安装依赖包
pip install akshare pandas numpy matplotlib tqdm -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动程序
python rsi_scanner.py
```
## 打开方式
**简单版本：**
1.<img width="1056" height="411" alt="c1b47e677bd3b83ac300d50bc45697eb" src="https://github.com/user-attachments/assets/14d3b1b3-00b9-469f-b442-ec4ebc9bf2dc" />
2.<img width="1878" height="630" alt="6bd7378498aed3926439b1501c2b646d" src="https://github.com/user-attachments/assets/a4fe5e39-5697-4f1b-8a15-84f65316d1c2" />
3.<img width="639" height="186" alt="1f739827a80fc9ee3af15b66947609e1" src="https://github.com/user-attachments/assets/f42d47d9-938b-437c-8f6a-e6ab57448ccc" />
## 使用方法

1. **启动程序**：运行 `python rsi_scanner.py`

2. **参数设置**：
   - RSI 阈值：设置筛选的 RSI 上限（默认 30）
   - 并发线程数：设置并发获取数据的线程数（默认 10）

3. **开始筛选**：点击"开始筛选"按钮

4. **查看结果**：
   - 实时查看筛选进度
   - 结果表格显示符合条件的股票
   - 查看统计信息（总计、符合条件数量、最低 RSI）

5. **数据导出**：点击"导出结果"保存为 CSV 或 Excel 文件

6. **可视化分析**：点击"可视化"查看 RSI 分布图表

## RSI 计算公式

本程序严格按照同花顺平台的 RSI 计算公式：

```
LC := REF(C, 1)
RSI := SMA(MAX(C-LC, 0), 14, 1) / SMA(ABS(C-LC), 14, 1) * 100
```

其中：
- C：当日收盘价
- LC：前一日收盘价
- SMA：简单移动平均
- 周期：14 日

## 界面说明

### 主界面
- **标题区**：程序名称
- **参数设置区**：RSI 阈值和并发线程数设置
- **按钮区**：开始筛选、停止、导出结果、可视化
- **进度条**：显示当前处理进度
- **统计区**：显示总计、符合条件数量、当前最低 RSI
- **结果区**：表格显示筛选结果
- **日志区**：显示程序运行日志

### 可视化窗口
- RSI 分布直方图
- RSI 最低的 10 只股票排行
- 支持保存图表为 PNG 或 PDF 格式

## 文件说明

- `rsi_scanner.py` - 主程序文件
- `requirements.txt` - Python 依赖包列表
- `install_dependencies.bat` - Windows 依赖包安装脚本
- `README.md` - 本说明文档
- `rsi_scanner.log` - 程序运行日志（运行后生成）

## 常见问题

### Q: 程序启动时提示缺少依赖包
A: 程序会自动检测并提示安装，点击"是"即可自动安装。也可以手动运行 `install_dependencies.bat`。

### Q: 获取股票数据失败
A: 请检查网络连接是否正常，AKshare 需要从网络获取股票数据。

### Q: 程序运行缓慢
A: 可以适当增加并发线程数（建议 10-20），但过高可能导致网络请求失败。

### Q: 导出的文件乱码
A: CSV 文件使用 UTF-8-SIG 编码，Excel 文件使用 xlsx 格式，建议用相应的软件打开。

## 日志查看

程序运行日志保存在 `rsi_scanner.log` 文件中，同时也会在界面的日志区域实时显示。

## 技术实现

- **数据源**：AKshare（开源财经数据接口）
- **GUI 框架**：Tkinter（Python 标准库）
- **并发处理**：concurrent.futures.ThreadPoolExecutor
- **数据处理**：Pandas, NumPy
- **可视化**：Matplotlib
- **日志系统**：Python logging 模块

## 注意事项

1. 本程序仅供学习和研究使用，不构成投资建议
2. 股票数据来源于公开信息，可能存在延迟
3. 使用并发功能时请注意网络带宽和系统资源
4. 建议在市场交易时间外运行程序，避免网络拥堵

## 更新日志

### v1.0.0 (2026-03-03)
- 初始版本发布
- 实现完整的 RSI 筛选功能
- 支持并发数据处理
- 提供图形化界面
- 自动依赖检测和安装

## 许可证

本程序仅供学习交流使用。

## 联系方式

如有问题，请查看日志文件或检查网络连接。
