"""
自定义异常模块
"""

class OrganizerError(Exception):
    """基础异常类"""
    pass

class ClassificationError(OrganizerError):
    """分类失败"""
    pass

class FileOperationError(OrganizerError):
    """文件操作失败（移动/复制/删除）"""
    pass

class RuleLoadError(OrganizerError):
    """规则加载失败"""
    pass

class StateError(OrganizerError):
    """状态管理失败"""
    pass

class ContentExtractionError(OrganizerError):
    """内容提取失败"""
    pass