# -*- coding: utf-8 -*-
"""
R6 — P0-1: cấu hình dùng chung (w17-site-config, ⚙ Cài đặt) và khôi phục bản nháp CV không làm mất thẻ mới.

  R6-01  tools/site_config.py --check trên bản sao: khối cấu hình hợp lệ, giống nhau ở 2 trang; canonical/og:url
         trỏ địa chỉ công khai (không phải gốc teoteo1081.github.io/ đang 404); settings script giống nhau
  R6-02  /api/settings: chặn origin lạ/thiếu token/giá trị sai (file không đổi); đổi hợp lệ thay MỌI chỗ ở cả 2 Final
         (href, chữ 4 ngôn ngữ, mailto trong JS), giữ link repo github.com/<tên>/<repo>, cập nhật canonical/og:url,
         sinh lại Creator, check() vẫn sạch
  R6-03  /api/save từ chối (409) bản lưu từ trang mở TRƯỚC khi đổi cài đặt; file trên đĩa giữ cài đặt mới
  R6-04  CV: bản nháp có knownIds giữ thẻ/tag MỚI (đặt cuối), vẫn xóa thẻ đã xóa; bản nháp cũ (không knownIds) giữ cách cũ;
         bản nháp mới ghi knownIds
  R6-05  editor: nút ⚙ mở hộp thoại có đủ giá trị, lưu thật qua server rồi tải lại; giá trị sai hiện lỗi;
         HTML Final xuất ra khi hộp thoại đang mở không chứa hộp thoại
"""

import importlib.util
import io
import json

R = None  # gán bởi run_all

OLD = {
    "contact.email": "teoteo108@gmail.com",
    "contact.phone": "+84 855 239 805",
    "contact.zaloUrl": "https://zalo.me/0855239805",
    "contact.githubUrl": "https://github.com/teoteo1081",
    "site.baseUrl": "https://teoteo1081.github.io/W17_03_Claude_porfolio/",
    "ga4.measurementId": "G-501ZEXPEVQ",
}
NEW = {
    "contact.email": "tj.work@example.com",
    "contact.phone": "+1 415 555 0100",
    "contact.zaloUrl": "https://zalo.me/0900000001",
    "contact.githubUrl": "https://github.com/tj-new-account",
    "site.baseUrl": "https://tj.example.com/portfolio/",
    "ga4.measurementId": "G-TEST123456",
}
FINALS = ["index.html", "index_portfolio_clean.html"]


def _site(env):
    spec = importlib.util.spec_from_file_location("w17_site_config_test", R.REPO / "tools" / "site_config.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sync(env):
    spec = importlib.util.spec_from_file_location("w17_sync_test", R.REPO / "tools" / "sync_creators.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _raw(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _token(env):
    _, _, body = R.http("GET", env.base + "/api/session", {"Origin": env.base})
    return json.loads(body)["token"]


def _post(env, path, payload, token=None, origin=None):
    hdr = {"Content-Type": "application/json", "Origin": origin or env.base}
    if token is not False:
        hdr["X-W17-Token"] = token or _token(env)
    st, _, body = R.http("POST", env.base + path, hdr, json.dumps(payload).encode("utf-8"))
    try:
        return st, json.loads(body.decode("utf-8"))
    except ValueError:
        return st, {}


def _hashes(env):
    return {n: R.sha(env.work / n) for n in FINALS + ["editor_workspace/editor_portfolio.html", "editor_workspace/editor_cv.html"]}


def t_static_config(env):
    S = _site(env)
    env.reset_work()
    problems = S.check(env.work)
    bad = list(problems)
    for name in FINALS:
        html = _raw(env.work / name)
        if 'content="https://teoteo1081.github.io/"' in html or 'href="https://teoteo1081.github.io/"' in html:
            bad.append(f"{name}: còn og:url/canonical trỏ gốc teoteo1081.github.io/ (404)")
    R.record("R6", "R6-01 khối w17-site-config hợp lệ & giống nhau ở 2 trang; canonical/og:url = địa chỉ công khai; settings script giống nhau", not bad, " | ".join(bad))


def t_settings_api(env):
    S, Y = _site(env), _sync(env)
    bad = []
    env.reset_work()
    st, _, body = R.http("GET", env.base + "/api/settings", {"Origin": env.base})
    got = json.loads(body).get("values") if st == 200 else None
    if got != OLD:
        bad.append(f"GET values={got} st={st}")
    st, _, _ = R.http("GET", env.base + "/api/settings", {"Origin": "http://evil.example"})
    if st != 403:
        bad.append(f"GET origin lạ -> {st}")

    before = _hashes(env)
    cases = [
        ("thiếu token", {"changes": {"contact.email": NEW["contact.email"]}}, False, None, 401),
        ("origin lạ", {"changes": {"contact.email": NEW["contact.email"]}}, None, "http://evil.example", 403),
        ("email sai", {"changes": {"contact.email": "a\"><script>x</script>@b.c"}}, None, None, 400),
        ("điện thoại không có mã nước", {"changes": {"contact.phone": "0855 239 805"}}, None, None, 400),
        ("điện thoại quá ngắn", {"changes": {"contact.phone": "+84 12"}}, None, None, 400),
        ("github kèm repo", {"changes": {"contact.githubUrl": "https://github.com/teoteo1081/repo"}}, None, None, 400),
        ("web localhost", {"changes": {"site.baseUrl": "https://localhost/x/"}}, None, None, 400),
        ("web repo GitHub", {"changes": {"site.baseUrl": "https://github.com/teoteo1081/W17/"}}, None, None, 400),
        ("web http", {"changes": {"site.baseUrl": "http://tj.example.com/"}}, None, None, 400),
        ("GA4 ID sai dạng", {"changes": {"ga4.measurementId": "UA-12345-1"}}, None, None, 400),
        ("trường lạ", {"changes": {"ga4.hosts": "x"}}, None, None, 400),
        ("changes không phải object", {"changes": "x"}, None, None, 400),
    ]
    for label, payload, token, origin, want in cases:
        st, data = _post(env, "/api/settings", payload, token=token, origin=origin)
        if st != want:
            bad.append(f"{label}: {st} (cần {want}) {data.get('message', '')[:80]}")
    if _hashes(env) != before:
        bad.append("request bị từ chối nhưng file đã đổi")

    st, data = _post(env, "/api/settings", {"changes": {k: OLD[k] for k in OLD}})
    if st != 200 or data.get("changed") != []:
        bad.append(f"không đổi gì -> {st} {data}")
    if _hashes(env) != before:
        bad.append("không đổi gì nhưng file đã đổi")

    st, data = _post(env, "/api/settings", {"changes": NEW})
    if st != 200 or sorted(data.get("changed", [])) != sorted(NEW) or not data.get("creator_synced"):
        bad.append(f"đổi hợp lệ -> {st} {str(data)[:200]}")
    pages = {n: _raw(env.work / n) for n in FINALS}
    for name, html in pages.items():
        for old in (OLD["contact.email"], OLD["contact.zaloUrl"], OLD["contact.phone"], "tel:+84855239805"):
            if old in html:
                bad.append(f"{name}: còn {old}")
        if 'href="tel:+14155550100"' not in html or "+1 415 555 0100" not in html:
            bad.append(f"{name}: thiếu số điện thoại mới / link tel")
        if "https://tj.example.com/portfolio/" not in html:
            bad.append(f"{name}: thiếu địa chỉ web mới")
        if 'href="https://github.com/teoteo1081"' in html:
            bad.append(f"{name}: còn href GitHub cũ")
        if NEW["contact.email"] not in html or NEW["contact.zaloUrl"] not in html:
            bad.append(f"{name}: thiếu giá trị mới")
    p = pages["index.html"]
    for needle in ['href="https://github.com/tj-new-account"', 'href="mailto:tj.work@example.com"',
                   "https://github.com/teoteo1081/w15-website-us-tax",           # link repo giữ nguyên
                   '<link rel="canonical" href="https://tj.example.com/portfolio/">',
                   '<meta property="og:url" content="https://tj.example.com/portfolio/">',
                   "return 'tj.work@example.com';"]:
        if needle not in p:
            bad.append(f"index.html thiếu {needle[:70]}")
    if p.count("tj.work@example.com") < 9:   # href + nút + 4 locale contact_btn_email + 4 form_success_msg + config
        bad.append(f"index.html: email mới chỉ có {p.count('tj.work@example.com')} chỗ")
    c = pages["index_portfolio_clean.html"]
    for needle in ['<link rel="canonical" href="https://tj.example.com/portfolio/index_portfolio_clean.html">',
                   'hero_email: "tj.work@example.com"', 'href="https://github.com/tj-new-account"']:
        if needle not in c:
            bad.append(f"CV thiếu {needle[:70]}")
    bad += [f"check: {x}" for x in S.check(env.work)]
    for src, dst, reps in Y.JOBS:
        if _raw(env.work / dst) != Y.build(src, reps, env.work):
            bad.append(f"{dst} lệch Final sau khi đổi cài đặt")
    st, _, body = R.http("GET", env.base + "/api/settings", {"Origin": env.base})
    if json.loads(body).get("values") != NEW:
        bad.append("GET sau khi đổi không trả giá trị mới")
    env.reset_work()
    R.record("R6", "R6-02 /api/settings: chặn origin/token/giá trị sai (file không đổi); đổi hợp lệ thay mọi chỗ ở 2 trang, giữ link repo, cập nhật canonical/og:url, Creator đồng bộ", not bad, " | ".join(bad[:8]))


def t_stale_save(env):
    bad = []
    env.reset_work()
    stale = _raw(env.work / "index.html")
    st, data = _post(env, "/api/settings", {"changes": {"contact.email": NEW["contact.email"]}})
    if st != 200:
        bad.append(f"đổi cài đặt -> {st}")
    after_settings = R.sha(env.work / "index.html")
    st, data = _post(env, "/api/save", {"html": stale, "targets": ["index.html"]})
    if st != 409:
        bad.append(f"lưu bản cũ -> {st} (cần 409) {data.get('message', '')[:80]}")
    if R.sha(env.work / "index.html") != after_settings:
        bad.append("bản cũ đã ghi đè file")
    fresh = _raw(env.work / "index.html")
    st, data = _post(env, "/api/save", {"html": fresh, "targets": ["index.html"]})
    if st != 200:
        bad.append(f"lưu bản mới -> {st} {data.get('message', '')[:80]}")
    no_cfg = fresh.replace('id="w17-site-config"', 'id="w17-site-config-x"')
    st, data = _post(env, "/api/save", {"html": no_cfg, "targets": ["index.html"]})
    if st != 422:
        bad.append(f"thiếu khối cấu hình -> {st} (cần 422)")
    env.reset_work()
    R.record("R6", "R6-03 /api/save từ chối 409 bản lưu từ trang mở trước khi đổi cài đặt (file giữ cài đặt mới); thiếu khối cấu hình -> 422", not bad, " | ".join(bad))


ORDER_JS = """() => ({
  sol: Array.from(document.querySelectorAll('#solutions-grid > .solution-card-item')).map((c) => c.getAttribute('data-card-id')),
  tags: Array.from(document.querySelectorAll('.skill-group-card[data-group-id="skill_grp_1"] .skill-tag')).map((t) => t.getAttribute('data-tag-id'))
})"""


def t_cv_known_ids(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    pg = R.new_page(ctx)
    R.open_page(pg, env, "editor_workspace/editor_cv.html")
    base = pg.evaluate(ORDER_JS)
    sol, tags = base["sol"], base["tags"]
    if len(sol) < 3 or len(tags) < 2:
        bad.append(f"không đủ thẻ để kiểm: {base}")
    else:
        key = "tj_capability_w17_03_state_v1"
        first, second, third = sol[0], sol[1], sol[2]
        keep_tags = [{"id": tags[1], "i18nKey": None, "text": "X"}]
        scenarios = [
            # (nhãn, trường thêm vào bản nháp, thứ tự thẻ mong đợi, tag mong đợi)
            ("không có trong thứ tự, không ghi nhận xóa: giữ, đặt cuối", {}, [second, first, third], [tags[1], tags[0]] + tags[2:]),
            ("ghi nhận xóa tường minh (deletedIds): gỡ", {"deletedIds": [third, tags[0]]}, [second, first], [tags[1]] + tags[2:]),
            ("nháp P0-1 chỉ có knownIds: KHÔNG suy 'vắng = đã xóa'", {"knownIds": [second, first, third] + tags}, [second, first, third], [tags[1], tags[0]] + tags[2:]),
        ]
        for label, extra, want_sol, want_tags in scenarios:
            state = {"schema": 1, "solutionsOrder": [second, first],
                     "skillTagsByGroup": {"skill_grp_1": keep_tags}}
            state.update(extra)
            pg.evaluate("([k, v]) => localStorage.setItem(k, v)", [key, json.dumps(state)])
            pg.reload(wait_until="load")
            pg.wait_for_timeout(600)
            got = pg.evaluate(ORDER_JS)
            if got["sol"] != want_sol:
                bad.append(f"{label}: thẻ {got['sol']} (cần {want_sol})")
            if sorted(got["tags"]) != sorted(want_tags) or got["tags"][0] != tags[1]:
                bad.append(f"{label}: tag {got['tags']} (cần {want_tags})")
            if "deletedIds" in extra:
                pg.evaluate("() => saveCurrentState()")
                saved = json.loads(pg.evaluate("(k) => localStorage.getItem(k)", key) or "{}")
                if sorted(saved.get("deletedIds") or []) != sorted(extra["deletedIds"]):
                    bad.append(f"bản nháp mới không giữ deletedIds: {saved.get('deletedIds')}")
                if pg.evaluate("document.getElementById('cv-trash-count') ? document.getElementById('cv-trash-count').textContent : null") != "2":
                    bad.append("thẻ đã xóa không vào thùng rác khi khôi phục nháp")
        pg.evaluate("(k) => localStorage.removeItem(k)", key)
    ctx.close()
    env.reset_work()
    R.record("R6", "R6-04 CV: khôi phục nháp chỉ gỡ thẻ/tag có trong deletedIds (vào thùng rác); thẻ vắng mặt không bị coi là đã xóa (kể cả nháp chỉ có knownIds)", not bad, " | ".join(bad))


def t_settings_dialog(b, env):
    bad = []
    env.reset_work()
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
    errors = []
    pg = R.new_page(ctx, errors)
    for rel, clone_fn in (("editor_workspace/editor_cv.html", "cloneCleanHtmlCV"), ("editor_workspace/editor_portfolio.html", "w17CloneCleanHtml")):
        R.open_page(pg, env, rel)
        btn = pg.locator("#btn-site-settings")
        if not btn.is_visible():
            bad.append(f"{rel}: không thấy nút ⚙")
            continue
        btn.click()
        pg.wait_for_selector("#w17-settings-dialog[open] #w17-settings-save:not([disabled])", timeout=5000)
        vals = pg.evaluate("() => Array.from(document.querySelectorAll('#w17-settings-dialog input')).map((i) => i.value)")
        if vals != list(OLD.values()):
            bad.append(f"{rel}: giá trị trong hộp thoại {vals}")
        html = pg.evaluate(f"() => {clone_fn}()")
        if 'id="w17-settings-dialog"' in html or "<dialog" in html:
            bad.append(f"{rel}: HTML Final chứa hộp thoại cài đặt")
        if rel.endswith("editor_cv.html"):
            pg.fill("#w17-set-contact-email", "sai-email")
            pg.click("#w17-settings-save")
            pg.wait_for_timeout(500)
            msg = pg.text_content("#w17-settings-status") or ""
            if "Email" not in msg:
                bad.append(f"giá trị sai không báo lỗi rõ: {msg!r}")
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(200)
            if pg.locator("#w17-settings-dialog").count():
                bad.append("Escape không đóng hộp thoại")
            continue
        pg.fill("#w17-set-contact-email", NEW["contact.email"])
        with pg.expect_navigation(timeout=8000):
            pg.click("#w17-settings-save")
        pg.wait_for_timeout(500)
        if NEW["contact.email"] not in _raw(env.work / "index_portfolio_clean.html"):
            bad.append("lưu qua hộp thoại không ghi CV")
        if 'href="mailto:tj.work@example.com"' not in pg.content():
            bad.append("trang tải lại chưa có email mới")
    if errors:
        bad.append("lỗi JS: " + " | ".join(errors[:3]))
    ctx.close()
    env.reset_work()
    R.record("R6", "R6-05 editor: nút ⚙ mở hộp thoại đủ giá trị, lưu thật rồi tải lại, giá trị sai báo lỗi, Escape đóng; HTML Final không chứa hộp thoại (2 trang)", not bad, " | ".join(bad))
