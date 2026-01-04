# ContextCapture 顺序多格式生产脚本使用指南

## 简介
`test_cc_sequential.py` 是一个用于自动化 ContextCapture (CC) 建模流程的 Python 脚本。它能够自动创建项目、提交空三运算 (AT)，并按顺序生成多种格式的三维模型（OBJ, LAS, 3D Tiles）。

脚本采用了**顺序执行**策略，并支持**自适应分块 (Adaptive Tiling)**，有效控制内存使用，防止在处理大数据量时发生内存溢出。

## 环境要求
*   ContextCapture Master / Engine 已安装
*   Python 环境 (建议使用 CC 推荐的Python环境)
*   `ccmasterkernel` 模块可被导入

## 命令行参数

脚本支持通过命令行参数进行灵活配置：

| 参数 | 必选/可选 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `--photos` | **必选** | - | 照片所在的源文件夹路径。支持 jpg, tif, png 等格式。 |
| `--project` | **必选** | - | 项目输出的根文件夹路径。脚本将在此目录下创建 `.ccm` 项目文件和各个产物文件夹。 |
| `--memory` | 可选 | `16.0` | 目标内存使用量 (GB)。用于控制分块大小，建议设置为机器物理内存的 50%-70%。 |
| `--formats` | 可选 | 全部 | 指定要生产的格式列表。可选值: `OBJ`, `LAS`, `3DTiles`。多个值之间用空格分隔。 |

## 使用示例

请在命令行 (CMD 或 PowerShell) 中运行以下命令。

### 1. 基础用法 (推荐)
生成所有默认格式 (OBJ, LAS, 3D Tiles)，默认使用 16GB 内存限制。

```powershell
python test_cc_sequential.py --photos "D:\MyData\Mission_01\Images" --project "D:\Projects\Mission_01"
```

### 2. 指定输出格式
如果你只需要点云 (LAS) 和 OBJ 模型，不需要 3D Tiles：

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --formats LAS OBJ
```

### 3. 自定义内存限制
针对大内存机器 (例如 64GB 内存)，可以调高限制以加快处理速度 (例如设为 48GB)：

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --memory 48.0
```

针对小内存机器 (例如 16GB 内存)，建议调低限制 (例如 8GB)：

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --memory 8.0
```

### 4. 自定义 Engine 路径
如果你的 ContextCapture Master 安装在非默认目录，或者脚本无法自动找到 Engine，请手动指定路径：

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --engine-path "E:\Software\Bentley\ContextCapture Center\bin\CCEngine.exe"
```

## 输出结构

运行完成后，在您指定的 `--project` 目录下会自动生成以下结构：

```text
D:\Projects\Mission_01\         <-- 项目根目录
│  Mission_01.ccm              <-- CC 工程文件
│  cc_sequential.log           <-- 详细运行日志
│
├─ Production_OBJ\             <-- OBJ 模型输出目录
│      metadata.xml
│      ...
│
├─ Production_LAS\             <-- LAS 点云输出目录
│      cloud.las
│      ...
│
└─ Production_3DTiles\         <-- Cesium 3D Tiles 输出目录
       tileset.json
       ...
```

## 日志
脚本运行过程中，简要信息会显示在屏幕上。
详细的带时间戳的日志会保存在脚本同级目录下的 `cc_sequential.log` 文件中。
