# PB05 Temporal split và purge

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M1 |
| Branch | `feat/pb05-temporal-splits` |
| Phụ thuộc | [PB03](PB03-data-quality-audit.md), [PB04](PB04-event-labels.md) |
| Nguồn | Backlog PB05; pipeline chương 4 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người chạy benchmark cần train/validation/test theo thời gian, với mốc chấm công bằng và không dùng chung nguồn quan sát qua biên.

## Phạm vi và ranh giới

Xây timeline, mask, warm-up và hợp đồng reference. PB07 cung cấp feature provenance để hoàn tất xác nhận purge; PB05 vẫn nghiệm thu được bằng fixture.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Cleaned timestamps/segments; events; config | delta0/gap_break từ train; biên split đã cố định. |
| Đầu ra | splits.json; scheduled grid; split/warm-up masks | Mốc một phút, thời lượng/số dòng/sự cố theo split. |
| Bàn giao | Reference/evaluation mask policy | PB07 bổ sung provenance; PB15 tạo common comparison mask. |

## Yêu cầu chức năng

- **PB05-FR01:** Train trước 2020-03-01 00:00, validation từ đó đến trước 2020-05-01 00:00, test từ đó đến hết tệp; không dịch biên theo score hoặc hiệu quả mô hình.
- **PB05-FR02:** Mỗi mốc thuộc đúng một split; mỗi cửa sổ chỉ dùng raw và fill origin cùng split/segment. Biên split hoặc gap reset trạng thái.
- **PB05-FR03:** Warm-up chung bằng Wmax + max fill age = 930 giây; mốc đầu đủ điều kiện nằm trên lưới phút tại hoặc sau thời điểm đủ warm-up, áp dụng lại mỗi đoạn liên tục.
- **PB05-FR04:** Train/validation reference loại cửa sổ có nguồn giao sự cố; evaluation giữ mọi mốc hợp lệ và gán nhãn tại window_end. Dùng contract provenance để bổ sung mask khi feature sẵn sàng.
- **PB05-FR05:** Lưu mốc dự kiến, hợp lệ, loại theo lý do, thời lượng, dương và số sự cố đánh giá được; E1 thuộc validation, E2–E4 test nếu dữ liệu nguồn đúng phiên bản.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Bảng mốc dự kiến vẫn giữ warm-up/invalid để đo coverage; không chỉ xuất những mốc đẹp.
- Audit timestamp của test được phép; phân phối cảm biến/score test không tham gia lựa chọn.

## Tiêu chí nghiệm thu

- [ ] **PB05-AC01** (FR01): **Khi** xét timestamp đúng 2020-03-01 và 2020-05-01, **thì** lần lượt vào validation và test, không trùng train.
- [ ] **PB05-AC02** (FR02, FR03): **Khi** split/segment bắt đầu đúng 00:00 và warm-up=930 giây, **thì** 00:15 chưa đủ; 00:16 mới đủ warm-up, vẫn phải qua kiểm tra chất lượng.
- [ ] **PB05-AC03** (FR02, FR04): **Khi** kiểm tra lineage fixture của hai split, **thì** không chung raw_row_id hoặc fill origin; reference và evaluation được phân biệt đúng.
- [ ] **PB05-AC04** (FR05): **Khi** một sự cố không có mốc hợp lệ, **thì** giữ nó trong tổng nguồn và ghi không đánh giá được, không xóa khỏi báo cáo.

## Checklist triển khai

- [ ] Triển khai `split.py`: train trước `2020-03-01`, validation từ mốc đó đến trước `2020-05-01`, test từ `2020-05-01` đến hết file.
- [ ] Lưu `splits.json`, lưới chấm điểm một phút và mask; E1 thuộc validation, E2–E4 thuộc test theo timeline nguồn.
- [ ] Reset fill và window ở biên split/segment; warm-up chung 930 giây rồi làm tròn lên mốc phút, kể cả cấu hình W ngắn hơn.
- [ ] Định nghĩa reference mask loại mọi cửa sổ có nguồn thô giao sự cố, kể cả nguồn fill; metric mask giữ tất cả cửa sổ hợp lệ. Hoàn thiện reference mask khi PB07 cung cấp provenance.

## Rủi ro và quyết định cần ghi nhận

- Cho W=1 dùng warm-up ngắn hơn W=15 tạo so sánh lệch: áp dụng warm-up chung.
- Chỉ dùng biên cửa sổ để kiểm tra purge có thể bỏ sót nguồn fill: kiểm tra cả lineage.

## Bằng chứng để đóng PB

- [ ] Cung cấp splits.json, đếm mốc theo reason và test ranh giới/provenance; ghi phần mask được hoàn tất tại PB07.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
