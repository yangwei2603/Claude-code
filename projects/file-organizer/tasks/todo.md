# Todo: file-organizer v5.0 LLM 智能分类任务清单

## Task 1：LLM 分类器模块 ✅
- [x] 新建 `llm/llm_classifier.py`
- [x] MiniMax API 客户端
- [x] DeepSeek API 客户端（OpenAI 兼容）
- [x] LRU Prompt 缓存（LLMCache）
- [x] 批量请求（ThreadPoolExecutor）
- [x] 置信度阈值过滤
- [x] LLMConfig dataclass（from_env / from_json / to_dict）
- **Acceptance**: `from llm.llm_classifier import LLMClassifier` 无报错

## Task 2：规则分类器扩展 ✅
- [x] 新增 `classify_cascade()` 方法
- [x] 4级优先级级联实现
- [x] P1 关键词规则 → P2 LLM → P3 内容分析 → P4 扩展名兜底
- **Acceptance**: `classify_cascade()` 顺序正确

## Task 3：文件整理器集成 ✅
- [x] `organizer/file_organizer.py` 使用 `classify_cascade()`
- [x] 统计 rule_matched / llm_matched
- [x] 更新 `llm/__init__.py` 导出
- **Acceptance**: `python run.py --preview` 正常运行

## Task 4：Config 配置 ✅
- [x] `config.json` 新增 `llm` 配置节
- [x] provider / api_key / base_url / model / min_confidence / max_tokens / timeout / batch / cache
- **Acceptance**: 配置可被 LLMConfig.from_json() 正确加载

## Task 5：CLI 适配 ✅
- [x] `run.py` 适配 FileOrganizer 接口（organize() / setup_directories()）
- [x] 修复 print_stats() 兼容 OrganizerStats dataclass
- [x] 回滚/重复文件检测暂时回退（旧引擎功能）
- **Acceptance**: `python run.py --preview --source /tmp` 输出正确

## Task 6：单元测试（待实施）
- [ ] 新建 `tests/` 目录
- [ ] `tests/test_classifier.py` — 4级级联测试
- [ ] `tests/test_llm_classifier.py` — 缓存 + API 测试
- [ ] `tests/test_file_organizer.py` — 整理流程测试
- **Acceptance**: `pytest tests/ --tb=short` 全部通过

## Task 7：集成验证（待实施）
- [ ] `python run.py --preview` 端到端测试
- [ ] `python run.py --setup` 目录初始化测试
- [ ] LLM API 实际调用测试（如有 API key）
- **Acceptance**: 所有 CLI 命令正常