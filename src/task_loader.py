"""任务加载器"""
import yaml
from pathlib import Path
from loguru import logger
from typing import List
from .models import TaskConfig


class TaskLoader:
    """任务加载器"""

    def __init__(self, tasks_dir: str = "tasks"):
        self.tasks_dir = Path(tasks_dir)

    def load_all(self) -> List[TaskConfig]:
        """加载所有任务配置"""
        if not self.tasks_dir.exists():
            logger.warning(f"任务目录不存在: {self.tasks_dir}")
            return []

        tasks = []
        for config_file in self.tasks_dir.glob("*.yaml"):
            try:
                task = self._load_config(config_file)
                if task:
                    tasks.append(task)
                    logger.info(f"加载任务配置: {config_file.name}")
            except Exception as e:
                logger.error(f"加载任务配置失败 {config_file}: {e}")

        logger.info(f"共加载 {len(tasks)} 个任务配置")
        return tasks

    def _load_config(self, config_file: Path) -> TaskConfig:
        """加载单个任务配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return TaskConfig(**data)
