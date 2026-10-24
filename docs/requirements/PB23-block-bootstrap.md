# PB23 Block bootstrap theo ngày

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P2 — tùy chọn |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | P2 — sau benchmark chính |
| Branch | `feat/pb23-block-bootstrap` |
| Phụ thuộc | [PB19](PB19-frozen-test-benchmark.md) |
| Nguồn | Backlog PB23; pipeline chương 12 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người đọc cần thấy mức biến thiên của AP và gánh nặng cảnh báo khi thay đổi các block ngày quan sát, thay vì coi mọi cửa sổ chồng lấn là độc lập.

## Phạm vi và ranh giới

Block bootstrap theo ngày như phân tích bổ sung; không dùng khoảng tin cậy để chọn lại model/threshold đã khóa hoặc tạo thêm sự cố độc lập.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Frozen scores/alarms/episodes; valid mask; day/segment keys | Benchmark PB19 hoàn tất, dữ liệu thời gian và event IDs còn nguyên. |
| Đầu ra | Bootstrap config/sample manifest/results | 1000 lần, seed cố định, resampled block IDs và số lần bị loại. |
| Đầu ra | Khoảng ước lượng và ghi chú giả định | AP/outside episodes per valid day; phương pháp/độ tin cậy công bố rõ. |

## Yêu cầu chức năng

- **PB23-FR01:** Xác định block theo ngày của đồng hồ gốc, giữ nguyên mốc và phụ thuộc nội block; resample block ngày có hoàn lại 1000 lần bằng seed cố định, không resample từng cửa sổ.
- **PB23-FR02:** Tính AP từ score liên tục trên mẫu bootstrap đủ hai lớp; loại lần thiếu dương hoặc âm và công bố n_valid_replicates/n_rejected với lý do.
- **PB23-FR03:** Tính gánh nặng cảnh báo dùng thời lượng hợp lệ thực tế; không nối episode qua các block không kề nhau hoặc bản sao ngày. Ghi quy ước phân bổ episode qua ngày trước khi tính.
- **PB23-FR04:** Không fit/recalibrate trong resample; giữ model/tau/mask policy cố định. Lưu sample indices và thống kê từng lần để tái lập.
- **PB23-FR05:** Đề xuất triển khai: percentile interval 95%, configurable và lưu method/level; nhãn rõ là uncertainty theo giả định block ngày, không chứng minh tổng quát hóa trên nhiều máy/sự cố.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Nếu không có đủ replicate hợp lệ thì báo N/A hoặc giới hạn phân tích, không tự điền khoảng 0.
- Day blocks có thể vẫn phụ thuộc giữa ngày; report phải nêu giới hạn, đặc biệt chỉ ít sự cố test.

## Tiêu chí nghiệm thu

- [ ] **PB23-AC01** (FR01, FR04): **Khi** chạy lại bootstrap cùng input/seed, **thì** cùng danh sách block lấy mẫu và thống kê, frozen artifacts không đổi.
- [ ] **PB23-AC02** (FR02): **Khi** sample bootstrap không có lớp dương hoặc âm, **thì** AP replicate bị loại có reason, tổng valid+rejected=1000.
- [ ] **PB23-AC03** (FR03): **Khi** một episode chạy qua nửa đêm hoặc hai block bị xếp lại, **thì** không tạo alarm/episode mới do nối block; quy tắc phân bổ duration/count được kiểm tra bằng fixture.
- [ ] **PB23-AC04** (FR05): **Khi** sinh kết quả khoảng ước lượng, **thì** có method/level/số replicate hợp lệ và ghi rõ giả định, không thay kết luận cấu hình chính.

## Checklist triển khai

- [ ] Chốt cấu hình seed, ngày/block, interval và cách xử lý episode qua ngày; ghi quyết định bổ sung.
- [ ] Xây sampler, metric từng replicate và lưu danh sách block/sample.
- [ ] Kiểm tra fixture thiếu lớp và episode qua ranh ngày.
- [ ] Sinh báo cáo interval kèm số lần bị loại và giới hạn diễn giải.

## Rủi ro và quyết định cần ghi nhận

- Gán một episode qua ngày cho cả hai ngày làm tăng count: định nghĩa rõ phân bổ trước bootstrap.
- AP dựa ít ngày có sự cố có thể tạo nhiều sample suy biến: công bố số lần loại.

## Bằng chứng để đóng PB

- [ ] Đính kèm bootstrap config, sample manifest, replicate table, báo cáo intervals và fixture đếm qua ngày.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
