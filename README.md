# W17_03_Claude_porfolio — Portfolio Freelancer: Vận hành & Dữ liệu (V3)

Hệ sinh thái **Portfolio Showcase & Hồ Sơ Năng Lực Tương Tác (Version 3)** của **Thao Nguyen (TJ)** — *Freelance Vận hành & Phân tích Dữ liệu • Tự động hóa Quy trình • Dashboard BI*.

> Bản W17_03 phái sinh từ W17_02 (commit `9a37799`): chỉ đổi **nội dung** để định vị freelancer, gồm 2 dịch vụ chính và 2 dịch vụ nhận theo yêu cầu. Mốc kiểm tra nằm ở [`docs/ANCHOR.md`](docs/ANCHOR.md), lý do từng thay đổi ở [`docs/CHANGE_RATIONALE.md`](docs/CHANGE_RATIONALE.md). Sổ tay sửa trang: [`docs/EDITOR_HANDBOOK.md`](docs/EDITOR_HANDBOOK.md); đo lường & tăng trưởng: [`docs/GROWTH_PLAN.md`](docs/GROWTH_PLAN.md).

---

## ✏️ Sửa nội dung web (cách đơn giản)

1. Bấm đúp **`MO_EDITOR.bat`** trong thư mục này. Một cửa sổ đen hiện ra (giữ nó mở) và trình duyệt tự mở trang editor.
2. Bấm **✏️ Bật sửa chữ**, sửa chữ trực tiếp trên trang. Trang CV: bấm link CV trên menu.
3. Bấm **🚀 Lưu & đăng lên web**. Máy chủ lưu file, cập nhật luôn file editor, rồi đẩy lên GitHub; khoảng 1–2 phút sau web cập nhật (Ctrl+F5 để xem).

Lưu ý:
- Sửa ở tiếng Việt thì chỉ bản tiếng Việt đổi; bản EN/ES/ZH sửa riêng (đổi ngôn ngữ trong editor) hoặc nhờ Claude dịch.
- Mở editor trên web thật hoặc bấm đúp file HTML thì chỉ là **bản xem thử** (có dòng nhắc màu vàng), không lưu và không đăng được.
- Nếu báo "Trên GitHub có bản mới hơn", nội dung vẫn đã lưu và commit trên máy; nhờ Claude gộp rồi đăng lại.
- Nút **💾 Chỉ lưu vào máy** chỉ lưu file trong thư mục, không đẩy lên web.
- **Đổi email, link Zalo, link GitHub hoặc địa chỉ web:** bấm **⚙ Cài đặt** trên thanh công cụ editor, sửa rồi bấm **Lưu cài đặt**. Máy chủ đổi ở cả Portfolio và CV (mọi ngôn ngữ), trang tự tải lại; sau đó bấm **🚀 Lưu & đăng lên web**. Nếu một tab editor khác mở từ trước báo "Cài đặt dùng chung vừa được đổi", bấm F5 ở tab đó rồi lưu lại (để không ghi đè cài đặt mới).
- Nên mở editor ở cửa sổ không bật tiện ích trình duyệt (eJOY, Grammarly, ...). Editor tự lọc mã tiện ích đã biết khi lưu; nếu máy chủ báo "còn mã do tiện ích trình duyệt chèn vào", bấm Ctrl+F5 rồi lưu lại.

---

## 📁 Cấu Trúc Thư Mục Chuẩn (V3)

```text
W17_03_Claude_porfolio/
├── index.html                  # [Final] Portfolio Showcase V3 (Dịch vụ + dashboard GA4 minh họa)
├── index_portfolio_clean.html  # [Final] Hồ Sơ Năng Lực / Interactive CV V3 (Bản sạch sẵn sàng deploy & in PDF)
├── editor_workspace/           # Không gian soạn thảo trực quan (Visual Editor)
│   ├── editor_portfolio.html   # Bản Editor của Portfolio Showcase (Có thanh công cụ sửa chữ & xuất bản Final)
│   └── editor_cv.html          # Bản Editor của Hồ Sơ Năng Lực (Có nút [⬆][⬇], kéo thả, đổi màu, đổi ảnh)
├── ga4_metrics_live.json       # Dữ liệu đo lường thực tế từ Google Analytics 4 & BigQuery (airy-web-503408-c6)
├── fetch_ga4_bigquery.py       # Script Python truy vấn dữ liệu GA4 từ Google BigQuery
├── dev_server.py               # Local Dev Server hỗ trợ xem trực tiếp & lưu file sạch tự động qua /api/save
└── server.py                   # Core HTTP handler cho Visual Editor
```

---

## 🚀 Điểm Nổi Bật (Key Features)

1. **`index.html` — Portfolio Showcase V3**:
   - **Mô phỏng Phễu & Hiệu suất (Interactive Funnel Simulation)**: Lọc KPI động theo khu vực/kênh bán hàng.
   - **Dashboard GA4** (số liệu 28 ngày, 14/10 – 10/11/2026, cập nhật thủ công, không phải thời gian thực):
     - 4 thẻ KPI (`174 người dùng`, `1.684 lượt xem`, `10.465 sự kiện`, `12m 30s tương tác TB/người dùng`) kèm bối cảnh: Việt Nam chiếm 89,8% sự kiện; Hoa Kỳ 80 người dùng nhưng 41 phiên, 11 giây.
     - Khối **Cách đọc số liệu**: nói rõ đây là sản phẩm cá nhân, không phải dữ liệu khách hàng, và lưu lượng nghi tự động chưa được lọc.
     - Bộ lọc `[Tất cả]`, `[🇺🇸 Hoa Kỳ]`, `[🇻🇳 Việt Nam]`; popup chi tiết Top 10 quốc gia và Top 10 trang.
     - Đã bỏ biểu đồ xu hướng theo ngày và bộ chọn 7 ngày: chuỗi số cũ không có nguồn trong `ga4_metrics_live.json` và không khớp tổng. Chỉ đưa lại khi có số theo ngày kéo thẳng từ GA4.

   - **4 Dự Án Cá Nhân**: Liên kết trực tiếp tới Live Demo & GitHub của *WRP Tax Services*, *Operation 0 — 1,000 Chunks Engine*, *TJ WordLoop Multiplayer Game*, và *TJ Courses Hub*.

2. **`index_portfolio_clean.html` — Hồ Sơ Năng Lực / Interactive CV V3**:
   - Giao diện Executive Dark/Light Mode với 4 bảng màu chủ đạo (*Ocean, Emerald, Royal Gold, Midnight Indigo*).
   - Tối ưu hóa CSS in ấn (`@media print`) xuất PDF chuẩn màu 100%.
   - Liên kết điều hướng 2 chiều mượt mà giữa **Portfolio Showcase (`./index.html`)** và **Hồ Sơ Năng Lực (`./index_portfolio_clean.html`)**.

---

## 💻 Cách Chạy Thử Nhanh Trên Máy Khác

### Cách 1: Mở trực tiếp (Zero-Config)
- Chỉ cần **double-click** mở trực tiếp file `index.html` hoặc `index_portfolio_clean.html` trên bất kỳ trình duyệt nào (mọi thư viện Tailwind CSS, Lucide Icons và Google Fonts đều hoạt động độc lập qua CDN và đường dẫn tương đối).

### Cách 2: Chạy qua Local Dev Server (Hỗ trợ tự động lưu file sạch từ Visual Editor)
```bash
python dev_server.py
```
Sau đó mở trình duyệt tại địa chỉ:
- **Portfolio Showcase (Final)**: `http://localhost:8000/index.html`
- **Hồ Sơ Năng Lực (Final)**: `http://localhost:8000/index_portfolio_clean.html`
- **Visual Editor Workspace**: `http://localhost:8000/editor_workspace/editor_portfolio.html`

### Bảo vệ endpoint lưu file (`/api/save`)
- Server chỉ bind `127.0.0.1`, **không bật CORS**; trang trong editor tự lấy token phiên ngẫu nhiên qua `GET /api/session` (chỉ trả cho đúng origin của dev server) rồi gửi kèm header `X-W17-Token`.
- Chỉ ghi `index.html` và `index_portfolio_clean.html`, body tối đa 12MB, HTML phải đủ các thành phần đặc trưng của trang, đủ kích thước và không còn trạng thái editor; ghi nguyên tử, tuần tự hóa các lần ghi đồng thời và tự sao lưu bản cũ vào `.w17_backups/` (giữ 5 bản, đã `.gitignore`).
- Chỉ phục vụ file tĩnh có đuôi trong allowlist; đường dẫn được kiểm sau khi giải mã percent-encoding; không liệt kê thư mục, không phục vụ `*.py` hay thư mục ẩn.
- Mở file bằng `file://` vẫn tải được file sạch về máy nhưng **không** ghi trực tiếp vào dự án; hãy dùng `python dev_server.py`.

### Creator ↔ Final (một nguồn duy nhất)
`index.html` và `index_portfolio_clean.html` là nguồn; hai file trong `editor_workspace/` được **sinh** từ chúng:
```bash
python tools/sync_creators.py          # ghi lại hai Creator sau khi sửa Final
python tools/sync_creators.py --check  # báo lệch (dùng trong kiểm thử)
python tools/site_config.py --check    # khối cấu hình dùng chung (w17-site-config) hợp lệ, giống nhau ở 2 trang; canonical đúng
```
Dữ liệu chỉnh sửa được lưu theo schema (không còn snapshot `innerHTML`) và được nhúng vào file Final khi xuất, nên mở lại bằng cache trống vẫn đủ nội dung.

### Kiểm thử hồi quy
```bash
pip install playwright && python -m playwright install chromium
python -X utf8 tests/regression/run_all.py --quick   # nhanh
python -X utf8 tests/regression/run_all.py           # đầy đủ 6 viewport x 4 locale
python -X utf8 tests/regression/native_zoom.py       # zoom trình duyệt 200% (native)
```
Bộ kiểm thử chạy trên bản sao tạm của repo và server thật trỏ vào thư mục tạm; không ghi file làm việc thật.
