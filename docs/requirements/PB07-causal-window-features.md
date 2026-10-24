# PB07 Đặc trưng cửa sổ F35 nhân quả

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M2 |
| Phụ thuộc | [PB05](PB05-temporal-splits.md) |
| Nguồn | Backlog PB07; pipeline chương 6 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người huấn luyện cần vector cảm biến tại từng phút chỉ sử dụng thông tin đã có lúc đó, đồng thời biết vì sao một mốc không được chấm.

## Phạm vi và ranh giới

Tạo F35 ở W=1/5/15, khởi đầu W=5; kiểm tra chất lượng và nguồn trong lúc tính. Fill chỉ triển khai khi audit cho thấy cần. F7 nằm ở PB15, F51/F55 ở PB16; chưa fit preprocessing hay detector.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Cleaned rows; segments; split policy; events | Có raw_row_id, delta0, gap_break và flags trước fill. |
| Đầu ra | features.parquet kèm cột quality/reference | Mọi mốc dự kiến, window/source times, valid và reason. |
| Đầu ra | Tên/thứ tự/công thức feature trong metadata; reference mask trong bảng | Tên/thứ tự/công thức/đơn vị/W/biên/version; bàn giao PB08. |

## Yêu cầu chức năng

- **PB07-FR01:** Tại mốc t trên lưới 60 giây lấy (t-W,t], không đọc tương lai; cửa sổ chỉ thuộc một split/segment và đủ warm-up chung của PB05.
- **PB07-FR02:** F35 gồm mean/std/min/max/slope cho 7 analog; std ddof=0, slope hồi quy tuyến tính theo phút thực từ đầu cửa sổ. Mean theo các hàng quan sát trong cửa sổ sau xử lý thiếu nếu có, không tự đổi sang trọng số thời gian; coverage vẫn chỉ đếm quan sát thật trước fill.
- **PB07-FR03:** Đo coverage trước fill cho từng sensor: ít nhất max(3,ceil(0.8×W_seconds/delta0)) quan sát thật hợp lệ; không gap nội bộ > gap_break; đầu/cuối quan sát cách biên không quá 2×delta0.
- **PB07-FR04:** Nếu có missing ngắn, chỉ forward fill trong cùng split/segment, tuổi giá trị gốc không quá 30 giây; giữ timestamp/raw_row_id nguồn. Không bfill, center rolling hay nội suy tương lai; không thêm impute nếu không cần.
- **PB07-FR05:** Trong lúc tạo feature, kiểm tra mọi nguồn thực dùng (kể cả fill origin) thuộc đúng split/segment và có giao sự cố không. Lưu window_start/end, source_min/max_time và cờ reference trong bảng. Không bắt buộc lưu danh sách raw_row_id cho từng cửa sổ/feature; phải tính lại được từ raw và code.
- **PB07-FR06:** Giữ các mốc invalid kèm reason như warmup/gap/stale_sensor/insufficient_coverage/missing_feature; chúng không vào detector. Feature schema có tên sensor__stat__Wmin, thứ tự và phiên bản.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Dữ liệu timestamp không đều phải cho slope theo thời gian thật; không lấy số thứ tự hàng làm thời gian.
- Nếu một mốc có nhiều lý do invalid, phải có chính sách lưu đủ lý do hoặc thứ tự ưu tiên cố định, ghi trong schema/quality policy.
- Quy tắc cột tham gia coverage phải thống nhất với feature set của run; việc lọc cột trên train ở PB08 không được âm thầm đổi policy giữa các split.

## Tiêu chí nghiệm thu

- [ ] **PB07-AC01:** **Khi** thay mọi quan sát sau t, **thì** feature/quality/reference tại t không đổi; nguồn không vượt t và fixture xác nhận không lấy nguồn qua split.
- [ ] **PB07-AC02** (FR01, FR02): **Khi** dùng fixture không đều có x tăng tuyến tính 2 đơn vị/phút, **thì** slope=2 trong dung sai, ddof=0 và các thống kê còn lại khớp tính tay.
- [ ] **PB07-AC03** (FR03, FR04): **Khi** fixture W=5 phút, delta0=10 giây, có 23 rồi 24 quan sát thật, **thì** 23 không đủ ngưỡng 24; 24 chỉ hợp lệ nếu đạt cả biên/gap; fill không làm tăng observed count.
- [ ] **PB07-AC04:** **Nếu dùng fill**, kiểm tra tuổi 30/31 giây, reset ở split/segment và fill origin trong sự cố; 30 được phép khi các điều kiện khác đạt, 31/qua biên bị từ chối. Không cần xây nhánh fill nếu baseline chưa dùng.
- [ ] **PB07-AC05** (FR05, FR06): **Khi** xuất feature trên lưới có warm-up/gap, **thì** đủ mọi mốc và reason; mask reference loại nguồn giao sự cố, evaluation vẫn tách biệt.

## Rủi ro và quyết định cần ghi nhận

- Chỉ min/max time chưa đủ kiểm tra fill giao sự cố: dùng timestamp gốc trong quá trình tính. Fixture kiểm tra nguồn trực tiếp; không xuất ma trận lineage cho mọi cửa sổ.
- Rolling mặc định theo số hàng dễ sai khi nhịp không đều: dùng cửa sổ thời gian với biên rõ.

## Kết quả cần xem

- [ ] Cung cấp feature/schema/mask mẫu và test sửa tương lai, slope không đều, coverage trước fill, provenance qua split/sự cố.
