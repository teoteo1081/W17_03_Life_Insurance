# -*- coding: utf-8 -*-
"""
R9 — P0-4: tách mục, thứ tự mới, menu động, ẩn/hiện + di chuyển mục trong editor, nút chuyển Portfolio | CV.

  R9-01  Portfolio: thứ tự Giới thiệu → Dịch vụ → Dashboard → Website → GA4 Tracking → Liên hệ; menu máy tính + điện thoại
         đúng thứ tự, đúng nhãn 4 ngôn ngữ; điểm neo cũ #ga4-ecosystem/#live-projects còn và nằm trong Dịch vụ; nút chuyển
         Portfolio | CV ở cả hai trang (trang đang xem không phải link), không còn chữ "Quay lại"; không còn "1040" hiển thị
  R9-02  mục có data-w17-hidden: không hiện trên web và không có trên menu (máy tính + điện thoại)
  R9-03  editor: nút ⬆ ⬇ Ẩn/Hiện trên mỗi mục (mục đầu không lên, mục cuối không xuống); đổi chỗ + ẩn cập nhật menu ngay,
         tải lại vẫn giữ (bản nháp); HTML Final xuất ra đúng thứ tự, giữ data-w17-hidden, không còn nút điều khiển;
         lưu qua server được; server từ chối bản còn nút điều khiển (422)
  R9-04  điện thoại 390px: nút chuyển hiện trong màn hình ở cả hai trang, Portfolio giấu chữ tên, không tràn ngang
"""

import io
import json

R = None  # gán bởi run_all

ORDER = ["about", "services", "dashboard", "website", "ga4-tracking", "contact"]
NAV = ["#about", "#services", "#dashboard", "#website", "#ga4-tracking", "#contact"]
LABELS = {
    "vi": ["Giới thiệu", "Dịch vụ", "Dashboard", "Website", "GA4 Tracking", "Liên hệ"],
    "en": [None, "Services", "Dashboard", "Websites", "GA4 Tracking", None],
    "es": [None, "Servicios", "Dashboard", "Sitios web", "GA4 Tracking", None],
    "zh": [None, "服务", "数据看板", "网站", "GA4 Tracking", None],
}
STATE_JS = """() => ({
  order: [...document.querySelectorAll('#portfolio-main > section')].map((s) => s.id),
  desktop: [...document.querySelectorAll('[data-w17-nav-list=desktop] a')].map((a) => [a.getAttribute('href'), a.textContent.trim()]),
  mobile: [...document.querySelectorAll('[data-w17-nav-list=mobile] a:not([data-i18n=nav_cta])')].map((a) => a.getAttribute('href')),
})"""


def _raw(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def t_structure(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    for rel in (R.FINAL_PORTFOLIO, R.CREATOR_PORTFOLIO):
        R.open_page(pg, env, rel)
        st = pg.evaluate(STATE_JS)
        if st["order"] != ORDER:
            bad.append(f"{rel}: thứ tự {st['order']}")
        if [h for h, _ in st["desktop"]] != NAV or st["mobile"] != NAV:
            bad.append(f"{rel}: menu {st['desktop']} / {st['mobile']}")
        for l in R.LOCALES:
            R.set_lang(pg, l)
            got = [x for _, x in pg.evaluate(STATE_JS)["desktop"]]
            for want, g in zip(LABELS[l], got):
                if want and want != g:
                    bad.append(f"{rel}/{l}: nhãn menu {got}")
                    break
        R.set_lang(pg, "vi")
        anchors = pg.evaluate("() => ['ga4-ecosystem', 'live-projects'].map((id) => { const e = document.getElementById(id); return !!e && !!e.closest('#services'); })")
        if anchors != [True, True]:
            bad.append(f"{rel}: điểm neo cũ {anchors}")
        sw = pg.evaluate("() => { const s = document.getElementById('w17-page-switch'); return s && [...s.children].map((c) => [c.tagName, c.textContent.trim(), c.getAttribute('aria-current')]); }")
        if not sw or sw[0] != ["SPAN", "Portfolio", "page"] or sw[1][:2] != ["A", "CV"]:
            bad.append(f"{rel}: nút chuyển {sw}")
        for l in ("vi", "en"):
            R.set_lang(pg, l)
            if "1040" in pg.evaluate("document.body.innerText"):
                bad.append(f"{rel}/{l}: còn chữ 1040")
        R.set_lang(pg, "vi")
    for rel in (R.FINAL_CV, R.CREATOR_CV):
        R.open_page(pg, env, rel)
        sw = pg.evaluate("() => { const s = document.getElementById('w17-page-switch'); return s && [...s.children].map((c) => [c.tagName, c.textContent.trim(), c.getAttribute('aria-current')]); }")
        if not sw or sw[0][:2] != ["A", "Portfolio"] or sw[1] != ["SPAN", "CV", "page"]:
            bad.append(f"{rel}: nút chuyển {sw}")
        text = pg.evaluate("document.body.innerText")
        if "Quay lại" in text or "1040" in text:
            bad.append(f"{rel}: còn 'Quay lại' hoặc '1040'")
    ctx.close()
    R.record("R9", "R9-01 thứ tự mục + menu (máy tính/điện thoại, 4 ngôn ngữ), điểm neo cũ, nút chuyển Portfolio | CV hai trang, không còn 'Quay lại'/'1040'", not bad, " | ".join(bad[:6]))


def t_hidden_public(b, env):
    bad = []
    env.reset_work()
    f = env.work / "index.html"
    html = _raw(f)
    _write(f, html.replace('<section id="dashboard" data-w17-section="dashboard"', '<section id="dashboard" data-w17-hidden="1" data-w17-section="dashboard"', 1))
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, R.FINAL_PORTFOLIO)
    st = pg.evaluate(STATE_JS)
    if pg.evaluate("getComputedStyle(document.getElementById('dashboard')).display") != "none":
        bad.append("mục ẩn vẫn hiện trên web")
    if "#dashboard" in [h for h, _ in st["desktop"]] or "#dashboard" in st["mobile"]:
        bad.append(f"menu còn mục ẩn: {st['desktop']}")
    ctx.close()
    env.reset_work()
    R.record("R9", "R9-02 mục có data-w17-hidden không hiện trên web và không có trên menu", not bad, " | ".join(bad))


def t_editor_layout(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    errors = []
    pg = R.new_page(ctx, errors)
    R.open_page(pg, env, R.CREATOR_PORTFOLIO, wait=900)
    if pg.evaluate("getComputedStyle(document.querySelector('#services > .w17-section-controls')).display") != "none":
        bad.append("chưa bật Sửa chữ mà đã hiện nút điều khiển")
    pg.click("#btn-toggle-edit"); pg.wait_for_timeout(250)
    info = pg.evaluate("""() => [...document.querySelectorAll('#portfolio-main > section[data-w17-section]')].map((s) => {
      const b = s.querySelectorAll(':scope > .w17-section-controls button'); return [s.id, b.length, b[0] && b[0].disabled, b[1] && b[1].disabled]; })""")
    if [x[0] for x in info] != ORDER[1:-1] or any(x[1] != 4 for x in info) or not info[0][2] or info[0][3] or info[-1][2] or not info[-1][3]:
        bad.append(f"nút điều khiển {info}")
    pg.locator("#services > .w17-section-controls button").nth(1).click()          # Dịch vụ xuống 1
    pg.locator("#website > .w17-section-controls button").nth(2).click()           # ẩn Website
    pg.wait_for_timeout(200)
    want_order = ["about", "dashboard", "services", "website", "ga4-tracking", "contact"]
    want_nav = ["#about", "#dashboard", "#services", "#ga4-tracking", "#contact"]
    st = pg.evaluate(STATE_JS)
    if st["order"] != want_order or [h for h, _ in st["desktop"]] != want_nav or st["mobile"] != want_nav:
        bad.append(f"sau thao tác: {st}")
    if pg.evaluate("getComputedStyle(document.getElementById('website')).display") == "none":
        bad.append("editor giấu hẳn mục ẩn (phải hiện mờ để bật lại)")
    pg.reload(wait_until="load"); pg.wait_for_timeout(900)
    st = pg.evaluate(STATE_JS)
    if st["order"] != want_order or [h for h, _ in st["desktop"]] != want_nav or not pg.evaluate("document.getElementById('website').hasAttribute('data-w17-hidden')"):
        bad.append(f"tải lại mất bản nháp: {st}")
    html = pg.evaluate("() => w17CloneCleanHtml()")
    import re
    order = re.findall(r'<section id="([\w-]+)"', html[html.index('<main id="portfolio-main"'):])
    if order != want_order:
        bad.append(f"Final sai thứ tự {order}")
    if re.search(r'class="[^"]*w17-section-controls', html) or not re.search(r'<section id="website"[^>]*data-w17-hidden="1"', html):
        bad.append("Final còn nút điều khiển hoặc mất data-w17-hidden")
    _, _, body = R.http("GET", env.base + "/api/session", {"Origin": env.base})
    token = json.loads(body)["token"]
    hdr = {"Content-Type": "application/json", "Origin": env.base, "X-W17-Token": token}
    st_code, _, body = R.http("POST", env.base + "/api/save", hdr, json.dumps({"html": html, "targets": ["index.html"]}).encode("utf-8"))
    if st_code != 200:
        bad.append(f"lưu Final -> {st_code} {body[:120]}")
    dirty = html.replace('<section id="dashboard"', '<div class="w17-section-controls"></div><section id="dashboard"', 1)
    st_code, _, _ = R.http("POST", env.base + "/api/save", hdr, json.dumps({"html": dirty, "targets": ["index.html"]}).encode("utf-8"))
    if st_code != 422:
        bad.append(f"server nhận bản còn nút điều khiển -> {st_code}")
    pg2 = R.new_page(ctx)
    R.open_page(pg2, env, R.FINAL_PORTFOLIO)
    st = pg2.evaluate(STATE_JS)
    if st["order"] != want_order or [h for h, _ in st["desktop"]] != want_nav or pg2.evaluate("getComputedStyle(document.getElementById('website')).display") != "none":
        bad.append(f"Final đã lưu: {st}")
    pg.evaluate("() => localStorage.removeItem('w17_03_portfolio_edits_v1')")
    if errors:
        bad.append("lỗi JS: " + " | ".join(errors[:2]))
    ctx.close()
    env.reset_work()
    R.record("R9", "R9-03 editor (bật Sửa chữ): ⬆ ⬇ Ẩn/Hiện cập nhật menu ngay, tải lại vẫn giữ, Final đúng thứ tự + giữ ẩn + sạch nút điều khiển, lưu được; server chặn bản còn nút điều khiển", not bad, " | ".join(bad[:6]))


def t_mobile_switch(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 390, "height": 844})
    pg = R.new_page(ctx)
    for rel in (R.FINAL_PORTFOLIO, R.FINAL_CV):
        R.open_page(pg, env, rel)
        r = pg.evaluate("() => { const s = document.getElementById('w17-page-switch').getBoundingClientRect(); return [s.width > 0 && s.left >= 0 && s.right <= innerWidth, document.documentElement.scrollWidth - innerWidth]; }")
        if r != [True, 0]:
            bad.append(f"{rel}: nút chuyển/tràn {r}")
    R.open_page(pg, env, R.FINAL_PORTFOLIO)
    if pg.evaluate("() => [...document.querySelectorAll('#main-navbar .brand-title')].some((e) => e.textContent.includes('Thao Nguyen') && e.offsetParent !== null)"):
        bad.append("điện thoại vẫn hiện chữ tên (đẩy mất nút chuyển)")
    ctx.close()
    R.record("R9", "R9-04 điện thoại 390px: nút chuyển nằm trong màn hình ở hai trang, Portfolio giấu chữ tên, không tràn ngang", not bad, " | ".join(bad))
