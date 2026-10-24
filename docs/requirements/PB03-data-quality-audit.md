# PB03 Audit và chia đoạn dữ liệu

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M1 |
| Phụ thuộc | [PB02](PB02-data-ingestion.md) |
| Nguồn | Backlog PB03; pipeline chương 2–3 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người xây feature cần dữ liệu đã kiểm tra chất lượng, nhịp nền và các đoạn liên tục để phân biệt không có quan sát với quan sát bình thường.

## Phạm vi và ranh giới

Parse, audit, xử lý duplicate xác định được và đánh dấu chất lượng. Không loại outlier bằng z-score/IQR hoặc dùng phân phối test để thiết kế feature.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Raw + raw_manifest.json + train_end | Nguồn đúng checksum; ranh giới lịch đã có trong config. |
| Đầu ra | Cleaned rows với quality flags; bảng lỗi/gap khi cần xem chi tiết | Giữ raw_row_id, flags, duplicate counts và segment_id. |
| Đầu ra | Một data_card.md gồm thống kê chất lượng và split | Thời gian, missing, nhịp và delta0/gap_break đã fit từ timestamp train. |

## Yêu cầu chức năng

- **PB03-FR01:** Parse timestamp theo định dạng quan sát được, giữ đồng hồ gốc không múi giờ; numeric không parse được có cờ invalid_numeric. Lưu dòng không parse được để kiểm tra thay vì âm thầm mất dấu.
- **PB03-FR02:** Ổn định thứ tự theo timestamp/raw_row_id; gộp dòng trùng hoàn toàn và ghi số bản; timestamp trùng nhưng cảm biến khác nhau bị loại khỏi dữ liệu hợp lệ, có bảng xung đột.
- **PB03-FR03:** Báo schema/types, missing, infinity, domain digital, số giá trị duy nhất, thời gian đầu/cuối, phân bố delta và gaps; tách thiếu ô với thiếu mốc thời gian. Thống kê phục vụ chọn mô hình chỉ trên train.
- **PB03-FR04:** Fit delta0 là mode delta timestamp dương trên phần train đã khai báo, lưu median/quantile; gap_break=3×delta0, gap chỉ khi delta > gap_break, tạo segment_id mới.
- **PB03-FR05:** Giữ giá trị cực đoan hợp lệ và phần dữ liệu 01/09/2020 nếu tồn tại; không tự áp luật áp suất không âm. Ghi số dòng và lý do làm sạch trong data card; giữ raw_row_id để xem lại raw, không tạo nhật ký mỗi thao tác.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không đủ delta train để fit thì dừng với lý do, không lấy nhịp validation/test thay thế.
- Nếu mode bị hòa, ghi một quy tắc chọn cố định trong artifact; đây là quyết định triển khai cần ghi, không suy đoán nhịp.

## Tiêu chí nghiệm thu

- [ ] **PB03-AC01** (FR01, FR02): **Khi** fixture có timestamp lỗi, numeric lỗi, exact duplicate và duplicate xung đột, **thì** mỗi loại có flag/bảng/số đếm đúng; raw_row_id truy ngược được.
- [ ] **PB03-AC02** (FR03, FR04): **Khi** fixture có delta train phổ biến 10 giây, một gap 30 và một gap 31 giây, **thì** delta0=10, gap_break=30; chỉ gap 31 tạo đoạn mới.
- [ ] **PB03-AC03** (FR04): **Khi** thay timestamp của phần test mà giữ train, **thì** delta0 và gap_break đã fit không đổi.
- [ ] **PB03-AC04** (FR05): **Khi** dữ liệu có giá trị cực đoan và các dòng ngày 01/09, **thì** giữ chúng nếu không vi phạm quy tắc chất lượng đã xác nhận.

## Rủi ro và quyết định cần ghi nhận

- Dùng mode từ toàn file làm leakage: fit nhịp trên timestamp train rồi đóng băng.
- Loại duplicate nhầm tín hiệu ổn định: chỉ gộp bản trùng hoàn toàn cùng timestamp.

## Kết quả cần xem

- [ ] Cung cấp một data card có counts trước/sau và tóm tắt gap; bảng chi tiết chỉ khi cần phân tích. Kiểm tra fixture lỗi chất lượng.
