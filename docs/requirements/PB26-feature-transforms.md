# PB26 PCA cho detector và lọc tương quan

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P2 — tùy chọn |
| Quy mô | L — tương đối, chưa quy đổi ngày |
| Mốc | P2 — thí nghiệm biến đổi feature |
| Branch | `experiment/pb26-feature-transforms` |
| Phụ thuộc | [PB15](PB15-experiment-runner.md), [PB17](PB17-operating-modes.md) |
| Nguồn | Backlog PB26; pipeline chương 5, 7, 13 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người nghiên cứu cần đo ảnh hưởng của PCA hoặc lọc tương quan tới detector mà giữ nguyên benchmark chính và giao thức không leakage.

## Phạm vi và ranh giới

Hai nhánh độc lập: detector dùng PCA và detector dùng lọc tương quan. Không mặc định gộp cả hai hoặc tái sử dụng PCA chỉ dùng vẽ mà chưa đăng ký cấu hình detector.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | PB17 transformers/EDA; features/runner | Cần cả runner PB15 cho train/validation, không chỉ biểu đồ PCA. |
| Đầu ra | Transform configs/artifacts; retained schemas | Scaler/PCA/correlation selections fit train, components/threshold/version. |
| Đầu ra | Validation results và mask summaries | So detector gốc với nhánh PCA hoặc correlation filter, tau riêng. |

## Yêu cầu chức năng

- **PB26-FR01:** Đăng ký riêng từng giả thuyết/nhánh, detector/feature_set/W và budget tìm kiếm; không mở grid lớn dựa trên test.
- **PB26-FR02:** Nhánh PCA: fit scaler/PCA trên train reference, chọn số component bằng quy tắc train đã ghi; đánh giá detector trên validation, lưu variance ratio và model input schema.
- **PB26-FR03:** Nhánh correlation: tính tương quan train, chốt metric/ngưỡng/quy tắc chọn đại diện nhóm; tie-break cố định, lưu các cột bỏ/giữ và không tính lại selection ở validation/test.
- **PB26-FR04:** Mỗi nhánh fit detector lại trên transformed train và lấy tau từ validation reference của chính nó; báo common timestamps, dimension trước/sau, AP/event/burden/runtime và coverage.
- **PB26-FR05:** Giải thích trong đúng không gian model; PCA contribution không được gọi trực tiếp là sensor contribution nếu chưa có phép quy đổi hợp lệ. Benchmark chính giữ nguyên.
- **PB26-FR06:** Nếu muốn test xác nhận, đăng ký/freeze trước khi xem test; nhánh phát sinh sau đó là exploratory hoặc cần dữ liệu đánh giá độc lập.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Lưu thứ tự feature trước/sau transform để không chiếu sai chiều khi nạp model.
- Đổi component count, correlation threshold hoặc retained list làm artifact/config hash đổi.

## Tiêu chí nghiệm thu

- [ ] **PB26-AC01** (FR01, FR02, FR03): **Khi** chạy hai nhánh đã đăng ký, **thì** registry phân biệt PCA/correlation; không âm thầm gộp biến đổi.
- [ ] **PB26-AC02** (FR02, FR03): **Khi** thay dữ liệu validation/test, **thì** scaler/components/correlation selection từ train không đổi.
- [ ] **PB26-AC03** (FR03, FR04): **Khi** fixture tương quan hoàn toàn có tie và một cột độc lập, **thì** danh sách giữ/bỏ theo quy tắc cố định; detector/tau riêng và bảng dùng common mask.
- [ ] **PB26-AC04** (FR04, FR05, FR06): **Khi** báo kết quả nhánh sau khi benchmark test đã xem, **thì** nhãn exploratory rõ, không đổi cấu hình chính hoặc diễn giải contribution sai không gian.

## Checklist triển khai

- [ ] Đăng ký giả thuyết, số component/tiêu chí train và correlation policy.
- [ ] Triển khai hai nhánh độc lập với lưu/nạp schema/transformer.
- [ ] Fit lại detector, hiệu chỉnh tau trên validation và kiểm tra train-only.
- [ ] Viết bảng so kết quả/chi phí/giới hạn giải thích, tuân điều kiện test đã đăng ký.

## Rủi ro và quyết định cần ghi nhận

- PC giữ variance lớn chưa chắc giữ tín hiệu bất thường: đánh giá validation, không suy cải thiện từ variance.
- Feature tương quan cao vẫn có thể chứa tín hiệu hữu ích: lọc là ablation riêng, không sửa baseline mặc định.

## Bằng chứng để đóng PB

- [ ] Cung cấp config/hypothesis registry, fitted transform metadata, test không leakage và bảng validation từng nhánh.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
