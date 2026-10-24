# PB03 Audit và chia đoạn dữ liệu

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M1 |
| Branch | `feat/pb03-data-quality-audit` |
| Phụ thuộc | [PB02](PB02-data-ingestion.md) |
| Nguồn | Backlog PB03; pipeline chương 2–3 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người xây feature cần dữ liệu đã kiểm tra chất lượng, nhịp nền và các đoạn liên tục để phân biệt không có quan sát với quan sát bình thường.

## Phạm vi và ranh giới

Parse, audit, xử lý duplicate xác định được và đánh dấu chất lượng. Không loại outlier bằng z-score/IQR hoặc dùng phân phối test để thiết kế feature.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Raw + raw_manifest.json + train_end | Nguồn đúng checksum; ranh giới lịch đã có trong config. |
| Đầu ra | Cleaned rows; quality/gap/conflict tables | Giữ raw_row_id, flags, duplicate counts và segment_id. |
| Đầu ra | data_card.md; audit artifact | Thời gian, missing, nhịp và delta0/gap_break đã fit từ timestamp train. |

## Yêu cầu chức năng

- **PB03-FR01:** Parse timestamp theo định dạng quan sát được, giữ đồng hồ gốc không múi giờ; numeric không parse được có cờ invalid_numeric. Lưu dòng không parse được để kiểm tra thay vì âm thầm mất dấu.
- **PB03-FR02:** Ổn định thứ tự theo timestamp/raw_row_id; gộp dòng trùng hoàn toàn và ghi số bản; timestamp trùng nhưng cảm biến khác nhau bị loại khỏi dữ liệu hợp lệ, có bảng xung đột.
- **PB03-FR03:** Báo schema/types, missing, infinity, domain digital, số giá trị duy nhất, thời gian đầu/cuối, phân bố delta và gaps; tách thiếu ô với thiếu mốc thời gian. Thống kê phục vụ chọn mô hình chỉ trên train.
- **PB03-FR04:** Fit delta0 là mode delta timestamp dương trên phần train đã khai báo, lưu median/quantile; gap_break=3×delta0, gap chỉ khi delta > gap_break, tạo segment_id mới.
- **PB03-FR05:** Giữ giá trị cực đoan hợp lệ và phần dữ liệu 01/09/2020 nếu tồn tại; không tự áp luật áp suất không âm. Mọi sửa đổi có lý do/provenance trong interim, raw bất biến.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không đủ delta train để fit thì dừng với lý do, không lấy nhịp validation/test thay thế.
- Nếu mode bị hòa, ghi một quy tắc chọn cố định trong artifact; đây là quyết định triển khai cần ghi, không suy đoán nhịp.

## Tiêu chí nghiệm thu

- [ ] **PB03-AC01** (FR01, FR02): **Khi** fixture có timestamp lỗi, numeric lỗi, exact duplicate và duplicate xung đột, **thì** mỗi loại có flag/bảng/số đếm đúng; raw_row_id truy ngược được.
- [ ] **PB03-AC02** (FR03, FR04): **Khi** fixture có delta train phổ biến 10 giây, một gap 30 và một gap 31 giây, **thì** delta0=10, gap_break=30; chỉ gap 31 tạo đoạn mới.
- [ ] **PB03-AC03** (FR04): **Khi** thay timestamp của phần test mà giữ train, **thì** delta0 và gap_break đã fit không đổi.
- [ ] **PB03-AC04** (FR05): **Khi** dữ liệu có giá trị cực đoan và các dòng ngày 01/09, **thì** giữ chúng nếu không vi phạm quy tắc chất lượng đã xác nhận.

## Checklist triển khai

- [ ] Triển khai `audit.py`: parse timestamp, numeric, missing, infinity, digital domain, số giá trị duy nhất, quantile, nhịp ghi và gap.
- [ ] Deduplicate dòng trùng hoàn toàn, lưu số bản gộp; timestamp trùng nhưng khác cảm biến vào bảng xung đột và bị loại khỏi dữ liệu hợp lệ.
- [ ] Ước lượng `delta0` từ timestamp của phần train theo ranh giới lịch đã khai báo; lưu `gap_break = 3 × delta0`, `segment_id` và bảng gap. PB05 sẽ xác nhận split đầy đủ sau đó.
- [ ] Giữ các giá trị cực đoan chưa có bằng chứng lỗi đo, giữ timestamp theo đồng hồ gốc và giữ phần dữ liệu ngày 01/09/2020 nếu có.

## Rủi ro và quyết định cần ghi nhận

- Dùng mode từ toàn file làm leakage: fit nhịp trên timestamp train rồi đóng băng.
- Loại duplicate nhầm tín hiệu ổn định: chỉ gộp bản trùng hoàn toàn cùng timestamp.

## Bằng chứng để đóng PB

- [ ] Cung cấp data card, bảng counts trước/sau làm sạch, gap list và test fixture các lỗi chất lượng.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
