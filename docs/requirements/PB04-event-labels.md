# PB04 Bảng sự cố và quy tắc nhãn

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M1 |
| Phụ thuộc | [PB02](PB02-data-ingestion.md) |
| Nguồn | Backlog PB04; pipeline chương 3–4 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người đánh giá cần một bảng sự cố có nguồn và hai phép kiểm tra tách biệt: nhãn tại mốc chấm và giao dữ liệu của cả cửa sổ với sự cố.

## Phạm vi và ranh giới

Chuẩn hóa E1–E4 và logic nhãn/giao khoảng. Không tự đổi ngày sự cố từ ghi chú bảo trì mâu thuẫn, không đưa nhãn vào feature.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Nguồn sự cố và quy ước timestamp | Dùng cùng đồng hồ gốc với cảm biến; bảo lưu ghi chú gốc. |
| Đầu ra | events.csv | event_id/start/end/failure_type/source/source_note/confidence_note. |
| Bàn giao | Logic nhãn tại mốc và kiểm tra nguồn giao sự cố | PB05/PB07 lọc reference; PB10/PB11 ghép và đánh giá. |

## Yêu cầu chức năng

- **PB04-FR01:** Ghi E1: 2020-04-18 00:00–23:59; E2: 2020-05-29 23:30–2020-05-30 06:00; E3: 2020-06-05 10:00–2020-06-07 14:30; E4: 2020-07-15 14:30–19:00; kiểm tra start<=end, ID không trùng.
- **PB04-FR02:** Khoảng sự cố đóng cả hai đầu, giây=00 khi nguồn chỉ ghi đến phút. Lưu provenance và ghi chú mâu thuẫn nguyên nghĩa, không dùng chúng để tự dịch mốc.
- **PB04-FR03:** Nhãn y(t)=1 nếu window_end thuộc ít nhất một sự cố, còn lại là 0 đối với mốc hợp lệ; invalid không tham gia metric. Trả danh sách event_id nếu có nhiều giao.
- **PB04-FR04:** Kiểm tra reference dựa trên mọi timestamp nguồn thực sự dùng trong cửa sổ, kể cả timestamp gốc của fill; nhãn tại window_end không thay cho phép kiểm tra này.
- **PB04-FR05:** Tách nhãn đối chiếu khỏi feature matrix và bước score; label 0 chỉ có nghĩa ngoài các khoảng đã báo cáo.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Chỉ áp dụng quy ước timestamp nhất quán; không tự chuyển timezone một phía.
- Có kiểm tra sự cố không có mốc hợp lệ để PB11 báo không đánh giá được.

## Tiêu chí nghiệm thu

- [ ] **PB04-AC01** (FR01, FR02, FR03): **Khi** chấm ngay trước, đúng start, đúng end và ngay sau end E1, **thì** nhãn lần lượt 0/1/1/0 theo độ chính xác timestamp.
- [ ] **PB04-AC02** (FR03, FR04): **Khi** cửa sổ kết thúc sau E1 nhưng còn dùng quan sát trong E1, **thì** y(window_end)=0 nhưng bị loại khỏi reference.
- [ ] **PB04-AC03** (FR04): **Khi** giá trị được fill có timestamp gốc nằm trong sự cố ngoài biên danh nghĩa cửa sổ, **thì** vẫn phát hiện giao nguồn với sự cố.
- [ ] **PB04-AC04** (FR02, FR05): **Khi** nguồn có ghi chú bảo trì lệch tháng, **thì** mốc chuẩn không tự đổi; ghi chú được lưu và feature không chứa nhãn.

## Rủi ro và quyết định cần ghi nhận

- Nhầm end ghi 23:59 thành 23:59:59 sẽ đổi nhãn: giữ giây=00 theo đặc tả.
- Dùng nhãn pointwise để lọc reference bỏ sót phần đuôi cửa sổ sau sự cố: kiểm tra nguồn thực dùng trong lúc tạo feature. Không cần xuất danh sách nguồn riêng cho từng cửa sổ.

## Kết quả cần xem

- [ ] Đính kèm events.csv, nguồn/ghi chú và các test biên sự cố, đặc biệt cửa sổ còn giao sau end.
