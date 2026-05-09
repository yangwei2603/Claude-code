"""
内容提取器测试
"""

import tempfile
import shutil
from pathlib import Path

import pytest

from organizer.content_extractor import ContentExtractor
from organizer.constants import DEFAULT_MAX_CONTENT_SIZE_MB, BYTES_PER_MB


class TestContentExtractor:
    """ContentExtractor 测试"""

    @pytest.fixture
    def extractor(self):
        """创建 ContentExtractor 实例"""
        return ContentExtractor(max_size_mb=DEFAULT_MAX_CONTENT_SIZE_MB)

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        d = Path(tempfile.mkdtemp())
        yield d
        shutil.rmtree(d, ignore_errors=True)

    # ---- can_extract 测试 ----

    def test_can_extract_supported_text(self, extractor, temp_dir):
        """测试支持的文件类型（.txt）"""
        f = temp_dir / "test.txt"
        f.write_text("hello")
        assert extractor.can_extract(f) is True

    def test_can_extract_supported_md(self, extractor, temp_dir):
        """测试 .md 文件"""
        f = temp_dir / "test.md"
        f.write_text("# title")
        assert extractor.can_extract(f) is True

    def test_can_extract_supported_json(self, extractor, temp_dir):
        """测试 .json 文件"""
        f = temp_dir / "test.json"
        f.write_text('{"key": "value"}')
        assert extractor.can_extract(f) is True

    def test_can_extract_unsupported(self, extractor, temp_dir):
        """测试不支持的文件类型"""
        f = temp_dir / "test.exe"
        f.write_bytes(b"binary")
        assert extractor.can_extract(f) is False

    def test_can_extract_unsupported_image(self, extractor, temp_dir):
        """测试图片文件不支持"""
        f = temp_dir / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n")
        assert extractor.can_extract(f) is False

    def test_can_extract_size_limit(self, extractor, temp_dir):
        """测试文件大小限制"""
        # 创建一个接近限制的文件（1MB，在 10MB 限制内）
        f = temp_dir / "small.txt"
        f.write_text("x" * 1024)
        assert extractor.can_extract(f) is True

    def test_can_extract_too_large(self, extractor, temp_dir):
        """测试超过大小限制的文件"""
        max_size = extractor.max_size_bytes
        f = temp_dir / "large.txt"
        # 创建一个超过限制的文件
        f.write_bytes(b"x" * (max_size + 1))
        assert extractor.can_extract(f) is False

    def test_can_extract_nonexistent(self, extractor, temp_dir):
        """测试不存在的文件"""
        f = temp_dir / "nonexistent.txt"
        assert extractor.can_extract(f) is False

    # ---- extract 文本文件 ----

    def test_extract_text_utf8(self, extractor, temp_dir):
        """测试提取 UTF-8 文本"""
        f = temp_dir / "test.txt"
        f.write_text("Hello, 世界！")
        content = extractor.extract(f)
        assert "Hello" in content
        assert "世界" in content

    def test_extract_text_gbk(self, extractor, temp_dir):
        """测试提取 GBK 编码文本"""
        f = temp_dir / "test_gbk.txt"
        content = "中文测试"
        with open(f, "wb") as fp:
            fp.write(content.encode("gbk"))
        result = extractor.extract(f)
        assert len(result) > 0

    def test_extract_text_truncation(self, extractor, temp_dir):
        """测试超长文本截断"""
        f = temp_dir / "long.txt"
        f.write_text("x" * 100000)
        content = extractor.extract(f)
        assert len(content) <= 50000

    def test_extract_nonexistent(self, extractor, temp_dir):
        """测试提取不存在的文件"""
        f = temp_dir / "nonexistent.txt"
        content = extractor.extract(f)
        assert content == ""

    def test_extract_unsupported_format(self, extractor, temp_dir):
        """测试不支持的格式"""
        f = temp_dir / "test.exe"
        f.write_bytes(b"\x00\x01\x02")
        content = extractor.extract(f)
        assert content == ""

    def test_extract_markdown(self, extractor, temp_dir):
        """测试提取 Markdown 文件"""
        f = temp_dir / "test.md"
        f.write_text("# Title\n\nSome content")
        content = extractor.extract(f)
        assert "Title" in content
        assert "Some content" in content

    def test_extract_json(self, extractor, temp_dir):
        """测试提取 JSON 文件"""
        f = temp_dir / "test.json"
        f.write_text('{"name": "test", "value": 123}')
        content = extractor.extract(f)
        assert "name" in content
        assert "test" in content

    def test_extract_yaml(self, extractor, temp_dir):
        """测试提取 YAML 文件"""
        f = temp_dir / "test.yaml"
        f.write_text("key: value\nlist:\n  - item1\n  - item2")
        content = extractor.extract(f)
        assert "key" in content
        assert "value" in content

    def test_extract_sql(self, extractor, temp_dir):
        """测试提取 SQL 文件"""
        f = temp_dir / "test.sql"
        f.write_text("SELECT * FROM users WHERE id = 1;")
        content = extractor.extract(f)
        assert "SELECT" in content
        assert "users" in content


class TestContentExtractorEdgeCases:
    """内容提取器边界情况测试"""

    def test_empty_file(self):
        """测试空文件"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            f = temp_dir / "empty.txt"
            f.write_text("")
            extractor = ContentExtractor()
            content = extractor.extract(f)
            assert content == ""
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_file_with_special_chars(self):
        """测试包含特殊字符的文件"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            f = temp_dir / "special.txt"
            f.write_text("Line1\nLine2\r\nLine3\tTab\n\r\n")
            extractor = ContentExtractor()
            content = extractor.extract(f)
            assert len(content) > 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_file_with_chinese_filename(self):
        """测试中文文件名"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            f = temp_dir / "测试文件.txt"
            f.write_text("中文内容测试")
            extractor = ContentExtractor()
            assert extractor.can_extract(f) is True
            content = extractor.extract(f)
            assert "中文内容测试" in content
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_different_max_size(self):
        """测试自定义最大文件大小"""
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # 1MB 限制
            extractor = ContentExtractor(max_size_mb=1)
            small = temp_dir / "small.txt"
            small.write_text("x" * 1024)
            assert extractor.can_extract(small) is True

            large = temp_dir / "large.txt"
            large.write_bytes(b"x" * (2 * 1024 * 1024))
            assert extractor.can_extract(large) is False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)