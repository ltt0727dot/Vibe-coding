# 打包指南

## 环境要求

- Python 3.7+ (64-bit 推荐)
- PyInstaller >= 5.0
- 在项目的 requirements.txt 依赖已安装的前提下

## 打包步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 2. 执行打包

在 `build/` 目录下运行：

```bash
cd build
pyinstaller build.spec
```

生成的可执行文件在 `build/dist/CART_Killing_Analyzer.exe`

### 3. 简化打包命令（可选，不用 spec 文件）

```bash
cd src
pyinstaller --onefile --windowed \
  --name "CART_Killing_Analyzer" \
  --hidden-import "matplotlib.backends.backend_tkagg" \
  --hidden-import "tkinter.filedialog" \
  --hidden-import "tkinter.messagebox" \
  --hidden-import "tkinter.ttk" \
  main.py
```

## 常见问题

### Q: 打包后运行报错 "No module named matplotlib.backends.backend_tkagg"

在 spec 文件的 `hiddenimports` 中添加 `matplotlib.backends.backend_tkagg`

### Q: 打包后 .exe 文件很大（>100MB）

这是正常的。主要体积来自：
- matplotlib (~40MB)
- pandas (~30MB)
- Tkinter (~10MB)

可以考虑：
- 使用 `--onedir` 代替 `--onefile`（启动更快）
- 用 `pip install --no-deps` 精简依赖

### Q: 打包时中文文件名乱码

确保 Python 文件使用 UTF-8 编码，PyInstaller 会自动处理。

### Q: Windows 杀毒软件误报

单文件 .exe 有时会被误报，可以提交到杀软厂商白名单或使用 `--onedir` 模式。

### Q: 运行时找不到 msvcp140.dll

需要安装 [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## 交付物

打包完成后，交付以下内容：

1. `CART_Killing_Analyzer.exe` — 主程序
2. README.md — 用户说明
3. 示例数据文件
