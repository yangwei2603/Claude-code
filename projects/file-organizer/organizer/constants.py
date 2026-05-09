"""整理模块常量 — 魔法数字集中管理"""

from pathlib import Path

# 文件大小
BYTES_PER_MB = 1024 * 1024
DEFAULT_MAX_CONTENT_SIZE_MB = 10
DEFAULT_LARGE_FILE_THRESHOLD_MB = 100
FILE_HASH_CHUNK_SIZE = 65536

# 分类置信度阈值
CONFIDENCE_KEYWORD_MATCH = 0.9        # P1: 关键词精确命中
CONFIDENCE_BUSINESS_RULE = 0.8        # 业务领域规则命中
CONFIDENCE_LLM_CLASSIFY = 0.7         # P2: LLM 分类正常结果
CONFIDENCE_LLM_HIGH = 0.8             # P2: LLM 分类高置信度
CONFIDENCE_EXTENSION_FALLBACK = 0.3   # P4: 扩展名兜底

# LLM 默认配置
DEFAULT_LLM_MIN_CONFIDENCE = 0.6
DEFAULT_LLM_TIMEOUT = 30
DEFAULT_LLM_MAX_TOKENS = 500
DEFAULT_LLM_BATCH_SIZE = 10
DEFAULT_LLM_CACHE_SIZE = 1000
DEFAULT_LLM_TEMPERATURE = 0.1

# 调度
DEFAULT_WATCH_INTERVAL = 300  # 秒

# ========== 新增：路径和目录配置 ==========
DEFAULT_STATE_FILE = "state/organizer_state.json"
DEFAULT_LOG_DIR = "logs"
DEFAULT_ROLLBACK_DIR = "state/rollback"
DEFAULT_TEMPLATES_DIR = "templates"

# ========== 保护目录 ==========
PROTECTED_FOLDERS = {".svn", ".git", ".idea", "__pycache__", "node_modules", ".vscode", "logs", "state", ".venv", ".pytest_cache"}

# ========== 删除模式（正则） ==========
DEFAULT_DELETE_PATTERNS = [
    r"^~\$",           # Office 临时文件
    r"\.svn-base$",
    r"\.tmp$",
    r"\.temp$",
    r"^\.DS_Store$",
    r"^Thumbs\.db$",
]

# ========== 备份文件扩展名 ==========
BACKUP_EXTENSIONS = {".bak", ".backup"}

# ========== 日志配置 ==========
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"