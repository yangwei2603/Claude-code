#!/usr/bin/env python3
"""桌面文件整理工具。

将桌面上的文件按扩展名自动归类到子目录中，支持 dry-run 和自定义目录。
"""

from __future__ import annotations

import argparse
import shutil
from collections import Counter
from pathlib import Path
from typing import Iterable

DEFAULT_CATEGORIES = {
    "Images": {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "svg", "heic"},
    "Documents": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "md", "rtf"},
    "Archives": {"zip", "tar", "gz", "tgz", "bz2", "rar", "7z"},
    "Code": {"py", "js", "ts", "jsx", "tsx", "html", "css", "json", "yaml", "yml", "sh", "go", "rs", "java", "c", "cpp", "h", "hpp", "swift", "kt", "sql"},
    "Video": {"mp4", "mov", "mkv", "avi", "wmv", "flv", "webm"},
    "Audio": {"mp3", "wav", "aac", "flac", "m4a", "ogg"},
    "Installers": {"dmg", "pkg", "exe", "msi"},
}
OTHER_CATEGORY = "Others"
HIDDEN_PREFIX = "."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="整理桌面文件到分类目录。")
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.home() / "Desktop",
        help="要整理的桌面目录，默认为当前用户 Desktop。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示将要移动的文件，不执行实际移动。",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="递归整理子目录中的文件。",
    )
    return parser


def categorize_file(path: Path) -> str:
    if path.suffix:
        ext = path.suffix[1:].lower()
        for category, extensions in DEFAULT_CATEGORIES.items():
            if ext in extensions:
                return category
    return OTHER_CATEGORY


def iter_targets(directory: Path, recursive: bool = False) -> Iterable[Path]:
    if recursive:
        for item in directory.rglob("*"):
            if item.is_file() and item.name[0] != HIDDEN_PREFIX:
                yield item
    else:
        for item in directory.iterdir():
            if item.is_file() and item.name[0] != HIDDEN_PREFIX:
                yield item


def safe_target_path(target: Path) -> Path:
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    count = 1
    while True:
        new_name = f"{stem} ({count}){suffix}"
        candidate = parent / new_name
        if not candidate.exists():
            return candidate
        count += 1


def move_file(source: Path, destination_dir: Path, dry_run: bool = False) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    destination = safe_target_path(destination)
    if dry_run:
        print(f"[dry-run] {source} -> {destination}")
    else:
        shutil.move(str(source), str(destination))
        print(f"Moved: {source.name} -> {destination_dir.name}/{destination.name}")
    return destination


def organize_desktop(directory: Path, recursive: bool = False, dry_run: bool = False) -> Counter[str]:
    summary: Counter[str] = Counter()
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"目标目录不存在或不是文件夹：{directory}")

    for file_path in sorted(iter_targets(directory, recursive=recursive)):
        category = categorize_file(file_path)
        target_dir = directory / category
        move_file(file_path, target_dir, dry_run=dry_run)
        summary[category] += 1
    return summary


def render_summary(summary: Counter[str], dry_run: bool) -> str:
    lines = ["整理完成。" if not dry_run else "Dry-run 完成。" ]
    if not summary:
        lines.append("未检测到需要整理的文件。")
        return "\n".join(lines)

    lines.append("已处理文件数量：")
    for category, count in summary.most_common():
        lines.append(f"- {category}: {count}")
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    directory = args.path.expanduser().resolve()

    print(f"整理目标：{directory}")
    print(f"递归模式：{args.recursive}")
    print(f"Dry-run：{args.dry_run}")

    summary = organize_desktop(directory, recursive=args.recursive, dry_run=args.dry_run)
    print(render_summary(summary, args.dry_run))


if __name__ == "__main__":
    main()
