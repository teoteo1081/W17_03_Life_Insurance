/**
 * Báo cáo GA4 -> Google Sheets cho https://teoteo1081.github.io/tjthaonguyen/
 * (property "TJ W17 Life Insurance (Portfolio + CV)" = 565375502).
 *
 * Cài đặt (một lần):
 *   1. Trong Sheet: Tiện ích mở rộng > Apps Script, dán toàn bộ file này vào Code.gs.
 *   2. Dịch vụ (+) > "Google Analytics Data API" > Thêm (tên mặc định: AnalyticsData).
 *   3. Chọn hàm caiDat > Chạy > cấp quyền. Sau đó script tự chạy mỗi sáng 7–8h (giờ của Sheet).
 * Muốn cập nhật ngay: chạy capNhat (hoặc menu "📊 Báo cáo CV" > Cập nhật ngay trong Sheet).
 *
 * Bản gốc lưu trong repo: tools/ga4_sheets_report.gs — sửa ở đây rồi dán lại vào Apps Script.
 */
const PROPERTY_ID = '565375502';
const DAYS = 30;
const CONTACT_EVENTS = [
  'contact_phone_click', 'contact_phone_copy', 'contact_email_click', 'contact_email_copy',
  'contact_zalo_click', 'cv_pdf_export_click', 'portfolio_from_cv_click', 'cv_from_portfolio_click',
  'project_demo_click', 'github_click',
];
const EVENT_LABELS = {
  contact_phone_click: 'Bấm gọi điện', contact_phone_copy: 'Copy số điện thoại',
  contact_email_click: 'Bấm email', contact_email_copy: 'Copy email', contact_zalo_click: 'Bấm Zalo',
  cv_pdf_export_click: 'Tải CV (PDF)', portfolio_from_cv_click: 'Từ CV sang Portfolio',
  cv_from_portfolio_click: 'Từ Portfolio sang CV', project_demo_click: 'Xem demo dự án', github_click: 'Mở GitHub',
};

function onOpen() {
  SpreadsheetApp.getUi().createMenu('📊 Báo cáo CV').addItem('Cập nhật ngay', 'capNhat').addToUi();
}

/** Chạy một lần: đặt lịch chạy mỗi ngày rồi cập nhật luôn. */
function caiDat() {
  ScriptApp.getProjectTriggers().forEach((t) => { if (t.getHandlerFunction() === 'capNhat') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('capNhat').timeBased().everyDays(1).atHour(7).create();
  capNhat();
}

function capNhat() {
  const range = [{ startDate: DAYS + 'daysAgo', endDate: 'today' }];
  const ketQua = [];

  ketQua.push(ghi_('Nguồn truy cập',
    ['Trang', 'Nguồn', 'Kênh', 'Chiến dịch', 'Nhóm / bài đăng', 'Phiên', 'Người dùng', 'Lượt xem trang'],
    () => chay_({
      dateRanges: range,
      dimensions: d_('pagePath', 'sessionSource', 'sessionMedium', 'sessionCampaignName', 'sessionManualAdContent'),
      metrics: m_('sessions', 'activeUsers', 'screenPageViews'),
      orderBys: [{ metric: { metricName: 'sessions' }, desc: true }],
      limit: 500,
    })));

  ketQua.push(ghi_('Liên hệ & hành động',
    ['Hành động', 'CV', 'Vị trí bấm', 'Nguồn', 'Kênh', 'Nhóm / bài đăng', 'Số lần'],
    () => chay_({
      dateRanges: range,
      dimensions: d_('eventName', 'customEvent:cv_variant', 'customEvent:link_location', 'sessionSource', 'sessionMedium', 'sessionManualAdContent'),
      metrics: m_('eventCount'),
      dimensionFilter: { filter: { fieldName: 'eventName', inListFilter: { values: CONTACT_EVENTS } } },
      orderBys: [{ metric: { metricName: 'eventCount' }, desc: true }],
      limit: 500,
    }).map((r) => [EVENT_LABELS[r[0]] || r[0]].concat(r.slice(1)))));

  ketQua.push(ghi_('Theo ngày',
    ['Ngày', 'Trang', 'Phiên', 'Lượt xem trang'],
    () => chay_({
      dateRanges: range,
      dimensions: d_('date', 'pagePath'),
      metrics: m_('sessions', 'screenPageViews'),
      orderBys: [{ dimension: { dimensionName: 'date' }, desc: true }],
      limit: 1000,
    }).map((r) => [String(r[0]).replace(/^(\d{4})(\d{2})(\d{2})$/, '$3/$2/$1')].concat(r.slice(1)))));

  const info = sheet_('Đọc trước');
  info.clear();
  info.getRange(1, 1, 7, 2).setValues([
    ['Cập nhật lần cuối', Utilities.formatDate(new Date(), 'Asia/Ho_Chi_Minh', 'dd/MM/yyyy HH:mm')],
    ['Khoảng thời gian', DAYS + ' ngày gần nhất (tính cả hôm nay)'],
    ['Nguồn dữ liệu', 'GA4 property ' + PROPERTY_ID + ' — teoteo1081.github.io/tjthaonguyen'],
    ['Lượt xem của chủ trang', 'Đã loại (bộ lọc Internal Traffic, đánh dấu bằng ?toi_la_chu_trang=1)'],
    ['"—" nghĩa là', 'GA4 không có giá trị (vd. vào thẳng không qua link UTM, hoặc trang Portfolio không có mã CV)'],
    ['Độ trễ', 'GA4 có thể trễ vài giờ; số liệu hôm nay chưa đủ'],
    ['Kết quả lần chạy', ketQua.join(' · ')],
  ]);
  info.getRange('A1:A7').setFontWeight('bold');
  info.autoResizeColumns(1, 2);
}

// ---------- hỗ trợ ----------
function d_() { return Array.prototype.map.call(arguments, (n) => ({ name: n })); }
function m_() { return Array.prototype.map.call(arguments, (n) => ({ name: n })); }

function chay_(req) {
  const res = AnalyticsData.Properties.runReport(req, 'properties/' + PROPERTY_ID);
  const nDim = (res.dimensionHeaders || []).length;
  return (res.rows || []).map((row) => {
    const dims = row.dimensionValues.map((v) => (v.value === '(not set)' || v.value === '' ? '—' : v.value));
    const mets = row.metricValues.map((v) => Number(v.value));
    return dims.slice(0, nDim).concat(mets);
  });
}

function sheet_(name) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  return ss.getSheetByName(name) || ss.insertSheet(name);
}

function ghi_(name, header, fetchRows) {
  const sh = sheet_(name);
  try {
    const rows = fetchRows();
    sh.clear();
    sh.getRange(1, 1, 1, header.length).setValues([header]).setFontWeight('bold').setBackground('#e8f0fe');
    if (rows.length) sh.getRange(2, 1, rows.length, header.length).setValues(rows);
    else sh.getRange(2, 1).setValue('Chưa có dữ liệu trong ' + DAYS + ' ngày qua.');
    sh.setFrozenRows(1);
    sh.autoResizeColumns(1, header.length);
    return name + ': ' + rows.length + ' dòng';
  } catch (e) {
    sh.getRange(1, 1).setValue('Lỗi khi lấy dữ liệu: ' + e.message);
    return name + ': LỖI';
  }
}
