"""调度服务核心"""
import asyncio
import signal
import sys
import io
from pathlib import Path
from loguru import logger

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .task_loader import TaskLoader
from .task_executor import TaskExecutor
from .models import TaskConfig


class SchedulerService:
    """调度服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.executor = TaskExecutor()
        self.loader = TaskLoader()
        self.running = True

        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _job_executed_listener(self, event):
        if event.exception:
            logger.error(f"任务 {event.job_id} 执行失败: {event.exception}")
        else:
            logger.info(f"任务 {event.job_id} 执行成功")

    def _signal_handler(self, signum, frame):
        logger.info(f"收到信号 {signum}，准备停止服务...")
        self.running = False
        if self.scheduler.running:
            self.scheduler.shutdown()
        sys.exit(0)

    async def _execute_task(self, task: TaskConfig):
        """执行任务"""
        logger.info("=" * 60)
        logger.info(f"开始执行任务: {task.name}")
        logger.info("=" * 60)

        for attempt in range(task.max_retries + 1):
            if attempt > 0:
                logger.info(f"重试第 {attempt} 次...")
                await asyncio.sleep(task.retry_delay)

            success = await self.executor.execute(task)
            if success:
                break

        logger.info("=" * 60)
        logger.info(f"任务执行完成: {task.name}")
        logger.info("=" * 60)

    def _parse_cron(self, cron_expr: str) -> tuple:
        """解析 Cron 表达式"""
        cron_parts = cron_expr.split()
        if len(cron_parts) != 5:
            raise ValueError(f"Cron 表达式格式错误: {cron_expr}")
        minute, hour, day, month, day_of_week = cron_parts
        return minute, hour, day, month, day_of_week

    def add_task(self, task: TaskConfig):
        """添加任务到调度器"""
        if not task.enabled:
            logger.info(f"任务 {task.id} 已禁用，跳过")
            return

        # 支持多个 cron 表达式
        cron_list = task.crons if task.crons else [task.cron]

        for idx, cron_expr in enumerate(cron_list):
            try:
                minute, hour, day, month, day_of_week = self._parse_cron(cron_expr)

                # 如果有多个 cron，给 job id 添加后缀
                job_id = task.id if len(cron_list) == 1 else f"{task.id}_{idx}"

                self.scheduler.add_job(
                    self._execute_task,
                    CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week),
                    id=job_id,
                    name=task.name,
                    args=[task]
                )

                logger.info(f"已添加任务: {task.name} ({cron_expr})")
            except ValueError as e:
                logger.error(f"任务 {task.id} 配置错误: {e}")

    def start(self):
        """启动调度服务"""
        tasks = self.loader.load_all()

        job_count = 0
        for task in tasks:
            cron_list = task.crons if task.crons else [task.cron]
            job_count += len(cron_list) if task.enabled else 0
            self.add_task(task)

        self.scheduler.start()
        logger.info("=" * 60)
        logger.info("Python Task Scheduler 已启动")
        logger.info(f"已加载 {len(tasks)} 个任务配置，共 {job_count} 个定时任务")
        logger.info("=" * 60)

        jobs = self.scheduler.get_jobs()
        for job in jobs:
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"任务 [{job.name}] 下次执行: {next_run}")

    async def run_forever(self):
        """保持服务运行"""
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止服务...")
            self.scheduler.shutdown()


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Python Task Scheduler")
    parser.add_argument("--tasks-dir", default="tasks", help="任务配置文件目录")
    parser.add_argument("--list", action="store_true", help="列出所有任务")

    args = parser.parse_args()

    logger.add("logs/scheduler.log", rotation="100 MB", retention="30 days")

    service = SchedulerService()
    service.loader.tasks_dir = Path(args.tasks_dir)

    if args.list:
        tasks = service.loader.load_all()
        print("\n" + "=" * 60)
        print("任务列表")
        print("=" * 60)
        for task in tasks:
            status = "启用" if task.enabled else "禁用"
            print(f"[{status}] {task.name} ({task.id})")
            cron_list = task.crons if task.crons else [task.cron]
            for cron in cron_list:
                print(f"  Cron: {cron}")
            print(f"  项目: {task.project_path}")
            print(f"  脚本: {task.script}")
            print()
        return

    service.start()
    await service.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
