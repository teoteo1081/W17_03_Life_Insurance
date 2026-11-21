# -*- coding: utf-8 -*-
"""
R11 — hoàn thiện: SEO kỹ thuật, thẻ bên trong mục (Portfolio), thẻ CV (xóa giải pháp/số liệu, thêm học vấn), cờ chủ trang GA4.

  R11-01  SEO: JSON-LD hợp lệ (WebSite + Person, CV thêm ProfilePage) khớp cấu hình, không có rating/review; og:image +
          twitter:image tuyệt đối trỏ file có thật; robots index; sitemap.xml đúng 2 URL; đổi địa chỉ web trong ⚙ thì
          JSON-LD, ảnh chia sẻ và sitemap đổi theo
  R11-02  Portfolio thẻ trong mục: chỉ hiện nút khi bật Sửa chữ; đổi chỗ thẻ dịch vụ -> số thứ tự tự đánh lại; ẩn thẻ ->
          không hiện trên web, số bỏ qua thẻ ẩn; thêm thẻ website có link; giữ sau tải lại; Final đúng và sạch nút;
          xóa thẻ tự thêm phải bấm 2 lần
  R11-03  CV: thẻ giải pháp/số liệu có ✕ (2 lần), vào thùng rác, khôi phục; thêm thẻ học vấn, giữ sau tải lại, vào Final
  R11-04  cờ chủ trang: ?toi_la_chu_trang=1 -> traffic_type=internal (nhớ cho lần sau), =0 bỏ; không gửi Google thật
"""

import io
import json
import re

R = None  # gán bởi run_all
X8 = None  # gán bởi run_all (dùng lại trang công khai giả lập của R8)

P_KEY = "w17_03_portfolio_edits_v1"
CV_KEY = "tj_capability_w17_03_state_v1"


def _raw(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _hdr(env):
    _, _, body = R.http("GET", env.base + "/api/session", {"Origin": env.base})
    return {"Content-Type": "application/json", "Origin": env.base, "X-W17-Token": json.loads(body)["token"]}


def _jsonld(html):
    m = re.search(r'<script type="application/ld\+json" id="w17-jsonld">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else None


def t_seo(b, env):
    bad = []
    env.reset_work()
    base = "https://teoteo1081.github.io/W17_03_Claude_porfolio/"
    for name, img in (("index.html", "assets/og-portfolio.png"), ("index_portfolio_clean.html", "assets/og-cv.png")):
        html = _raw(env.work / name)
        ld = _jsonld(html)
        if not ld:
            bad.append(f"{name}: thiếu JSON-LD")
            continue
        types = {n["@type"]: n for n in ld["@graph"]}
        person = types.get("Person", {})
        if types.get("WebSite", {}).get("url") != base or person.get("email") != "teoteo108@gmail.com" or person.get("telephone") != "+84855239805" \
                or person.get("sameAs") != ["https://github.com/teoteo1081"]:
            bad.append(f"{name}: JSON-LD lệch cấu hình {person}")
        if name.startswith("index_portfolio_clean") and types.get("ProfilePage", {}).get("mainEntity", {}).get("@id") != base + "#person":
            bad.append("CV thiếu ProfilePage trỏ Person")
        if re.search(r"aggregateRating|\"review\"|Review", json.dumps(ld)):
            bad.append(f"{name}: JSON-LD có đánh giá/review")
        for tag in ('<meta property="og:image" content="' + base + img + '">', '<meta name="twitter:image" content="' + base + img + '">',
                    '<meta name="robots" content="index, follow">', '<meta name="twitter:card" content="summary_large_image">'):
            if tag not in html:
                bad.append(f"{name}: thiếu {tag[:60]}")
        if not (env.work / img).is_file():
            bad.append(f"thiếu file {img}")
    sm = _raw(env.work / "sitemap.xml")
    if re.findall(r"<loc>(.*?)</loc>", sm) != [base, base + "index_portfolio_clean.html"]:
        bad.append(f"sitemap sai: {sm}")
    st, _, body = R.http("POST", env.base + "/api/settings", _hdr(env), json.dumps({"changes": {"site.baseUrl": "https://tj.example.com/p/"}}).encode("utf-8"))
    if st != 200:
        bad.append(f"đổi địa chỉ web -> {st}")
    else:
        ld = _jsonld(_raw(env.work / "index_portfolio_clean.html"))
        html = _raw(env.work / "index.html")
        if not ld or {n["@type"]: n for n in ld["@graph"]}["ProfilePage"]["url"] != "https://tj.example.com/p/index_portfolio_clean.html" \
                or '<meta property="og:image" content="https://tj.example.com/p/assets/og-portfolio.png">' not in html \
                or "<loc>https://tj.example.com/p/</loc>" not in _raw(env.work / "sitemap.xml"):
            bad.append("đổi địa chỉ web: JSON-LD/ảnh chia sẻ/sitemap chưa đổi")
    env.reset_work()
    (env.work / "sitemap.xml").write_text(sm, encoding="utf-8", newline="\n")
    R.record("R11", "R11-01 SEO: JSON-LD (WebSite/Person/ProfilePage) khớp cấu hình, không rating/review; og/twitter image tuyệt đối có file; robots; sitemap 2 URL; đổi địa chỉ web thì tất cả đổi theo", not bad, " | ".join(bad[:6]))


CARDS_JS = """(g) => [...document.querySelectorAll('[data-w17-card-group=' + g + '] > [data-w17-card]')].map((c) => c.getAttribute('data-w17-card'))"""
# Số do CSS counter vẽ: trình duyệt không cho đọc số đã tính, nên kiểm cơ chế: thẻ hiện có counter-increment, ::before dùng counter.
NUM_JS = """() => [...document.querySelectorAll('[data-w17-card-group=services] > [data-w17-card]')].filter((c) => getComputedStyle(c).display !== 'none')
  .map((c) => [c.getAttribute('data-w17-card'), getComputedStyle(c).counterIncrement.startsWith('w17svc') && getComputedStyle(c.querySelector('h3[data-i18n]'), '::before').content.includes('counter(w17svc)') ? 'ok' : 'x'])"""


def t_portfolio_cards(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    errors = []
    pg = R.new_page(ctx, errors)
    R.open_page(pg, env, R.CREATOR_PORTFOLIO, wait=900)
    vis = "() => [...document.querySelectorAll('.w17-card-controls')].filter((c) => c.offsetParent !== null).length"
    if pg.evaluate(vis) != 0:
        bad.append("tắt Sửa chữ mà còn nút thẻ")
    pg.click("#btn-toggle-edit"); pg.wait_for_timeout(250)
    if pg.evaluate(vis) != 10:
        bad.append(f"bật Sửa chữ: {pg.evaluate(vis)} thanh nút thẻ (cần 10)")
    before = pg.evaluate(CARDS_JS, "services")
    pg.click(f"[data-w17-card='{before[1]}'] > .w17-card-controls [data-role=prev]"); pg.wait_for_timeout(150)
    after = pg.evaluate(CARDS_JS, "services")
    if after[:2] != [before[1], before[0]]:
        bad.append(f"đổi chỗ thẻ dịch vụ: {after}")
    nums = pg.evaluate(NUM_JS)
    if any(n != 'ok' for _, n in nums) or nums[0][0] != before[1]:
        bad.append(f"số thứ tự không đánh lại: {nums[:3]}")
    pg.click(f"[data-w17-card='{before[2]}'] > .w17-card-controls [data-role=toggle]"); pg.wait_for_timeout(150)
    # thêm thẻ website
    pg.click(".w17-card-add"); pg.wait_for_timeout(200)
    new_id = pg.evaluate("() => { const c = [...document.querySelectorAll('[data-w17-card-group=website] > [data-w17-custom-card]')].pop(); return c && c.getAttribute('data-w17-card'); }")
    if not new_id:
        bad.append("không thêm được thẻ website")
    else:
        pg.fill(f"[data-w17-card='{new_id}'] [data-role=url]", "https://example.com/demo")
        pg.dispatch_event(f"[data-w17-card='{new_id}'] [data-role=url]", "change")
        pg.evaluate("(id) => { const h = document.querySelector('[data-w17-card=\"' + id + '\"] [data-w17-cc-title]'); h.textContent = 'Website khách mẫu'; h.dispatchEvent(new Event('input', {bubbles: true})); }", new_id)
        pg.click(f"[data-w17-card='{new_id}'] [data-role=del]"); pg.wait_for_timeout(100)
        if not pg.evaluate("(id) => !!document.querySelector('[data-w17-card=\"' + id + '\"]')", new_id):
            bad.append("xóa thẻ tự thêm không cần xác nhận")
    pg.reload(wait_until="load"); pg.wait_for_timeout(900)
    if pg.evaluate(CARDS_JS, "services")[:2] != [before[1], before[0]] or not pg.evaluate("(id) => document.querySelector('[data-w17-card=\"' + id + '\"]').hasAttribute('data-w17-hidden')", before[2]):
        bad.append("tải lại mất thứ tự/ẩn thẻ")
    if new_id and pg.evaluate("(id) => { const c = document.querySelector('[data-w17-card=\"' + id + '\"]'); return c ? [c.querySelector('[data-w17-cc-title]').textContent, c.querySelector('a[data-w17-cc-link]').getAttribute('href')] : null; }", new_id) != ["Website khách mẫu", "https://example.com/demo"]:
        bad.append("tải lại mất thẻ website mới")
    html = pg.evaluate("() => w17CloneCleanHtml()")
    if re.search(r'class="[^"]*w17-card-(controls|add)', html) or (new_id and f'data-w17-card="{new_id}"' not in html):
        bad.append("Final còn nút thẻ hoặc thiếu thẻ mới")
    st, _, _ = R.http("POST", env.base + "/api/save", _hdr(env), json.dumps({"html": html, "targets": ["index.html"]}).encode("utf-8"))
    pub = R.new_page(ctx)
    R.open_page(pub, env, R.FINAL_PORTFOLIO)
    shown = pub.evaluate(NUM_JS)
    if st != 200 or before[2] in [c for c, _ in shown] or len(shown) != 5 or any(n != 'ok' for _, n in shown):
        bad.append(f"Final đã lưu ({st}): {shown}")
    if new_id and pub.evaluate("(id) => { const a = document.querySelector('[data-w17-card=\"' + id + '\"] a[data-w17-cc-link]'); return a && a.offsetParent !== null; }", new_id) is not True:
        bad.append("thẻ website mới không hiện trên web")
    pg.evaluate("(k) => localStorage.removeItem(k)", P_KEY)
    if errors:
        bad.append("lỗi JS: " + " | ".join(errors[:2]))
    ctx.close()
    env.reset_work()
    R.record("R11", "R11-02 Portfolio thẻ trong mục: nút chỉ khi Sửa chữ; đổi chỗ -> số tự đánh lại; ẩn thẻ (web bỏ qua, số bỏ qua); thêm thẻ website có link; giữ sau tải lại; Final sạch, hiện trên web; xóa thẻ tự thêm phải xác nhận", not bad, " | ".join(bad[:6]))


def t_cv_cards(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, R.CREATOR_CV, wait=800)
    if pg.evaluate("getComputedStyle(document.getElementById('btn-add-edu') || document.body).display") not in ("none",) and pg.evaluate("!!document.getElementById('btn-add-edu')"):
        bad.append("tắt Sửa chữ mà còn nút Thêm học vấn")
    pg.evaluate("toggleEditMode()"); pg.wait_for_timeout(250)
    sol = "[...document.querySelectorAll('#solutions-grid > .solution-card-item')].map((c) => c.getAttribute('data-card-id'))"
    first = pg.evaluate(sol)[0]
    btn = f"#solutions-grid > [data-card-id='{first}'] > .delete-btn"
    pg.click(btn); pg.wait_for_timeout(100)
    if first not in pg.evaluate(sol):
        bad.append("thẻ giải pháp bị xóa khi mới bấm 1 lần")
    pg.click(btn); pg.wait_for_timeout(200)
    if first in pg.evaluate(sol):
        bad.append("bấm 2 lần không xóa thẻ giải pháp")
    pg.click("#btn-cv-trash"); pg.click(f"#w17-cv-trash [data-trash-id='{first}'] button"); pg.wait_for_timeout(200)
    if first not in pg.evaluate(sol):
        bad.append("không khôi phục được thẻ giải pháp")
    # Khối 3 bước (thẻ số liệu) đã bỏ khỏi CV theo chủ hồ sơ (2026-11-21)
    if pg.evaluate("() => !!document.getElementById('metrics-grid')"):
        bad.append("CV còn khối 3 bước (metrics) đã bỏ")
    pg.click("#btn-add-edu"); pg.wait_for_timeout(200)
    new_id = pg.evaluate("() => { const c = document.querySelector('[data-w17-custom-edu]'); return c && c.getAttribute('data-card-id'); }")
    if not new_id:
        bad.append("không thêm được thẻ học vấn")
    else:
        pg.evaluate("(id) => { const t = document.querySelector('[data-card-id=\"' + id + '\"] [data-w17-edu-title]'); t.textContent = 'Chứng chỉ Power BI PL-300'; t.dispatchEvent(new Event('input', {bubbles: true})); saveCurrentState(); }", new_id)
        pg.reload(wait_until="load"); pg.wait_for_timeout(800)
        got = pg.evaluate("(id) => { const c = document.querySelector('[data-card-id=\"' + id + '\"]'); return c ? c.querySelector('[data-w17-edu-title]').textContent : null; }", new_id)
        if got != "Chứng chỉ Power BI PL-300":
            bad.append(f"tải lại mất thẻ học vấn mới: {got!r}")
        html = pg.evaluate("() => cloneCleanHtmlCV()")
        if f'data-card-id="{new_id}"' not in html or "Chứng chỉ Power BI PL-300" not in html or 'id="btn-add-edu"' in html:
            bad.append("Final thiếu thẻ học vấn mới hoặc còn nút thêm")
    pg.evaluate("(k) => localStorage.removeItem(k)", CV_KEY)
    ctx.close()
    env.reset_work()
    R.record("R11", "R11-03 CV: thẻ giải pháp có ✕, không còn khối 3 bước; (bấm 2 lần) + thùng rác khôi phục; thêm thẻ học vấn, giữ sau tải lại, vào Final", not bad, " | ".join(bad))


def t_owner_flag(b, env):
    bad = []
    env.reset_work()
    ctx, _ = X8._public_context(b, env)
    pg = R.new_page(ctx)
    internal = "() => JSON.stringify((window.dataLayer || []).map((a) => Array.from(a))).includes('\"traffic_type\":\"internal\"')"
    X8._goto(pg, X8.PUBLIC)
    if pg.evaluate(internal):
        bad.append("khách thường bị đánh dấu nội bộ")
    X8._goto(pg, X8.PUBLIC + "?toi_la_chu_trang=1")
    if not pg.evaluate(internal):
        bad.append("?toi_la_chu_trang=1 không đánh dấu nội bộ")
    X8._goto(pg, X8.PUBLIC + "index_portfolio_clean.html")
    if not pg.evaluate(internal):
        bad.append("không nhớ cờ chủ trang cho lần sau / trang CV")
    X8._goto(pg, X8.PUBLIC + "?toi_la_chu_trang=0")
    if pg.evaluate(internal):
        bad.append("?toi_la_chu_trang=0 không bỏ đánh dấu")
    ctx.close()
    R.record("R11", "R11-04 cờ chủ trang: ?toi_la_chu_trang=1 -> traffic_type=internal (nhớ cho lần sau, cả CV), =0 bỏ; khách thường không bị đánh dấu", not bad, " | ".join(bad))
