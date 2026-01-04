# ContextCapture Sequential Multi-format Production Script Usage Guide

## Introduction
`test_cc_sequential.py` is a Python script designed to automate the ContextCapture (CC) modeling workflow. It automatically creates a project, submits Aerotriangulation (AT), and sequentially generates 3D models in multiple formats (OBJ, LAS, 3D Tiles).

The script employs a **sequential execution** strategy and supports **Adaptive Tiling** to effectively manage memory usage, preventing out-of-memory errors when processing massive datasets.

## Requirements
*   ContextCapture Master / Engine installed.
*   Python environment (It is recommended to use the Python environment recommended by CC.).
*   `ccmasterkernel` module importable.

## Command Line Arguments

The script can be flexibly configured using command-line arguments:

| Argument | Required/Optional | Default | Description |
| :--- | :--- | :--- | :--- |
| `--photos` | **Required** | - | Path to the source folder containing photos. Supports jpg, tif, png, etc. |
| `--project` | **Required** | - | Root path for project output. The script will create the `.ccm` project file and production directories here. |
| `--memory` | Optional | `16.0` | Target memory usage (GB). Used to control tiling size. Recommended to set to 50%-70% of physical machine memory. |
| `--formats` | Optional | All | List of formats to produce. Options: `OBJ`, `LAS`, `3DTiles`. Separate multiple values with spaces. |

## Usage Examples

Run the following commands in your command line (CMD or PowerShell).

### 1. Basic Usage (Recommended)
Generate all default formats (OBJ, LAS, 3D Tiles) with a default 16GB memory limit.

```powershell
python test_cc_sequential.py --photos "D:\MyData\Mission_01\Images" --project "D:\Projects\Mission_01"
```

### 2. Specify Output Formats
If you only need Point Cloud (LAS) and OBJ models, and do not need 3D Tiles:

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --formats LAS OBJ
```

### 3. Custom Memory Limit
For high-memory workstations (e.g., 64GB RAM), you can increase the limit to speed up processing (e.g., set to 48GB):

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --memory 48.0
```

For low-memory machines (e.g., 16GB RAM), it is recommended to lower the limit (e.g., 8GB):

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --memory 8.0
```

### 4. Custom Engine Path
If your ContextCapture Master is installed in a non-default directory, or the script cannot automatically find the Engine, manually specify the path:

```powershell
python test_cc_sequential.py --photos "D:\Images" --project "D:\Output" --engine-path "E:\Software\Bentley\ContextCapture Center\bin\CCEngine.exe"
```

## Output Structure

Upon completion, the following structure will be automatically created in your specified `--project` directory:

```text
D:\Projects\Mission_01\         <-- Project Root Directory
│  Mission_01.ccm              <-- CC Project File
│  cc_sequential.log           <-- Detailed Execution Log
│
├─ Production_OBJ\             <-- OBJ Model Output Directory
│      metadata.xml
│      ...
│
├─ Production_LAS\             <-- LAS Point Cloud Output Directory
│      cloud.las
│      ...
│
└─ Production_3DTiles\         <-- Cesium 3D Tiles Output Directory
       tileset.json
       ...
```

## Logs
During execution, brief information is displayed on the screen.
Detailed, timestamped logs are saved in the `cc_sequential.log` file in the same directory as the script.

## Blog

For detailed usage instructions, please refer to the blog post:

**[Python-based Automated 3D Reconstruction Using the ContextCapture SDK](https://www.cnblogs.com/foury/p/19438102)**

> This repository provides example code only.  
> For full background information, environment setup, and parameter explanations, please refer to the blog.