"""任务执行器"""
import asyncio
import sys
from pathlib import Path
from loguru import logger
from .models import TaskConfig


class TaskExecutor:
    """任务执行器"""

    async def execute(self, task: TaskConfig) -> bool:
        """执行任务"""
        logger.info(f"执行任务: {task.name} ({task.id})")

        work_dir = Path(task.working_dir or task.project_path)
        if not work_dir.exists():
            logger.error(f"工作目录不存在: {work_dir}")
            return False

        python_exe = self._get_python_executable(task)

        cmd = [python_exe]
        if task.script.endswith('.py'):
            cmd.append(task.script)
        else:
            cmd.extend(["-m", task.script])
        cmd.extend(task.args)

        logger.info(f"执行命令: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(work_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_env(task)
            )

            stdout, stderr = await process.communicate()

            if stdout:
                logger.info(f"任务输出:\n{stdout.decode('utf-8', errors='replace')}")

            if stderr:
                logger.warning(f"任务错误输出:\n{stderr.decode('utf-8', errors='replace')}")

            success = process.returncode == 0
            logger.info(f"任务 {task.name} 执行{'成功' if success else '失败'}")
            return success

        except Exception as e:
            logger.error(f"执行任务 {task.name} 异常: {e}", exc_info=True)
            return False

    def _get_python_executable(self, task: TaskConfig) -> str:
        """获取 Python 解释器路径"""
        if task.python_executable:
            return task.python_executable

        if task.venv_path:
            venv_path = Path(task.venv_path)
            python_path = venv_path / ("Scripts/python.exe" if sys.platform == 'win32' else "bin/python")
            if python_path.exists():
                return str(python_path)

        project_path = Path(task.project_path)
        for venv_name in [".venv", "venv", "env"]:
            venv_path = project_path / venv_name
            python_path = venv_path / ("Scripts/python.exe" if sys.platform == 'win32' else "bin/python")
            if python_path.exists():
                return str(python_path)

        return sys.executable

    def _get_env(self, task: TaskConfig) -> dict:
        """获取环境变量"""
        import os
        env = os.environ.copy()
        env.update(task.env)
        return env
