# PB13 Isolation Forest

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M3 |
| Phụ thuộc | [PB12](PB12-baseline-workflow.md) |
| Nguồn | Backlog PB13; pipeline chương 8 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người đánh giá cần detector đa biến Isolation Forest chạy trên cùng feature/mask với MAD, với chiều score và chi phí đo thống nhất.

## Phạm vi và ranh giới

Wrapper IF, grid tham số và tích hợp workflow; chưa chọn cấu hình bằng test hoặc tạo feature importance không được model hỗ trợ.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Train reference sau preprocessing; schema | Cùng hợp đồng input như MAD; validation chỉ để score/chọn sau. |
| Đầu ra | model.joblib; model metadata | Tham số, seed, n_train, tên/thứ tự feature và version thư viện. |
| Bàn giao | Validation scores; timing | PB15 so sánh; PB18 chọn/freeze; PB21 giải thích. |

## Yêu cầu chức năng

- **PB13-FR01:** Triển khai cùng giao diện fit/score/save/load và kiểm tra fitted/schema/finite như MAD; score = -model.score_samples(X), lớn hơn luôn là bất thường hơn.
- **PB13-FR02:** Mặc định n_estimators=200, max_samples=min(256,n_train), max_features=1.0, contamination=auto, bootstrap=false, random_state=42, n_jobs=1.
- **PB13-FR03:** Đăng ký grid n_estimators=100/200/400 × max_samples=256/1024, chặn max_samples theo train; ghi giá trị yêu cầu và giá trị thực dùng để không đếm hai config hiệu dụng trùng nhau như hai kết quả độc lập.
- **PB13-FR04:** Không dùng predict/offset mặc định làm alarm cuối và không suy contamination từ nhãn test; threshold đi qua cùng PB18.
- **PB13-FR05:** Đo fit_seconds và score_seconds bằng perf_counter, cùng máy/n_jobs khi so sánh; lưu seed/tham số và n_scored. Suy ms/mốc từ các số này khi cần, không cần profiler/telemetry. Seed 7/2026 dùng kiểm tra ổn định, không chọn theo test.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Thời gian benchmark không bao gồm vô tình refit lúc score; ghi batch size/phạm vi đo.
- Không yêu cầu feature_importances_; giải thích bằng sensor timeline và ablation.

## Tiêu chí nghiệm thu

- [ ] **PB13-AC01** (FR01): **Khi** so score wrapper với score_samples của model đã fit, **thì** đúng dấu đối nhau và schema sai bị từ chối.
- [ ] **PB13-AC02** (FR02, FR03): **Khi** train có ít hơn 256 mẫu, **thì** max_samples không vượt n_train; metadata ghi thực tế.
- [ ] **PB13-AC03** (FR01, FR05): **Khi** save/load cùng model và score cùng dữ liệu, **thì** kết quả tương đương trong dung sai; score không đổi trạng thái model.
- [ ] **PB13-AC04** (FR04, FR05): **Khi** tích hợp với baseline workflow, **thì** có validation score/timing và alarm lấy từ tau caller, không từ predict mặc định.

## Rủi ro và quyết định cần ghi nhận

- IF có tính ngẫu nhiên: lưu seed; không che biến thiên bằng chọn seed có test tốt nhất.
- So timing trên cùng máy/n_jobs; ghi điều kiện một lần cho bảng thí nghiệm.

## Kết quả cần xem

- [ ] Đính kèm config/model metadata, test score direction/save-load và một lượt validation qua CLI.
