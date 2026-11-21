# -*- coding: utf-8 -*-
"""
R5 — mã do tiện ích trình duyệt chèn vào trang (sự cố eJOY, commit b9d6ef8/85ba3d9, sửa ở bd811e6).

  R5-01  editor tự lọc: chèn nút rác (script chrome-extension://, div/pre eJOY, style SweetAlert/eJOY,
         thuộc tính lạ trên <html> và <body>, nút lạ ngay dưới <html>) → bản lưu giống hệt bản lưu khi chưa chèn,
         và /api/save nhận bản đó (portfolio + CV)
  R5-02  server chặn: bản lưu còn từng loại rác → 422 và file trên đĩa không đổi; bản sạch → 200
"""

import io
import json

R = None  # gán bởi run_all

PAGES = [  # (trang Creator, file Final, hàm tạo bản lưu)
    ("editor_workspace/editor_portfolio.html", "index.html", "w17CloneCleanHtml"),
    ("editor_workspace/editor_cv.html", "index_portfolio_clean.html", "cloneCleanHtmlCV"),
]

INJECT_JS = r"""
(fn) => {
  const before = window[fn]();
  const add = (parent, html) => { const t = document.createElement('template'); t.innerHTML = html; parent.appendChild(t.content); };
  add(document.head, '<script type="text/plain" src="chrome-extension://abcdefghijklmnop/js/recorder.js"></script>');
  add(document.head, '<link rel="stylesheet" href="moz-extension://abc/x.css">');
  add(document.head, '<style>.swal2-popup.swal2-toast{box-sizing:border-box}</style>');
  add(document.head, '<style>body {transition: opacity ease-in 0.2s; } body[unresolved] {opacity: 0;}</style>');
  add(document.head, '<style>.ej-trans-sub{position:absolute} #eJOY__extension_root{all:unset}</style>');
  add(document.body, '<div id="eJOY__extension_root" class="eJOY__extension_root_class"></div>');
  add(document.body, '<div class="eJOY__popup"><span>x</span></div>');
  add(document.body, '<pre id="__ejoy_debug" style="display:none">query returned open=false</pre>');
  document.documentElement.setAttribute('suppresshydrationwarning', 'true');
  document.documentElement.setAttribute('data-qb-installed', 'true');
  document.body.setAttribute('data-gr-ext-installed', '');
  document.body.setAttribute('data-new-gr-c-s-check-loaded', '14.1');
  document.documentElement.appendChild(document.createElement('grammarly-desktop-integration'));
  const after = window[fn]();
  return {before, after};
}
"""


def _raw(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _post_save(env, html, target):
    _, _, body = R.http("GET", env.base + "/api/session", {"Origin": env.base})
    token = json.loads(body)["token"]
    hdr = {"Content-Type": "application/json", "Origin": env.base, "X-W17-Token": token}
    st, _, body = R.http("POST", env.base + "/api/save", hdr, json.dumps({"html": html, "targets": [target]}).encode("utf-8"))
    return st, body.decode("utf-8", "replace")


def t_editor_strips(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    for creator, final, fn in PAGES:
        pg = R.new_page(ctx)
        R.open_page(pg, env, creator, wait=900)
        res = pg.evaluate(INJECT_JS, fn)
        pg.close()
        if res["before"] != res["after"]:
            bad.append(f"{creator}: bản lưu khác sau khi chèn rác (độ dài {len(res['before'])} -> {len(res['after'])})")
            continue
        st, body = _post_save(env, res["after"], final)
        if st != 200:
            bad.append(f"{final}: /api/save trả {st} {body[:160]}")
    ctx.close()
    env.reset_work()
    R.record("R5-01", "editor bỏ mã tiện ích trình duyệt (script/style/div eJOY, SweetAlert, thuộc tính lạ trên html/body) khi lưu; server nhận bản đó (portfolio + CV)", not bad, " | ".join(bad))


def t_server_rejects(env):
    bad = []
    env.reset_work()
    variants = {
        "script chrome-extension://": ("</head>", '<script src="chrome-extension://abc/js/x.js"></script></head>'),
        "link moz-extension://": ("</head>", '<link rel="stylesheet" href="moz-extension://abc/x.css"></head>'),
        "id eJOY": ("</body>", '<div id="eJOY__extension_root"></div></body>'),
        "id __ejoy_debug": ("</body>", '<pre id="__ejoy_debug">x</pre></body>'),
        "class eJOY__": ("</body>", '<div class="eJOY__extension_root_class"></div></body>'),
        "style .swal2-": ("</head>", "<style>.swal2-container{z-index:1060}</style></head>"),
        "style body[unresolved]": ("</head>", "<style>body[unresolved]{opacity:0}</style></head>"),
    }
    for _, final, _ in PAGES:
        clean = _raw(env.work / final)
        for name, (anchor, repl) in variants.items():
            if clean.count(anchor) != 1:
                bad.append(f"{final}: mốc {anchor} không duy nhất")
                continue
            st, _ = _post_save(env, clean.replace(anchor, repl), final)
            if st != 422:
                bad.append(f"{final} + {name}: phải 422, nhận {st}")
            if _raw(env.work / final) != clean:
                bad.append(f"{final} + {name}: file trên đĩa bị đổi dù bị từ chối")
        st, body = _post_save(env, clean, final)
        if st != 200:
            bad.append(f"{final}: bản sạch phải 200, nhận {st} {body[:160]}")
    env.reset_work()
    R.record("R5-02", "server từ chối bản lưu còn mã tiện ích trình duyệt (7 dạng) với 422 và không ghi file; bản sạch vẫn lưu được (portfolio + CV)", not bad, " | ".join(bad))
