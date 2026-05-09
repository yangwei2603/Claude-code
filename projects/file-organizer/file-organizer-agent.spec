# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 构建配置 - file-organizer-agent
支持 Windows 和 macOS 绿色打包 (onefile 模式)
"""

import sys
import os
from pathlib import Path

block_cipher = None

# 项目根目录 - 使用 __file__ 或当前目录
try:
    PROJECT_ROOT = Path(__file__).parent.resolve()
except NameError:
    PROJECT_ROOT = Path.cwd()

# 收集所有数据文件
datas = [
    (str(PROJECT_ROOT / 'rules'), 'rules'),
    (str(PROJECT_ROOT / 'templates'), 'templates'),
    (str(PROJECT_ROOT / 'web'), 'web'),
    (str(PROJECT_ROOT / 'config.json'), '.'),
    (str(PROJECT_ROOT / 'config.yaml'), '.'),
]

# 收集所有子模块（避免隐藏导入问题）
hiddenimports = [
    # Flask 相关
    'flask', 'flask_cors', 'flask_cors.extension',
    # YAML
    'yaml', '_yaml',
    # 文档处理
    'docx', 'docx.table', 'docx.text.paragraph', 'docx.oxml.text.paragraph',
    'docx.oxml', 'docx.oxml.ns', 'docx.oxml.shape',
    'PyPDF2', 'PyPDF2._page', 'PyPDF2.reader', 'PyPDF2.filter',
    'openpyxl', 'openpyxl.workbook', 'openpyxl.worksheet', 'openpyxl.cell',
    'pptx', 'pptx.presentation', 'pptx.util', 'pptx.shapes',
    # 文本处理
    'striprtf',
    # 项目模块
    'organizer', 'organizer.file_organizer', 'organizer.content_extractor',
    'rules', 'rules.rule_loader', 'rules.classifier',
    'task_manager', 'scheduler', 'web',
    'llm', 'llm.llm_classifier',
    # LLM providers (MiniMaxClient/DeepSeekClient are inline in llm_classifier.py)
    # 注意：llm.minimax_client 和 llm.deepseek_client 不是独立模块，不要单独引用
    # 确保 json 模块被正确收集
    'json',
    'encodings',
]

# Windows 特定配置
if sys.platform == 'win32':
    exe_name = 'FileOrganizerAgent.exe'
    exe_config = {
        'name': exe_name,
        'debug': False,
        'bootloader_ignore_signals': False,
        'strip': False,
        'upx': False,
        'console': False,
        'disable_windowed_traceback': False,
        'argv_emulation': False,
        'target_arch': None,
        'codesign_identity': None,
        'entitlements_file': None,
        'icon': None,
    }
# macOS 特定配置
else:
    exe_name = 'FileOrganizerAgent'
    exe_config = {
        'name': exe_name,
        'debug': False,
        'bootloader_ignore_signals': False,
        'strip': False,
        'upx': False,
        'console': False,
        'disable_windowed_traceback': False,
        'argv_emulation': True,
        'target_arch': None,
        'codesign_identity': None,
        'entitlements_file': None,
        'icon': None,
    }

a = Analysis(
    [str(PROJECT_ROOT / 'run.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'PIL', 'cv2', 'torch', 'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Onefile 模式：生成单一可执行文件
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False,
    **exe_config
)
