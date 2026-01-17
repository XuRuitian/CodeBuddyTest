# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集 ttkbootstrap 主题文件
ttkbootstrap_datas = collect_data_files('ttkbootstrap', include_py_files=False)
# 收集 tkinter 数据文件（Tcl/Tk）
tkinter_datas = collect_data_files('tkinter')

# 合并数据文件
datas = ttkbootstrap_datas + tkinter_datas

# 收集隐藏导入
hiddenimports = []
hiddenimports += collect_submodules('akshare')
hiddenimports += collect_submodules('ttkbootstrap')
hiddenimports += collect_submodules('pandas')

a = Analysis(
    ['SelectionFunction.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SelectionFunction',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SelectionFunction',
)