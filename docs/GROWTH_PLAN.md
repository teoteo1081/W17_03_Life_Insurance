# Kế hoạch tăng trưởng — Portfolio & CV (W17_03)

> Viết cho: TJ (chủ hồ sơ, không cần biết code).
> Mục tiêu: có thêm **lượt liên hệ thật** (Zalo / email / điện thoại) từ khách freelance và nhà tuyển dụng remote.
> Nguyên tắc: chỉ dùng cách "mũ trắng". Không có số liệu nào trong tài liệu này là cam kết: thứ hạng Google, lượt hiển thị trên AI hay số khách đều **không ai bảo đảm được**.

---

## 1. Đo cái gì (đã cài xong)

| Câu hỏi của TJ | Xem ở đâu trong GA4 | Sự kiện / tham số |
|---|---|---|
| Có ai liên hệ không? | Báo cáo → Tương tác → **Sự kiện quan trọng** | `contact_zalo_click`, `contact_email_click`, `contact_phone_click` (đã đánh dấu là sự kiện quan trọng) |
| Họ bấm từ chỗ nào? | Khám phá → bảng tự do, thêm phương diện **Vị trí nút bấm** | `link_location` |
| Dịch vụ nào được quan tâm? | Phương diện **Mã dịch vụ** (p1…p6) | `service_detail_open` + `service_id` |
| Website mẫu nào được bấm? | Phương diện **Mã website demo** | `project_demo_click` + `project_id` |
| Người xem dùng ngôn ngữ nào? | Phương diện **Ngôn ngữ trang** / **Ngôn ngữ chuyển sang** | `site_lang`, `language_change` + `language` |
| Từ Portfolio sang CV và ngược lại? | Sự kiện | `cv_from_portfolio_click`, `portfolio_from_cv_click` |
| Người ta có tải CV PDF không? | Sự kiện | `cv_pdf_export_click` |
| Đến từ link nào TJ gửi? | Báo cáo → Thu nạp → **Phiên theo nguồn/phương tiện/chiến dịch** | link có `utm_…` (bảng ngay dưới + link dùng sẵn ở [EDITOR_HANDBOOK.md](EDITOR_HANDBOOK.md) mục 7) |

- **Lượt xem của chính TJ không bị tính:** bộ lọc "Internal Traffic" đã **bật** (20/11/2026). Mỗi trình duyệt/máy TJ dùng, mở trang 1 lần với `?toi_la_chu_trang=1`; muốn tắt thì `?toi_la_chu_trang=0`. Chrome chính của TJ đã được đánh dấu.
- Các phương diện tùy chỉnh chỉ có số liệu **từ ngày tạo trở đi** (20/11/2026), không tính ngược.
- Property GA4 mới: báo cáo thường chậm 24–48 giờ; muốn xem ngay dùng **Báo cáo → Thời gian thực** hoặc `?ga_debug=1` + DebugView.

### Nhịp xem số liệu (10 phút mỗi tuần)

1. Thứ Hai: mở **Sự kiện quan trọng** → ghi số liên hệ tuần trước vào 1 dòng Google Sheet (ngày, Zalo, email, phone, nguồn chính).
2. Xem **Thu nạp** → nguồn nào mang tới liên hệ (không phải nguồn nào nhiều lượt xem nhất).
3. Mỗi tháng: xem `service_id` → dịch vụ nào được mở chi tiết nhiều nhưng ít liên hệ → sửa mô tả dịch vụ đó trước.

### Link gửi đi phải có UTM (bắt buộc với app chat)

Zalo, Viber, Messenger (và nhiều ứng dụng email) mở link **không kèm nguồn** → GA4 ghi "(direct) / (none)", không biết khách từ đâu. Facebook/LinkedIn có báo nguồn nhưng không tách được hồ sơ / bài đăng / tin nhắn. Vì vậy **mọi link TJ tự gửi đều lấy từ bảng dùng sẵn** ở [EDITOR_HANDBOOK.md mục 7](EDITOR_HANDBOOK.md#7-link-có-utm-biết-khách-đến-từ-kênh-nào). Tóm tắt quy ước để đọc báo cáo:

| Kênh | `utm_source` | `utm_medium` | `utm_campaign` | Trang đích | GA4 xếp vào nhóm kênh |
|---|---|---|---|---|---|
| Zalo | `zalo` | `social` | `chat` / `post` / `apply` | Portfolio (chat, post), CV (apply) | Mạng xã hội không phải trả tiền |
| Viber | `viber` | `social` | `chat` / `apply` | Portfolio / CV | Mạng xã hội không phải trả tiền |
| Facebook | `facebook` | `social` | `profile` / `post` / `group` | Portfolio | Mạng xã hội không phải trả tiền |
| Messenger | `messenger` | `social` | `chat` / `apply` | Portfolio / CV | Mạng xã hội không phải trả tiền |
| LinkedIn | `linkedin` | `social` | `profile` / `post` / `chat` / `apply` | Portfolio (profile, post, chat), CV (apply) | Mạng xã hội không phải trả tiền |
| Email | `email` | `email` | `signature` / `proposal` / `apply` | Portfolio (signature, proposal), CV (apply) | Email |
| Upwork, Fiverr | `upwork`, `fiverr` | `referral` | `profile` | Portfolio | Giới thiệu |
| TopCV, ITviec | `topcv`, `itviec` | `referral` | `apply` | CV | Giới thiệu |
| CV PDF (tự động) | `cv_pdf` | `pdf` / `qr` | `cv` | Portfolio | (không thuộc nhóm mặc định — xem theo nguồn) |

- `utm_campaign` cho biết **kiểu gửi**: `chat` (nhắn 1-1), `post`/`group` (bài đăng), `profile` (gắn cố định), `signature`, `proposal` (chào giá), `apply` (ứng tuyển). Thử nghiệm T1–T4 ở mục 4 đọc kết quả theo đúng các giá trị này.
- Muốn so sánh từng bài đăng: thêm `&utm_content=<ngày hoặc chủ đề>` (vd. `2026-11-24`).
- Một kênh mới chưa có trong bảng: thêm dòng vào bảng ở Handbook trước, rồi mới gửi — giữ một cách viết duy nhất cho mỗi nguồn.

---

## 2. Bản đồ từ khóa (theo dịch vụ thật trên trang)

Chưa có số liệu lượng tìm kiếm. Trước khi viết thêm nội dung, kiểm bằng **Google Keyword Planner** (miễn phí trong tài khoản Google Ads) và sau 4–8 tuần bằng **Search Console → Hiệu suất → Truy vấn**. Cột "Ý định" quyết định trang nào nhận từ khóa đó.

| Dịch vụ | Từ khóa tiếng Việt (gợi ý) | Từ khóa quốc tế (EN) | Ý định | Trang nhận |
|---|---|---|---|---|
| Tự động hóa vận hành | tự động hóa excel, tự động nhập liệu google sheets, freelancer python tự động hóa, đối soát hóa đơn tự động | freelance python automation, excel automation freelancer, google sheets automation, playwright automation freelancer | Thuê người | Portfolio — mục Dịch vụ p1 |
| Phân tích dữ liệu & Dashboard BI | thuê làm dashboard power bi, freelancer power bi, làm sạch dữ liệu excel | power bi freelancer, power bi dashboard remote, data cleaning freelancer | Thuê người | Portfolio — p2, mục Dashboard |
| Website & Landing Page | làm landing page giá rẻ, website giới thiệu dịch vụ, landing page form google sheets | landing page freelancer, small business website freelancer | Thuê người | Portfolio — p3, mục Website mẫu |
| Quảng cáo & Đo lường | cài đặt ga4, gắn gtm cho website, đo lường chuyển đổi quảng cáo | ga4 setup freelancer, google tag manager setup, conversion tracking setup | Thuê người | Portfolio — p4, mục GA4 Tracking |
| Hỗ trợ văn phòng thuế Mỹ | (thị trường VN nhỏ) nhân viên hỗ trợ thuế mỹ remote | us tax preparation assistant remote, cch axcess autoflow support, tax workpaper bookmarking, 1040 document intake | Tuyển dụng / thuê ngoài | CV + Portfolio p5 |
| Lương thưởng, hoa hồng & KPI | thiết kế cơ chế hoa hồng, tính kpi đội kinh doanh, mô hình lương thưởng bảo hiểm | sales commission plan design, incentive compensation analyst remote | Thuê người / tuyển dụng | Portfolio p6 + CV |
| Thương hiệu cá nhân | Thao Nguyen TJ, tên TJ + "portfolio" | Thao Nguyen data operations, Thao Nguyen TJ CV | Tìm đúng người | Cả 2 trang |

**Lưu ý thực tế:** một trang portfolio cá nhân hiếm khi lên top các từ khóa rộng ("power bi freelancer"). Kênh có hiệu quả nhất thường là **các nền tảng nơi khách đang tìm người** (mục 3), còn website là nơi để họ **tin và liên hệ**. Từ khóa tên riêng ("Thao Nguyen TJ") và các từ khóa ngách (CCH Autoflow, bookmark workpaper) là những từ trang có cơ hội thật.

---

## 3. Việc nên làm (mũ trắng), xếp theo hiệu quả / công sức

| # | Việc | Ai làm | Công sức | Ghi chú |
|---|---|---|---|---|
| 1 | Xác minh **Google Search Console** cho `teoteo1081.github.io/W17_03_Claude_porfolio/`, nộp `sitemap.xml` | TJ đăng nhập; Claude hướng dẫn / thêm thẻ xác minh | 15 phút | Không có cái này thì không biết Google thấy trang thế nào |
| 2 | Gắn link Portfolio/CV (có UTM) vào hồ sơ **LinkedIn, Upwork, Fiverr, Freelancer, TopCV, ITviec**, chữ ký email | TJ | 1–2 giờ | Mỗi nơi một `utm_source` riêng để đo |
| 3 | Viết **2–3 case study ngắn** (vấn đề → cách làm → kết quả đo được, không lộ dữ liệu khách) trên chính trang hoặc LinkedIn | TJ viết nội dung thật, Claude dàn trang | 2–4 giờ/bài | Số liệu chỉ ghi khi có thật |
| 4 | Thêm **Work Experience thật** (công ty, thời gian) vào CV | TJ cung cấp dữ liệu | 30 phút | Đang thiếu — nhà tuyển dụng remote hỏi đầu tiên |
| 5 | Đăng 1 bài/tuần trên LinkedIn hoặc nhóm Facebook nghề (mẹo Excel/Power BI/GA4), cuối bài dẫn link có UTM | TJ | 30 phút/tuần | Đều đặn quan trọng hơn dài |
| 6 | Xin **lời nhận xét** (testimonial) có tên/chức danh từ khách hoặc quản lý cũ, được họ đồng ý cho đăng | TJ | — | Không tự viết thay, không đăng khi chưa đồng ý |
| 7 | URL riêng cho từng ngôn ngữ (`/en/`, `/es/`, `/zh/`) | Claude, khi TJ duyệt | 1 phiên làm | Hiện Google chỉ thấy bản tiếng Việt; xem mục 6 |

---

## 4. Thử nghiệm tăng trưởng (làm từng cái, không chạy cùng lúc)

Mỗi thử nghiệm: đổi **một** thứ, đo **một** chỉ số chính, dừng đúng hạn.

| # | Giả thuyết | Chỉ số chính | Thời gian | Chi phí | Rủi ro | Dừng / kết luận khi |
|---|---|---|---|---|---|---|
| T1 | Gửi CV kèm link có UTM `cv_pdf` thay vì file đính kèm trơn → nhà tuyển dụng mở Portfolio nhiều hơn | Phiên từ `utm_source=cv_pdf` + `portfolio_from_cv_click` | 4 tuần hoặc 20 lần gửi | 0 đ | Thấp | < 3 phiên sau 20 lần gửi → link không giúp, quay về file PDF |
| T2 | Đưa nút **Zalo** lên trước email ở mục Liên hệ → khách VN liên hệ nhiều hơn | `contact_zalo_click` / tổng phiên VN | 4 tuần | 0 đ | Thấp (đảo lại được ngay trong Editor) | Không tăng sau 4 tuần → trả về thứ tự cũ |
| T3 | Hồ sơ Upwork/Fiverr dẫn về Portfolio (UTM riêng) → có khách hỏi giá | Liên hệ từ `utm_source=upwork`/`fiverr` | 6 tuần | 0 đ (có thể phí nền tảng khi nhận việc) | Trung bình: tốn thời gian chào giá | 0 liên hệ sau 6 tuần → đổi tiêu đề hồ sơ trước khi bỏ kênh |
| T4 | Bài LinkedIn hằng tuần dẫn về 1 dịch vụ cụ thể → `service_detail_open` của dịch vụ đó tăng | `service_detail_open` theo `service_id` + nguồn `linkedin` | 6 bài | 0 đ | Thấp | < 5 phiên/bài sau 6 bài → đổi chủ đề hoặc định dạng |
| T5 (khi có ngân sách) | Google Ads từ khóa ngách (vd. "ga4 setup freelancer") với ngân sách nhỏ → có liên hệ với chi phí chấp nhận được | Chi phí / 1 sự kiện quan trọng | 2 tuần | Ngân sách do TJ đặt trước (gợi ý thử ≤ 500.000 đ) | Mất tiền nếu từ khóa sai | Hết ngân sách mà 0 liên hệ → dừng, xem lại trang đích |

Ghi kết quả mỗi thử nghiệm 3 dòng: **đã đổi gì — số trước/sau — quyết định giữ hay bỏ**.

---

## 5. Những việc KHÔNG làm (mũ đen / xám)

- Mua backlink, trao đổi link hàng loạt, đăng link vào diễn đàn/bình luận rác.
- Nhồi từ khóa, chữ ẩn, trang cửa ngõ (doorway) cho từng từ khóa.
- Tự viết đánh giá/khách hàng giả, logo khách chưa đồng ý, số liệu kết quả chưa có thật.
- Bot/traffic giả để "đẹp" GA4, tự bấm nút liên hệ (đã có bộ lọc nội bộ, nhưng đừng thử).
- Sao chép nội dung người khác hoặc AI viết hàng loạt không biên tập.
- Hứa "top 1 Google", "xuất hiện trên ChatGPT" với khách — không ai bảo đảm được.

Hậu quả thường gặp: Google hạ hạng hoặc loại khỏi kết quả; với nền tảng freelance có thể bị khóa tài khoản; mất uy tín khi khách kiểm chứng.

---

## 6. Tìm kiếm bằng AI (GEO) — làm được gì, không hứa gì

Các công cụ như Google AI Overviews, ChatGPT search, Perplexity tự quyết định trích nguồn nào; **không có cách bảo đảm** được nhắc tới. Những việc giúp tăng khả năng được hiểu đúng:

- **Đã có:** dữ liệu có cấu trúc JSON-LD (`Person` + `WebSite`, thêm `ProfilePage` ở CV) trên cả 2 trang, thẻ chia sẻ (OG/Twitter), `sitemap.xml`, tiêu đề/mô tả rõ ràng, nội dung là chữ thật (không phải ảnh).
- **Nên thêm:** câu trả lời ngắn, rõ cho các câu khách hay hỏi (phạm vi dịch vụ, cách làm việc remote, thời gian bàn giao) — viết như mục Hỏi–Đáp; tên riêng nhất quán ở mọi nơi ("Thao Nguyen (TJ)").
- **Giới hạn hiện tại:** nội dung EN/ES/ZH được đổi bằng JavaScript trên cùng một URL nên công cụ tìm kiếm/AI chủ yếu đọc bản tiếng Việt. Muốn được tìm bằng tiếng Anh cần URL riêng cho từng ngôn ngữ (việc #7 ở mục 3 — cần TJ duyệt).
- `robots.txt` không đặt được ở gốc tên miền `teoteo1081.github.io` từ repo này; trang đã có thẻ `robots: index, follow`, đủ cho việc lập chỉ mục.

---

## 7. Báo cáo kết hợp GA4 + Search Console (sau khi xác minh)

1. Search Console → **Cài đặt → Liên kết** → liên kết với property GA4 "TJ Portfolio & CV".
2. Hằng tháng xem trong Search Console: **Hiệu suất → Truy vấn** (người ta gõ gì để thấy trang), **Trang**, **Quốc gia**.
3. Truy vấn có lượt hiển thị nhưng ít lượt nhấp → sửa tiêu đề/mô tả trang (qua nút ⚙ Cài đặt trong Editor hoặc nhờ Claude).
4. Ghép với GA4: truy vấn/kênh nào dẫn tới **sự kiện quan trọng** → ưu tiên viết thêm cho chủ đề đó.
