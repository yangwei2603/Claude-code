"""
测试 FileOrganizer 文件整理器
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from organizer.file_organizer import FileOrganizer, OrganizerStats


class TestFileOrganizer:
    """测试 FileOrganizer 核心功能"""

    def setup_method(self):
        self.test_dir = Path("/tmp/test_file_organizer")
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_organize_empty_dir(self):
        """空目录扫描"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        stats = organizer.organize(incremental=False)
        assert stats.scanned == 0

    def test_organize_single_file(self):
        """单文件扫描"""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("hello")

        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        stats = organizer.organize(incremental=False)

        assert stats.scanned == 1
        assert stats.organized == 1

    def test_organize_stats_dataclass(self):
        """OrganizerStats 是 dataclass"""
        stats = OrganizerStats(scanned=10, organized=5)
        assert stats.scanned == 10
        assert stats.organized == 5

    def test_preview_classify_keyword(self):
        """预览分类：关键词匹配"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        test_file = self.test_dir / "合同协议.docx"
        test_file.write_text("contract")

        result = organizer.preview_classify(str(test_file))
        assert "error" not in result
        assert result["filename"] == "合同协议.docx"
        assert result["method"] == "rule"

    def test_preview_classify_extension(self):
        """预览分类：扩展名兜底"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        test_file = self.test_dir / "random.unknown"
        test_file.write_text("data")

        result = organizer.preview_classify(str(test_file))
        assert "error" not in result
        assert result["method"] == "extension"

    def test_setup_directories_preview(self):
        """预览创建目录结构"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        # 不应报错
        organizer.setup_directories()

    def test_get_summary(self):
        """获取统计摘要"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        test_file = self.test_dir / "test.txt"
        test_file.write_text("hello")
        organizer.organize(incremental=False)

        summary = organizer.get_summary()
        assert "stats" in summary
        assert summary["stats"]["scanned"] == 1
        assert summary["source_dir"] == str(self.test_dir)

    def test_large_file_archived(self):
        """大文件归档"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
            large_file_threshold_mb=0,  # 极小阈值
        )
        test_file = self.test_dir / "large.dat"
        test_file.write_bytes(b"x" * 1024 * 1024)  # 1MB

        organizer.organize(incremental=False)

        assert organizer.stats.archived >= 1

    def test_protected_folder_skipped(self):
        """保护目录文件跳过"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        # 在保护目录中创建文件
        protected_dir = self.test_dir / ".git"
        protected_dir.mkdir()
        test_file = protected_dir / "config"
        test_file.write_text("git data")

        organizer.organize(incremental=False)

        assert organizer.stats.skipped >= 1

    def test_delete_pattern_files(self):
        """临时文件删除"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=False,  # 执行模式才会真删除
        )
        test_file = self.test_dir / "~$_temp.docx"
        test_file.write_text("temp")

        organizer.organize(incremental=False)

        assert organizer.stats.deleted >= 1


class TestClassifyIntegration:
    """测试分类集成"""

    def setup_method(self):
        self.test_dir = Path("/tmp/test_classify_integration")
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_classify_unknown_file_goes_to_extension(self):
        """未知文件走扩展名兜底"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        test_file = self.test_dir / "xyz123.abc"
        test_file.write_text("unknown")

        organizer.organize(incremental=False)

        assert organizer.stats.unmatched >= 1

    def test_classify_keyword_priority(self):
        """关键词优先于扩展名"""
        organizer = FileOrganizer(
            source_dir=str(self.test_dir),
            use_llm=False,
            dry_run=True,
        )
        # 周报
        test_file = self.test_dir / "项目周报_2026.xlsx"
        test_file.write_text("report")

        organizer.organize(incremental=False)

        assert organizer.stats.rule_matched >= 1
        assert organizer.stats.unmatched == 0