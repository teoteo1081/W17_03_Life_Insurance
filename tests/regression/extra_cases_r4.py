# -*- coding: utf-8 -*-
"""
R4 — luồng sửa đơn giản (MO_EDITOR.bat → sửa → [Lưu & đăng lên web]).

  R4-01  lưu Final qua /api/save thì file Creator được sinh lại đúng bằng build(Final)
  R4-02  /api/publish: chỉ commit 4 file trang, push lên remote; không có thay đổi thì không tạo commit;
         chặn token/origin lạ; GitHub có bản mới hơn → 409, không force push; sai nhánh → 409
  R4-03  web công khai (host không phải localhost) không hiện bản nháp trong trình duyệt; editor thì vẫn hiện
         và có dòng nhắc "bản xem thử"; nút đăng không gửi gì
  R4-04  chạy thật trên giao diện: editor mở tiếng Việt (trình duyệt en-US), sửa → đổi sang EN + giao diện sáng →
         bấm [Lưu & đăng lên web] → remote có commit, file Final ở dạng chuẩn (lang vi, dark, og:title tiếng Việt),
         editor tải lại là bản đã sửa, bản nháp đã dọn; lặp lại lần 2 không phình file

Remote là repo Git trần trong thư mục tạm; không chạm GitHub thật.
"""

import io
import importlib.util
import json
import re
import shutil
import subprocess
from urllib.parse import urlsplit

R = None  # gán bởi run_all

PUBLISH_PATHS = {"index.html", "index_portfolio_clean.html", "editor_workspace/editor_portfolio.html", "editor_workspace/editor_cv.html"}


def _raw(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_raw(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _sync(env):
    spec = importlib.util.spec_from_file_location("w17_sync_test", env.work / "tools" / "sync_creators.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _token(env):
    _, _, body = R.http("GET", env.base + "/api/session", {"Origin": env.base})
    return json.loads(body)["token"]


def _post(env, path, payload, token=None, origin=None):
    hdr = {"Content-Type": "application/json", "Origin": origin or env.base,
           "X-W17-Token": _token(env) if token is None else token}
    st, _, body = R.http("POST", env.base + path, hdr, json.dumps(payload).encode("utf-8"))
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        data = None
    return st, data


def _git(cwd, *args, check=True):
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r


def _init_repo(env):
    """Biến thư mục làm việc tạm thành repo Git nhánh main, remote là repo trần cục bộ."""
    work = env.work
    shutil.rmtree(work / ".git", ignore_errors=True)
    remote = env.tmp / "remote.git"
    shutil.rmtree(remote, ignore_errors=True)
    _git(env.tmp, "init", "--bare", "-b", "main", str(remote))
    _git(work, "init", "-b", "main")
    for k, v in (("user.name", "W17 Test"), ("user.email", "w17-test@example.invalid"), ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
        _git(work, "config", k, v)
    _git(work, "add", "-A")
    _git(work, "commit", "-m", "init")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-u", "origin", "main")
    return remote


def _cleanup_repo(env):
    shutil.rmtree(env.work / ".git", ignore_errors=True)
    shutil.rmtree(env.tmp / "remote.git", ignore_errors=True)
    shutil.rmtree(env.tmp / "other", ignore_errors=True)
    shutil.copyfile(env.pristine / "README.md", env.work / "README.md")
    env.reset_work()


def _remote_head(remote):
    return _git(remote, "rev-parse", "main").stdout.strip()


def _remote_files(remote):
    return set(_git(remote, "show", "--name-only", "--format=", "main").stdout.split())


def t_save_syncs_creator(env):
    bad = []
    sync = _sync(env)
    cases = [("index.html", "editor_workspace/editor_portfolio.html", "Cách đọc số liệu này"),
             ("index_portfolio_clean.html", "editor_workspace/editor_cv.html", "Business English")]
    for final, creator, marker in cases:
        env.reset_work()
        html = _raw(env.work / final)
        if marker not in html:
            bad.append(f"{final}: thiếu chuỗi mốc '{marker}'")
            continue
        st, data = _post(env, "/api/save", {"html": html.replace(marker, marker + " R4", 1), "targets": [final]})
        if st != 200 or not data or data.get("creator_synced") is not True:
            bad.append(f"{final}: lưu trả {st} {data and {k: data.get(k) for k in ('creator_synced', 'creators', 'message')}}")
            continue
        ctext = _raw(env.work / creator)
        if marker + " R4" not in ctext or 'data-w17-mode="creator"' not in ctext:
            bad.append(f"{creator}: không mang nội dung vừa lưu hoặc mất cờ creator")
        _, expected = sync.creator_for(final, root=env.work)
        if expected != ctext:
            bad.append(f"{creator}: khác build(Final)")
    env.reset_work()
    R.record("R4-01", "lưu Final qua /api/save thì file editor (Creator) được sinh lại đúng bằng build(Final) (portfolio + CV)", not bad, " | ".join(bad))


def t_publish_api(env):
    bad = []
    try:
        remote = _init_repo(env)
        head0 = _remote_head(remote)
        # chặn yêu cầu không hợp lệ trước khi làm gì với Git
        st, _ = _post(env, "/api/publish", {}, token="sai-token")
        if st != 401:
            bad.append(f"token sai phải 401, nhận {st}")
        st, _ = _post(env, "/api/publish", {}, origin="http://evil.example")
        if st != 403:
            bad.append(f"origin lạ phải 403, nhận {st}")
        if _remote_head(remote) != head0:
            bad.append("yêu cầu bị chặn nhưng remote vẫn đổi")

        # lưu một thay đổi + sửa một file ngoài danh sách đăng
        html = _raw(env.work / "index.html")
        st, data = _post(env, "/api/save", {"html": html.replace("Cách đọc số liệu này", "Cách đọc số liệu này R4-02", 1), "targets": ["index.html"]})
        if st != 200:
            bad.append(f"lưu trước khi đăng trả {st}")
        _write_raw(env.work / "README.md", _raw(env.work / "README.md") + "\nthay đổi chỉ trên máy\n")
        st, data = _post(env, "/api/publish", {})
        if st != 200 or not data or not data.get("pushed") or not data.get("committed"):
            bad.append(f"đăng lần 1 trả {st} {data}")
        else:
            files = _remote_files(remote)
            if not files or not files <= PUBLISH_PATHS:
                bad.append(f"commit chứa file ngoài danh sách: {sorted(files - PUBLISH_PATHS)}")
            if not {"index.html", "editor_workspace/editor_portfolio.html"} <= files:
                bad.append(f"commit thiếu Final/Creator: {sorted(files)}")
            if "R4-02" not in _git(remote, "show", "main:index.html").stdout:
                bad.append("remote không có nội dung vừa lưu")
            if not _git(env.work, "status", "--porcelain", "--", "README.md").stdout.strip():
                bad.append("README.md (ngoài danh sách) lẽ ra vẫn chưa commit")

        # không có gì mới: 200, không tạo commit
        head1 = _remote_head(remote)
        st, data = _post(env, "/api/publish", {})
        if st != 200 or not data or data.get("committed") is not False or _remote_head(remote) != head1:
            bad.append(f"đăng khi không có thay đổi trả {st} {data}")

        # GitHub có bản mới hơn: 409, không force push
        other = env.tmp / "other"
        _git(env.tmp, "clone", "-b", "main", str(remote), str(other))
        for k, v in (("user.name", "Other"), ("user.email", "other@example.invalid"), ("commit.gpgsign", "false")):
            _git(other, "config", k, v)
        _write_raw(other / "ghi-chu.txt", "commit từ máy khác\n")
        _git(other, "add", "ghi-chu.txt")
        _git(other, "commit", "-m", "commit khác")
        _git(other, "push", "origin", "main")
        head_other = _remote_head(remote)
        html = _raw(env.work / "index.html")
        _post(env, "/api/save", {"html": html.replace("Cách đọc số liệu này R4-02", "Cách đọc số liệu này R4-02b", 1), "targets": ["index.html"]})
        st, data = _post(env, "/api/publish", {})
        if st != 409 or not data or data.get("pushed") is not False:
            bad.append(f"remote mới hơn phải 409, nhận {st} {data}")
        if _remote_head(remote) != head_other:
            bad.append("remote bị ghi đè khi đang có bản mới hơn (force push?)")

        # sai nhánh: 409
        _git(env.work, "checkout", "-b", "thu-nghiem")
        st, data = _post(env, "/api/publish", {})
        if st != 409:
            bad.append(f"đăng từ nhánh khác main phải 409, nhận {st}")
        _git(env.work, "checkout", "main")

        # không phải repo Git: báo lỗi rõ, không 200
        shutil.rmtree(env.work / ".git", ignore_errors=True)
        st, data = _post(env, "/api/publish", {})
        if st == 200 or not data or data.get("status") != "error":
            bad.append(f"thư mục không có Git phải báo lỗi, nhận {st} {data}")
    except Exception as exc:  # noqa
        bad.append(f"ngoại lệ: {exc}")
    finally:
        _cleanup_repo(env)
    R.record("R4-02", "/api/publish: chỉ commit 4 file trang và push; không thay đổi thì không commit; chặn token/origin lạ; remote mới hơn → 409 không force; sai nhánh/không có Git → lỗi rõ", not bad, " | ".join(bad[:6]))


def t_public_host_drafts(b, env):
    bad = []
    env.reset_work()
    pub = "http://w17-public.test"
    ctx = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})

    def handler(route):
        rel = urlsplit(route.request.url).path.lstrip("/") or "index.html"
        path = env.work / rel
        if path.is_file():
            route.fulfill(status=200, path=str(path))
        else:
            route.fulfill(status=404, body="not found")

    ctx.route(pub + "/**", handler)
    ctx.add_init_script("""try {
      localStorage.setItem('w17_03_portfolio_edits_v1', JSON.stringify({schema: 1, editsByLang: {vi: {hero_badge: 'DRAFT-R4-PORTFOLIO'}}}));
      localStorage.setItem('tj_capability_w17_03_state_v1', JSON.stringify({schema: 1, textEditsByLang: {vi: {pill_lang: 'DRAFT-R4-CV'}}}));
    } catch (e) {}""")
    pg = R.new_page(ctx)
    checks = [
        (f"{pub}/index.html", "[data-i18n=hero_badge]", "DRAFT-R4-PORTFOLIO", False),
        (f"{pub}/index_portfolio_clean.html", "[data-i18n=pill_lang]", "DRAFT-R4-CV", False),
        (f"{pub}/{R.CREATOR_PORTFOLIO}", "[data-i18n=hero_badge]", "DRAFT-R4-PORTFOLIO", True),
        (f"{pub}/{R.CREATOR_CV}", "[data-i18n=pill_lang]", "DRAFT-R4-CV", True),
        (f"{env.base}/index.html", "[data-i18n=hero_badge]", "DRAFT-R4-PORTFOLIO", True),
    ]
    for url, sel, draft, want_draft in checks:
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(700)
        txt = pg.inner_text(sel).strip()
        if (txt == draft) != want_draft:
            bad.append(f"{url}: '{txt}' (phải {'là' if want_draft else 'không phải'} bản nháp)")
        if "/editor_workspace/" in url:
            if not pg.evaluate("(() => { const n = document.getElementById('w17-not-local-notice'); return !!(n && n.offsetParent && n.textContent.includes('MO_EDITOR.bat')); })()"):
                bad.append(f"{url}: không có dòng nhắc 'bản xem thử'")
            sent = []
            pg.on("request", lambda r: sent.append(r.url) if "/api/" in r.url else None)
            pg.click("#btn-publish")
            pg.wait_for_timeout(500)
            if sent:
                bad.append(f"{url}: nút đăng vẫn gửi yêu cầu {sent}")
            if "MO_EDITOR.bat" not in pg.inner_text("#toast-notification"):
                bad.append(f"{url}: nút đăng không nhắc mở bằng MO_EDITOR.bat")
    ctx.close()
    R.record("R4-03", "web công khai không hiện bản nháp trong trình duyệt (portfolio + CV); editor trên web công khai vẫn hiện nháp, có dòng nhắc 'bản xem thử', nút đăng không gửi gì; máy chủ trên máy vẫn hiện nháp", not bad, " | ".join(bad[:6]))


def _edit_badge(pg, text):
    if not pg.evaluate("document.body.classList.contains('is-editing')"):
        pg.click("#btn-toggle-edit")
        pg.wait_for_timeout(250)
    pg.evaluate("""(t) => { const e = document.querySelector('[data-i18n=hero_badge]'); e.focus(); e.textContent = t; e.dispatchEvent(new Event('input', {bubbles: true})); }""", text)
    pg.wait_for_timeout(200)


def t_editor_publish_e2e(b, env):
    bad = []
    sizes = []
    try:
        remote = _init_repo(env)
        ctx = b.new_context(locale="en-US", viewport={"width": 1280, "height": 900}, accept_downloads=True)
        pg = R.new_page(ctx)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        R.open_page(pg, env, R.CREATOR_PORTFOLIO)
        if pg.evaluate("document.documentElement.lang") != "vi":
            bad.append("editor không mở bằng tiếng Việt khi trình duyệt là en-US")
        for cycle, text in enumerate(("R4 E2E lần 1", "R4 E2E lần 2"), start=1):
            head_before = _remote_head(remote)
            _edit_badge(pg, text)
            R.set_lang(pg, "en")
            if cycle == 1:
                pg.evaluate("toggleTheme()")  # giao diện sáng lúc bấm đăng
            with pg.expect_navigation(timeout=60000):
                pg.click("#btn-publish")
            pg.wait_for_timeout(800)
            if "🚀" not in pg.inner_text("#toast-notification"):
                bad.append(f"lần {cycle}: không thấy thông báo đã đăng sau khi tải lại")
            if _remote_head(remote) == head_before:
                bad.append(f"lần {cycle}: remote không có commit mới")
            final = _raw(env.work / "index.html")
            sizes.append(len(final))
            if not re.search(r'<html lang="vi" class="dark scroll-smooth"[ >]', final):
                bad.append(f"lần {cycle}: thẻ <html> của Final không ở dạng chuẩn: {re.search(r'<html[^>]*>', final).group(0)}")
            og = re.search(r'<meta property="og:title" content="([^"]*)"', final)
            if not og or "Chuyên viên Vận hành" not in og.group(1):
                bad.append(f"lần {cycle}: og:title không phải tiếng Việt: {og and og.group(1)}")
            if text not in _raw(env.work / R.CREATOR_PORTFOLIO):
                bad.append(f"lần {cycle}: file editor không mang chữ vừa sửa")
            _, expected = _sync(env).creator_for("index.html", root=env.work)
            if expected != _raw(env.work / R.CREATOR_PORTFOLIO):
                bad.append(f"lần {cycle}: file editor lệch khỏi build(Final)")
            drafts = pg.evaluate("JSON.parse(localStorage.getItem('w17_03_portfolio_edits_v1') || 'null')")
            if not drafts or any(drafts.get("editsByLang", {}).values()):
                bad.append(f"lần {cycle}: bản nháp chưa được dọn {drafts}")
            R.set_lang(pg, "vi")
            if pg.inner_text("[data-i18n=hero_badge]").strip() != text:
                bad.append(f"lần {cycle}: editor tải lại không phải bản đã sửa")
        if len(sizes) == 2 and sizes[1] > sizes[0] * 1.02:
            bad.append(f"file Final phình sau mỗi lần lưu: {sizes}")
        if errs:
            bad.append(f"lỗi JS: {errs[:2]}")
        ctx.close()
        # người xem mới (không có bộ nhớ trình duyệt) thấy đúng bản đã đăng
        ctx2 = b.new_context(locale="vi-VN", viewport={"width": 1280, "height": 900})
        pg2 = R.new_page(ctx2)
        R.open_page(pg2, env, R.FINAL_PORTFOLIO)
        if pg2.inner_text("[data-i18n=hero_badge]").strip() != "R4 E2E lần 2":
            bad.append("người xem mới không thấy bản đã đăng")
        ctx2.close()
    except Exception as exc:  # noqa
        bad.append(f"ngoại lệ: {exc}")
    finally:
        _cleanup_repo(env)
    R.record("R4-04", "giao diện thật: editor mở tiếng Việt; sửa → (EN + giao diện sáng) → [Lưu & đăng lên web] → remote có commit, Final dạng chuẩn (lang vi, dark, og:title tiếng Việt), editor tải lại là bản đã sửa, nháp đã dọn; 2 lần liên tiếp không phình file", not bad, " | ".join(bad[:6]))
