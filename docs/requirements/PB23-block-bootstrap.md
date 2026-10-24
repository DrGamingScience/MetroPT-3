# PB23 Block bootstrap theo ngày

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P2 — tùy chọn |
| Mốc | P2 — sau benchmark chính |
| Phụ thuộc | [PB19](PB19-frozen-test-benchmark.md) |
| Nguồn | Backlog PB23; pipeline chương 12 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

**Phạm vi hiện tại: Deferred.** Chỉ triển khai khi có câu hỏi hoặc nhu cầu cụ thể; các yêu cầu dưới đây áp dụng nếu mở lại mục này.

## Mục tiêu và nhu cầu

Người đọc cần thấy mức biến thiên của AP và gánh nặng cảnh báo khi thay đổi các block ngày quan sát, thay vì coi mọi cửa sổ chồng lấn là độc lập.

## Phạm vi và ranh giới

Block bootstrap theo ngày như phân tích bổ sung; không dùng khoảng tin cậy để chọn lại model/threshold đã khóa hoặc tạo thêm sự cố độc lập.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Frozen scores/alarms/episodes; valid mask; day/segment keys | Benchmark PB19 hoàn tất, dữ liệu thời gian và event IDs còn nguyên. |
| Đầu ra | Seed/quy tắc lấy mẫu và bảng kết quả bootstrap | 1000 lần, seed cố định, quy tắc tạo lại block IDs và số lần bị loại. |
| Đầu ra | Khoảng ước lượng và ghi chú giả định | AP/outside episodes per valid day; phương pháp/độ tin cậy công bố rõ. |

## Yêu cầu chức năng

- **PB23-FR01:** Xác định block theo ngày của đồng hồ gốc, giữ nguyên mốc và phụ thuộc nội block; resample block ngày có hoàn lại 1000 lần bằng seed cố định, không resample từng cửa sổ.
- **PB23-FR02:** Tính AP từ score liên tục trên mẫu bootstrap đủ hai lớp; loại lần thiếu dương hoặc âm và công bố n_valid_replicates/n_rejected với lý do.
- **PB23-FR03:** Tính gánh nặng cảnh báo dùng thời lượng hợp lệ thực tế; không nối episode qua các block không kề nhau hoặc bản sao ngày. Ghi quy ước phân bổ episode qua ngày trước khi tính.
- **PB23-FR04:** Không fit/recalibrate trong resample; giữ model/tau/mask policy cố định. Lưu seed, code/quy tắc sampler và thống kê từng lần; tạo lại được sample indices, không bắt buộc file chỉ mục riêng.
- **PB23-FR05:** Đề xuất triển khai: percentile interval 95%, configurable và lưu method/level; nhãn rõ là uncertainty theo giả định block ngày, không chứng minh tổng quát hóa trên nhiều máy/sự cố.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Nếu không có đủ replicate hợp lệ thì báo N/A hoặc giới hạn phân tích, không tự điền khoảng 0.
- Day blocks có thể vẫn phụ thuộc giữa ngày; report phải nêu giới hạn, đặc biệt chỉ ít sự cố test.

## Tiêu chí nghiệm thu

- [ ] **PB23-AC01** (FR01, FR04): **Khi** chạy lại bootstrap cùng input/seed, **thì** cùng danh sách block lấy mẫu và thống kê, frozen artifacts không đổi.
- [ ] **PB23-AC02** (FR02): **Khi** sample bootstrap không có lớp dương hoặc âm, **thì** AP replicate bị loại có reason, tổng valid+rejected=1000.
- [ ] **PB23-AC03** (FR03): **Khi** một episode chạy qua nửa đêm hoặc hai block bị xếp lại, **thì** không tạo alarm/episode mới do nối block; quy tắc phân bổ duration/count được kiểm tra bằng fixture.
- [ ] **PB23-AC04** (FR05): **Khi** sinh kết quả khoảng ước lượng, **thì** có method/level/số replicate hợp lệ và ghi rõ giả định, không thay kết luận cấu hình chính.

## Rủi ro và quyết định cần ghi nhận

- Gán một episode qua ngày cho cả hai ngày làm tăng count: định nghĩa rõ phân bổ trước bootstrap.
- AP dựa ít ngày có sự cố có thể tạo nhiều sample suy biến: công bố số lần loại.

## Kết quả cần xem

- [ ] Cung cấp seed/quy tắc sampler, replicate table và intervals trong report; kiểm tra fixture đếm qua ngày.
