# PB11 Metric cửa sổ và sự kiện

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M2 |
| Phụ thuộc | [PB10](PB10-alert-episodes.md) |
| Nguồn | Backlog PB11; pipeline chương 12 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người so sánh mô hình cần metric phản ánh cả phát hiện sự cố, độ trễ và gánh nặng cảnh báo trên thời gian thực sự quan sát được.

## Phạm vi và ranh giới

Tính metric từ score/alarm/episode đã có với explicit mask. Không point adjustment hoặc đặt accuracy làm chỉ số chính.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Score/alarm; events; episodes; evaluation mask | Cùng lưới phút, có valid/reason và score liên tục. |
| Đầu ra | metrics.json; PR data/curve | Số đếm, AP/precision/recall/F1, tỷ lệ dương, coverage, N/A reasons. |
| Đầu ra | Bảng sự cố và gánh nặng cảnh báo | Detected/evaluable, delay, first_valid, observational delay, episode/day. |

## Yêu cầu chức năng

- **PB11-FR01:** Tính TP/FP/FN/TN chỉ trên mốc hợp lệ thuộc mask; AP dùng score liên tục với average_precision_score, PR curve và positive_rate; không thay AP bằng tích phân hình thang.
- **PB11-FR02:** Precision N/A khi không alarm, recall N/A khi không dương, F1 N/A khi mẫu số 2TP+FP+FN=0; AP N/A khi thiếu dương hoặc âm. JSON dùng null cùng reason thay vì NaN không chuẩn.
- **PB11-FR03:** Sự cố đánh giá được khi có ít nhất một mốc hợp lệ trong mask; event recall là số được phát hiện/tổng đánh giá được và công bố tổng sự cố nguồn cùng số bị loại.
- **PB11-FR04:** Delay=first actual alarm in event−event.start tính phút; sự cố bỏ sót có delay N/A. Báo first_valid_time, observational_delay và median delay chỉ trên detected kèm số missed.
- **PB11-FR05:** Valid days=n_valid_minute_ticks/1440; ngoài báo cáo/ngày=số episode không có alarm khớp sự cố / valid days. Xuất thêm alert_fraction và tổng phút alarm.
- **PB11-FR06:** Policy common mask/danh sách cấu hình, số mốc, positive rate và coverage được lưu cùng metric; trường hợp không có valid time hoặc evaluable event trả N/A với lý do, không tạo tỷ lệ 0 giả.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không bootstrap từng cửa sổ chồng lấn như mẫu độc lập; bootstrap block tùy chọn ở PB23.
- Input mask phải khớp timestamp/schema; không cắt dữ liệu bằng positional index lệch bảng.

## Tiêu chí nghiệm thu

- [ ] **PB11-AC01** (FR01): **Khi** fixture nhỏ có số đếm biết trước và score liên tục, **thì** TP/FP/FN/TN và precision/recall/F1/AP khớp kết quả chuẩn.
- [ ] **PB11-AC02** (FR02, FR06): **Khi** không có alarm, thiếu một lớp hoặc không có mốc hợp lệ, **thì** các metric theo từng quy tắc N/A, có reason và JSON hợp lệ.
- [ ] **PB11-AC03** (FR03, FR04): **Khi** một sự cố được phát hiện, một bỏ sót, một không quan sát được, **thì** event recall dùng đúng mẫu số; delay không gán 0 cho missed/unobservable và hiện đủ bảng.
- [ ] **PB11-AC04** (FR04, FR05): **Khi** có alarm trước sự cố và 720 mốc hợp lệ, **thì** alarm trước sự cố không tạo delay âm; valid_days=0.5 và episode/day dùng đúng mẫu số.

## Rủi ro và quyết định cần ghi nhận

- Bỏ qua coverage làm metric cao nhưng giám sát kém: luôn hiển thị valid/planned ticks.
- Median delay đẹp có thể che missed events: bắt buộc báo cả hai.

## Kết quả cần xem

- [ ] Cung cấp fixture tính tay cho cửa sổ/sự cố, metrics.json có N/A reasons và dữ liệu PR curve.
