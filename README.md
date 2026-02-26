# Python Task Scheduler

一个独立的 Python 定时任务调度服务，用于管理多个 Python 项目的定时任务。

## 特性

- 独立运行，不依赖具体项目
- 通过 YAML 配置文件定义任务
- 支持 Cron 表达式调度
- 自动激活虚拟环境
- 任务重试机制
- 完善的日志记录
- 可注册为 Windows 系统服务

## 安装

### 1. 安装依赖

```bash
cd F:\github\person_project\windows-schedule
uv sync
```

### 2. 下载 NSSM

1. 访问 https://nssm.cc/download
2. 下载最新版本
3. 解压并将 `nssm.exe` 添加到系统 PATH

### 3. 安装服务

```bash
scripts\install.bat
```

## 使用

### 添加任务

在 `tasks/` 目录创建 YAML 配置文件：

```yaml
id: "my_task"
name: "我的任务"
enabled: true
cron: "0 2 * * *"
project_path: "F:/projects/my-project"
script: "main.py"
args: []
```

### 管理任务

```bash
# 列出所有任务
python -m src.scheduler --list

# 查看日志
type logs\scheduler.log
```

### 管理服务

```bash
# 启动服务
nssm start PyTaskSched

# 停止服务
nssm stop PyTaskSched

# 重启服务
nssm restart PyTaskSched

# 查看状态
nssm status PyTaskSched

# 删除服务
nssm remove PyTaskSched confirm
```

## Cron 表达式说明

```
┌───────────── 分钟 (0 - 59)
│ ┌─────────── 小时 (0 - 23)
│ │ ┌───────── 日期 (1 - 31)
│ │ │ ┌─────── 月份 (1 - 12)
│ │ │ │ ┌───── 星期 (0 - 6, 0=周日)
│ │ │ │ │
* * * * *
```

常用示例：
- `0 2 * * *` - 每天凌晨 2 点
- `0 */6 * * *` - 每 6 小时
- `0 18 * * 1-5` - 周一到周五下午 6 点
- `*/30 * * * *` - 每 30 分钟

## 项目结构

```
windows-schedule/
├── src/
│   ├── __init__.py
│   ├── models.py           # 数据模型
│   ├── task_executor.py    # 任务执行器
│   ├── task_loader.py      # 任务加载器
│   └── scheduler.py        # 调度服务核心
├── tasks/                   # 任务配置目录
│   └── douying-collect.yaml
├── scripts/
│   ├── install.bat         # 安装服务
│   └── uninstall.bat       # 卸载服务
├── logs/                    # 日志目录
├── pyproject.toml
└── README.md
```

## License

MIT License
