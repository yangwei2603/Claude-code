#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件整理 Agent — Web 管理界面 API 服务
提供 RESTful 接口供前端调用，管理任务和执行整理操作。

启动方式：
  python run.py --web
  python run.py --web --port 5001

依赖：
  pip install flask flask-cors
"""

import os
import sys
import json
import logging
import threading
from pathlib import Path
from datetime import datetime

# 确保 agent 目录在路径中
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from task_manager import TaskManager
from organizer import FileOrganizer, get_default_rules, load_rules

logger = logging.getLogger("web_api")


app = Flask(__name__, static_folder="web")
CORS(app)

# 全局实例
task_mgr = TaskManager(agent_dir=AGENT_DIR)
running_tasks = {}  # task_id -> {"thread": Thread, "status": str, "stats": dict}

# ============================================================
# API 认证配置
# ============================================================
_config_path = AGENT_DIR / "config.json"
_api_key = os.environ.get("FILE_ORGANIZER_API_KEY", "")
_api_auth_enabled = True

if _config_path.exists():
    try:
        _cfg = json.loads(_config_path.read_text(encoding="utf-8"))
        _api_key = _cfg.get("api_key", _api_key) or os.environ.get("FILE_ORGANIZER_API_KEY", "")
        _api_auth_enabled = _cfg.get("api_auth_enabled", True)
    except Exception:
        pass

def _check_api_key():
    """验证 API Key，返回 (authorized: bool, error_response)"""
    if not _api_auth_enabled:
        return True, None
    if not _api_key:
        # 未配置密钥时跳过验证（仅在开发环境）
        return True, None
    provided = request.headers.get("X-API-Key", "")
    if not provided:
        return False, jsonify({"success": False, "error": "缺少 API Key，请通过 X-API-Key header 提供"}), 401
    if provided != _api_key:
        return False, jsonify({"success": False, "error": "API Key 无效"}), 401
    return True, None

@app.before_request
def _require_api_key():
    """所有 /api/* 端点需要 API Key 认证"""
    if not request.path.startswith("/api/"):
        return None
    authorized, err = _check_api_key()
    if not authorized:
        return err


# ============================================================
# 首页路由 — 返回前端 SPA
# ============================================================
@app.route("/")
def index():
    return send_from_directory(AGENT_DIR / "web", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(AGENT_DIR / "web", path)


# ============================================================
# 任务管理 API
# ============================================================

@app.route("/api/tasks", methods=["GET"])
def api_list_tasks():
    """获取任务列表"""
    tasks = task_mgr.list_tasks()
    # 补充运行状态
    for t in tasks:
        tid = t["id"]
        if tid in running_tasks:
            t["running"] = True
            t["run_status"] = running_tasks[tid]["status"]
        else:
            t["running"] = False
    return jsonify({"success": True, "data": tasks})


@app.route("/api/tasks/<task_id>", methods=["GET"])
def api_get_task(task_id):
    """获取单个任务详情"""
    task = task_mgr.get_task(task_id)
    if not task:
        return jsonify({"success": False, "error": f"任务 {task_id} 不存在"}), 404
    if task_id in running_tasks:
        task["running"] = True
        task["run_status"] = running_tasks[task_id]["status"]
    else:
        task["running"] = False
    # 隐藏敏感信息
    return jsonify({"success": True, "data": task})


@app.route("/api/tasks", methods=["POST"])
def api_create_task():
    """创建新任务"""
    data = request.get_json(silent=True) or {}
    try:
        task = task_mgr.create_task(data)
        return jsonify({"success": True, "data": task}), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"创建失败: {e}"}), 500


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def api_update_task(task_id):
    """更新任务配置"""
    data = request.get_json(silent=True) or {}
    # 不允许通过 API 更改 id 和 created_at
    data.pop("id", None)
    data.pop("created_at", None)
    task = task_mgr.update_task(task_id, data)
    if not task:
        return jsonify({"success": False, "error": f"任务 {task_id} 不存在"}), 404
    return jsonify({"success": True, "data": task})


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    """删除任务"""
    # 如果任务正在运行，不允许删除
    if task_id in running_tasks:
        return jsonify({"success": False, "error": "任务正在运行，请先停止"}), 409
    ok = task_mgr.delete_task(task_id)
    if not ok:
        return jsonify({"success": False, "error": f"任务 {task_id} 不存在"}), 404
    return jsonify({"success": True, "message": "已删除"})


@app.route("/api/tasks/<task_id>/toggle", methods=["POST"])
def api_toggle_task(task_id):
    """切换启用/禁用"""
    task = task_mgr.toggle_task(task_id)
    if not task:
        return jsonify({"success": False, "error": f"任务 {task_id} 不存在"}), 404
    return jsonify({"success": True, "data": task})


@app.route("/api/tasks/<task_id>/export", methods=["GET"])
def api_export_task(task_id):
    """导出任务配置为 JSON"""
    result = task_mgr.export_task(task_id)
    if not result:
        return jsonify({"success": False, "error": f"任务 {task_id} 不存在"}), 404
    from flask import Response
    return Response(
        result,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}.json"}
    )


@app.route("/api/tasks/import", methods=["POST"])
def api_import_task():
    """从 JSON 导入任务"""
    data = request.get_data(as_text=True)
    if not data:
        return jsonify({"success": False, "error": "请求体不能为空"}), 400
    try:
        task = task_mgr.import_task(data)
        return jsonify({"success": True, "data": task}), 201
    except Exception as e:
        return jsonify({"success": False, "error": f"导入失败: {e}"}), 400


# ============================================================
# 执行控制 API
# ============================================================

def _run_organize(task_id, mode="preview"):
    """
    后台线程：执行整理任务。
    mode = "preview" | "execute" | "setup" | "rollback"
    """
    task = task_mgr.get_task(task_id)
    if not task:
        running_tasks[task_id] = {"thread": None, "status": "error: 任务不存在", "stats": {}}
        return

    config = dict(task)
    # setup/rollback/execute 模式不应该是 dry_run；只有 preview 模式是
    config["dry_run"] = (mode == "preview")

    running_tasks[task_id] = {
        "thread": None,
        "status": "running",
        "stats": {},
        "logs": [],
        "started_at": datetime.now().isoformat(),
    }

    try:
        organizer = FileOrganizer(
            source_dir=config["source_dir"],
            target_dir=config.get("target_dir") or None,
            dry_run=config.get("dry_run", True),
            keep_original=config.get("keep_original", False),
            scan_days=config.get("scan_days", 7),
            large_file_threshold_mb=config.get("large_file_threshold_mb", 100),
        )

        if mode == "setup":
            organizer.setup_directories()
            status = "setup_done"
        elif mode == "rollback":
            organizer.rollback_last_session()
            status = "rollback_done"
        elif mode == "duplicates":
            organizer.handle_duplicates()
            status = "duplicates_done"
        else:
            organizer.organize(incremental=True)
            status = "preview_done" if mode == "preview" else "executed"

        running_tasks[task_id]["status"] = status
        running_tasks[task_id]["stats"] = organizer.stats
        running_tasks[task_id]["logs"] = organizer.session_logs[-50:]  # 最近50条日志
        running_tasks[task_id]["unmatched_files"] = organizer.unmatched_files[:50]  # 未匹配文件

        task_mgr.update_run_status(task_id, status, organizer.stats)

    except Exception as e:
        running_tasks[task_id]["status"] = f"error: {e}"
        task_mgr.update_run_status(task_id, f"error: {e}")


@app.route("/api/tasks/<task_id>/preview", methods=["POST"])
def api_preview(task_id):
    """预览模式（不移动文件）"""
    if task_id in running_tasks:
        return jsonify({"success": False, "error": "任务正在运行中"}), 409
    t = threading.Thread(target=_run_organize, args=(task_id, "preview"), daemon=True)
    running_tasks[task_id] = {"thread": t, "status": "starting", "stats": {}}
    t.start()
    return jsonify({"success": True, "message": "预览任务已开始"})


@app.route("/api/tasks/<task_id>/execute", methods=["POST"])
def api_execute(task_id):
    """执行整理（实际移动文件）"""
    if task_id in running_tasks:
        return jsonify({"success": False, "error": "任务正在运行中"}), 409
    t = threading.Thread(target=_run_organize, args=(task_id, "execute"), daemon=True)
    running_tasks[task_id] = {"thread": t, "status": "starting", "stats": {}}
    t.start()
    return jsonify({"success": True, "message": "整理任务已开始（注意：会实际移动文件！）"})


@app.route("/api/tasks/<task_id>/setup", methods=["POST"])
def api_setup_dirs(task_id):
    """初始化目录结构"""
    if task_id in running_tasks:
        return jsonify({"success": False, "error": "任务正在运行中"}), 409
    t = threading.Thread(target=_run_organize, args=(task_id, "setup"), daemon=True)
    running_tasks[task_id] = {"thread": t, "status": "starting", "stats": {}}
    t.start()
    return jsonify({"success": True, "message": "目录结构初始化已开始"})


@app.route("/api/tasks/<task_id>/rollback", methods=["POST"])
def api_rollback(task_id):
    """回滚最后一次操作"""
    if task_id in running_tasks:
        return jsonify({"success": False, "error": "任务正在运行中"}), 409
    t = threading.Thread(target=_run_organize, args=(task_id, "rollback"), daemon=True)
    running_tasks[task_id] = {"thread": t, "status": "starting", "stats": {}}
    t.start()
    return jsonify({"success": True, "message": "回滚操作已开始"})


@app.route("/api/tasks/<task_id>/duplicates", methods=["POST"])
def api_duplicates(task_id):
    """检测重复文件"""
    if task_id in running_tasks:
        return jsonify({"success": False, "error": "任务正在运行中"}), 409
    t = threading.Thread(target=_run_organize, args=(task_id, "duplicates"), daemon=True)
    running_tasks[task_id] = {"thread": t, "status": "starting", "stats": {}}
    t.start()
    return jsonify({"success": True, "message": "重复检测已开始"})


@app.route("/api/tasks/<task_id>/status", methods=["GET"])
def api_run_status(task_id):
    """查询当前运行状态"""
    if task_id not in running_tasks:
        return jsonify({"success": True, "data": {"running": False}})
    info = running_tasks[task_id]
    # 检查线程是否已完成但状态未更新
    if info.get("thread") and not info["thread"].is_alive():
        if info["status"] == "running" or info["status"] == "starting":
            info["status"] = "completed"
    # 计算已运行时长（秒）
    elapsed_seconds = 0
    if info.get("started_at"):
        try:
            started = datetime.fromisoformat(info["started_at"])
            elapsed_seconds = int((datetime.now() - started).total_seconds())
        except Exception as e:
            logger.warning(f"计算运行时间失败: {e}")
    return jsonify({
        "success": True,
        "data": {
            "running": info.get("thread") and info["thread"].is_alive(),
            "status": info.get("status"),
            "stats": info.get("stats"),
            "logs": info.get("logs", []),
            "unmatched_files": info.get("unmatched_files", []),
            "started_at": info.get("started_at"),
            "elapsed_seconds": elapsed_seconds,
        }
    })


# ============================================================
# 规则 & 模板 API
# ============================================================

@app.route("/api/templates", methods=["GET"])
def api_list_templates():
    """列出规则模板"""
    templates = task_mgr.list_templates()
    return jsonify({"success": True, "data": templates})


@app.route("/api/templates/<filename>", methods=["GET"])
def api_get_template(filename):
    """获取模板详情"""
    template = task_mgr.get_template(filename)
    if not template:
        return jsonify({"success": False, "error": f"模板 {filename} 不存在"}), 404
    return jsonify({"success": True, "data": template})


@app.route("/api/templates", methods=["POST"])
def api_create_template():
    """创建自定义模板"""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    rules = data.get("rules", {})
    if not name:
        return jsonify({"success": False, "error": "模板名称不能为空"}), 400
    try:
        filename = task_mgr.create_template(name, rules)
        return jsonify({"success": True, "data": {"filename": filename}}), 201
    except PermissionError as e:
        return jsonify({"success": False, "error": str(e)}), 403
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/templates/<filename>", methods=["DELETE"])
def api_delete_template(filename):
    """删除自定义模板"""
    try:
        ok = task_mgr.delete_template(filename)
        if not ok:
            return jsonify({"success": False, "error": f"模板 {filename} 不存在或无法删除"}), 404
        return jsonify({"success": True})
    except PermissionError as e:
        return jsonify({"success": False, "error": str(e)}), 403


@app.route("/api/templates/<filename>", methods=["PUT"])
def api_update_template(filename):
    """更新规则模板"""
    data = request.get_json(silent=True) or {}
    try:
        template = task_mgr.update_template(filename, data)
        if not template:
            return jsonify({"success": False, "error": f"模板 {filename} 不存在或无法更新"}), 404
        return jsonify({"success": True, "data": template})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"更新失败: {e}"}), 500


@app.route("/api/templates/upload", methods=["POST"])
def api_upload_template():
    """上传规则文件（支持 .json / .md / .txt）"""
    # 检查是否有上传的文件
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未找到上传的文件，请使用 multipart/form-data 的 'file' 字段"}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"success": False, "error": "文件名为空"}), 400

    # 安全检查文件扩展名
    allowed_exts = {".json", ".md", ".txt"}
    ext = Path(uploaded.filename).suffix.lower()
    if ext not in allowed_exts:
        return jsonify({
            "success": False,
            "error": f"不支持的文件格式: {ext}，仅允许: {', '.join(allowed_exts)}"
        }), 400

    # 文件大小限制（2MB）
    content = uploaded.read()
    if len(content) > 2 * 1024 * 1024:
        return jsonify({"success": False, "error": "文件过大，限制 2MB 以内"}), 400

    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text_content = content.decode("gbk")
        except UnicodeDecodeError:
            return jsonify({"success": False, "error": "文件编码不支持，请使用 UTF-8 或 GBK"}), 400

    try:
        result = task_mgr.upload_template_file(uploaded.filename, text_content)
        return jsonify({"success": True, "data": result}), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"上传处理失败: {e}"}), 500


@app.route("/api/rules/default", methods=["GET"])
def api_default_rules():
    """获取默认规则（内置）"""
    return jsonify({"success": True, "data": get_default_rules()})


@app.route("/api/browse", methods=["GET"])
def api_browse():
    """
    浏览目录树（供前端目录选择器使用）。
    path 为空 → 返回平台根目录或用户主目录
    path 有值   → 返回该目录下的子目录列表
    """
    path_str = request.args.get("path", "").strip()

    if not path_str:
        # 返回平台适当的起始目录（macOS/Linux 用 /，Windows 用盘符）
        import os, platform
        try:
            if platform.system() == "Windows":
                drives = []
                for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    drive = Path(f"{letter}:\\")
                    if drive.exists():
                        drives.append({"name": f"{letter}:", "path": str(drive), "is_dir": True})
                return jsonify({"success": True, "data": {"current": "", "items": drives}})
            else:
                # Unix-like: 返回根目录和用户主目录
                home = Path(os.path.expanduser("~"))
                root = Path("/")
                items = []
                if home.exists() and home != root:
                    items.append({"name": "~", "path": str(home), "is_dir": True})
                items.append({"name": "/", "path": "/", "is_dir": True})
                return jsonify({"success": True, "data": {"current": "", "items": items}})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        # 使用 pathlib 处理路径（跨平台兼容）
        p = Path(path_str)
        if not p.exists() or not p.is_dir():
            return jsonify({"success": False, "error": "目录不存在或不可访问"}), 400

        items = []
        try:
            for child in sorted(p.iterdir()):
                if child.is_dir():
                    try:
                        items.append({
                            "name": child.name,
                            "path": str(child),
                            "is_dir": True,
                        })
                    except PermissionError:
                        pass
        except PermissionError:
            return jsonify({"success": False, "error": "无权限访问该目录"}), 403
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

        return jsonify({"success": True, "data": {"current": str(p), "items": items}})


@app.route("/api/validate/path", methods=["POST"])
def api_validate_path():
    """验证目录路径是否可用"""
    data = request.get_json(silent=True) or {}
    path_str = data.get("path", "")
    result = TaskManager.validate_source_dir(path_str)
    return jsonify({"success": True, "data": result})


@app.route("/api/classify/preview", methods=["POST"])
def api_classify_preview():
    """对指定文件进行分类预览（不创建任务，仅测试规则效果）"""
    data = request.get_json(silent=True) or {}
    filepath = data.get("filepath")
    task_id = data.get("task_id")
    rules_override = data.get("rules")

    if task_id:
        task = task_mgr.get_task(task_id)
        if not task:
            return jsonify({"success": False, "error": f"任务 {task_id} 不存在"}), 404
        config = dict(task)
    else:
        config = {
            "source_dir": str(Path.home()),
            "dry_run": True,
            "delete_patterns": [],
        }

    if rules_override:
        config["rules"] = rules_override

    try:
        organizer = FileOrganizer(
            source_dir=config["source_dir"],
            target_dir=config.get("target_dir") or None,
            dry_run=True,
        )
        result = organizer.preview_classify(filepath)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# 日志 & 统计 API
# ============================================================

@app.route("/api/logs", methods=["GET"])
def api_list_logs():
    """列出现有日志文件（递归扫描子目录）"""
    log_dir = AGENT_DIR / "logs"
    logs = []
    if log_dir.exists():
        # 递归扫描所有文件，按修改时间倒序，最多取 50 条
        all_files = sorted(log_dir.rglob("*.*"), key=lambda f: f.stat().st_mtime, reverse=True)[:50]
        for f in all_files:
            if f.is_file():  # 排除目录
                # 计算相对于 logs/ 的路径作为 name
                rel_name = str(f.relative_to(log_dir))
                logs.append({
                    "name": rel_name,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "mtime": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
    return jsonify({"success": True, "data": logs})


@app.route("/api/logs/<path:log_name>", methods=["GET"])
def api_get_log(log_name):
    """读取日志内容 — 支持子目录路径，带编码容错"""
    import urllib.parse
    # URL decode（前端用 encodeURIComponent 传文件名）
    log_name = urllib.parse.unquote(log_name)

    # 安全检查：防止路径穿越
    log_path = (AGENT_DIR / "logs" / log_name).resolve()
    if not log_path.is_relative_to(AGENT_DIR / "logs"):
        return jsonify({"success": False, "error": "非法日志路径"}), 403
    if not log_path.is_file():
        return jsonify({"success": False, "error": f"日志文件不存在: {log_name}"}), 404

    # 尝试多种编码读取
    encodings = ["utf-8", "gbk", "latin-1"]
    content = None
    last_err = None
    for enc in encodings:
        try:
            content = log_path.read_text(encoding=enc)
            break
        except (UnicodeDecodeError, Exception) as e:
            last_err = e
            continue

    if content is None:
        return jsonify({
            "success": False,
            "error": f"日志文件编码无法识别: {last_err}"
        }), 500

    # 大文件截断（超过 2MB 只返回末尾部分）
    if len(content) > 2 * 1024 * 1024:
        content = (
            f"[... 文件过大 ({len(content) // 1024}KB)，仅显示末尾 1MB ...]\n\n"
            + content[-1 * 1024 * 1024:]
        )

    return jsonify({"success": True, "data": {"content": content}})


@app.route("/api/stats/summary", methods=["GET"])
def api_stats_summary():
    """全局统计摘要"""
    return jsonify({
        "success": True,
        "data": {
            "total_tasks": len(task_mgr.list_tasks()),
            "active_tasks": len([t for t in task_mgr.list_tasks() if t.get("enabled")]),
            "running_count": len(running_tasks),
            "templates_count": len(task_mgr.list_templates()),
        }
    })


# ============================================================
# LLM 配置 API
# ============================================================

def _load_llm_config() -> dict:
    """从 config.json 加载 LLM 配置"""
    config_path = AGENT_DIR / "config.json"
    try:
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return data.get("llm", {}) or {}
    except Exception as e:
        logger.warning(f"读取 LLM 配置失败: {e}")
    return {}


def _save_llm_config(llm_config: dict) -> bool:
    """保存 LLM 配置到 config.json"""
    config_path = AGENT_DIR / "config.json"
    try:
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
        else:
            data = {}
        data["llm"] = llm_config
        config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"保存 LLM 配置失败: {e}")
        return False


@app.route("/api/llm/config", methods=["GET"])
def api_llm_get_config():
    """获取当前 LLM 配置（不返回 api_key 明文）"""
    from llm.llm_classifier import LLMConfig
    llm_data = _load_llm_config()
    cfg = LLMConfig.from_json(llm_data)
    d = cfg.to_dict()
    d["has_api_key"] = bool(cfg.api_key)
    d["api_key_masked"] = "*" * max(len(cfg.api_key) - 4, 4) + cfg.api_key[-4:] if cfg.api_key else ""
    return jsonify({"success": True, "data": d})


@app.route("/api/llm/config", methods=["PUT"])
def api_llm_update_config():
    """更新 LLM 配置"""
    from llm.llm_classifier import LLMConfig
    try:
        body = request.get_json()
        if not body:
            return jsonify({"success": False, "error": "请求体不能为空"}), 400

        # 合并现有配置
        current = _load_llm_config()
        current.update({
            "provider": body.get("provider", current.get("provider", "deepseek")),
            "api_key": body.get("api_key", current.get("api_key", "")),
            "base_url": body.get("base_url", current.get("base_url", "")),
            "model": body.get("model", current.get("model", "")),
            "min_confidence": float(body.get("min_confidence", 0.6)),
            "max_tokens": int(body.get("max_tokens", 500)),
            "timeout_seconds": int(body.get("timeout_seconds", 30)),
            "max_batch_size": int(body.get("max_batch_size", 10)),
            "enable_cache": bool(body.get("enable_cache", True)),
            "cache_max_size": int(body.get("cache_max_size", 1000)),
        })

        if _save_llm_config(current):
            return jsonify({"success": True, "data": LLMConfig.from_json(current).to_dict()})
        else:
            return jsonify({"success": False, "error": "保存配置失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/llm/test", methods=["POST"])
def api_llm_test_connection():
    """测试 LLM 连接"""
    from llm.llm_classifier import LLMConfig
    try:
        body = request.get_json() or {}
        # 使用请求中的配置或当前保存的配置
        if body.get("api_key"):
            llm_data = _load_llm_config()
            llm_data.update(body)
        else:
            llm_data = _load_llm_config()

        if not llm_data.get("api_key"):
            return jsonify({"success": False, "error": "API Key 不能为空"}), 400

        cfg = LLMConfig.from_json(llm_data)
        from llm.llm_classifier import LLMClassifier
        classifier = LLMClassifier(config=cfg)

        if not classifier.is_available():
            return jsonify({"success": False, "error": f"无法初始化 {cfg.provider} 客户端"}), 400

        # 用一个简单文件名测试调用
        try:
            result = classifier.classify(filename="测试文件.txt")
            return jsonify({
                "success": True,
                "data": {
                    "provider": cfg.provider,
                    "model": cfg.model,
                    "available": True,
                    "result": result.target_path if result else None
                }
            })
        except Exception as e:
            return jsonify({"success": False, "error": f"调用失败: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# 启动入口
# ============================================================

def run_web(host="0.0.0.0", port=5000, debug=False):
    """启动 Web 服务"""
    print(f"""
╔══════════════════════════════════════════╗
║     文件整理 Agent - Web 管理界面         ║
╠══════════════════════════════════════════╣
║  地址 : http://{host}:{port}              ║
║  任务目录 : {str(task_mgr.tasks_dir):<28} ║
║  模板目录 : {str(task_mgr.templates_dir):<27} ║
╚══════════════════════════════════════════╝
    """)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Web 管理服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=5000, help="端口号")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()
    run_web(args.host, args.port, args.debug)
