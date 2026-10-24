# PB15 Runner thí nghiệm và đối chiếu cửa sổ

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | L — tương đối, chưa quy đổi ngày |
| Mốc | M3 |
| Branch | `feat/pb15-experiment-runner` |
| Phụ thuộc | [PB13](PB13-isolation-forest.md), [PB14](PB14-frozen-ecod.md) |
| Nguồn | Backlog PB15; pipeline chương 10, 12–13 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người quản lý thí nghiệm cần registry và kết quả validation công bằng giữa mô hình/cửa sổ, có cache để tránh fit lại khi chỉ thay ngưỡng.

## Phạm vi và ranh giới

X1, X2 và hạ tầng runner/cache; đăng ký X6/X7. PB18 thực hiện lựa chọn/freeze cuối; PB16 bổ sung X3–X5.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Ba model; feature builder; preprocessing; registry config | Train/validation hợp lệ, version dữ liệu và code rõ. |
| Đầu ra | Experiment registry; score cache; common masks | Mỗi run có model/feature_set/W/seed/hashes/mask_id. |
| Đầu ra | Bảng validation X1/X2 | Có coverage riêng và chung; F7 baseline tức thời, grid F35. |

## Yêu cầu chức năng

- **PB15-FR01:** X1 dùng MAD/IF/FrozenECOD, F35 W=5; X2 dùng W=1/5/15 và F7 là 7 analog mới nhất tại t có tuổi tối đa 2×delta0, cùng split/segment và warm-up chung.
- **PB15-FR02:** Với mỗi bảng, giao valid timestamps của các cấu hình tham gia; cùng nguồn cảm biến/schema trong phép so model cùng feature_set. Không ép các W hoặc F7/F35 có tên/số feature giống nhau; công bố rõ khác biệt.
- **PB15-FR03:** Fit preprocessing/model riêng từng cấu hình từ train reference; lưu mask_id, n_valid, positive_rate, removed counts và phụ lục mask riêng. Không so AP khác mask như cùng tập đánh giá.
- **PB15-FR04:** Lưới F35 chính tối đa 24 lượt fit trước F7/mở rộng: 3 W×(1 MAD+1 ECOD+6 IF); score cache định danh bằng data/config/schema/model/code hashes.
- **PB15-FR05:** Đổi q hoặc merge policy chỉ cần tính lại phần hậu xử lý từ score cache đúng nguồn; đổi W/features/model/data làm cache không hợp lệ. Không dùng lại alarm như score.
- **PB15-FR06:** Đăng ký X6 với seed 42/7/2026 và kế hoạch X7 q/merge chỉ trên validation; registry nêu rõ config dự kiến test trước khi chạy PB19.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Mỗi run lỗi có trạng thái/lý do và không được đưa vào bảng như một run thành công.
- Benchmark timing cùng điều kiện đo; registry/cached scores phải truy ra input artifacts.

## Tiêu chí nghiệm thu

- [ ] **PB15-AC01** (FR01): **Khi** chạy registry X1 rồi X2 trên fixture/validation, **thì** đủ model/W/F7 đã đăng ký; F7 stale bị loại và không lấy mẫu tương lai.
- [ ] **PB15-AC02** (FR02, FR03): **Khi** hai cấu hình có valid masks khác nhau, **thì** bảng chính chỉ dùng giao timestamps, có mask_id/số loại và phụ lục coverage riêng.
- [ ] **PB15-AC03** (FR04, FR05): **Khi** chạy lại cùng registry rồi chỉ thay q, **thì** score cache được dùng lại đúng hash; không phát sinh fit mới chỉ vì đổi threshold.
- [ ] **PB15-AC04** (FR04, FR05): **Khi** đổi W hoặc schema/model hash, **thì** không tái sử dụng cache cũ, tạo run mới.
- [ ] **PB15-AC05** (FR06): **Khi** kiểm tra registry trước test, **thì** seed/config dự kiến được đăng ký, không có lựa chọn dựa trên test.

## Checklist triển khai

- [ ] Hoàn thành X1: ba model, F35 W=5; X2: F35 W=1/5/15 và F7 mới nhất với tuổi tối đa `2 × delta0`.
- [ ] Mỗi bảng dùng giao các mốc hợp lệ, warm-up chung và cùng cột sau preprocessing trong phép so sánh; lưu `mask_id`, số mốc loại, positive rate. Báo thêm độ phủ riêng từng cấu hình ở phụ lục.
- [ ] Lưới F35 seed chính có tối đa 24 lượt fit: 3 W × (1 MAD + 1 ECOD + 6 IF); F7 và mở rộng tính riêng.
- [ ] Lưu/cache score theo data/config/model/schema hash để khảo sát q và gộp mà không fit lại; tránh dùng score cache của cấu hình khác.
- [ ] Đăng ký X6 với seed 42/7/2026 cho cấu hình IF chọn trên validation; không chọn seed theo test. Tạo kế hoạch X7 chỉ trên validation.

## Rủi ro và quyết định cần ghi nhận

- Yêu cầu 'cùng cột' bị áp nhầm cho so F7/F35 hoặc các W: chỉ giữ cùng schema khi đang so model trên cùng feature set.
- Cache thiếu code/data hash có thể dùng nhầm kết quả: định danh đầy đủ và kiểm tra stage cha.

## Bằng chứng để đóng PB

- [ ] Cung cấp registry, bảng validation X1/X2, mask summaries và log cache hit/miss/fit count.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
