# PB02 Nhập dữ liệu và khóa nguồn

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | S — tương đối, chưa quy đổi ngày |
| Mốc | M1 |
| Branch | `feat/pb02-data-ingestion` |
| Phụ thuộc | [PB01](PB01-project-scaffold.md) |
| Nguồn | Backlog PB02; pipeline chương 2 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người chạy thí nghiệm cần biết chính xác dữ liệu gốc nào tạo ra kết quả, đồng thời có thể nhập lại cùng nguồn mà không làm thay đổi raw.

## Phạm vi và ranh giới

Tải/nhập gói MetroPT-3 và xác minh nguồn, tệp, header. Chưa sửa dữ liệu, deduplicate hay phân tích giá trị cảm biến.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | URL gói chính thức hoặc đường dẫn gói local | Ghi rõ nguồn; không suy ra nguồn từ tên file đơn thuần. |
| Đầu ra | data/raw/ và raw_manifest.json | Giữ CSV/PDF gốc; URL, ngày tải, file, byte, SHA-256, schema version. |
| Bàn giao | Raw cho PB03/PB04 | Giữ cột gốc, quy ước raw_row_id và dataset version. |

## Yêu cầu chức năng

- **PB02-FR01:** Hỗ trợ nhập gói chính thức hoặc gói local; phát hiện tải dở, ZIP lỗi, thiếu CSV hoặc thiếu PDF mô tả trước khi công bố ingest thành công.
- **PB02-FR02:** Kiểm tra header gồm timestamp, 7 analog và 8 digital; analog: TP2/TP3/H1/DV_pressure/Reservoirs/Oil_temperature/Motor_current; digital: COMP/DV_eletric/Towers/MPG/LPS/Pressure_switch/Oil_level/Caudal_impulses.
- **PB02-FR03:** Giữ tên cột và cột index gốc để truy vết; timestamp/index không được tự xem là feature. Chốt quy ước raw_row_id ổn định theo vị trí dòng gốc.
- **PB02-FR04:** Tính checksum/byte từ tệp thực nhận và ghi manifest. SHA-256 tham chiếu của CSV là `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`; khác checksum tạo phiên bản mới cần audit lại.
- **PB02-FR05:** Nhập lại đúng nội dung là thao tác idempotent; không ghi đè raw đã khóa, không nhân đôi phiên bản, không lấy số dòng công bố làm số đo thực tế.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Tải/ghi qua tệp tạm rồi xác minh trước khi công bố manifest hoàn tất.
- Manifest dùng checksum của dữ liệu, không chỉ thời gian sửa file; lỗi không để lại trạng thái ready giả.

## Tiêu chí nghiệm thu

- [ ] **PB02-AC01** (FR01): **Khi** gói bị cắt hoặc thiếu CSV/PDF, **thì** ingest thất bại rõ lý do và không phát hành manifest thành công.
- [ ] **PB02-AC02** (FR02, FR03): **Khi** header có DV_eletric và Towers đúng tên, **thì** giữ nguyên tên; thiếu sensor hoặc đổi tên ngoài ánh xạ được báo rõ.
- [ ] **PB02-AC03** (FR04): **Khi** nhập một CSV có checksum khác bản tham chiếu, **thì** lưu version mới và yêu cầu audit; raw cũ giữ nguyên.
- [ ] **PB02-AC04** (FR05): **Khi** ingest cùng một gói hai lần, **thì** version/checksum raw không đổi và không sinh bản sao dữ liệu.

## Checklist triển khai

- [ ] Triển khai `ingest.py`, nhận gói tải chính thức hoặc đường dẫn local, giữ nguyên CSV và PDF mô tả trong `data/raw/`.
- [ ] Lưu `raw_manifest.json`: URL, ngày tải, tên file, byte, SHA-256, schema version; giữ `raw_row_id` và tên cột gốc.
- [ ] Kiểm tra header 15 cảm biến, `timestamp` và cột chỉ mục; giữ chính tả `DV_eletric`, `Towers`; index không vào feature.
- [ ] Đối chiếu SHA-256 CSV mà pipeline đã ghi: `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`. Nếu khác, tạo phiên bản dữ liệu mới và yêu cầu audit lại trong luồng chạy.

## Rủi ro và quyết định cần ghi nhận

- Tên file giống nhau không bảo đảm cùng dataset: dùng checksum làm bằng chứng.
- Mạng ngắt có thể để lại tệp dở: phân biệt trạng thái tạm và trạng thái đã xác minh.

## Bằng chứng để đóng PB

- [ ] Đính kèm manifest mẫu, kết quả hai lần ingest và ví dụ xử lý checksum/header lỗi.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
