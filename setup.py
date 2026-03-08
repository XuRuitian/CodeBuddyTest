# -*- coding: utf-8 -*-
"""
依赖包自动安装脚本
"""

import subprocess
import sys

PACKAGES = [
    'akshare',
    'pandas', 
    'numpy',
    'matplotlib',
    'tqdm'
]

def check_python():
    """检查 Python 环境"""
    print("=" * 60)
    print("A 股市场 RSI 筛选工具 - 依赖包安装")
    print("=" * 60)
    print()
    print(f"Python 版本：{sys.version}")
    print(f"Python 路径：{sys.executable}")
    print()
    return True

def check_package(package):
    """检查包是否已安装"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def install_package(package):
    """安装单个包"""
    print(f"正在安装 {package}...")
    try:
        cmd = [
            sys.executable, 
            "-m", 
            "pip", 
            "install", 
            package,
            "-i", 
            "https://pypi.tuna.tsinghua.edu.cn/simple"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✓ {package} 安装成功")
            return True
        else:
            print(f"  ✗ {package} 安装失败")
            if result.stderr:
                print(f"  错误：{result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ {package} 安装出错：{str(e)}")
        return False

def main():
    """主函数"""
    if not check_python():
        input("按回车键退出...")
        return
    
    # 检查已安装的包
    print("检查已安装的包...")
    installed = []
    missing = []
    
    for package in PACKAGES:
        if check_package(package):
            installed.append(package)
            print(f"  ✓ {package} 已安装")
        else:
            missing.append(package)
            print(f"  ✗ {package} 未安装")
    
    print()
    
    if not missing:
        print("✓ 所有依赖包已安装！")
        print()
        print("现在可以运行主程序：python rsi_scanner.py")
        input("按回车键退出...")
        return
    
    # 安装缺失的包
    print(f"需要安装 {len(missing)} 个包：{', '.join(missing)}")
    print()
    print("开始安装...")
    print()
    
    success_count = 0
    for package in missing:
        if install_package(package):
            success_count += 1
        print()
    
    # 总结
    print("=" * 60)
    print("安装完成")
    print("=" * 60)
    print()
    print(f"成功：{success_count}/{len(missing)}")
    
    if success_count == len(missing):
        print()
        print("✓ 所有包安装成功！")
        print()
        print("下一步:")
        print("  运行 python rsi_scanner.py 启动程序")
    else:
        print()
        print("✗ 部分包安装失败，请检查网络连接或手动安装")
        print()
        print("手动安装命令:")
        for package in missing:
            print(f"  pip install {package}")
    
    print()
    input("按回车键退出...")

if __name__ == "__main__":
    main()
