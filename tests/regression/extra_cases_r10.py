# -*- coding: utf-8 -*-
"""
R10 — các lỗi do audit độc lập tại 2b91184 chỉ ra (mỗi ca một test). Không gọi API thật bên ngoài.

  R10-01  tab editor cũ (cùng cấu hình) KHÔNG ghi đè nội dung mới: API (/api/revision + expected_revision -> 409, file không đổi)
          và giao diện thật (2 tab: tab A lưu, tab B lưu sau -> 409, file giữ bản A, nháp của B còn nguyên)
  R10-02  nháp CV kiểu cũ (không có deletedIds/knownIds) KHÔNG làm mất thẻ ngoài danh sách thứ tự; HTML Final xuất ra và
          file lưu qua server còn đủ thẻ
  R10-03  lưu cài đặt thất bại giữa chừng (Final CV hoặc Creator CV không ghi được) -> 5xx, KHÔNG file nào đổi
          (2 Final + 2 Creator giữ nguyên byte), cấu hình hai trang vẫn khớp
  R10-04  Portfolio mục ↔ menu: tắt Sửa chữ thì không còn nút điều khiển; đổi tên trên menu (máy tính + điện thoại) và giữ
          sau tải lại + vào Final; sắp xếp ngay trên menu (Alt+←, kéo-thả); thêm mục mới có mục menu, giữ sau tải lại,
          lưu ra Final hiện trên web; xóa mục tự thêm phải bấm 2 lần; Giới thiệu/Liên hệ khóa
  R10-05  CV: xóa thẻ phải xác nhận (bấm 2 lần), vào thùng rác, khôi phục từng thẻ; sau tải lại vẫn khôi phục được
  R10-06  chặn mọi CDN: PDF CV vẫn 4 trang như khi có mạng, không in chữ "Đổi ảnh", giữ bố cục hai cột; Portfolio giữ menu ngang
"""

import io
import json
import os
import re
import stat

R = None  # gán bởi run_all

CV_KEY = "tj_capability_w17_03_state_v1"
P_KEY = "w17_03_portfolio_edits_v1"


def _raw(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _hdr(env):
    _, _, body = R.http("GET", env.base + "/api/session", {"Origin": env.base})
    return {"Content-Type": "application/json", "Origin": env.base, "X-W17-Token": json.loads(body)["token"]}


def _post(env, path, payload):
    st, _, body = R.http("POST", env.base + path, _hdr(env), json.dumps(payload).encode("utf-8"))
    try:
        return st, json.loads(body.decode("utf-8"))
    except ValueError:
        return st, {}


def _rev(env, name):
    st, _, body = R.http("GET", env.base + "/api/revision?file=" + name, {"Origin": env.base})
    return json.loads(body).get("revision") if st == 200 else None


def t_stale_tab(b, env):
    bad = []
    env.reset_work()
    # --- API ---
    r0 = _rev(env, "index.html")
    html = _raw(env.work / "index.html")
    st, data = _post(env, "/api/save", {"html": html.replace("</body>", "<!-- A --></body>", 1), "targets": ["index.html"], "expected_revision": r0})
    r1 = (data.get("revisions") or {}).get("index.html")
    if st != 200 or not r1 or r1 == r0:
        bad.append(f"lưu đúng phiên bản -> {st} rev={r1}")
    before = R.sha(env.work / "index.html")
    st, data = _post(env, "/api/save", {"html": html.replace("</body>", "<!-- B stale --></body>", 1), "targets": ["index.html"], "expected_revision": r0})
    if st != 409 or R.sha(env.work / "index.html") != before:
        bad.append(f"lưu phiên bản cũ -> {st} (cần 409, file không đổi)")
    st, _, _ = R.http("GET", env.base + "/api/revision?file=index.html", {"Origin": "http://evil.example"})
    st2, _, _ = R.http("GET", env.base + "/api/revision?file=server.py", {"Origin": env.base})
    if st != 403 or st2 != 400:
        bad.append(f"/api/revision không chặn origin lạ/file lạ: {st}/{st2}")
    # --- giao diện thật: 2 tab cùng mở, A lưu trước, B lưu sau ---
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900}, accept_downloads=True)
    a, bb = R.new_page(ctx), R.new_page(ctx)
    R.open_page(a, env, R.CREATOR_PORTFOLIO, wait=900)
    R.open_page(bb, env, R.CREATOR_PORTFOLIO, wait=900)
    edit = """(txt) => { if (!document.body.classList.contains('is-editing')) toggleEditMode();
      const e = document.querySelector('[data-i18n=hero_badge]'); e.focus(); e.textContent = txt; e.dispatchEvent(new Event('input', {bubbles: true})); }"""
    a.evaluate(edit, "TAB-A-EDIT"); a.wait_for_timeout(200)
    res_a = a.evaluate("async () => w17SaveToServer('index.html', w17BuildCleanHtml())")
    bb.evaluate(edit, "TAB-B-EDIT"); bb.wait_for_timeout(200)
    res_b = bb.evaluate("async () => w17SaveToServer('index.html', w17BuildCleanHtml())")
    disk = _raw(env.work / "index.html")
    draft = bb.evaluate("(k) => localStorage.getItem(k) || ''", P_KEY)
    if not res_a.get("ok"):
        bad.append(f"tab A không lưu được: {res_a}")
    if res_b.get("ok") or res_b.get("status") != 409:
        bad.append(f"tab B (cũ) vẫn lưu được: {res_b}")
    if "TAB-A-EDIT" not in disk or "TAB-B-EDIT" in disk:
        bad.append("file trên đĩa không phải bản của tab A")
    if "TAB-B-EDIT" not in draft:
        bad.append("nháp của tab B bị mất")
    bb.reload(wait_until="load"); bb.wait_for_timeout(900)
    res_b2 = bb.evaluate("async () => w17SaveToServer('index.html', w17BuildCleanHtml())")
    if not res_b2.get("ok") or "TAB-B-EDIT" not in _raw(env.work / "index.html"):
        bad.append(f"tải lại rồi lưu lại không được: {res_b2}")
    a.evaluate("(k) => localStorage.removeItem(k)", P_KEY)
    ctx.close()
    env.reset_work()
    R.record("R10", "R10-01 tab editor cũ cùng cấu hình bị chặn 409 (API + 2 tab thật), file giữ bản mới, nháp tab cũ còn; tải lại rồi lưu được", not bad, " | ".join(bad))


def t_cv_legacy_draft(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, R.CREATOR_CV)
    sol = pg.evaluate("[...document.querySelectorAll('#solutions-grid > .solution-card-item')].map((c) => c.getAttribute('data-card-id'))")
    state = {"schema": 1, "solutionsOrder": [sol[1], sol[0]]}   # nháp cũ: thiếu thẻ thứ 3, không có deletedIds/knownIds
    pg.evaluate("([k, v]) => localStorage.setItem(k, v)", [CV_KEY, json.dumps(state)])
    pg.reload(wait_until="load"); pg.wait_for_timeout(700)
    got = pg.evaluate("[...document.querySelectorAll('#solutions-grid > .solution-card-item')].map((c) => c.getAttribute('data-card-id'))")
    if sorted(got) != sorted(sol) or got[:2] != [sol[1], sol[0]]:
        bad.append(f"nháp cũ làm mất/xáo thẻ: {got}")
    html = pg.evaluate("() => cloneCleanHtmlCV()")
    if any(f'data-card-id="{c}"' not in html for c in sol):
        bad.append("HTML Final xuất ra thiếu thẻ")
    st, data = _post(env, "/api/save", {"html": html, "targets": ["index_portfolio_clean.html"]})
    disk = _raw(env.work / "index_portfolio_clean.html")
    if st != 200 or any(f'data-card-id="{c}"' not in disk for c in sol):
        bad.append(f"file lưu qua server thiếu thẻ ({st})")
    pg.evaluate("(k) => localStorage.removeItem(k)", CV_KEY)
    ctx.close()
    env.reset_work()
    R.record("R10", "R10-02 nháp CV kiểu cũ (không deletedIds/knownIds) không làm mất thẻ ngoài danh sách; Final xuất ra và file đã lưu đủ thẻ", not bad, " | ".join(bad))


def t_settings_rollback(b, env):
    bad = []
    files = ["index.html", "index_portfolio_clean.html", "editor_workspace/editor_portfolio.html", "editor_workspace/editor_cv.html"]
    for victim in ("index_portfolio_clean.html", "editor_workspace/editor_cv.html"):
        env.reset_work()
        before = {f: R.sha(env.work / f) for f in files}
        path = env.work / victim
        os.chmod(path, stat.S_IREAD)
        try:
            st, data = _post(env, "/api/settings", {"changes": {"contact.email": "rollback.test@example.com"}})
        finally:
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
        after = {f: R.sha(env.work / f) for f in files}
        if st < 500:
            bad.append(f"{victim} khóa ghi: /api/settings -> {st} (cần 5xx)")
        changed = [f for f in files if before[f] != after[f]]
        if changed:
            bad.append(f"{victim} khóa ghi: file bị đổi dù thất bại: {changed}")
        if "khôi phục" not in (data.get("message") or ""):
            bad.append(f"thông báo không nói rõ đã khôi phục: {data.get('message')!r}")
        _, _, body = R.http("GET", env.base + "/api/settings", {"Origin": env.base})
        if json.loads(body).get("values", {}).get("contact.email") != "teoteo108@gmail.com":
            bad.append("cấu hình bị đổi một phần")
    env.reset_work()
    R.record("R10", "R10-03 lưu cài đặt thất bại giữa chừng (khóa ghi Final CV / Creator CV) -> 5xx, cả 2 Final + 2 Creator giữ nguyên byte, cấu hình còn khớp", not bad, " | ".join(bad))


NAV_JS = """() => ({
  order: [...document.querySelectorAll('#portfolio-main > section')].map((s) => s.id),
  desk: [...document.querySelectorAll('[data-w17-nav-list=desktop] a')].map((a) => [a.getAttribute('href'), a.textContent.trim()]),
  mob: [...document.querySelectorAll('[data-w17-nav-list=mobile] a:not([data-i18n=nav_cta])')].map((a) => [a.getAttribute('href'), a.textContent.trim()]),
})"""


def t_menu_sections(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    errors = []
    pg = R.new_page(ctx, errors)
    R.open_page(pg, env, R.CREATOR_PORTFOLIO, wait=900)
    vis = "() => [...document.querySelectorAll('.w17-section-controls')].filter((c) => c.offsetParent !== null).length"
    if pg.evaluate(vis) != 0:
        bad.append("tắt Sửa chữ mà còn nút điều khiển")
    pg.click("#btn-toggle-edit"); pg.wait_for_timeout(250)
    if pg.evaluate(vis) != 4:
        bad.append(f"bật Sửa chữ: {pg.evaluate(vis)} thanh điều khiển (cần 4)")
    if pg.evaluate("() => !!document.querySelector('#about > .w17-section-controls, #contact > .w17-section-controls, [data-w17-nav-fixed][draggable=true]')"):
        bad.append("Giới thiệu/Liên hệ không bị khóa")
    pg.click("#btn-toggle-edit"); pg.wait_for_timeout(200)
    if pg.evaluate(vis) != 0:
        bad.append("tắt lại Sửa chữ mà còn nút điều khiển")
    pg.click("#btn-toggle-edit"); pg.wait_for_timeout(200)
    # đổi tên trên menu
    pg.fill("#services > .w17-section-controls input", "Dịch vụ của TJ")
    pg.wait_for_timeout(150)
    st = pg.evaluate(NAV_JS)
    if ["#services", "Dịch vụ của TJ"] not in st["desk"] or ["#services", "Dịch vụ của TJ"] not in st["mob"]:
        bad.append(f"đổi tên không đổi menu: {st['desk']}")
    # sắp xếp ngay trên menu: Alt+← trên mục Website
    pg.focus("[data-w17-nav-list=desktop] a[href='#website']")
    pg.keyboard.press("Alt+ArrowLeft"); pg.wait_for_timeout(150)
    if pg.evaluate(NAV_JS)["order"][1:5] != ["services", "website", "dashboard", "ga4-tracking"]:
        bad.append(f"Alt+← trên menu không đổi thứ tự: {pg.evaluate(NAV_JS)['order']}")
    # kéo-thả: GA4 Tracking thả vào nửa trái mục Dịch vụ
    src = pg.locator("[data-w17-nav-list=desktop] a[href='#ga4-tracking']")
    dst = pg.locator("[data-w17-nav-list=desktop] a[href='#services']")
    src.drag_to(dst, target_position={"x": 2, "y": 5}); pg.wait_for_timeout(200)
    want = ["ga4-tracking", "services", "website", "dashboard"]
    builtin = lambda order: [x for x in order if not x.startswith("sec-")]
    if pg.evaluate(NAV_JS)["order"][1:5] != want:
        bad.append(f"kéo-thả trên menu không đổi thứ tự: {pg.evaluate(NAV_JS)['order']}")
    # thêm mục mới sau Website
    pg.click("#website > .w17-section-controls [data-role=add]"); pg.wait_for_timeout(200)
    new_id = pg.evaluate("() => { const s = document.getElementById('website').nextElementSibling; return s && s.hasAttribute('data-w17-custom') ? s.id : null; }")
    if not new_id:
        bad.append("không thêm được mục mới")
    else:
        pg.fill(f"#{new_id} > .w17-section-controls input", "Khách hàng")
        pg.evaluate("(id) => { const h = document.querySelector('#' + id + ' [data-w17-custom-title]'); h.textContent = 'Khách hàng tiêu biểu'; h.dispatchEvent(new Event('input', {bubbles: true})); }", new_id)
        st = pg.evaluate(NAV_JS)
        if [f"#{new_id}", "Khách hàng"] not in st["desk"]:
            bad.append(f"mục mới không có trên menu: {st['desk']}")
        # xóa mục tự thêm: bấm 1 lần chưa xóa
        pg.click(f"#{new_id} > .w17-section-controls [data-role=del]"); pg.wait_for_timeout(100)
        if not pg.evaluate("(id) => !!document.getElementById(id)", new_id):
            bad.append("xóa mục tự thêm không cần xác nhận")
    # tải lại: giữ tên, thứ tự, mục mới
    pg.reload(wait_until="load"); pg.wait_for_timeout(900)
    st = pg.evaluate(NAV_JS)
    if ["#services", "Dịch vụ của TJ"] not in st["desk"] or builtin(st["order"])[1:5] != want or (new_id and f"#{new_id}" not in [h for h, _ in st["desk"]]):
        bad.append(f"tải lại mất thay đổi: {st}")
    if new_id and pg.evaluate("(id) => (document.querySelector('#' + id + ' [data-w17-custom-title]') || {}).textContent", new_id) != "Khách hàng tiêu biểu":
        bad.append("tải lại mất chữ của mục mới")
    html = pg.evaluate("() => w17CloneCleanHtml()")
    if re.search(r'class="[^"]*w17-section-controls', html) or re.search(r'<a [^>]*draggable=', html):
        bad.append("Final còn nút điều khiển/thuộc tính kéo-thả")
    if "Dịch vụ của TJ" not in html or (new_id and f'id="{new_id}"' not in html):
        bad.append("Final thiếu tên menu mới hoặc mục mới")
    st_code, _ = _post(env, "/api/save", {"html": html, "targets": ["index.html"]})
    pub = R.new_page(ctx)
    R.open_page(pub, env, R.FINAL_PORTFOLIO)
    st = pub.evaluate(NAV_JS)
    if st_code != 200 or ["#services", "Dịch vụ của TJ"] not in st["desk"] or (new_id and [f"#{new_id}", "Khách hàng"] not in st["desk"]):
        bad.append(f"Final đã lưu ({st_code}): {st['desk']}")
    pg.evaluate("(k) => localStorage.removeItem(k)", P_KEY)
    if errors:
        bad.append("lỗi JS: " + " | ".join(errors[:2]))
    ctx.close()
    env.reset_work()
    R.record("R10", "R10-04 mục ↔ menu: tắt Sửa chữ ẩn nút điều khiển; đổi tên menu (2 menu), Alt+← và kéo-thả trên menu, thêm mục mới, xóa phải xác nhận; giữ sau tải lại, vào Final và hiện trên web; Giới thiệu/Liên hệ khóa", not bad, " | ".join(bad[:6]))


def t_cv_trash(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, R.CREATOR_CV, wait=800)
    pg.evaluate("toggleEditMode()"); pg.wait_for_timeout(250)
    ids = "[...document.querySelectorAll('#education-grid > .edu-card-item')].map((c) => c.getAttribute('data-card-id'))"
    edu = pg.evaluate(ids)
    target = edu[0]
    btn = f"#education-grid > [data-card-id='{target}'] .delete-btn"
    tag_btn = "#skill-groups-list .skill-tag .delete-btn"
    n_tags = pg.evaluate("document.querySelectorAll('#skill-groups-list .skill-tag').length")
    pg.click(tag_btn); pg.wait_for_timeout(100)
    if pg.evaluate("document.querySelectorAll('#skill-groups-list .skill-tag').length") != n_tags:
        bad.append("tag kỹ năng bị xóa khi mới bấm 1 lần")
    pg.wait_for_timeout(4200)   # hết 4 giây: nút tự trả về trạng thái thường
    pg.click(btn); pg.wait_for_timeout(150)
    if target not in pg.evaluate(ids):
        bad.append("bấm ✕ lần 1 đã xóa (không xác nhận)")
    pg.click(btn); pg.wait_for_timeout(200)
    if target in pg.evaluate(ids) or pg.text_content("#cv-trash-count") != "1":
        bad.append("bấm ✕ lần 2 không xóa / không vào thùng rác")
    pg.click("#btn-cv-trash"); pg.wait_for_timeout(150)
    pg.click(f"#w17-cv-trash [data-trash-id='{target}'] button"); pg.wait_for_timeout(200)
    if target not in pg.evaluate(ids) or pg.text_content("#cv-trash-count") != "0":
        bad.append("khôi phục không đưa thẻ trở lại")
    # xóa lại (xác nhận), tải lại: thẻ vẫn ẩn và còn trong thùng rác, khôi phục được
    pg.click(btn); pg.click(btn); pg.wait_for_timeout(200)
    pg.reload(wait_until="load"); pg.wait_for_timeout(800)
    if target in pg.evaluate(ids) or pg.text_content("#cv-trash-count") != "1":
        bad.append("sau tải lại: thẻ đã xóa hiện lại hoặc không còn trong thùng rác")
    pg.click("#btn-cv-trash"); pg.wait_for_timeout(150)
    pg.click(f"#w17-cv-trash [data-trash-id='{target}'] button"); pg.wait_for_timeout(200)
    html = pg.evaluate("() => cloneCleanHtmlCV()")
    if target not in pg.evaluate(ids) or f'data-card-id="{target}"' not in html or 'id="w17-cv-trash"' in html:
        bad.append("sau tải lại không khôi phục được / Final sai")
    pg.evaluate("(k) => localStorage.removeItem(k)", CV_KEY)
    ctx.close()
    env.reset_work()
    R.record("R10", "R10-05 CV: xóa thẻ Học vấn/tag kỹ năng phải bấm 2 lần, vào thùng rác, khôi phục từng thẻ (cả sau tải lại); Final không mang thùng rác", not bad, " | ".join(bad))


def t_cdn_blocked(b, env):
    bad = []
    env.reset_work()
    import fitz
    pages = {}
    for blocked in (False, True):
        ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
        if blocked:
            ctx.route("**/*", lambda r: r.abort() if not r.request.url.startswith(env.base) else r.continue_())
        pg = R.new_page(ctx)
        R.open_page(pg, env, R.FINAL_CV, wait=1200)
        doc = fitz.open(stream=pg.pdf(format="A4", print_background=True), filetype="pdf")
        text = " ".join(p.get_text() for p in doc)
        two_col = pg.evaluate("() => document.getElementById('avatar-img').getBoundingClientRect().left > document.querySelector('[data-i18n=hero_title]').getBoundingClientRect().left + 300")
        pages[blocked] = doc.page_count
        if "Đổi ảnh" in text or not two_col:
            bad.append(f"{'chặn CDN' if blocked else 'có mạng'}: in 'Đổi ảnh'={('Đổi ảnh' in text)} hai cột={two_col}")
        if blocked:
            R.open_page(pg, env, R.FINAL_PORTFOLIO, wait=900)
            if pg.evaluate("getComputedStyle(document.querySelector('[data-w17-nav-list=desktop]')).display") != "flex":
                bad.append("Portfolio chặn CDN: mất menu ngang")
        ctx.close()
    if pages[True] != pages[False]:
        bad.append(f"số trang PDF: có mạng {pages[False]}, chặn CDN {pages[True]}")
    R.record("R10", f"R10-06 chặn mọi CDN: PDF CV {pages.get(True)} trang = khi có mạng ({pages.get(False)}), không in 'Đổi ảnh', giữ bố cục; Portfolio giữ menu ngang", not bad, " | ".join(bad))
