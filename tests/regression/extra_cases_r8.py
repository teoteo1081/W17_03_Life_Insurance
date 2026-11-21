# -*- coding: utf-8 -*-
"""
R8 — P0-3: GA4 cho Portfolio + CV, đồng ý (Consent Mode v2, lựa chọn 2b), sự kiện, không lọt dữ liệu cá nhân.

KHÔNG gửi dữ liệu thật lên Google: trang "công khai" được giả lập bằng route của Playwright (phục vụ file trong bản sao tạm
dưới địa chỉ https://teoteo1081.github.io/W17_03_Claude_porfolio/), gtag.js được thay bằng file rỗng, mọi request tới
google-analytics.com / googletagmanager.com khác đều bị chặn. Kiểm bằng cách đọc window.dataLayer.

  R8-01  localhost (Final + editor) và trình duyệt tự động thật: không tải gtag, không có dataLayer, không request Google
  R8-02  web công khai (múi giờ VN): consent mặc định (từ chối ở EEA/UK/CH, cho phép nơi khác, quảng cáo luôn từ chối),
         config đúng Measurement ID + content_group; không banner; bấm thật sinh đúng sự kiện ở Portfolio và CV;
         form liên hệ chỉ ghi contact_mailto_open; KHÔNG có tên/email/số điện thoại/nội dung khách gõ trong dataLayer
  R8-03  múi giờ châu Âu: banner hiện; Từ chối -> consent update denied + nhớ lựa chọn, tải lại không hiện nữa;
         nút "Quyền riêng tư & cookie" mở lại banner (4 ngôn ngữ cho nhãn nút); Đồng ý -> update granted
  R8-04  ?ga_debug=1 bật debug_mode (DebugView); Final lưu từ editor không chứa banner/gtag.js
"""

import json

R = None  # gán bởi run_all

PUBLIC = "https://teoteo1081.github.io/W17_03_Claude_porfolio/"
GA_ID = "G-501ZEXPEVQ"
PII = ["Nguyen Van Khach", "khach.test@example.com", "0901234567", "Noi dung bi mat"]
PRIVACY = {"vi": "Quyền riêng tư & cookie", "en": "Privacy & cookies", "es": "Privacidad y cookies", "zh": "隐私与 Cookie"}

DL_JS = "() => JSON.stringify((window.dataLayer || []).map((a) => Array.from(a)))"
EVENTS_JS = "() => (window.dataLayer || []).map((a) => Array.from(a)).filter((a) => a[0] === 'event').map((a) => [a[1], a[2]])"
STOP_NAV_JS = """() => { window.__noNav = (e) => { const a = e.target.closest && e.target.closest('a[href]'); if (a) e.preventDefault(); };
  window.addEventListener('click', window.__noNav); window.print = () => {}; }"""


def _public_context(b, env, tz="Asia/Ho_Chi_Minh"):
    ctx = b.new_context(locale="vi-VN", timezone_id=tz, viewport={"width": 1280, "height": 900})
    ctx.add_init_script("Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false });")
    sent = []

    def serve(route):
        path = route.request.url.split("?")[0][len(PUBLIC):] or "index.html"
        f = env.work / path
        if f.is_file() and f.suffix == ".html":
            route.fulfill(status=200, body=f.read_bytes(), headers={"Content-Type": "text/html; charset=utf-8"})
        else:
            route.fulfill(status=404, body=b"")

    def google(route):
        sent.append(route.request.url)
        if "googletagmanager.com/gtag/js" in route.request.url:
            route.fulfill(status=200, body=b"/* stub */", headers={"Content-Type": "application/javascript"})
        else:
            route.abort()

    ctx.route(PUBLIC + "**", serve)
    ctx.route("**/*google-analytics.com/**", google)
    ctx.route("**/*googletagmanager.com/**", google)
    ctx.route("**/*analytics.google.com/**", google)
    return ctx, sent


def _goto(pg, url, wait=900):
    pg.goto(url, wait_until="load")
    pg.wait_for_timeout(wait)


def t_no_tracking_local(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    reqs = []
    ctx.on("request", lambda r: reqs.append(r.url) if ("google-analytics" in r.url or "googletagmanager" in r.url) else None)
    pg = R.new_page(ctx)
    for rel in R.ALL_PAGES:
        R.open_page(pg, env, rel)
        st = pg.evaluate("() => ({ dl: typeof window.dataLayer, track: typeof window.w17Track, gtag: !!document.querySelector('script[src*=\"googletagmanager\"]') })")
        if st != {"dl": "undefined", "track": "function", "gtag": False}:
            bad.append(f"{rel}: {st}")
        pg.evaluate("() => { const a = document.querySelector('a[href^=\"tel:\"], a[href^=\"mailto:\"]'); if (a) { a.addEventListener('click', (e) => e.preventDefault(), { once: true }); a.click(); } }")
    if reqs:
        bad.append(f"có request Google: {reqs[:3]}")
    ctx.close()
    R.record("R8", "R8-01 localhost/editor/trình duyệt tự động: không tải gtag, không dataLayer, không request Google (4 trang)", not bad, " | ".join(bad))


def t_public_events(b, env):
    bad = []
    env.reset_work()
    ctx, sent = _public_context(b, env)
    pg = R.new_page(ctx)
    # ---------------- Portfolio ----------------
    _goto(pg, PUBLIC)
    dl = json.loads(pg.evaluate(DL_JS))
    consents = [a for a in dl if a[0] == "consent" and a[1] == "default"]
    if len(consents) != 2 or consents[0][2].get("analytics_storage") != "denied" or not {"DE", "FR", "GB", "CH"} <= set(consents[0][2].get("region", [])) \
            or consents[1][2].get("analytics_storage") != "granted" or "region" in consents[1][2] \
            or any(c[2].get(k) != "denied" for c in consents for k in ("ad_storage", "ad_user_data", "ad_personalization")):
        bad.append(f"consent mặc định sai: {consents}")
    cfgs = [a for a in dl if a[0] == "config"]
    if len(cfgs) != 1 or cfgs[0][1] != GA_ID or cfgs[0][2].get("content_group") != "portfolio" or cfgs[0][2].get("debug_mode"):
        bad.append(f"config Portfolio: {cfgs}")
    if not any(f"gtag/js?id={GA_ID}" in u for u in sent):
        bad.append("không tải gtag.js đúng ID")
    if pg.locator("#w17-consent-banner").count():
        bad.append("banner hiện ở múi giờ VN")
    pg.evaluate(STOP_NAV_JS)
    clicks = [
        ("#contact a[href^='tel:']", "contact_phone_click"),
        ("#contact a[href^='mailto:'] [data-i18n=contact_btn_email]", "contact_email_click"),
        ("#contact a[href*='zalo.me'] [data-i18n=contact_btn_zalo]", "contact_zalo_click"),
        ("#main-navbar a[href$='index_portfolio_clean.html']", "cv_from_portfolio_click"),
        ("[data-i18n=spoke1_btn_demo]", "project_demo_click"),
    ]
    for sel, _ in clicks:
        loc = pg.locator(sel).first
        loc.scroll_into_view_if_needed()
        loc.click()
    pg.evaluate("() => openGA4DrilldownModal('countries', null, 'p1')")
    pg.evaluate("() => closeGA4DrilldownModal()")
    pg.evaluate(R.SELECT_LANG_JS, "en")
    pg.evaluate(R.SELECT_LANG_JS, "vi")
    pg.fill("#formName", PII[0])
    pg.fill("#formEmail", PII[1])
    pg.fill("#formMessage", PII[2] + " " + PII[3])
    pg.evaluate("() => { window.location.assign = () => {}; }")
    pg.evaluate("() => document.getElementById('contactForm').requestSubmit()")
    pg.wait_for_timeout(300)
    ev = pg.evaluate(EVENTS_JS)
    names = [e[0] for e in ev]
    want = [w for _, w in clicks] + ["service_detail_open", "language_change", "language_change", "contact_mailto_open"]
    if names != want:
        bad.append(f"Portfolio sự kiện {names} (cần {want})")
    if ev:
        if ev[0][1].get("link_location") != "contact" or ev[3][1].get("link_location") != "nav":
            bad.append(f"link_location sai: {ev[0][1]} / {ev[3][1]}")
        if ev[4][1].get("project_id") != "spoke1" or ev[5][1].get("service_id") != "p1" or ev[6][1].get("language") != "en":
            bad.append(f"tham số sự kiện sai: {ev[4:7]}")
    dump = pg.evaluate(DL_JS)
    for s in PII + ["mailto:", "tel:+", "teoteo108@gmail.com", "zalo.me/"]:
        if s in dump:
            bad.append(f"dataLayer chứa {s!r}")
    # ---------------- CV ----------------
    _goto(pg, PUBLIC + "index_portfolio_clean.html")
    dl = json.loads(pg.evaluate(DL_JS))
    cfgs = [a for a in dl if a[0] == "config"]
    if len(cfgs) != 1 or cfgs[0][2].get("content_group") != "cv":
        bad.append(f"config CV: {cfgs}")
    pg.evaluate(STOP_NAV_JS)
    for sel in ("a[data-w17-link='portfolio']", "#btn-cv-pdf", "#portfolio-root > section a[href^='tel:']",
                "#portfolio-root > section a[href^='mailto:']", "#portfolio-root > section a[href*='github.com']", "a[href='./index.html']"):
        pg.locator(sel).first.click()
    ev = pg.evaluate(EVENTS_JS)
    names = [e[0] for e in ev]
    want = ["portfolio_from_cv_click", "cv_pdf_export_click", "contact_phone_click", "contact_email_click", "github_click", "portfolio_from_cv_click"]
    if names != want:
        bad.append(f"CV sự kiện {names} (cần {want})")
    elif ev[0][1].get("link_location") != "hero" or ev[4][1].get("link_type") != "profile" or ev[5][1].get("link_location") != "topbar":
        bad.append(f"CV tham số: {ev}")
    if any(e[1].get("content_group") != "cv" for e in ev):
        bad.append("sự kiện CV thiếu content_group=cv")
    ctx.close()
    R.record("R8", "R8-02 web công khai (giả lập, không gửi Google): consent mặc định 2b, config đúng ID/content_group, 11 sự kiện Portfolio + 6 sự kiện CV đúng tên/tham số, không lọt tên/email/số/nội dung khách gõ", not bad, " | ".join(bad[:6]))


def t_consent_europe(b, env):
    bad = []
    env.reset_work()
    ctx, _ = _public_context(b, env, tz="Europe/Berlin")
    pg = R.new_page(ctx)
    _goto(pg, PUBLIC)
    if not pg.locator("#w17-consent-banner").is_visible():
        bad.append("múi giờ châu Âu: banner không hiện")
    else:
        pg.click("#w17-consent-decline")
        dl = json.loads(pg.evaluate(DL_JS))
        if ["consent", "update", {"analytics_storage": "denied"}] not in dl:
            bad.append("Từ chối không gửi consent update denied")
        if pg.evaluate("() => localStorage.getItem('w17_03_consent')") != "denied":
            bad.append("không nhớ lựa chọn từ chối")
    _goto(pg, PUBLIC)
    if pg.locator("#w17-consent-banner").count():
        bad.append("đã chọn rồi mà banner vẫn hiện lại")
    dl = json.loads(pg.evaluate(DL_JS))
    if ["consent", "update", {"analytics_storage": "denied"}] not in dl:
        bad.append("tải lại không áp lựa chọn đã lưu")
    for l in R.LOCALES:
        pg.evaluate(R.SELECT_LANG_JS, l)
        txt = pg.locator("footer [data-w17-consent-open]").text_content().strip()
        if txt != PRIVACY[l]:
            bad.append(f"nhãn nút quyền riêng tư/{l}: {txt!r}")
    pg.evaluate(R.SELECT_LANG_JS, "vi")
    pg.locator("footer [data-w17-consent-open]").click()
    if not pg.locator("#w17-consent-banner").is_visible() or "từ chối" not in (pg.text_content("#w17-consent-banner") or ""):
        bad.append("nút quyền riêng tư không mở lại banner kèm lựa chọn hiện tại")
    else:
        pg.click("#w17-consent-accept")
        dl = json.loads(pg.evaluate(DL_JS))
        if ["consent", "update", {"analytics_storage": "granted"}] not in dl:
            bad.append("Đồng ý không gửi consent update granted")
    _goto(pg, PUBLIC + "index_portfolio_clean.html")
    pg.locator("footer [data-w17-consent-open]").click()
    if not pg.locator("#w17-consent-banner").is_visible():
        bad.append("CV: nút quyền riêng tư không mở banner")
    ctx.close()
    R.record("R8", "R8-03 múi giờ châu Âu: banner hiện; Từ chối/Đồng ý cập nhật consent và được nhớ; nút Quyền riêng tư (4 ngôn ngữ) mở lại banner ở Portfolio và CV", not bad, " | ".join(bad))


def t_debug_and_clean(b, env):
    bad = []
    env.reset_work()
    ctx, _ = _public_context(b, env)
    pg = R.new_page(ctx)
    _goto(pg, PUBLIC + "?ga_debug=1")
    dl = json.loads(pg.evaluate(DL_JS))
    cfgs = [a for a in dl if a[0] == "config"]
    if not cfgs or cfgs[0][2].get("debug_mode") is not True:
        bad.append(f"?ga_debug=1 không bật debug_mode: {cfgs}")
    ctx.close()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    for rel, fn in ((R.CREATOR_PORTFOLIO, "w17CloneCleanHtml"), (R.CREATOR_CV, "cloneCleanHtmlCV")):
        R.open_page(pg, env, rel)
        pg.locator("footer [data-w17-consent-open]").click()
        if not pg.locator("#w17-consent-banner").count():
            bad.append(f"{rel}: nút quyền riêng tư không mở banner trong editor")
        html = pg.evaluate(f"() => {fn}()")
        if 'id="w17-consent-banner"' in html or 'src="https://www.googletagmanager.com' in html:
            bad.append(f"{rel}: Final chứa banner hoặc gtag.js")
    ctx.close()
    R.record("R8", "R8-04 ?ga_debug=1 bật DebugView; Final lưu từ editor không chứa banner/gtag.js", not bad, " | ".join(bad))
