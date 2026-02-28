"""数据模型定义"""
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class TaskConfig:
    """任务配置"""
    id: str                      # 任务唯一标识
    name: str                    # 任务名称
    description: str = ""        # 任务描述
    enabled: bool = True         # 是否启用

    # 调度配置
    cron: str = ""               # Cron 表达式（单个）
    crons: Optional[List[str]] = None  # Cron 表达式列表（多个执行时间）

    # 执行配置
    project_path: str = ""       # 项目路径
    venv_path: str = ""          # 虚拟环境路径（可选，自动检测）
    script: str = ""             # 执行的脚本或模块
    args: List[str] = None       # 命令行参数
    working_dir: str = ""        # 工作目录（默认项目路径）

    # 环境配置
    env: Dict[str, str] = None   # 环境变量
    python_executable: str = ""  # Python 解释器路径（可选）

    # 重试配置
    max_retries: int = 0         # 最大重试次数
    retry_delay: int = 5         # 重试延迟（秒）

    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}
