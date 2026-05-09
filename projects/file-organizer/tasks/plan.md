# Plan: file-organizer v5.0 — LLM 智能分类增强

## Context

根据 SPEC.md v5.0，对 file-organizer 增加 LLM 智能分类，优先级顺序调整为：
**关键词 → LLM智能分类 → 内容分析 → 扩展名兜底**

---

## 依赖关系图

```
P1: keyword_rules ──命中──> return (done)
         │
         └──未命中
              │
              ├─ P2: LLMClassifier.classify()
              │        ├─ cache hit? ──> return cached
              │        └─ cache miss ─> batch queue → API call
              │              │
              │              └─ confidence >= threshold? ─NO─> P3
              │
              ├─ P3: ContentExtractor (文件内容关键词)
              │
              └─ P4: extension_rules (扩展名兜底)
```

---

## 新优先级 4 级分类流程

```
classify(filepath):
  1. result = classify_by_keyword_only(filepath)   # P1
     if result: return result

  2. result = llm_classifier.classify(...)          # P2
     if result and result.confidence >= threshold: return result

  3. result = _classify_by_content(filepath)         # P3
     if result: return result

  4. return classify_by_extension(filepath)          # P4 (兜底)
```

---

## Module 变更

| 文件 | 改动 | 行数 |
|------|------|------|
| `llm/llm_classifier.py` | 新建（替换 claude_classifier.py） | ~560 |
| `rules/classifier.py` | 扩展：classify_cascade() → 4级级联 | +63 |
| `organizer/file_organizer.py` | 集成级联分类 | +20 |
| `run.py` | 适配 FileOrganizer 接口 | +15 |
| `config.json` | 新增 `llm` 配置节 | +13 |

---

## 执行顺序

```
Step 1: llm/llm_classifier.py (MiniMax+DeepSeek + caching + batch) ✅
Step 2: rules/classifier.py (4级级联 classify_cascade) ✅
Step 3: organizer/file_organizer.py (集成 LLM + 级联) ✅
Step 4: run.py (适配 FileOrganizer 接口) ✅
Step 5: config.json (新增 llm 配置节) ✅
Step 6: tests/ (待实施)
Step 7: 验证 (待实施)
```

---

## Checkpoints

| 阶段 | 里程碑 |
|------|--------|
| CP1 | `from llm.llm_classifier import LLMClassifier` 无报错 |
| CP2 | `classify_cascade()` 4级级联顺序正确（keyword→LLM→content→extension）|
| CP3 | MiniMax / DeepSeek 均可调用 |
| CP4 | cache 命中率测试通过 |
| CP5 | batch 请求分组正确 |
| CP6 | `python run.py --preview` 回归正常 |
| CP7 | pytest 全部通过 |