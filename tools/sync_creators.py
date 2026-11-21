#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh (hoặc kiểm tra) hai bản Creator từ hai bản Final — Final là NGUỒN DUY NHẤT.

    editor_workspace/editor_portfolio.html  <-  index.html
    editor_workspace/editor_cv.html         <-  index_portfolio_clean.html

Creator khác Final đúng hai điểm, nên i18n (vi/en/es/zh), sanitizer, lưu dữ liệu có schema, modal và toolbar
không thể lệch nhau (AGENTS.md §2, §9; báo cáo audit F04/F05/F06/F08):
  1. <html ... data-w17-mode="creator">  -> thanh công cụ hiện sẵn khi mở trang.
  2. Liên kết điều hướng tĩnh trỏ sang Creator tương ứng thay vì Final.

Dùng:
    python tools/sync_creators.py          # ghi lại hai Creator
    python tools/sync_creators.py --check  # thoát mã 1 nếu Creator lệch khỏi Final (dùng trong kiểm thử)

server.py cũng gọi creator_for() sau mỗi lần lưu Final, để file editor luôn là bản vừa lưu.
"""

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HTML_OPEN = '<html lang="vi" class="dark scroll-smooth"'
MODE_ATTR = ' data-w17-mode="creator"'
HTML_TAG_RE = re.compile(r"<html\b[^>]*>", re.IGNORECASE)

# (nguồn Final, đích Creator, [(chuỗi cũ, chuỗi mới, số lần xuất hiện bắt buộc)])
JOBS = [
    (
        "index.html",
        "editor_workspace/editor_portfolio.html",
        [('href="./index_portfolio_clean.html"', 'href="./editor_cv.html"', 2),
         ('href="./assets/portfolio-base.css"', 'href="../assets/portfolio-base.css"', 1)],
    ),
    (
        "index_portfolio_clean.html",
        "editor_workspace/editor_cv.html",
        [('href="./index.html"', 'href="./editor_portfolio.html"', 1),
         ('href="./assets/cv-base.css"', 'href="../assets/cv-base.css"', 1)],
    ),
]


class SyncError(Exception):
    """Final không đúng khuôn để sinh Creator (thiếu thẻ <html>, sai số liên kết...)."""


def read(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def build(src_rel, replacements, root=ROOT):
    text = read(Path(root) / src_rel)
    match = HTML_TAG_RE.search(text)
    if not match:
        raise SyncError(f"{src_rel}: không tìm thấy thẻ <html> để gắn data-w17-mode")
    tag = match.group(0)
    if "data-w17-mode=" in tag:
        raise SyncError(f"{src_rel}: bản Final còn cờ data-w17-mode (là bản Creator, không phải Final)")
    # Final chuẩn: gắn cờ ngay sau class="..." như trước (kết quả trùng từng byte với các Creator đã có).
    # Final khác khuôn (vd. lưu từ editor khi thuộc tính đổi thứ tự): gắn ngay trước dấu '>' của thẻ <html>.
    if tag.startswith(HTML_OPEN):
        new_tag = HTML_OPEN + MODE_ATTR + tag[len(HTML_OPEN):]
    else:
        new_tag = tag[:-1] + MODE_ATTR + ">"
    text = text[:match.start()] + new_tag + text[match.end():]
    for old, new, expected in replacements:
        found = text.count(old)
        if found != expected:
            raise SyncError(f"{src_rel}: cần {expected} lần '{old}', thực tế {found}")
        text = text.replace(old, new)
    return text


def creator_for(final_rel, root=ROOT):
    """Trả (đường dẫn Creator, nội dung Creator) sinh từ một file Final; SyncError nếu Final sai khuôn."""
    for src_rel, dst_rel, replacements in JOBS:
        if src_rel == final_rel:
            return dst_rel, build(src_rel, replacements, root)
    raise SyncError(f"{final_rel}: không phải file Final có Creator tương ứng")


def main(argv):
    check = "--check" in argv
    drift = []
    for src_rel, dst_rel, replacements in JOBS:
        try:
            expected = build(src_rel, replacements)
        except SyncError as err:
            print(f"LỖI     {err}")
            return 1
        dst = ROOT / dst_rel
        current = read(dst) if dst.exists() else None
        if current == expected:
            print(f"OK       {dst_rel}")
            continue
        if check:
            drift.append(dst_rel)
            print(f"LỆCH     {dst_rel}")
        else:
            with io.open(dst, "w", encoding="utf-8", newline="") as fh:
                fh.write(expected)
            print(f"ĐÃ GHI   {dst_rel}")
    if drift:
        print("Creator lệch khỏi Final. Chạy: python tools/sync_creators.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
