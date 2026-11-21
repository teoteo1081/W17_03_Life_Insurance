# ANCHOR — W17_03_Claude_porfolio

> Mốc chuẩn (anchor) để Codex kiểm. Mọi mục dưới đây đều kiểm được bằng lệnh hoặc bằng việc mở file; mục nào chưa kiểm được ghi rõ ở phần "Chưa kiểm".

## 0. Nguồn gốc và phạm vi

| Mục | Giá trị |
|---|---|
| Nguồn | `W17_02` tại commit `9a37799` (nhánh `main`) |
| Bản này | `W17_03_Claude_porfolio`, repo Git độc lập, lịch sử bắt đầu từ commit khởi tạo của bản này |
| Mục tiêu | Đổi định vị từ "ứng viên có nhiều dịch vụ" sang **freelancer về dữ liệu, nhận ít dịch vụ, làm được và chứng minh được** |
| Quyết định của chủ hồ sơ (vòng 2) | Dịch vụ là **dữ liệu**; Digital Marketing **đang học**, không nhận chạy quảng cáo. Nhận làm website, không cam kết doanh thu. Được dùng tên công ty cũ. Xóa số điện thoại. Dữ liệu demo và GA4 (trang do chính chủ làm) dùng bình thường |
| Phạm vi sửa (vòng 2–3) | Chỉ **nội dung chữ** (4 locale `vi/en/es/zh`) trong 2 file Final, hai file Creator sinh lại từ Final, và chuỗi kỳ vọng trong `tests/regression/run_all.py` |
| Phạm vi sửa (vòng 4, từ 2026-11-20) | Theo từng phase của Master Upgrade Spec đã được chủ hồ sơ duyệt; được sửa `server.py`, `tools/`, logic JS, bố cục trong phạm vi phase đó. Số liệu GA4 trưng bày, dữ liệu phễu mẫu, ảnh đại diện vẫn **không đổi** nếu chưa được duyệt riêng |

Lý do từng thay đổi nằm ở `docs/CHANGE_RATIONALE.md`.

## 1. Anchor định vị (A1–A3)

**A1 (cập nhật vòng 4, P0-4). Sáu dịch vụ** — dịch vụ 6 nay là **`6. Quảng cáo & Đo lường hiệu suất`** (nhãn "Theo yêu cầu • Quảng cáo"): nhận thiết lập và chạy Google Ads / Meta Ads **theo yêu cầu**, ngân sách thử nhỏ, tài khoản thuộc khách, báo cáo chi phí trên mỗi khách tiềm năng; **không nêu kết quả hay kinh nghiệm chưa có**. Quyết định của chủ hồ sơ 2026-11-20, thay quyết định vòng 3d ("không ghi nhận chạy quảng cáo"). Chữ "1040" bỏ khỏi chữ giới thiệu ở Portfolio và CV (tên trang thật trong bảng GA4 giữ nguyên). Các dịch vụ — chính: `1. Tự động hóa Vận hành`, `2. Phân tích Dữ liệu & Dashboard BI`; chuyên ngành: `3. Hỗ trợ văn phòng thuế Mỹ (1040)`, `4. Lương thưởng, hoa hồng & KPI`; nhận làm: `5. Website & Trang đích`, `6. Đo lường hiệu suất quảng cáo`. Khóa cũ `eco_card3/4`, `modal_p3/p4` hiển thị số 5/6; khóa mới `eco_card5/6`, `modal_p5/p6`. Kiểm: test CONTENT. **Nhãn thẻ (20/11/2026, chủ hồ sơ duyệt qua ảnh demo):** nhãn nhỏ trên thẻ (`eco_badge_N`) chỉ ghi lĩnh vực; cửa sổ chi tiết không còn nhãn (`modal_pN_badge` đã xóa vì lặp tên dịch vụ) — Tự động hóa / Dữ liệu & BI / Thuế Mỹ / Lương thưởng & KPI / Website / Quảng cáo — không còn chữ nhóm "Dịch vụ chính / thứ hai / Chuyên ngành / Nhận làm / Theo yêu cầu" (vì thẻ đổi chỗ được và "thứ hai" nghe như hạng hai). `eco_property` liệt kê 6 dịch vụ ngang hàng; đã bỏ `modal_pkg_note`, "(theo yêu cầu)" ở `modal_p4_title`, chữ chia hạng ở `modal_pkg_heading` và `meta_desc` — 6 dịch vụ ngang hàng, không chia "chính / chuyên ngành / nhận làm". Nội dung A1 gốc bên dưới chỉ còn giá trị lịch sử (vòng 3d đã bỏ "đang học").

**A1 gốc (vòng 2, không còn áp dụng). Dữ liệu là chính; website nhận làm; đo lường theo yêu cầu; Digital Marketing đang học.**
- Chính: `1. Tự động hóa Vận hành`, `2. Phân tích Dữ liệu & Dashboard BI`.
- Nhận làm: `3. Website & Trang đích` (không cam kết doanh thu hay lượng khách).
- Theo yêu cầu: `4. Kiểm lỗi Đo lường` (GA4/GTM, chỉ phần kỹ thuật).
- Digital Marketing: ghi rõ **đang học**, không nhận chạy quảng cáo (`hero_bio`, `hero_desc`, `eco_property`, `modal_pkg_note`, `skill_grp_1`).
- Kiểm: khóa `eco_badge_1..4`, `modal_p1..4_badge`, `modal_pkg_heading` ở đủ 4 locale trong `index.html`.

**A2. Không còn tuyên bố không kiểm chứng được.** Các lệnh sau phải **không** trả kết quả trong nội dung hiển thị của 2 file Final:
```bash
grep -nE "xác thực 100|100% Verified|Verified Specialist|đã xác thực|认证专家|100% 真实|Verificad|verificad" index.html index_portfolio_clean.html
grep -nE "~60%|500\+|12 Vùng|12 Regions|12 Regiones|12 个战区|80–90%" index.html index_portfolio_clean.html
grep -nE "ROAS|CPA|CVR" index.html index_portfolio_clean.html
grep -nE "Google Ads|Meta Ads|TikTok" index.html index_portfolio_clean.html
```
Ngoại lệ vòng 4 (P0-4): "Google Ads / Meta Ads" **được phép** trong thẻ và cửa sổ chi tiết dịch vụ 6 (`eco_card4_desc`, `modal_p4_item2`) vì đó là phạm vi nhận làm theo yêu cầu, không phải tuyên bố kết quả.
Ghi chú: lệnh `ROAS|CPA|CVR` còn trả vài dòng `CPA/EA` trong mô tả WRP Tax Services (Certified Public Accountant / Enrolled Agent, không phải chỉ số quảng cáo) và một dòng nằm trong chuỗi ảnh nhúng base64; cả hai chấp nhận được. Tên Prudential, Chubb Life, AIA **được phép** xuất hiện (chủ hồ sơ cho phép ở vòng 2); chúng chỉ nằm trong `sol_desc` của CV.

**A3. Số liệu GA4 là của các trang do chính chủ hồ sơ xây.** Nguồn ghi là "thuộc tính GA4 của các trang do TJ xây dựng"; `hub_desc` nói số liệu lấy từ chính các trang này. Các con số (174 người dùng, 1.684 lượt xem, 10.465 sự kiện) và dữ liệu phễu mẫu **không đổi**.

## 2. Anchor nội dung dịch vụ (A4–A5)

**A4. Mỗi dịch vụ có đúng 3 đầu việc; dịch vụ 1–4 đều ghi sản phẩm bàn giao.** Mỗi `modal_pN_itemM` (N = 1..4, M = 1..3) chứa cụm "Bàn giao:" (vi), "Delivered:" (en), "Entrega:" (es), "交付：" (zh). Riêng `modal_p3_item*` vẫn là 3 mục.

**A5. Câu "không cam kết" còn đúng ở chỗ cần thiết.** Còn trong: `hero_desc`/`hero_bio`, `eco_card4_desc` (đúng cụm kiểm thử: `không cam kết doanh thu/lead`, `no revenue/lead KPI commitments`, `sin compromiso de ingresos/leads`, `不承诺获客或营收 KPI`), `modal_p4_item3`, `footer_desc`. Không lặp ở mọi khối như bản W17_02.

## 3. Anchor riêng tư (A6)

**A6 (cập nhật vòng 4, P0-2). Số điện thoại công khai `+84 855 239 805`** (chủ hồ sơ xác nhận 2026-11-20: đúng số 0855239805, hiển thị dạng quốc tế), link `tel:+84855239805`; ở mục Liên hệ Portfolio, hero CV và khối in PDF. Quản lý ở trường `contact.phone` của `w17-site-config`. Kiểm: test R7-01, R6-02. Nội dung A6 gốc bên dưới là lịch sử.

**A6 gốc (vòng 2). Số điện thoại không còn hiển thị.** Dòng điện thoại ở hero CV và khóa `hero_phone` đã bị xóa; nhãn Zalo không còn ghi số. Kiểm: `grep -n "855" index.html index_portfolio_clean.html` chỉ được trả các liên kết `https://zalo.me/…`. **Giới hạn cần biết:** số Zalo trùng số điện thoại nên địa chỉ liên kết `zalo.me` vẫn chứa số; chỉ ẩn được khỏi chữ hiển thị. Email công khai giữ nguyên.

## 4. Anchor kỹ thuật (A7–A9)

**A7. Quy tắc `AGENTS.md` vẫn đúng.** Không thêm màu/font/spacing mới. Chuỗi mới có `text-balance`/`inline-block` bảo vệ hai chữ cuối ở các tiêu đề và mô tả đã có (`hero_title`, `hub_title`, `contact_section_sub`, `footer_title`). Không dùng `innerHTML` với chuỗi thô mới ngoài cơ chế sẵn có.

**A8. Từ điển và HTML tĩnh đồng bộ.** Mọi khóa sửa có đủ 4 locale. Giá trị `vi` trong từ điển khớp văn bản tĩnh của phần tử `data-i18n` tương ứng.

**A9. Creator ↔ Final không lệch.**
```bash
python -X utf8 tools/sync_creators.py --check   # phải in OK cho cả hai Creator
```

**A10. Cấu hình dùng chung một nguồn (vòng 4).** Email, link Zalo, link GitHub (trang cá nhân) và địa chỉ web công khai nằm trong khối `<script type="application/json" id="w17-site-config">` **giống hệt nhau** ở hai file Final. Đổi qua nút ⚙ Cài đặt của editor (`POST /api/settings`) thì server thay giá trị cũ → mới ở mọi chỗ của cả hai file (giữ nguyên link repo `github.com/<tên>/<repo>`), đặt lại canonical/og:url, sinh lại Creator. `/api/save` trả 409 nếu bản lưu mang cấu hình khác bản trên đĩa (trang mở trước khi đổi cài đặt). Canonical Portfolio = địa chỉ web; canonical CV = địa chỉ web + `index_portfolio_clean.html`; không còn `og:url` trỏ `https://teoteo1081.github.io/` (404). Kiểm: `python -X utf8 tools/site_config.py --check`, test R6-01..03, R6-05.

**A11 (sửa sau audit 2b91184). Xóa thẻ CV là thao tác TƯỜNG MINH.** Bấm ✕ hai lần (xác nhận) -> mã thẻ vào `deletedIds` của nháp + thẻ vào thùng rác "🗑 Đã xóa" (khôi phục từng thẻ, cả sau tải lại, tới khi Lưu). Khôi phục nháp CHỈ gỡ thẻ trong `deletedIds`; không suy "vắng = đã xóa" (nháp snapshot cũ, nháp chỉ có `knownIds` đều giữ mọi thẻ). Áp cho thẻ Học vấn và tag kỹ năng (thẻ giải pháp/số liệu không có nút xóa trên giao diện). Kiểm: R6-04, N01, R10-02, R10-05. Nội dung A11 cũ bên dưới là lịch sử.

**A11 cũ. Khôi phục bản nháp CV không làm mất thẻ mới (vòng 4).** Bản nháp lưu `knownIds` (mọi mã thẻ/tag từng thấy). Khi khôi phục: thẻ có trong `knownIds` mà không có trong thứ tự → đã bị xóa → xóa; thẻ không có trong `knownIds` → thẻ mới thêm vào file → giữ, đặt cuối nhóm. Bản nháp cũ không có `knownIds` giữ cách xử lý cũ. Kiểm: test R6-04.

**A12. CV → PDF/QR (vòng 4, P0-2).** Hero CV có nút theo thứ tự `Zalo | GitHub | Portfolio`; link Portfolio là `data-w17-link="portfolio"` = địa chỉ web công khai (do `tools/site_config.py` đặt). Khối `#cv-print-contact` chỉ hiện khi in: QR (vẽ lúc mở trang từ `w17-site-config`, thư viện qrcode-generator 1.4.4 MIT nhúng sẵn, không gọi dịch vụ ngoài) trỏ địa chỉ web + `utm_source=cv_pdf&utm_medium=qr&utm_campaign=cv`; link chữ + nút hero trong PDF mang `utm_medium=pdf`. Trên màn hình link Portfolio không có UTM. Nút "📄 Tải CV (PDF)" cho khách mở hộp thoại in. Số trang PDF A4 không đổi (4). Kiểm: test R7-01..04 (PDF thật bằng Chromium, đọc link bằng PyMuPDF, giải mã QR bằng OpenCV).

**A13. GA4 cho Portfolio + CV (vòng 4, P0-3).** Property "TJ Portfolio & CV" (565302376), luồng web `teoteo1081.github.io` (16382251060), Measurement ID `G-501ZEXPEVQ` trong `w17-site-config` (đổi/tắt ở ⚙). Dùng `gtag.js` trực tiếp, không GTM. Tag chỉ tải trên https + đúng host của địa chỉ web công khai; không chạy ở editor, localhost, file://, trình duyệt tự động. Consent Mode v2 theo lựa chọn 2b: mặc định từ chối đo lường ở EEA/Anh/Thụy Sĩ, cho phép nơi khác; quảng cáo luôn từ chối; banner tự hiện khi múi giờ châu Âu, nút "Quyền riêng tư & cookie" ở chân 2 trang. Đo lường nâng cao trên GA chỉ bật lượt xem trang (tắt đếm theo lịch sử trình duyệt) + cuộn. Sự kiện: contact_phone/email/zalo_click, cv_from_portfolio_click, portfolio_from_cv_click, github_click, project_demo_click, service_detail_open, ga4_detail_open, cv_pdf_export_click, contact_mailto_open (không phải "gửi thành công"), language_change; tham số chỉ là mã ngắn, không gửi chữ người dùng gõ. Dữ liệu GA4 trưng bày trên Portfolio (property WordLoop Hub, ảnh chụp thủ công) KHÔNG đổi và không trộn với property này. Không tuyên bố tuân thủ pháp luật. Kiểm: R8-01..04 (giả lập web công khai, chặn mọi request tới Google).

**A14. Bố cục Portfolio & menu (vòng 4, P0-4).** Thứ tự mặc định: Giới thiệu (`#about`, luôn đầu) → Dịch vụ (`#services`) → Dashboard mẫu (`#dashboard`) → Các website tiêu biểu (`#website`) → GA4 Tracking (`#ga4-tracking`) → Liên hệ (`#contact`, luôn cuối). Điểm neo cũ `#ga4-ecosystem`, `#live-projects` vẫn nằm trong Dịch vụ. Mỗi mục giữa có `data-w17-section` + `data-w17-nav` (khóa nhãn menu); menu máy tính và điện thoại (`data-w17-nav-list`) dựng theo thứ tự mục, bỏ mục có `data-w17-hidden`. Mục ẩn không hiện trên web; trong editor hiện mờ có viền. Editor: nút ⬆ ⬇ Ẩn/Hiện trên mỗi mục (`w17-layout-script`), lưu nháp ở trường `layout`; khi lưu, thứ tự + `data-w17-hidden` ghi thẳng vào HTML; server từ chối bản còn `.w17-section-controls`. Nút chuyển `Portfolio | CV` (`#w17-page-switch`) cùng vị trí ở hai trang, trang đang xem là chữ (aria-current), không còn "Quay lại". Kiểm: R9-01..04.

**A15. Không ghi đè bản mới bằng tab editor cũ (sau audit 2b91184).** Editor lấy phiên bản file Final (`GET /api/revision`, SHA-256 rút gọn) khi mở; `/api/save` nhận `expected_revision`, lệch -> 409, file không đổi, nháp giữ nguyên; lưu thành công trả phiên bản mới. Kiểm: R10-01.

**A16. Lưu cài đặt là một giao dịch.** `/api/settings` ghi 2 Final + 2 Creator; bất kỳ bước nào lỗi -> trả cả 4 file về nội dung cũ, báo 5xx "đã khôi phục". Kiểm: R10-03 (khóa ghi Final CV, khóa ghi Creator CV).

**A17. CSS dự phòng trên site.** `assets/portfolio-base.css`, `assets/cv-base.css` (sinh bởi `tools/build_fallback_css.py` từ Tailwind CDN) nạp trước CDN; khi CDN bị chặn PDF CV vẫn 4 trang, giữ bố cục; lớp phủ "Đổi ảnh" luôn ẩn khi in. Thêm class Tailwind mới vào trang thì chạy lại công cụ (`--check` để kiểm). Kiểm: R10-06.

**A14 bổ sung (sau audit).** Nút điều khiển mục chỉ hiện khi bật Sửa chữ (tắt = xem như web). Mục ↔ menu: ô "Tên trên menu" đổi nhãn menu (máy tính + điện thoại, lưu nháp, vào Final); sắp xếp ngay trên menu bằng kéo-thả hoặc Alt+←/→; "＋ Thêm mục" tạo mục mới (`sec-…`, chữ chung mọi ngôn ngữ, chưa dịch) có mục menu; xóa mục tự thêm phải bấm 2 lần. Giới thiệu/Liên hệ khóa; CV là trang riêng. Kiểm: R10-04.

**A18. SEO kỹ thuật (vòng 4, P1).** Cả 2 trang có canonical, og:url/og:image (1200×630, `assets/og-portfolio.png`, `assets/og-cv.png`), twitter:card `summary_large_image`, `robots: index, follow`, JSON-LD `id="w17-jsonld"` (Person + WebSite, CV thêm ProfilePage); `sitemap.xml` 2 URL. Tất cả dựng lại từ `w17-site-config` bằng `tools/site_config.py` (đổi địa chỉ web ở ⚙ là đổi theo). Chưa có: URL riêng từng ngôn ngữ, Search Console, robots.txt ở gốc tên miền (không đặt được từ repo dự án). Kiểm: R11, `site_config.py --check`.

**A19. Thẻ bên trong mục Portfolio.** Lưới `data-w17-card-group="services"` (svc-p1…p6) và `"website"` (spoke1…4 + thẻ tự thêm `web-*`). Khi bật Sửa chữ: ⬅ ➡ đổi chỗ, Ẩn/Hiện từng thẻ; "＋ Thêm website" tạo thẻ (tiêu đề, mô tả, link chỉ nhận https), xóa thẻ tự thêm bấm 2 lần. Số thứ tự dịch vụ do CSS đếm theo vị trí (thẻ ẩn không tính), không nằm trong chữ. Chưa có: thêm thẻ dịch vụ (cần nội dung cửa sổ chi tiết); thẻ tự thêm dùng chung chữ cho mọi ngôn ngữ. Kiểm: R11.

**A20. Thẻ CV.** Nút ✕ (bấm 2 lần, vào thùng rác) có trên thẻ học vấn, tag kỹ năng, thẻ giải pháp. Khối 3 bước làm việc (`data-section-id="metrics"`, khóa `metric_*`) **đã bỏ khỏi CV** theo chủ hồ sơ 2026-11-21 (quy trình dành cho khách dịch vụ, không hợp CV gửi nhà tuyển dụng); bản nháp cũ có `metricsOrder` được bỏ qua an toàn. PDF CV: `@page { margin: 0 }` để trình duyệt không in đầu/chân trang; "+ Thêm học vấn" tạo thẻ `edu_custom_*` (nháp ở `customEdu`, khi Lưu nằm thẳng trong HTML). Kiểm: R11.

**A21. GA4 phía Google (cấu hình 20/11/2026, property 565302376).** 7 phương diện tùy chỉnh phạm vi sự kiện: link_location, project_id, service_id, link_type, site_lang, language, detail_tab. 3 sự kiện quan trọng: contact_zalo_click, contact_email_click, contact_phone_click. Bộ lọc "Internal Traffic" (loại `traffic_type=internal`) **đang hoạt động**; trang đặt `traffic_type=internal` khi trình duyệt có `localStorage.w17_03_internal=1` (bật/tắt bằng `?toi_la_chu_trang=1|0`). Đã thấy trang thật gửi `g/collect`. Không gửi dữ liệu cá nhân. Kế hoạch đo + tăng trưởng: `docs/GROWTH_PLAN.md`.

## 5. Lệnh kiểm tổng

```bash
python -X utf8 tools/sync_creators.py --check
python -X utf8 tools/site_config.py --check
python -X utf8 tests/regression/run_all.py --quick
python -X utf8 tests/regression/native_zoom.py
```
Kết quả đã chạy khi tạo bản này được ghi ở `docs/CHANGE_RATIONALE.md`, mục "Kết quả kiểm tra".

## 6. Chưa kiểm (ghi thẳng, không tuyên bố PASS)

- Chưa mở site đã deploy; chỉ kiểm trên file trong repo.
- Chất lượng bản dịch `es` và `zh` do Claude viết, **chưa có người bản ngữ rà**.
- Chưa so sánh thị giác từng viewport 320/375/390/768/1024/1440 bằng ảnh chụp mới cho các đoạn chữ vừa đổi; chuỗi mới dài hơn ở một số khối (modal dịch vụ có thêm "Bàn giao: …"). Codex nên chụp modal dịch vụ ở 375px và 720×450.
- Việc nêu tên công ty cũ do chủ hồ sơ xác nhận bằng lời; chưa có tài liệu nào chứng minh quyền đó.

## 7. Cập nhật vòng 3 (2026-11-18)

Xem `docs/CHANGE_RATIONALE.md`, mục "Vòng 3". Tóm tắt các anchor bị ảnh hưởng: A1/A5 (`hero_desc` bỏ câu "đang học", vẫn giữ "không cam kết"), A3 (đã gỡ chuỗi số theo ngày và số liệu 7 ngày; chỉ còn các số 28 ngày trong `ga4_metrics_live.json`, chưa đối soát với GA4 thật). Kiểm: `grep -nE "Chart|trend28d|airy-web|Telemetry" index.html` phải không trả kết quả hiển thị.

Vòng 3b (2026-11-19): ngôn ngữ mặc định theo trình duyệt (kiểm bằng R3-09), CV ghi "Business English", khối phễu ghi rõ dữ liệu mẫu. Giữ nguyên theo chủ hồ sơ: "Hệ sinh thái", "Power BI (Nâng cao)", "Báo cáo thời gian thực" trong CV.

Vòng 3d (2026-11-19): A1/A5 thay đổi theo chủ hồ sơ — trang không còn câu "đang học" / "không cam kết"; dịch vụ 4 là "Đo lường hiệu suất quảng cáo". Chi tiết ở CHANGE_RATIONALE.md, mục Vòng 3d.

## 8. Vòng 4 (2026-11-20) — Master Upgrade, phase P0-1

Chủ hồ sơ duyệt phase P0-1 và việc cập nhật Anchor. Thay đổi so với anchor cũ:
- A1 → sáu dịch vụ (đã thực hiện ở vòng 3e, nay ghi lại vào anchor).
- A6 → số điện thoại được phép công khai sau khi chủ hồ sơ xác nhận số (P0-2).
- Phạm vi "ngoài phạm vi: `server.py`, `tools/`, logic JS" không còn đúng; phạm vi theo từng phase được duyệt.
- Thêm A10 (cấu hình dùng chung) và A11 (khôi phục bản nháp CV).
- P0-2 (CV/số điện thoại/PDF/QR/nút tải PDF) đã duyệt và làm xong (A6, A12).
- Test F04/R3/CONTENT theo chữ chủ hồ sơ sửa qua editor; 4 cụm tiếng Anh được giữ cố ý (Freelance & Remote, End-to-End Operations Automation, Website & Landing Page, Rubric Engineering).
- P0-3 (GA4 + consent 2b) đã duyệt và làm xong (A13); chủ hồ sơ cho phép Claude tự tạo property GA4 bằng phiên Chrome đang đăng nhập.
- P0-4 (tách mục, thứ tự mới, menu động, ẩn/hiện + di chuyển mục, nút chuyển, chữ dịch vụ 6, bỏ 1040) đã duyệt qua ảnh demo và làm xong (A1, A14).
- Các phase sau (P1: SEO kỹ thuật, dịch Gemini, thêm thẻ/kinh nghiệm làm việc, URL đa ngôn ngữ; P2) chưa được duyệt; chưa làm.
