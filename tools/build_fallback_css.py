#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sinh CSS dự phòng đặt ngay trên site cho hai trang Final, để khi CDN Tailwind bị chặn (mạng công ty, tiện ích chặn
quảng cáo, mất mạng lúc in PDF) trang vẫn giữ bố cục, nút editor vẫn ẩn và bản PDF không đổi số trang.

Cách làm: mở từng trang bằng Chromium (Playwright) khi CDN còn truy cập được, lấy đúng khối <style> mà Tailwind CDN
sinh ra cho các class đang có trên trang, ghi vào assets/<trang>-base.css. Trang nạp file này TRƯỚC script CDN;
khi CDN chạy được, CSS của CDN trùng nội dung nên không đổi gì.

Chạy lại khi thêm class Tailwind mới vào trang (sửa chữ qua editor thì KHÔNG cần):
    python tools/build_fallback_css.py          # ghi lại 2 file
    python tools/build_fallback_css.py --check  # báo nếu file đang có thiếu class so với trang hiện tại
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {"index.html": "assets/portfolio-base.css", "index_portfolio_clean.html": "assets/cv-base.css"}
HEADER = "/* Sinh bởi tools/build_fallback_css.py từ Tailwind CDN 3.4.17 — đừng sửa tay. */\n"

GRAB_JS = """() => [...document.querySelectorAll('style')].map((s) => s.textContent || '')
  .filter((t) => t.includes('--tw-border-spacing-x')).join('\\n')"""


def generate():
    from playwright.sync_api import sync_playwright
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for page, _ in PAGES.items():
            pg = b.new_page(viewport={"width": 1280, "height": 900})
            # chặn file dự phòng cũ để chắc CSS lấy ra là của CDN
            pg.route("**/assets/*-base.css", lambda r: r.fulfill(status=200, body="", content_type="text/css"))
            pg.goto((ROOT / page).as_uri(), wait_until="networkidle")
            pg.wait_for_timeout(800)
            css = pg.evaluate(GRAB_JS)
            if len(css) < 5000:
                raise SystemExit(f"{page}: không lấy được CSS từ Tailwind CDN (mạng bị chặn?)")
            out[page] = HEADER + css.strip() + "\n"
            pg.close()
        b.close()
    return out


def main(argv):
    css = generate()
    if "--check" in argv:
        bad = [PAGES[p] for p, text in css.items() if not (ROOT / PAGES[p]).exists() or (ROOT / PAGES[p]).read_text(encoding="utf-8") != text]
        for f in bad:
            print("LỆCH   " + f + "  (chạy: python tools/build_fallback_css.py)")
        if not bad:
            print("OK     CSS dự phòng khớp class đang dùng")
        return 1 if bad else 0
    for page, text in css.items():
        target = ROOT / PAGES[page]
        target.parent.mkdir(exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
        print(f"ĐÃ GHI  {PAGES[page]}  ({len(text) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
