#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Portfolio Visual Editor Server (/api/save)

Phục vụ trang web và ghi file Final sạch vào thư mục Git khi bấm [Lưu file sạch (Final)].

Bảo vệ endpoint ghi file (F10):
  * Chỉ bind loopback; kiểm tra header Host (chặn DNS rebinding).
  * Không còn CORS "*": trang ngoài origin không đọc được token và không gọi được /api/save.
  * Token phiên ngẫu nhiên (secrets.token_urlsafe) cấp qua GET /api/session cho đúng same-origin
    (Sec-Fetch-Site / Origin / Referer phải khớp dev origin); POST bắt buộc header X-W17-Token.
  * Bắt buộc Content-Type: application/json, giới hạn kích thước body, chỉ ghi allowlist tên file.
  * Kiểm tra cấu trúc HTML trước khi ghi; ghi nguyên tử (tệp tạm + os.replace) và backup bản cũ.
  * Trả đúng trạng thái: 200 chỉ khi mọi target đã ghi; 4xx/5xx kèm lý do nếu không.

Sau khi lưu một file Final, server sinh lại file Creator tương ứng (tools/sync_creators.py), để lần mở editor
sau là bản vừa lưu.

POST /api/publish (cùng các lớp bảo vệ như /api/save): commit đúng bốn file trang (PUBLISH_PATHS) rồi
git push lên nhánh main. Không bao giờ push --force, không tự pull/gộp; GitHub có bản mới hơn thì trả 409.

GET/POST /api/settings: đọc/đổi cấu hình dùng chung (email, Zalo, GitHub, địa chỉ web) trong khối
w17-site-config của CẢ HAI file Final (tools/site_config.py), rồi sinh lại hai Creator. /api/save từ chối (409)
bản lưu có khối cấu hình khác bản trên đĩa: trang editor mở từ trước khi đổi cài đặt sẽ không ghi đè được giá trị mới.
"""

import hashlib
import hmac
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

BASE_DIR = Path(os.environ.get("W17_BASE_DIR") or Path(__file__).resolve().parent).resolve()
BACKUP_DIR_NAME = ".w17_backups"
BACKUP_KEEP = 5
MAX_BODY_BYTES = 12 * 1024 * 1024  # file Final ~0.3MB; chừa chỗ cho ảnh đại diện base64

# filename -> {id: thẻ} các phần tử BẮT BUỘC phải tồn tại trong CÂY HTML đã parse (comment/chuỗi trong script không được tính),
# mỗi id đúng một lần; cùng kích thước tối thiểu. Bản ghi quá nhỏ so với file hiện có cũng bị từ chối.
ALLOWED_FILES = {
    "index.html": {
        "main-navbar": "header", "services": "section", "website": "section", "ga4-tracking": "section",
        "pbi-ga4-dashboard": "div", "core-portfolio-script": "script", "w17-layout-script": "script",
        "visual-editor-script": "script", "w17-baked-edits": "script", "ga4-drilldown-modal": "div",
        "w17-site-config": "script", "w17-settings-script": "script", "w17-analytics-script": "script", "w17-jsonld": "script",
    },
    "index_portfolio_clean.html": {
        "portfolio-root": "main", "reorderable-sections": "div", "interactive-editor-script": "script",
        "w17-baked-edits": "script", "solutions-grid": "div", "education-grid": "div",
        "w17-site-config": "script", "w17-settings-script": "script", "w17-analytics-script": "script", "w17-jsonld": "script",
    },
}
MIN_SCRIPT_CHARS = 20000   # tổng độ dài các <script> thực thi (không tính JSON nhúng)
MIN_ELEMENTS = 300         # số phần tử thật trong cây HTML
MIN_HTML_BYTES = 100 * 1024
MIN_RATIO_OF_CURRENT = 0.5

# Chỉ phục vụ các loại file tĩnh cần cho trang; không phục vụ mã nguồn server, dữ liệu nhạy cảm, thư mục ẩn
# hay danh sách thư mục. Kiểm tra trên ĐƯỜNG DẪN ĐÃ GIẢI MÃ/CHUẨN HÓA (percent-encoding không vượt được).
SERVED_SUFFIXES = {".html", ".htm", ".json", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".woff", ".woff2", ".txt"}
BLOCKED_PREFIXES = ("service_account", "credentials")

SESSION_TOKEN = secrets.token_urlsafe(32)
WRITE_LOCK = threading.Lock()
MAX_DRAIN_BYTES = 64 * 1024 * 1024  # body lớn hơn mức này: đóng kết nối thay vì đọc bỏ

# ---- Sinh lại Creator sau khi lưu Final (cùng quy tắc với tools/sync_creators.py) ----
_SYNC_PATH = Path(__file__).resolve().parent / "tools" / "sync_creators.py"


def _load_sync_module():
    try:
        spec = importlib.util.spec_from_file_location("w17_sync_creators", _SYNC_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


SYNC = _load_sync_module()
CREATOR_FILES = {dst for _, dst, _ in SYNC.JOBS} if SYNC else set()

# ---- Cấu hình dùng chung (tools/site_config.py) ----
_SITE_CONFIG_PATH = Path(__file__).resolve().parent / "tools" / "site_config.py"
_site_spec = importlib.util.spec_from_file_location("w17_site_config", _SITE_CONFIG_PATH)
SITE = importlib.util.module_from_spec(_site_spec)
_site_spec.loader.exec_module(SITE)   # thiếu module này thì server không chạy: cấu hình là bắt buộc
MAX_SETTINGS_BODY = 16 * 1024

# ---- Đăng lên web (git commit + push) ----
PUBLISH_BRANCH = "main"
PUBLISH_PATHS = ["index.html", "index_portfolio_clean.html", "editor_workspace/editor_portfolio.html", "editor_workspace/editor_cv.html",
                 "sitemap.xml"]
PUBLISH_LOCK = threading.Lock()
MAX_PUBLISH_BODY = 64 * 1024
GIT_TIMEOUT = 30
PUSH_TIMEOUT = 180


def allowed_hosts(port):
    return {f"127.0.0.1:{port}", f"localhost:{port}"}


def allowed_origins(port):
    return {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}


class SaveError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


# Dấu hiệu CSS do tiện ích trình duyệt chèn (SweetAlert của tiện ích, eJOY); khớp bộ lọc phía editor.
_FOREIGN_STYLE_RE = re.compile(r"\.swal2-|\.ejoy-|ejoy|body\[unresolved\]", re.IGNORECASE)


class _PageProbe(HTMLParser):
    """Dựng bản tóm tắt cây HTML thật: comment và nội dung trong <script>/<style> không bao giờ được tính là phần tử."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.elements = 0
        self.ids = {}            # id -> [tag, ...]
        self.html_tags = 0
        self.body_tags = 0
        self.editor_attrs = []   # contenteditable / toolbar / is-editing
        self.script_chars = 0
        self.baked_json = []
        self.foreign = []        # nút do tiện ích trình duyệt chèn vào (chrome-extension://, eJOY, ...)
        self._cur_script = None
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        self.elements += 1
        a = dict(attrs)
        if tag == "html":
            self.html_tags += 1
        if tag == "body":
            self.body_tags += 1
            if "is-editing" in (a.get("class") or "").split():
                self.editor_attrs.append("body.is-editing")
        if "w17-section-controls" in (a.get("class") or "").split():
            self.editor_attrs.append(".w17-section-controls")
        if "contenteditable" in a:
            self.editor_attrs.append(f"{tag}[contenteditable]")
        if a.get("id"):
            self.ids.setdefault(a["id"], []).append(tag)
            if a["id"] in ("visual-toolbar", "floating-toolbar"):
                self.editor_attrs.append("#" + a["id"])
        src = a.get("src") or a.get("href") or ""
        if src.lower().startswith(("chrome-extension://", "moz-extension://", "safari-web-extension://")):
            self.foreign.append(f"<{tag}> {src[:60]}")
        if (a.get("id") or "").lower().startswith(("ejoy", "__ejoy")):
            self.foreign.append("#" + a["id"])
        if "ejoy__" in (a.get("class") or "").lower():
            self.foreign.append(f"<{tag}>.eJOY__")
        if tag == "style":
            self._in_style = True
        if tag == "script":
            self._cur_script = {"id": a.get("id"), "type": (a.get("type") or "").lower(), "chars": 0, "data": []}

    def handle_data(self, data):
        if self._in_style:
            m = _FOREIGN_STYLE_RE.search(data)
            if m:
                self.foreign.append("<style> " + m.group(0))
        if self._cur_script is not None:
            self._cur_script["chars"] += len(data)
            self._cur_script["data"].append(data)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        if tag == "script" and self._cur_script is not None:
            s = self._cur_script
            if s["type"] == "application/json":
                self.baked_json.append((s["id"], "".join(s["data"])))
            else:
                self.script_chars += s["chars"]
            self._cur_script = None


def validate_html(filename, html):
    if not isinstance(html, str) or not html.strip():
        raise SaveError(400, "Nội dung HTML rỗng hoặc không phải chuỗi.")
    head = html.lstrip()[:200].lower()
    if not (head.startswith("<!doctype html") or head.startswith("<html")):
        raise SaveError(422, "Nội dung không bắt đầu bằng <!DOCTYPE html> hoặc <html>.")
    if "</html>" not in html[-400:].lower():
        raise SaveError(422, "Nội dung HTML không kết thúc bằng </html> (có thể bị cắt cụt).")
    probe = _PageProbe()
    try:
        probe.feed(html)
        probe.close()
    except Exception:
        raise SaveError(422, "Không parse được HTML.")
    if probe.html_tags != 1 or probe.body_tags != 1:
        raise SaveError(422, "HTML phải có đúng một thẻ <html> và một thẻ <body>.")
    problems = []
    for rid, tag in ALLOWED_FILES[filename].items():
        found = probe.ids.get(rid, [])
        if found != [tag]:
            problems.append(f"{rid} (cần đúng 1 <{tag}>, tìm thấy {found or 'không có'})")
    if problems:
        raise SaveError(422, f"HTML không phải bản đầy đủ của {filename}: " + "; ".join(problems))
    if probe.elements < MIN_ELEMENTS:
        raise SaveError(422, f"HTML chỉ có {probe.elements} phần tử (< {MIN_ELEMENTS}); không phải trang đầy đủ.")
    if probe.script_chars < MIN_SCRIPT_CHARS:
        raise SaveError(422, f"Mã script quá ít ({probe.script_chars} ký tự < {MIN_SCRIPT_CHARS}); không phải trang đầy đủ.")
    for sid, data in probe.baked_json:
        if sid == "w17-baked-edits":
            try:
                parsed = json.loads(data or "null")
            except json.JSONDecodeError:
                raise SaveError(422, "Khối w17-baked-edits không phải JSON hợp lệ.")
            if not isinstance(parsed, dict):
                raise SaveError(422, "Khối w17-baked-edits phải là object JSON.")
    try:
        if SITE.parse_config(html) is None:
            raise SaveError(422, "Thiếu khối cấu hình w17-site-config.")
    except SITE.ConfigError as err:
        raise SaveError(422, f"Khối cấu hình w17-site-config không hợp lệ: {err}")
    if probe.foreign:
        raise SaveError(422, "Bản lưu còn mã do tiện ích trình duyệt chèn vào (" + ", ".join(sorted(set(probe.foreign))[:5])
                        + "); từ chối ghi. Tải lại trang editor (Ctrl+F5) rồi lưu lại, hoặc tắt tiện ích đó khi chỉnh sửa.")
    if probe.editor_attrs:
        raise SaveError(422, "Bản Final còn trạng thái editor (" + ", ".join(sorted(set(probe.editor_attrs))) + "); từ chối ghi.")
    size = len(html.encode("utf-8"))
    current = BASE_DIR / filename
    floor = MIN_HTML_BYTES
    if current.exists():
        floor = max(floor, int(current.stat().st_size * MIN_RATIO_OF_CURRENT))
    if size < floor:
        raise SaveError(422, f"HTML quá nhỏ ({size} byte < {floor}); có thể bị cắt cụt hoặc không phải trang đầy đủ.")


def backup_existing(target):
    if not target.exists():
        return None
    backup_dir = BASE_DIR / BACKUP_DIR_NAME
    backup_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{target.name}.{stamp}.bak"
    counter = 1
    while backup_path.exists():
        backup_path = backup_dir / f"{target.name}.{stamp}-{counter}.bak"
        counter += 1
    backup_path.write_bytes(target.read_bytes())
    old = sorted(backup_dir.glob(f"{target.name}.*.bak"), key=lambda p: p.stat().st_mtime)
    for stale in old[:-BACKUP_KEEP]:
        try:
            stale.unlink()
        except OSError:
            pass
    return backup_path


def atomic_write(target, text):
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        # Trên Windows os.replace có thể tạm thời bị từ chối khi có tiến trình đang đọc file: thử lại ngắn.
        for attempt in range(40):
            try:
                os.replace(tmp_name, target)
                return
            except PermissionError:
                if attempt == 39:
                    raise
                time.sleep(0.025)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def file_revision(path):
    """Phiên bản của một file Final = 16 ký tự đầu SHA-256 nội dung (đổi khi file đổi)."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return None


def _assert_revision(target, expected):
    """Gọi trong WRITE_LOCK. Tab editor gửi phiên bản file lúc nó mở; file đã đổi (tab khác/cửa sổ khác đã lưu) thì từ chối."""
    if expected is None or not target.exists():
        return
    if not isinstance(expected, str) or file_revision(target) != expected:
        raise SaveError(409, "Trang này đã được lưu từ một cửa sổ/tab editor khác sau khi bạn mở. Chưa lưu để không ghi đè "
                             "nội dung mới hơn; bản nháp của bạn vẫn giữ trên máy. Tải lại trang (F5) để xem bản mới — "
                             "các chỉnh sửa nháp sẽ được áp lại — rồi lưu lại.")


def _assert_config_current(target, html):
    """Gọi trong WRITE_LOCK. Bản lưu phải mang đúng cấu hình đang có trên đĩa (đã kiểm hợp lệ ở validate_html)."""
    if not target.exists():
        return
    try:
        on_disk = SITE.parse_config(SITE.read(target))
    except SITE.ConfigError:
        return  # file trên đĩa hỏng cấu hình: cho bản lưu hợp lệ thay thế
    if on_disk is not None and SITE.parse_config(html) != on_disk:
        raise SaveError(409, "Cài đặt dùng chung (email/Zalo/GitHub/địa chỉ web) vừa được đổi sau khi trang này mở. "
                             "Chưa lưu để không ghi đè cài đặt mới: tải lại trang (F5) rồi sửa và lưu lại.")


def save_with_backup(name, html, expected_revision=None):
    """Backup + ghi nguyên tử, tuần tự hóa toàn bộ chuỗi để các request đồng thời không giẫm lên nhau."""
    target = BASE_DIR / name
    with WRITE_LOCK:
        _assert_revision(target, expected_revision)
        _assert_config_current(target, html)
        backup = backup_existing(target)
        atomic_write(target, html)
    return backup


def current_settings():
    """Cấu hình đang dùng; hai file Final phải có khối cấu hình giống nhau."""
    configs = []
    for name in SITE.FINALS:
        try:
            cfg = SITE.parse_config(SITE.read(BASE_DIR / name))
        except (OSError, SITE.ConfigError) as err:
            raise SaveError(500, f"{name}: không đọc được cấu hình ({err}).")
        if cfg is None:
            raise SaveError(500, f"{name}: thiếu khối cấu hình w17-site-config.")
        configs.append(cfg)
    if configs[0] != configs[1]:
        raise SaveError(409, "Cấu hình của Portfolio và CV đang khác nhau; nhờ Claude kiểm (python tools/site_config.py --check).")
    return configs[0]


def update_settings(changes):
    """Đổi cấu hình ở cả hai file Final trong một lần khóa; trả kết quả kèm số chỗ đã thay ở từng file."""
    try:
        with WRITE_LOCK:
            cfg = current_settings()
            new_cfg, diffs = SITE.merge_changes(cfg, changes)
            if not diffs:
                return {"status": "ok", "changed": [], "counts": {}}
            pages = {name: SITE.read(BASE_DIR / name) for name in SITE.FINALS}
            rendered, counts = SITE.render_pages(pages, new_cfg, diffs)
            for name, html in rendered.items():
                validate_html(name, html)
            backups = _write_all_or_nothing(rendered, {SITE.SITEMAP: SITE.sitemap_xml(new_cfg)})
    except SITE.ConfigError as err:
        raise SaveError(400, str(err))
    creators = {name: "ok" for name in SITE.FINALS}
    return {"status": "ok", "changed": [d for d, _, _ in diffs], "counts": counts, "backups": backups,
            "creator_synced": True, "creators": creators,
            "revisions": {name: file_revision(BASE_DIR / name) for name in SITE.FINALS}}


def _write_all_or_nothing(rendered, extra=None):
    """Gọi trong WRITE_LOCK. Ghi mọi file Final + Creator tương ứng như MỘT giao dịch: bất kỳ bước nào lỗi (ghi file,
    sinh Creator) thì trả TẤT CẢ file đã đụng về nội dung cũ rồi báo lỗi — không bao giờ để Portfolio và CV lệch cấu hình."""
    originals = {}   # đường dẫn -> bytes cũ (None nếu file chưa có)

    def remember(path):
        if path not in originals:
            originals[path] = path.read_bytes() if path.exists() else None

    backups = []
    try:
        for name, html in rendered.items():
            target = BASE_DIR / name
            remember(target)
            backup = backup_existing(target)
            if backup is not None:
                backups.append(backup.name)
            atomic_write(target, html)
        for rel, text in (extra or {}).items():   # vd. sitemap.xml theo địa chỉ web mới
            target = BASE_DIR / rel
            remember(target)
            atomic_write(target, text)
        if SYNC is None:
            raise SaveError(500, "Không nạp được tools/sync_creators.py.")
        for name in rendered:
            dst_rel, text = SYNC.creator_for(name, root=BASE_DIR)
            target = BASE_DIR / dst_rel
            remember(target)
            atomic_write(target, text)
        return backups
    except BaseException as err:
        failed = []
        for path, data in originals.items():
            try:
                if data is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, data.decode("utf-8"))
            except OSError:
                failed.append(path.name)
        detail = err.message if isinstance(err, SaveError) else (getattr(err, "strerror", None) or str(err) or type(err).__name__)
        if failed:
            raise SaveError(500, f"Lưu cài đặt thất bại ({detail}) và KHÔNG khôi phục được: {', '.join(failed)}. "
                                 f"Dùng bản sao lưu trong .w17_backups hoặc nhờ Claude khôi phục.")
        raise SaveError(500, f"Lưu cài đặt thất bại ({detail}); đã khôi phục nguyên trạng cả Portfolio và CV, không file nào đổi.")


def sync_creator(final_name):
    """Sinh lại file Creator từ file Final vừa lưu. Trả (đã cập nhật hay chưa, lý do nếu chưa)."""
    if SYNC is None:
        return False, "Không nạp được tools/sync_creators.py."
    with WRITE_LOCK:
        try:
            dst_rel, text = SYNC.creator_for(final_name, root=BASE_DIR)
        except SYNC.SyncError as err:
            return False, str(err)
        target = BASE_DIR / dst_rel
        try:
            current = SYNC.read(target) if target.exists() else None
            if current != text:
                atomic_write(target, text)
        except OSError as err:
            return False, f"Không ghi được {dst_rel}: {err.strerror or err}"
    return True, ""


def run_git(args, timeout=GIT_TIMEOUT):
    # Không bao giờ chờ nhập liệu trên terminal (server không có ai gõ); cửa sổ đăng nhập GitHub (nếu có) vẫn hiện được.
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        return subprocess.run(["git", *args], cwd=str(BASE_DIR), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise SaveError(504, f"Git chạy quá {timeout} giây (mạng chậm hoặc đang chờ đăng nhập GitHub). Thử lại sau.")
    except OSError as err:
        raise SaveError(500, f"Không chạy được git: {err.strerror or err}")


def _git_tail(result, limit=300):
    text = " ".join(((result.stderr or "") + " " + (result.stdout or "")).split())
    return text[-limit:] if text else "không có thông tin"


def publish_to_github():
    """Commit đúng bốn file trang (nếu có thay đổi) rồi push nhánh main. Không force, không tự gộp."""
    with PUBLISH_LOCK:
        if shutil.which("git") is None:
            raise SaveError(500, "Máy này chưa cài Git nên chưa đăng được lên web.")
        top = run_git(["rev-parse", "--show-toplevel"])
        if top.returncode != 0:
            raise SaveError(409, "Thư mục web không phải repo Git nên chưa đăng được lên web.")
        try:
            same_root = Path(top.stdout.strip()).resolve() == BASE_DIR
        except OSError:
            same_root = False
        if not same_root:
            raise SaveError(409, "Thư mục web không phải gốc của repo Git; không đăng để tránh commit nhầm chỗ.")
        head = run_git(["symbolic-ref", "--short", "HEAD"])
        branch = head.stdout.strip()
        if head.returncode != 0 or branch != PUBLISH_BRANCH:
            raise SaveError(409, f"Repo đang ở nhánh '{branch or '?'}', không phải '{PUBLISH_BRANCH}' (nhánh web chạy); chưa đăng.")
        status = run_git(["status", "--porcelain", "--", *PUBLISH_PATHS])
        if status.returncode != 0:
            raise SaveError(500, "Không đọc được trạng thái Git: " + _git_tail(status))
        committed = False
        if status.stdout.strip():
            added = run_git(["add", "--", *PUBLISH_PATHS])
            if added.returncode != 0:
                raise SaveError(500, "Không thêm được file vào Git: " + _git_tail(added))
            message = "content: cập nhật nội dung từ editor (" + time.strftime("%Y-%m-%d %H:%M") + ")"
            commit = run_git(["commit", "--only", "-m", message, "--", *PUBLISH_PATHS])
            if commit.returncode != 0:
                raise SaveError(500, "Không tạo được commit: " + _git_tail(commit))
            committed = True
        sha = run_git(["rev-parse", "--short", "HEAD"]).stdout.strip()
        push = run_git(["push", "origin", f"{PUBLISH_BRANCH}:{PUBLISH_BRANCH}"], timeout=PUSH_TIMEOUT)
        if push.returncode != 0:
            detail = (push.stderr or "") + (push.stdout or "")
            if any(s in detail for s in ("[rejected]", "non-fast-forward", "fetch first", "Updates were rejected")):
                raise SaveError(409, "Trên GitHub có bản mới hơn bản trên máy nên chưa đăng (nội dung đã lưu và commit trên máy). Nhờ Claude gộp giúp rồi đăng lại.")
            raise SaveError(502, "Chưa đẩy được lên GitHub (nội dung đã lưu và commit trên máy): " + _git_tail(push))
        return {"status": "ok", "committed": committed, "commit": sha, "pushed": True, "branch": branch}


class PortfolioEditorHandler(SimpleHTTPRequestHandler):
    server_version = "W17Editor/1.0"
    sys_version = ""
    timeout = 20  # chống kết nối treo (slowloris) giữ luồng xử lý

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    # ---- helpers -------------------------------------------------------------
    @property
    def _port(self):
        return self.server.server_address[1]

    def _host_ok(self):
        return (self.headers.get("Host") or "") in allowed_hosts(self._port)

    def _same_origin_ok(self):
        origin = self.headers.get("Origin")
        if origin is not None:
            return origin in allowed_origins(self._port)
        site = self.headers.get("Sec-Fetch-Site")
        if site is not None:
            return site in ("same-origin", "none")
        referer = self.headers.get("Referer")
        if referer:
            parts = urlsplit(referer)
            return f"{parts.scheme}://{parts.netloc}" in allowed_origins(self._port)
        return False

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()

    # ---- static --------------------------------------------------------------
    def _path_blocked(self):
        """Chặn dựa trên đường dẫn thật sau khi giải mã percent-encoding và chuẩn hóa (cùng hàm mà server dùng để mở file)."""
        try:
            raw = urlsplit(self.path).path
            if "\x00" in raw or "\\" in raw:
                return True
            fs_path = Path(self.translate_path(self.path)).resolve()
            rel = fs_path.relative_to(BASE_DIR)
        except (ValueError, OSError):
            return True
        if any(part.startswith(".") for part in rel.parts):
            return True
        if rel.parts and rel.parts[-1].lower().startswith(BLOCKED_PREFIXES):
            return True
        if fs_path.is_dir():
            # không liệt kê thư mục; chỉ cho phép khi có index.html
            return not (fs_path / "index.html").is_file()
        return fs_path.suffix.lower() not in SERVED_SUFFIXES

    def _serve_final_file(self, head_only):
        """Hai file Final đang được ghi đè bởi /api/save: đọc dưới cùng khóa với ghi để không bao giờ thấy trạng thái nửa chừng
        (trên Windows, mở file đúng lúc os.replace có thể lỗi thoáng qua và bị trả 404 giả)."""
        try:
            fs_path = Path(self.translate_path(self.path)).resolve()
            name = fs_path.relative_to(BASE_DIR).as_posix()
        except (ValueError, OSError):
            return False
        if name not in ALLOWED_FILES and name not in CREATOR_FILES:
            return False
        try:
            with WRITE_LOCK:
                data = fs_path.read_bytes()
        except OSError:
            self._send_json(503, {"status": "error", "message": "File đang được ghi, thử lại."})
            return True
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        if not head_only:
            self.wfile.write(data)
        return True

    def do_GET(self):
        if not self._host_ok():
            self._send_json(403, {"status": "error", "message": "Host không được phép."})
            return
        path = urlsplit(self.path).path
        if path == "/api/session":
            if not self._same_origin_ok():
                self._send_json(403, {"status": "error", "message": "Chỉ trang cùng origin mới lấy được token."})
                return
            self._send_json(200, {"status": "ok", "token": SESSION_TOKEN, "files": sorted(ALLOWED_FILES)})
            return
        if path == "/api/revision":
            if not self._same_origin_ok():
                self._send_json(403, {"status": "error", "message": "Chỉ trang editor cùng origin mới đọc được phiên bản."})
                return
            name = (parse_qs(urlsplit(self.path).query).get("file") or [""])[0]
            if name not in ALLOWED_FILES:
                self._send_json(400, {"status": "error", "message": "Tên file không nằm trong allowlist."})
                return
            with WRITE_LOCK:
                rev = file_revision(BASE_DIR / name)
            self._send_json(200, {"status": "ok", "file": name, "revision": rev})
            return
        if path == "/api/settings":
            if not self._same_origin_ok():
                self._send_json(403, {"status": "error", "message": "Chỉ trang editor cùng origin mới đọc được cài đặt."})
                return
            try:
                cfg = current_settings()
                self._send_json(200, {"status": "ok", "values": {k: SITE.get(cfg, k) for k in SITE.FIELDS}})
            except SaveError as err:
                self._send_json(err.status, {"status": "error", "message": err.message})
            return
        if self._path_blocked():
            self._send_json(404, {"status": "error", "message": "Không tìm thấy."})
            return
        if self._serve_final_file(head_only=False):
            return
        super().do_GET()

    def do_HEAD(self):
        if not self._host_ok() or self._path_blocked():
            self.send_response(404)
            self.end_headers()
            return
        if self._serve_final_file(head_only=True):
            return
        super().do_HEAD()

    def do_OPTIONS(self):
        # Không cấp CORS: preflight từ origin khác không nhận Access-Control-Allow-*.
        self.send_response(405)
        self.send_header("Allow", "GET, HEAD, POST")
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ---- save ----------------------------------------------------------------
    def _discard_unread_body(self):
        """Từ chối sớm mà không đọc body dễ làm TCP gửi RST, client không nhận được mã lỗi: đọc bỏ body nhỏ, đóng kết nối nếu lớn."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if getattr(self, "_body_consumed", False) or length <= 0:
            return
        if length > MAX_DRAIN_BYTES:
            self.close_connection = True
            return
        # Client thật đang gửi body: đọc bỏ (không giữ trong bộ nhớ) rồi mới trả mã lỗi để client nhận được 4xx thay vì bị ngắt kết nối.
        remaining = length
        try:
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
        except OSError:
            self.close_connection = True

    def _authorized_json_body(self, max_bytes):
        """Các lớp bảo vệ chung của mọi POST ghi dữ liệu: Host, Origin, token phiên, Content-Type, kích thước, JSON object."""
        if not self._host_ok():
            raise SaveError(403, "Host không được phép.")
        if not self._same_origin_ok():
            raise SaveError(403, "Origin không được phép.")
        supplied = self.headers.get("X-W17-Token") or ""
        if not hmac.compare_digest(supplied.encode("utf-8"), SESSION_TOKEN.encode("utf-8")):
            raise SaveError(401, "Thiếu hoặc sai token phiên. Tải lại trang editor rồi lưu lại.")
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            raise SaveError(415, "Content-Type phải là application/json.")
        try:
            length = int(self.headers.get("Content-Length") or "")
        except ValueError:
            raise SaveError(411, "Thiếu Content-Length hợp lệ.")
        if length <= 0:
            raise SaveError(400, "Body rỗng.")
        if length > max_bytes:
            limit = f"{max_bytes // (1024 * 1024)}MB" if max_bytes >= 1024 * 1024 else f"{max_bytes // 1024}KB"
            raise SaveError(413, f"Body vượt giới hạn {limit}.")
        raw = self.rfile.read(length)
        self._body_consumed = True
        if len(raw) != length:
            raise SaveError(400, "Body bị cắt cụt.")
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise SaveError(400, "Body không phải JSON UTF-8 hợp lệ.")
        if not isinstance(data, dict):
            raise SaveError(400, "Body JSON phải là object.")
        return data

    def do_POST(self):
        self._body_consumed = False
        path = urlsplit(self.path).path
        if path not in ("/api/save", "/api/publish", "/api/settings"):
            self._discard_unread_body()
            self._send_json(404, {"status": "error", "message": "Không tìm thấy endpoint."})
            return
        if path == "/api/settings":
            try:
                data = self._authorized_json_body(MAX_SETTINGS_BODY)
                self._send_json(200, update_settings(data.get("changes")))
            except SaveError as err:
                self._discard_unread_body()
                self._send_json(err.status, {"status": "error", "message": err.message})
            except OSError as err:
                self._send_json(500, {"status": "error", "message": f"Không ghi được file: {err.strerror or err}"})
            except Exception:
                self._send_json(500, {"status": "error", "message": "Lỗi nội bộ khi lưu cài đặt."})
            return
        if path == "/api/publish":
            try:
                self._authorized_json_body(MAX_PUBLISH_BODY)
                self._send_json(200, publish_to_github())
            except SaveError as err:
                self._discard_unread_body()
                self._send_json(err.status, {"status": "error", "pushed": False, "message": err.message})
            except Exception:
                self._send_json(500, {"status": "error", "pushed": False, "message": "Lỗi nội bộ khi đăng lên web."})
            return
        try:
            data = self._authorized_json_body(MAX_BODY_BYTES)

            html = data.get("html")
            targets = data.get("targets")
            if targets is None:
                targets = [data.get("filename")]
            if not isinstance(targets, list) or not targets or len(targets) > len(ALLOWED_FILES):
                raise SaveError(400, "Danh sách targets không hợp lệ.")
            if any(not isinstance(t, str) or t not in ALLOWED_FILES for t in targets):
                raise SaveError(400, "Tên file không nằm trong allowlist: " + ", ".join(sorted(ALLOWED_FILES)))
            targets = list(dict.fromkeys(targets))
            for name in targets:
                validate_html(name, html)
            # Phiên bản file lúc tab editor mở (chuỗi khi chỉ 1 file, hoặc {file: phiên bản}). Có gửi mà lệch -> 409.
            expected = data.get("expected_revision")
            if expected is not None and not isinstance(expected, (str, dict)):
                raise SaveError(400, "expected_revision phải là chuỗi hoặc object.")

            saved, backups = [], []
            for name in targets:
                exp = expected.get(name) if isinstance(expected, dict) else expected
                backup = save_with_backup(name, html, exp)
                saved.append(name)
                if backup is not None:
                    backups.append(backup.name)
            # File editor (Creator) đi theo bản vừa lưu; lỗi sinh Creator không làm hỏng lần lưu đã thành công.
            creators, creator_synced = {}, True
            for name in saved:
                ok, reason = sync_creator(name)
                creators[name] = "ok" if ok else reason
                creator_synced = creator_synced and ok
            self._send_json(200, {"status": "ok", "saved": saved, "backups": backups, "bytes": len(html.encode("utf-8")),
                                  "creator_synced": creator_synced, "creators": creators,
                                  "revisions": {name: file_revision(BASE_DIR / name) for name in saved}})
        except SaveError as err:
            self._discard_unread_body()
            self._send_json(err.status, {"status": "error", "saved": [], "message": err.message})
        except OSError as err:
            self._send_json(500, {"status": "error", "saved": [], "message": f"Không ghi được file: {err.strerror or err}"})
        except Exception:
            self._send_json(500, {"status": "error", "saved": [], "message": "Lỗi nội bộ khi lưu file."})

    def log_message(self, fmt, *args):
        super().log_message(fmt, *args)


def make_server(port):
    return ThreadingHTTPServer(("127.0.0.1", port), PortfolioEditorHandler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    server = make_server(port)
    print(f"Portfolio Editor Server running at http://127.0.0.1:{port}  (token phiên được cấp tự động cho trang cùng origin)")
    server.serve_forever()
