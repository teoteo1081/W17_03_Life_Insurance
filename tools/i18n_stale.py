#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phát hiện chữ cần dịch lại: so bản tiếng Việt HIỆN TẠI (từ điển + bản sửa đã nhúng từ editor) của mỗi khóa với bản tiếng Việt
lúc dịch EN/ES/ZH lần gần nhất (lưu dấu vân tay ở i18n/translated_from.json).

    python tools/i18n_stale.py            # liệt kê khóa có bản VI đã đổi mà EN/ES/ZH chưa dịch lại (thoát 1 nếu có)
    python tools/i18n_stale.py --show     # như trên, in kèm bản VI + EN/ES/ZH hiện tại để dịch
    python tools/i18n_stale.py --mark K1 K2 ...   # ghi nhận đã dịch xong các khóa này (lấy dấu vân tay VI hiện tại)
    python tools/i18n_stale.py --mark-all # ghi nhận toàn bộ (chỉ dùng khi vừa rà xong mọi khóa)

Không gọi dịch vụ ngoài. Bản dịch do người (hoặc Claude theo skill w17-translate) viết rồi sửa thẳng trong từ điển.
"""

import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "i18n" / "translated_from.json"
PAGES = {
    "index.html": ("const translations = {", "const W17_PRISTINE", "editsByLang"),
    "index_portfolio_clean.html": ("const translationsCV = {", "const PRISTINE_CV", "textEditsByLang"),
}
LANGS = ("vi", "en", "es", "zh")


def _blocks(text, start, end):
    s = text.index(start)
    d = text[s:text.index(end, s)]
    pos = sorted(((l, d.index("\n      " + l + ": {")) for l in LANGS), key=lambda x: x[1])
    return {l: d[i:(pos[n + 1][1] if n + 1 < len(pos) else len(d))] for n, (l, i) in enumerate(pos)}


def _dict(block):
    out = {}
    for m in re.finditer(r'\n\s+([A-Za-z0-9_]+): (".*?"),?(?=\n)', block):
        try:
            out[m.group(1)] = json.loads(m.group(2))
        except json.JSONDecodeError:
            pass
    return out


def load():
    """{trang: {khóa: {"vi": hiệu lực, "en":..., "es":..., "zh":...}}}"""
    out = {}
    for page, (start, end, field) in PAGES.items():
        text = io.open(ROOT / page, encoding="utf-8").read()
        b = {l: _dict(blk) for l, blk in _blocks(text, start, end).items()}
        baked = json.loads(re.search(r'id="w17-baked-edits">(.*?)</script>', text, re.S).group(1)).get(field, {}).get("vi", {})
        page_keys = {}
        for key, vi in b["vi"].items():
            page_keys[key] = {"vi": baked.get(key, vi), **{l: b[l].get(key) for l in LANGS[1:]}}
        out[page] = page_keys
    return out


def fp(s):
    return hashlib.sha256(re.sub(r"\s+", " ", s or "").strip().encode("utf-8")).hexdigest()[:12]


def read_state():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_state(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(argv):
    data, state = load(), read_state()
    if "--mark-all" in argv or "--mark" in argv:
        keys = set(argv[argv.index("--mark") + 1:]) if "--mark" in argv else None
        for page, keys_map in data.items():
            for key, v in keys_map.items():
                if keys is None or key in keys:
                    state.setdefault(page, {})[key] = fp(v["vi"])
        write_state(state)
        print("ĐÃ GHI NHẬN", "toàn bộ" if keys is None else ", ".join(sorted(keys)))
        return 0
    stale = []
    for page, keys_map in data.items():
        for key, v in keys_map.items():
            if state.get(page, {}).get(key) != fp(v["vi"]):
                stale.append((page, key, v))
    for page, key, v in stale:
        print(f"CẦN DỊCH  {page}  {key}")
        if "--show" in argv:
            for l in LANGS:
                print(f"    {l.upper()}: {re.sub(r'<[^>]+>', ' ', v[l] or '')[:300]}")
    if not stale:
        print("OK     EN/ES/ZH theo kịp bản tiếng Việt")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
