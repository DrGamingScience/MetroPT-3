# PB13 Isolation Forest

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | S — tương đối, chưa quy đổi ngày |
| Mốc | M3 |
| Branch | `feat/pb13-isolation-forest` |
| Phụ thuộc | [PB12](PB12-baseline-workflow.md) |
| Nguồn | Backlog PB13; pipeline chương 8 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người đánh giá cần detector đa biến Isolation Forest chạy trên cùng feature/mask với MAD, với chiều score và chi phí đo thống nhất.

## Phạm vi và ranh giới

Wrapper IF, grid tham số và tích hợp workflow; chưa chọn cấu hình bằng test hoặc tạo feature importance không được model hỗ trợ.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Train reference sau preprocessing; schema | Cùng hợp đồng input như MAD; validation chỉ để score/chọn sau. |
| Đầu ra | model.joblib; model metadata | Tham số, seed, n_train, schema hash và version thư viện. |
| Bàn giao | Validation scores; timing | PB15 so sánh; PB18 chọn/freeze; PB21 giải thích. |

## Yêu cầu chức năng

- **PB13-FR01:** Triển khai cùng giao diện fit/score/save/load và kiểm tra fitted/schema/finite như MAD; score = -model.score_samples(X), lớn hơn luôn là bất thường hơn.
- **PB13-FR02:** Mặc định n_estimators=200, max_samples=min(256,n_train), max_features=1.0, contamination=auto, bootstrap=false, random_state=42, n_jobs=1.
- **PB13-FR03:** Đăng ký grid n_estimators=100/200/400 × max_samples=256/1024, chặn max_samples theo train; ghi giá trị yêu cầu và giá trị thực dùng để không đếm hai config hiệu dụng trùng nhau như hai kết quả độc lập.
- **PB13-FR04:** Không dùng predict/offset mặc định làm alarm cuối và không suy contamination từ nhãn test; threshold đi qua cùng PB18.
- **PB13-FR05:** Đo fit/score bằng perf_counter, cùng phần cứng/n_jobs khi so sánh; lưu throughput, độ trễ/mốc, seed/tham số và model artifact. Seed 7/2026 là kiểm tra ổn định, không chọn theo test.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Thời gian benchmark không bao gồm vô tình refit lúc score; ghi batch size/phạm vi đo.
- Không yêu cầu feature_importances_; giải thích bằng sensor timeline và ablation.

## Tiêu chí nghiệm thu

- [ ] **PB13-AC01** (FR01): **Khi** so score wrapper với score_samples của model đã fit, **thì** đúng dấu đối nhau và schema sai bị từ chối.
- [ ] **PB13-AC02** (FR02, FR03): **Khi** train có ít hơn 256 mẫu, **thì** max_samples không vượt n_train; metadata ghi thực tế.
- [ ] **PB13-AC03** (FR01, FR05): **Khi** save/load cùng model và score cùng dữ liệu, **thì** kết quả tương đương trong dung sai; score không đổi trạng thái model.
- [ ] **PB13-AC04** (FR04, FR05): **Khi** tích hợp với baseline workflow, **thì** có validation score/timing và alarm lấy từ tau caller, không từ predict mặc định.

## Checklist triển khai

- [ ] Triển khai `models/isolation_forest.py` qua cùng giao diện fit/score/save/load như MAD.
- [ ] Dùng `-score_samples`, không lấy `predict` làm alarm. Mặc định 200 cây, max_samples=min(256, n_train), seed 42, n_jobs=1, không bootstrap.
- [ ] Khai báo grid 100/200/400 cây × 256/1024 samples; lưu tham số, fit time, score time và throughput.

## Rủi ro và quyết định cần ghi nhận

- IF có tính ngẫu nhiên: lưu seed; không che biến thiên bằng chọn seed có test tốt nhất.
- So benchmark khác n_jobs/phần cứng không công bằng: khóa điều kiện đo trong manifest.

## Bằng chứng để đóng PB

- [ ] Đính kèm config/model metadata, test score direction/save-load và một lượt validation qua CLI.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
