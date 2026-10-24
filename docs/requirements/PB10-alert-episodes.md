# PB10 Alarm, episode và ghép sự cố

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M2 |
| Phụ thuộc | [PB04](PB04-event-labels.md), [PB05](PB05-temporal-splits.md) |
| Nguồn | Backlog PB10; pipeline chương 11 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người giám sát cần danh sách đợt cảnh báo truy được các alarm thật, tránh coi phần nối giữa hai alarm là bằng chứng phát hiện sự cố.

## Phạm vi và ranh giới

Áp threshold, gộp episode và ghép sự cố; nhận score có sẵn hoặc fixture. Không làm mượt score hoặc tự thêm điều kiện nhiều phút liên tiếp.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Scheduled score grid; tau; quality; events | Có split/segment và valid; cấu hình/model ghi một lần cho bảng, tau do caller cung cấp. |
| Đầu ra | Score/alarm table | Mọi mốc có score/alarm/valid/reason; threshold và model có thể lưu một lần trong metadata. |
| Đầu ra | episodes.csv với event_ids; timestamp liên kết score table | Các alarm gốc, start/end, n_alarm_points, peak/max score và event_ids. |

## Yêu cầu chức năng

- **PB10-FR01:** Với valid=true, alarm khi score>tau; score=tau không alarm. Invalid giữ score và alarm null, không chuyển thành 0 hoặc bình thường.
- **PB10-FR02:** Mở đợt ở alarm đầu; alarm kế tiếp nhập đợt nếu cách alarm gần nhất <=300 giây, cùng split/segment và mọi mốc dự kiến ở giữa hợp lệ.
- **PB10-FR03:** Gap, invalid, biên split/segment hoặc khoảng cách vượt ngưỡng phải ngắt đợt; không suy tất cả mốc giữa hai dòng được nhập là hợp lệ nếu thiếu grid.
- **PB10-FR04:** Giữ alarm nhị phân gốc; start_alarm/end_alarm là phạm vi hiển thị. Chỉ khớp sự cố khi có alarm thật trong khoảng sự cố đóng hai đầu.
- **PB10-FR05:** Một episode có thể lưu nhiều event_id; mỗi sự cố chỉ đếm một lần ở metric. Episode không chứa alarm khớp sự cố là ngoài báo cáo; lưu peak/time/version và liên kết tới mốc nguồn.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Nhập score theo thứ tự timestamp; đầu vào trùng mốc hoặc sai schema phải được từ chối/chuẩn hóa theo policy có tài liệu.
- Nếu score hữu hạn bị thiếu tại valid=true, báo hợp đồng đầu vào lỗi; không tự coi là normal.

## Tiêu chí nghiệm thu

- [ ] **PB10-AC01** (FR01): **Khi** có score dưới/bằng/trên tau và một mốc invalid, **thì** alarm lần lượt 0/0/1/null, invalid score vẫn null.
- [ ] **PB10-AC02** (FR02, FR03): **Khi** hai alarm cách 300 giây, sau đó 301 giây, **thì** cặp 300 gộp nếu toàn bộ mốc giữa hợp lệ; 301 tạo đợt mới.
- [ ] **PB10-AC03** (FR03, FR04): **Khi** hai alarm ngoài sự cố có đoạn nối đi qua sự cố, hoặc có invalid ở giữa, **thì** không tự tạo true positive; invalid ngắt đợt.
- [ ] **PB10-AC04** (FR04, FR05): **Khi** một đợt có alarm thật trong hai sự cố, **thì** lưu hai event_ids, giữ alarm gốc và không nhân đôi đếm cùng sự cố.

## Rủi ro và quyết định cần ghi nhận

- Gộp sau khi bỏ invalid khỏi bảng sẽ nối qua vùng không quan sát: luôn nhận đủ grid.
- Dùng interval overlap của episode thay alarm membership làm event recall tăng giả: test trường hợp đường nối.

## Kết quả cần xem

- [ ] Đính kèm fixture score/episodes tự tính được và các test threshold equality, invalid gap, đường nối qua sự cố.
