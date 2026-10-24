# PB07 Đặc trưng cửa sổ F35 nhân quả

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | L — tương đối, chưa quy đổi ngày |
| Mốc | M2 |
| Branch | `feat/pb07-causal-window-features` |
| Phụ thuộc | [PB05](PB05-temporal-splits.md) |
| Nguồn | Backlog PB07; pipeline chương 6 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người huấn luyện cần vector cảm biến tại từng phút chỉ sử dụng thông tin đã có lúc đó, đồng thời biết vì sao một mốc không được chấm.

## Phạm vi và ranh giới

Tạo F35 ở W=1/5/15, khởi đầu W=5; quản lý chất lượng, fill và lineage. F7 nằm ở PB15, F51/F55 ở PB16; chưa fit preprocessing hay detector.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Cleaned rows; segments; split policy; events | Có raw_row_id, delta0, gap_break và flags trước fill. |
| Đầu ra | features.parquet; quality/provenance masks | Mọi mốc dự kiến, window/source times, valid và reason. |
| Đầu ra | feature_schema.json; reference masks hoàn chỉnh | Tên/thứ tự/công thức/đơn vị/W/biên/version; bàn giao PB08. |

## Yêu cầu chức năng

- **PB07-FR01:** Tại mốc t trên lưới 60 giây lấy (t-W,t], không đọc tương lai; cửa sổ chỉ thuộc một split/segment và đủ warm-up chung của PB05.
- **PB07-FR02:** F35 gồm mean/std/min/max/slope cho 7 analog; std ddof=0, slope hồi quy tuyến tính theo phút thực từ đầu cửa sổ. Mean theo các hàng quan sát trong cửa sổ sau xử lý thiếu nếu có, không tự đổi sang trọng số thời gian; coverage vẫn chỉ đếm quan sát thật trước fill.
- **PB07-FR03:** Đo coverage trước fill cho từng sensor: ít nhất max(3,ceil(0.8×W_seconds/delta0)) quan sát thật hợp lệ; không gap nội bộ > gap_break; đầu/cuối quan sát cách biên không quá 2×delta0.
- **PB07-FR04:** Nếu có missing ngắn, chỉ forward fill trong cùng split/segment, tuổi giá trị gốc không quá 30 giây; giữ timestamp/raw_row_id nguồn. Không bfill, center rolling hay nội suy tương lai; không thêm impute nếu không cần.
- **PB07-FR05:** Lưu window_start/end, source_min/max_time và lineage đủ kiểm tra nguồn fill, giao sự cố và chia tập; hoàn thiện train/validation reference mask theo toàn bộ nguồn đã dùng.
- **PB07-FR06:** Giữ các mốc invalid kèm reason như warmup/gap/stale_sensor/insufficient_coverage/missing_feature; chúng không vào detector. Feature schema có tên sensor__stat__Wmin, thứ tự và phiên bản.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Dữ liệu timestamp không đều phải cho slope theo thời gian thật; không lấy số thứ tự hàng làm thời gian.
- Nếu một mốc có nhiều lý do invalid, phải có chính sách lưu đủ lý do hoặc thứ tự ưu tiên cố định, ghi trong schema/quality policy.
- Quy tắc cột tham gia coverage phải thống nhất với feature set của run; việc lọc cột trên train ở PB08 không được âm thầm đổi policy giữa các split.

## Tiêu chí nghiệm thu

- [ ] **PB07-AC01** (FR01, FR05): **Khi** thay mọi quan sát sau t nhưng giữ lịch sử tới t, **thì** feature và lineage tại t không đổi; source_max_time không vượt t.
- [ ] **PB07-AC02** (FR01, FR02): **Khi** dùng fixture không đều có x tăng tuyến tính 2 đơn vị/phút, **thì** slope=2 trong dung sai, ddof=0 và các thống kê còn lại khớp tính tay.
- [ ] **PB07-AC03** (FR03, FR04): **Khi** fixture W=5 phút, delta0=10 giây, có 23 rồi 24 quan sát thật, **thì** 23 không đủ ngưỡng 24; 24 chỉ hợp lệ nếu đạt cả biên/gap; fill không làm tăng observed count.
- [ ] **PB07-AC04** (FR04, FR05): **Khi** fill có tuổi 30 rồi 31 giây hoặc đi qua biên split/segment, **thì** 30 được phép nếu các điều kiện khác đạt; 31 và qua biên bị từ chối, nguồn sự cố vẫn được kiểm tra.
- [ ] **PB07-AC05** (FR05, FR06): **Khi** xuất feature trên lưới có warm-up/gap, **thì** đủ mọi mốc và reason; mask reference loại nguồn giao sự cố, evaluation vẫn tách biệt.

## Checklist triển khai

- [ ] Triển khai `features.py` cho `(t-W, t]`, stride 60 giây; hỗ trợ W = 1, 5, 15 phút, khởi đầu chạy W = 5.
- [ ] Tính 7 analog × mean/std/min/max/slope; `ddof=0`, slope theo thời gian thật bằng phút, mean theo các mẫu quan sát.
- [ ] Độ phủ tính trước fill, mỗi cảm biến cần ít nhất `max(3, ceil(0.8 × W_seconds / delta0))` mẫu thật; kiểm tra gap và hai biên với dung sai `2 × delta0`.
- [ ] Nếu cần fill, chỉ forward fill tuổi tối đa 30 giây cùng split/segment, lưu thời điểm nguồn. Không tạo impute khi dữ liệu đã đầy đủ.
- [ ] Lưu toàn bộ mốc dự kiến, `valid`, reason, biên cửa sổ, min/max source time và provenance đủ kiểm tra giao sự cố/purge.
- [ ] Xuất `features.parquet`, quality mask và `feature_schema.json` gồm cột/thứ tự/công thức/đơn vị/phiên bản.

## Rủi ro và quyết định cần ghi nhận

- Lưu min/max time không đủ chứng minh toàn bộ lineage trong một số cách fill: giữ tham chiếu raw_row_id hoặc cấu trúc lineage có thể kiểm tra.
- Rolling mặc định theo số hàng dễ sai khi nhịp không đều: dùng cửa sổ thời gian với biên rõ.

## Bằng chứng để đóng PB

- [ ] Cung cấp feature/schema/mask mẫu và test sửa tương lai, slope không đều, coverage trước fill, provenance qua split/sự cố.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
