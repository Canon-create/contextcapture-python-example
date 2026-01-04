# -*- coding: utf-8 -*-
"""
ContextCapture 顺序多格式生产脚本
支持 OBJ、LAS 点云、Cesium 3D Tiles 三种格式
使用分块处理 (Tiling) 控制内存
顺序执行避免内存不足
"""
import sys
import time
import os
import logging
from logging.handlers import RotatingFileHandler
import traceback
import argparse

# --- 日志配置 ---
# 日志文件名为 cc_sequential.log，位于脚本所在目录
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc_sequential.log')

logger = logging.getLogger('CC_Production')
logger.setLevel(logging.INFO)

# 1. RotatingFileHandler: 10MB 切割，保留 5 个备份
# maxBytes = 10 * 1024 * 1024 = 10485760 B
rf_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
rf_handler.setFormatter(file_formatter)
logger.addHandler(rf_handler)

# 2. StreamHandler: 输出到控制台
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(message)s'))  # 控制台输出保持原样，纯文本方便阅读
logger.addHandler(console_handler)
# ----------------

try:
    import ccmasterkernel

    logger.info("成功导入 ccmasterkernel 模块")
except ImportError:
    logger.error("错误: 无法导入 ccmasterkernel 模块。")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="ContextCapture 顺序多格式生产脚本")

    # 路径参数 (必须)
    parser.add_argument('--photos', required=True, help='照片所在目录路径')
    parser.add_argument('--project', required=True, help='项目输出目录路径')

    # 可选参数
    parser.add_argument('--memory', type=float, default=16.0, help='目标内存使用量 (GB)，默认 16.0')
    parser.add_argument('--formats', nargs='+', default=['OBJ', 'LAS', '3DTiles'],
                        choices=['OBJ', 'LAS', '3DTiles'],
                        help='指定要生产的格式 (默认全部): OBJ, LAS, 3DTiles')

    return parser.parse_args()


def main():
    args = parse_args()

    # 定义路径变量 (从 args 获取)
    project_dir = args.project
    # 自动根据目录名生成项目文件名
    project_name_base = os.path.basename(os.path.normpath(project_dir))
    project_file_path = os.path.join(project_dir, f"{project_name_base}.ccm")
    photos_dir = args.photos

    # 多格式输出目录
    production_obj_dir = os.path.join(project_dir, "Production_OBJ")
    production_las_dir = os.path.join(project_dir, "Production_LAS")
    production_3dtiles_dir = os.path.join(project_dir, "Production_3DTiles")

    logger.info("\n" + "=" * 60)
    logger.info("ContextCapture 顺序多格式自动化脚本 (CLI Mode)")
    logger.info("=" * 60)
    logger.info(f"项目文件路径: {project_file_path}")
    logger.info(f"照片目录:     {photos_dir}")
    logger.info(f"目标内存:     {args.memory} GB")

    # 确定要生产的格式
    formats_to_produce_list = []

    # 格式定义映射: Name -> (DriverName, OutputDir, Description)
    format_map = {
        'OBJ': ("OBJ", production_obj_dir, "OBJ 网格模型"),
        'LAS': ("LAS", production_las_dir, "LAS 点云"),
        '3DTiles': ("Cesium 3D Tiles", production_3dtiles_dir, "Cesium 3D Tiles")
    }

    req_formats = args.formats

    logger.info(f"计划生产格式: {', '.join(req_formats)}")

    # 构建 production list
    # 保持原有顺序: OBJ -> LAS -> 3DTiles (如果被选中)
    if 'OBJ' in req_formats:
        formats_to_produce_list.append(('OBJ', *format_map['OBJ']))
    if 'LAS' in req_formats:
        formats_to_produce_list.append(('LAS', *format_map['LAS']))
    if '3DTiles' in req_formats:
        formats_to_produce_list.append(('Cesium 3D Tiles', *format_map['3DTiles']))

    logger.info("\n输出位置预览:")
    for _, _, out_dir, desc in formats_to_produce_list:
        logger.info(f"  - {desc}: {out_dir}")

    logger.info("\n注意: 选中格式将依次执行，避免内存不足")
    logger.info("=" * 60 + "\n")

    # 确保项目目录存在
    if not os.path.exists(project_dir):
        try:
            os.makedirs(project_dir)
        except OSError as e:
            logger.error(f"错误: 无法创建项目目录 {project_dir}: {e}")
            return

    # 1. 创建并配置项目
    logger.info("正在创建项目...")
    project = ccmasterkernel.Project()
    project.setName(project_name_base)  # 使用目录名作为项目名
    project.setProjectFilePath(project_file_path)

    # 2. 创建区块并添加照片
    logger.info("正在创建初始区块...")
    block = ccmasterkernel.Block(project)
    project.addBlock(block)
    block.setName("InitialBlock")

    logger.info("正在添加照片...")
    photogroups = block.getPhotogroups()

    if os.path.exists(photos_dir):
        photo_files = [f for f in os.listdir(photos_dir)
                       if f.lower().endswith(('.jpg', '.jpeg', '.tif', '.tiff', '.png'))]
        if not photo_files:
            logger.warning(f"警告: 在 {photos_dir} 中未找到照片文件。")

        for f in photo_files:
            full_path = os.path.join(photos_dir, f)
            photogroups.addPhotoInAutoMode(full_path)
        logger.info(f"已尝试添加 {len(photo_files)} 张照片。")
    else:
        logger.error(f"错误: 照片目录 {photos_dir} 不存在。")
        return

    # 验证区块是否有效
    if not block.isReadyForAT():
        logger.error("错误: 区块未准备好进行 AT。")
        return

    # 保存项目
    logger.info("正在保存项目...")
    save_error = project.writeToFile()
    if not save_error.isNone():
        logger.error(f"保存项目失败: {save_error.message}")
        return
    logger.info("项目保存成功。")

    # 3. 空中三角测量 (AT)
    logger.info("\n准备空中三角测量 (AT) 区块...")
    block_at = ccmasterkernel.Block(project)
    project.addBlock(block_at)
    block_at.setName("AT_Block")
    block_at.setBlockTemplate(ccmasterkernel.BlockTemplate.Template_adjusted, block)

    # 保存更新后的项目
    logger.info("正在保存更新后的项目...")
    save_error = project.writeToFile()
    if not save_error.isNone():
        logger.error(f"保存项目失败: {save_error.message}")
        return

    logger.info("开始提交 AT 处理...")
    at = block_at.getAT()
    if at is None:
        logger.error("错误: 无法获取 AT 对象。")
        return

    # 提交 AT 处理
    submit_error = at.submitProcessing()
    if not submit_error.isNone():
        logger.error(f"AT 提交失败: {submit_error.message}")
        return

    # 监控 AT 任务
    if not monitor_job(at, "AT"):
        logger.error("AT 处理未成功完成，脚本终止。")
        return

    logger.info("AT 处理完成。\n")

    # 4. 重建 (Reconstruction) - 配置分块处理
    logger.info("=" * 60)
    logger.info("创建重建项目...")
    logger.info("=" * 60)

    reconstruction = ccmasterkernel.Reconstruction(block_at)
    block_at.addReconstruction(reconstruction)
    reconstruction.setName("Reconstruction_Sequential")

    # 配置重建设置
    logger.info("\n配置重建设置...")
    settings = reconstruction.getSettings()
    reconstruction.setSettings(settings)

    # 配置分块处理 (Tiling)
    logger.info("配置分块处理 (Tiling)...")
    tiling = reconstruction.getTiling()
    tiling.tilingMode = ccmasterkernel.TilingMode.TilingMode_adaptive
    tiling.targetMemoryUse = args.memory  # 使用命令行参数
    tiling.overlapRatio = 0.2
    tiling.discardEmptyTiles = True
    reconstruction.setTiling(tiling)

    logger.info(f"  - 模式: Adaptive (自动分块)")
    logger.info(f"  - 目标内存: {tiling.targetMemoryUse} GB")
    logger.info(f"  - 瓦片重叠率: {tiling.overlapRatio * 100}%")

    # 保存重建配置
    logger.info("\n保存重建配置...")
    save_error = project.writeToFile()
    if not save_error.isNone():
        logger.error(f"保存项目失败: {save_error.message}")
        return

    # 获取瓦片数量
    num_tiles = reconstruction.getNumInternalTiles()
    logger.info(f"\n重建包含 {num_tiles} 个瓦片")

    # 5. 顺序生产 - 依次执行每种格式
    logger.info("\n" + "=" * 60)
    logger.info("开始顺序生产（依次执行，避免内存不足）")
    logger.info("=" * 60)

    results = []

    # 遍历我们构建的格式列表
    for idx, (prod_name, driver_name, output_dir, description) in enumerate(formats_to_produce_list, 1):
        logger.info("\n" + "=" * 60)
        logger.info(f"第 {idx}/{len(formats_to_produce_list)} 步: 生产 {description}")
        logger.info("=" * 60)

        # 创建生产
        logger.info(f"\n配置 {description}...")
        production = ccmasterkernel.Production(reconstruction)
        reconstruction.addProduction(production)
        production.setName(f"Production_{prod_name}")
        production.setDriverName(driver_name)
        production.setDestination(output_dir)
        logger.info(f"  ✓ {description} 配置完成")

        # 保存项目
        save_error = project.writeToFile()
        if not save_error.isNone():
            logger.error(f"  ✗ 保存项目失败: {save_error.message}")
            results.append((description, False))
            continue

        # 添加所有瓦片任务
        logger.info(f"\n为 {description} 添加 {num_tiles} 个瓦片任务...")
        production_jobs = []
        try:
            for i in range(num_tiles):
                tile = reconstruction.getInternalTile(i)
                job = ccmasterkernel.TileProductionJob(production, tile)
                production.addProductionJob(job)
                production_jobs.append(job)
            logger.info(f"  ✓ 已添加 {num_tiles} 个瓦片任务")
        except Exception as e:
            logger.error(f"  ✗ 添加任务时出错: {e}")
            results.append((description, False))
            continue

        # 提交生产
        logger.info(f"\n提交 {description} 生产...")
        submit_error = production.submitProcessing()
        if not submit_error.isNone():
            logger.error(f"  ✗ 提交失败: {submit_error.message}")
            results.append((description, False))
            continue
        logger.info(f"  ✓ 提交成功")

        # 监控所有瓦片任务
        logger.info(f"\n监控 {description} 任务（{num_tiles} 个瓦片）...")
        all_tiles_success = True
        for tile_idx, job in enumerate(production_jobs):
            job_desc = f"{description} - 瓦片 {tile_idx}"
            if not monitor_job(job, job_desc):
                logger.error(f"  ✗ 瓦片 {tile_idx} 处理失败")
                all_tiles_success = False
                break  # 如果一个瓦片失败，停止监控后续瓦片
            else:
                logger.info(f"  ✓ 瓦片 {tile_idx} 处理成功")

        if all_tiles_success:
            logger.info(f"\n✓ {description} 所有瓦片处理成功！")
            logger.info(f"  输出位置: {output_dir}")
            results.append((description, True))
        else:
            logger.error(f"\n✗ {description} 处理失败")
            results.append((description, False))

    # 最终结果汇总
    logger.info("\n" + "=" * 60)
    logger.info("生产结果汇总")
    logger.info("=" * 60)

    for description, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        logger.info(f"  {status}: {description}")

    all_success = all(success for _, success in results)

    if all_success:
        logger.info("\n" + "=" * 60)
        logger.info("所有请求的格式生产成功完成！")
        logger.info("=" * 60)
    else:
        logger.error("\n部分格式生产失败，请检查日志获取详细信息。")


def monitor_job(job_object, job_name):
    """
    通用任务监控函数
    """
    previous_status = ccmasterkernel.JobStatus.Job_unknown

    while True:
        # 更新状态
        try:
            job_object.updateJobStatus()
        except AttributeError:
            pass

        status = job_object.getJobStatus()

        # 显示状态变化
        if status != previous_status:
            status_str = ccmasterkernel.jobStatusAsString(status)
            logger.info(f"    [{job_name}] {status_str}")
            previous_status = status

        # 检查是否结束
        if status in [ccmasterkernel.JobStatus.Job_completed,
                      ccmasterkernel.JobStatus.Job_failed,
                      ccmasterkernel.JobStatus.Job_cancelled]:
            break

        time.sleep(2)

    # 最终结果检查
    if status == ccmasterkernel.JobStatus.Job_completed:
        return True
    else:
        msg = job_object.getJobMessage()
        if msg:
            logger.error(f"    [{job_name}] 错误: {msg}")
        return False


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n用户中断脚本执行。")
    except Exception as e:
        logger.error(f"\n错误: {e}")
        logger.error("详细堆栈:", exc_info=True)

    # CLI 模式通常不需要最后 input() 暂停，除非是为了调试
    # logger.info("\n按 Enter 键退出...")
    # input()
