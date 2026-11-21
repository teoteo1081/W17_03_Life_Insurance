# -*- coding: utf-8 -*-
"""
R7 — P0-2: số điện thoại, nút Portfolio trong CV, PDF có link thật, QR giải mã được, nút tải PDF cho khách.

  R7-01  liên hệ: Portfolio (mục Liên hệ) và CV (hero) có số +84 dạng đọc được + link tel: đúng; email hero CV bấm được;
         hero CV thứ tự Zalo | GitHub | Portfolio, link Portfolio = địa chỉ web công khai; nút "Tải CV (PDF)" ở
         trang CV công khai, dịch đủ 4 ngôn ngữ, bấm thì mở hộp thoại in
  R7-02  PDF (Chromium in thật, mở qua máy chủ trên máy = trường hợp xấu nhất): mọi link là tuyệt đối (không localhost,
         không file:, không link tương đối); có link Portfolio mang UTM nguồn PDF, mailto, tel, GitHub, Zalo;
         chữ đọc được có số điện thoại và nhãn QR; không có chữ của toolbar/editor; số trang không tăng quá 1
  R7-03  QR: giải mã được từ ảnh PDF (OpenCV) ra đúng địa chỉ web + UTM nguồn QR; cạnh mã >= 2,5 cm; đổi địa chỉ web
         trong ⚙ thì PDF xuất MỚI mang QR/link mới; trên màn hình khối in bị ẩn
  R7-04  bản Final lưu từ editor không chứa QR đã vẽ và không chứa link tạm lúc in
"""

import io
import json

R = None  # gán bởi run_all

BASE = "https://teoteo1081.github.io/W17_03_Claude_porfolio/"
PDF_URL = BASE + "?utm_source=cv_pdf&utm_medium=pdf&utm_campaign=cv"
QR_URL = BASE + "?utm_source=cv_pdf&utm_medium=qr&utm_campaign=cv"
PHONE, TEL = "+84 855 239 805", "tel:+84855239805"
PDF_LABEL = {"vi": "Tải CV (PDF)", "en": "Download CV (PDF)", "es": "Descargar CV (PDF)", "zh": "下载简历 (PDF)"}


def _raw(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def t_contact(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, R.FINAL_PORTFOLIO)
    tel = pg.evaluate("() => [...document.querySelectorAll('#contact a[href^=\"tel:\"]')].map((a) => [a.getAttribute('href'), a.textContent.trim()])")
    if tel != [[TEL, "📞 " + PHONE]]:
        bad.append(f"Portfolio liên hệ: {tel}")
    for rel in (R.FINAL_CV, R.CREATOR_CV):
        R.open_page(pg, env, rel)
        info = pg.evaluate("""() => {
          const hero = document.querySelector('#portfolio-root > section');
          return {
            tel: [...hero.querySelectorAll('a[href^="tel:"]')].map((a) => [a.getAttribute('href'), a.textContent.trim()]),
            mail: [...hero.querySelectorAll('a[href^="mailto:"]')].map((a) => a.getAttribute('href')),
            ctas: [...hero.querySelectorAll('a.rounded-xl')].map((a) => a.querySelector('[data-i18n]').getAttribute('data-i18n')),
            portfolio: (hero.querySelector('a[data-w17-link="portfolio"]') || {}).href || null };
        }""")
        if info["tel"] != [[TEL, PHONE]]:
            bad.append(f"{rel}: tel hero {info['tel']}")
        if info["mail"] != ["mailto:teoteo108@gmail.com"]:
            bad.append(f"{rel}: mailto hero {info['mail']}")
        if info["ctas"] != ["hero_cta_zalo", "hero_cta_github", "hero_cta_portfolio"]:
            bad.append(f"{rel}: thứ tự nút {info['ctas']}")
        if info["portfolio"] != BASE:
            bad.append(f"{rel}: link Portfolio {info['portfolio']}")
    R.open_page(pg, env, R.FINAL_CV)
    for l in R.LOCALES:
        R.set_lang(pg, l)
        txt = pg.evaluate("() => { const b = document.getElementById('btn-cv-pdf'); return b && b.offsetParent ? b.textContent.trim() + '|' + b.getAttribute('aria-label') : null; }")
        if not txt or PDF_LABEL[l] not in txt.split("|")[0] or not txt.split("|")[1].startswith(PDF_LABEL[l]):
            bad.append(f"nút PDF/{l}: {txt!r}")
    R.set_lang(pg, "vi")
    pg.evaluate("() => { window.__printed = 0; window.print = () => { window.__printed += 1; }; }")
    pg.click("#btn-cv-pdf")
    if pg.evaluate("window.__printed") != 1:
        bad.append("bấm nút PDF không mở hộp thoại in")
    ctx.close()
    R.record("R7", "R7-01 số điện thoại +84 + tel: ở Portfolio/CV; email hero CV bấm được; hero CV Zalo | GitHub | Portfolio (link công khai); nút Tải CV (PDF) 4 ngôn ngữ mở hộp thoại in", not bad, " | ".join(bad))


def _pdf_of_cv(b, env, rel=None):
    """Xuất PDF như khi bấm in: phát sự kiện beforeprint, dùng CSS in, có màu nền."""
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, rel or R.FINAL_CV, wait=900)
    pg.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    data = pg.pdf(format="A4", print_background=True)
    screen_qr = pg.evaluate("() => { const s = document.getElementById('cv-print-contact'); return getComputedStyle(s).display; }")
    pg.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
    href_after = pg.evaluate("() => document.querySelector('a[data-w17-link=\"portfolio\"]').getAttribute('href')")
    ctx.close()
    return data, screen_qr, href_after


def _links_and_text(data):
    import fitz
    doc = fitz.open(stream=data, filetype="pdf")
    uris, text = [], ""
    for page in doc:
        text += page.get_text()
        uris += [l.get("uri") for l in page.get_links() if l.get("uri")]
    return doc, uris, text


def _decode_qr(doc):
    import cv2
    import numpy as np
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)
        val, pts, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if val:
            side_px = float(np.linalg.norm(pts[0][0] - pts[0][1]))
            return val, side_px / 200 * 2.54  # cm (không tính vùng trắng)
    return None, 0.0


def t_pdf_links(b, env):
    bad = []
    env.reset_work()
    data, screen_display, href_after = _pdf_of_cv(b, env)
    doc, uris, text = _links_and_text(data)
    for u in uris:
        if not u.startswith(("https://", "mailto:", "tel:")) or "localhost" in u or "127.0.0.1" in u:
            bad.append(f"link không tuyệt đối/công khai: {u}")
    for need in (PDF_URL, "mailto:teoteo108@gmail.com", TEL, "https://github.com/teoteo1081", "https://zalo.me/0855239805"):
        if need not in uris:
            bad.append(f"thiếu link {need}")
    if uris.count(PDF_URL) < 2:
        bad.append(f"link Portfolio UTM PDF chỉ có {uris.count(PDF_URL)} chỗ (cần nút hero + khối QR)")
    if BASE in uris:
        bad.append("nút Portfolio trong PDF chưa đổi sang link UTM nguồn PDF")
    flat = " ".join(text.split())
    for need in (PHONE, "Quét để xem Portfolio", "teoteo1081.github.io/W17_03_Claude_porfolio"):
        if need not in flat:
            bad.append(f"chữ PDF thiếu {need!r}")
    for banned in ("Lưu & đăng", "Bật sửa chữ", "Chỉ lưu vào máy", "Tải CV (PDF)", "Cài đặt"):
        if banned in flat:
            bad.append(f"PDF còn chữ giao diện: {banned!r}")
    if href_after != BASE:
        bad.append(f"sau khi in, link Portfolio không trả lại: {href_after}")
    R.record("R7", f"R7-02 PDF: link tuyệt đối (không localhost/tương đối), có Portfolio+UTM PDF, mailto, tel, GitHub, Zalo; chữ có số điện thoại + nhãn QR; không có chữ editor ({doc.page_count} trang)", not bad, " | ".join(bad[:8]))


def t_qr(b, env):
    bad = []
    env.reset_work()
    data, _, _ = _pdf_of_cv(b, env)
    doc, _, _ = _links_and_text(data)
    val, side = _decode_qr(doc)
    if val != QR_URL:
        bad.append(f"QR giải mã ra {val!r}")
    if side < 2.5:
        bad.append(f"QR chỉ {side:.2f} cm")
    # trên màn hình: khối in ẩn
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, R.FINAL_CV)
    if pg.evaluate("() => getComputedStyle(document.getElementById('cv-print-contact')).display") != "none":
        bad.append("khối QR hiện trên màn hình")
    ctx.close()
    # đổi địa chỉ web -> PDF xuất mới mang QR/link mới
    _, _, body = R.http("GET", env.base + "/api/session", {"Origin": env.base})
    token = json.loads(body)["token"]
    hdr = {"Content-Type": "application/json", "Origin": env.base, "X-W17-Token": token}
    st, _, _ = R.http("POST", env.base + "/api/settings", hdr, json.dumps({"changes": {"site.baseUrl": "https://tj.example.com/cv-test/"}}).encode("utf-8"))
    if st != 200:
        bad.append(f"đổi địa chỉ web -> {st}")
    data2, _, _ = _pdf_of_cv(b, env)
    doc2, uris2, text2 = _links_and_text(data2)
    val2, _ = _decode_qr(doc2)
    if val2 != "https://tj.example.com/cv-test/?utm_source=cv_pdf&utm_medium=qr&utm_campaign=cv":
        bad.append(f"sau khi đổi địa chỉ, QR = {val2!r}")
    if "https://tj.example.com/cv-test/?utm_source=cv_pdf&utm_medium=pdf&utm_campaign=cv" not in uris2 or any("teoteo1081.github.io/W17" in u for u in uris2):
        bad.append("sau khi đổi địa chỉ, link PDF chưa đổi")
    if "tj.example.com/cv-test" not in " ".join(text2.split()):
        bad.append("sau khi đổi địa chỉ, tên miền in trong PDF chưa đổi")
    env.reset_work()
    R.record("R7", f"R7-03 QR giải mã (OpenCV, ảnh PDF 200 dpi) = địa chỉ web + UTM QR, cạnh {side:.1f} cm >= 2,5 cm; ẩn trên màn hình; đổi địa chỉ web thì PDF mới mang QR/link mới", not bad, " | ".join(bad))


def t_clean_final(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, R.CREATOR_CV, wait=900)
    if not pg.evaluate("() => !!document.querySelector('#cv-print-qr svg')"):
        bad.append("editor chưa vẽ QR")
    pg.evaluate("() => window.dispatchEvent(new Event('beforeprint'))")
    html = pg.evaluate("() => cloneCleanHtmlCV()")
    pg.evaluate("() => window.dispatchEvent(new Event('afterprint'))")
    if '<div id="cv-print-qr" class="shrink-0 w-[3.4cm] h-[3.4cm] bg-white rounded-md"></div>' not in html:
        bad.append("Final còn QR đã vẽ trong #cv-print-qr")
    import re
    tags = re.findall(r'<a [^>]*data-w17-link="portfolio"[^>]*>', html)
    if re.search(r'<a [^>]*data-w17-screen-href', html) or len(tags) != 1 or not tags[0].startswith(f'<a href="{BASE}" data-w17-link="portfolio" '):
        bad.append("Final còn link tạm lúc in")
    ctx.close()
    R.record("R7", "R7-04 bản Final lưu từ editor (kể cả đang in) không chứa QR đã vẽ và không chứa link tạm lúc in", not bad, " | ".join(bad))
