# PB18 Chọn cấu hình, ngưỡng và freeze

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M4 |
| Phụ thuộc | [PB15](PB15-experiment-runner.md); [PB16](PB16-feature-ablations.md) nếu dùng mở rộng |
| Nguồn | Backlog PB18; pipeline chương 10 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người review benchmark cần quyết định cấu hình và ngưỡng dựa trên validation, được ghi lại cùng các model đã fit trước khi xem kết quả test.

## Phạm vi và ranh giới

Lựa chọn và hiệu chỉnh q/tau; lưu một frozen_config.json cùng model đã chọn. X7 là phân tích validation tùy chọn. Freeze nghĩa là giữ nguyên lựa chọn khi dùng test, không phải cơ chế khóa file hoặc một dịch vụ riêng. Không refit train+validation hoặc chọn seed theo test.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Bảng cấu hình, score validation/common masks; train-fitted models | PB16 cần hoàn tất nếu đưa biến thể mở rộng vào test xác nhận. |
| Đầu ra | validation_results.csv; lý do chọn ngắn trong report/config | AP/config selection, q/tau, budget/recall/delay, trade-off. |
| Đầu ra | frozen_config.json; đường dẫn model/preprocessing đã chọn | Đủ model/preprocess/features/mask/event/merge/code/data reference cho PB19. |

## Yêu cầu chức năng

- **PB18-FR01:** Chọn W/hyperparameter của từng detector theo AP validation trên common mask đã đăng ký; AP hòa 4 chữ số ưu tiên ít chiều, ít cây với IF, rồi score time thấp; hòa tiếp dùng config_id cố định có ghi quy ước.
- **PB18-FR02:** Tau lấy từ score validation reference đã loại mọi nguồn giao sự cố, q=0.95/0.975/0.99/0.995/0.999, method=higher; alarm dùng >, không >=.
- **PB18-FR03:** Với merge chính 5 phút, budget thí nghiệm<=1 episode ngoài báo cáo/ngày hợp lệ: ưu tiên ngưỡng phát hiện E1 trong budget, rồi recall cao/delay thấp/ít đợt/q cao. Nếu không có ngưỡng đạt cả phát hiện và budget, giữ q=0.99 và công bố trade-off.
- **PB18-FR04:** Có thể đối chiếu merge 1/5/10 phút trên validation (X7) nếu cần hiểu độ nhạy. Benchmark chính vẫn merge=5 phút; X7 không phải điều kiện hoàn thành và không dùng test để chọn merge.
- **PB18-FR05:** Ghi feature_set/W, cột/order, đường dẫn preprocessing/model, seed, q/tau, quality/reference/merge/matching policy, raw version và code reference trong frozen_config.json. Một file có thể chứa ba detector và các seed đã chọn; không bắt buộc checksum từng artifact hoặc registry riêng.
- **PB18-FR06:** Trước test, kiểm tra có cấu hình đã chốt, model/preprocessing tồn tại và metadata/cột/tham số tương ứng. Thiếu/sai thì dừng, không tự fit lại. Không refit train+validation; thay nhãn test không được đổi lựa chọn.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Nếu validation thiếu hai lớp hoặc không có reference score, ghi không đủ điều kiện chọn chính theo AP/tau; không ngầm chọn bằng test.
- Ghi rõ budget là lựa chọn đồ án, không bảo đảm tiêu chuẩn vận hành; q=0.99 không đồng nghĩa chính xác 1% alarm.

## Tiêu chí nghiệm thu

- [ ] **PB18-AC01** (FR01): **Khi** hai config hòa AP đến 4 số, **thì** lựa chọn theo thứ tự tie-break đã ghi, không theo thứ tự hoàn tất job.
- [ ] **PB18-AC02** (FR02): **Khi** score tham chiếu có ties và có cửa sổ sau event còn giao nguồn, **thì** quantile higher/điều kiện > đúng; cửa sổ giao nguồn không vào tập lấy tau.
- [ ] **PB18-AC03:** **Khi** không ngưỡng nào vừa phát hiện E1 vừa đạt budget, **thì** giữ q=0.99 và báo trade-off; nếu có X7, kết quả được ghi tách khỏi cấu hình chính.
- [ ] **PB18-AC04:** **Khi** đã chốt rồi thay nhãn test, **thì** model/tau/config không đổi. Thiếu model/preprocessing hoặc cột/tham số không khớp thì test dừng; không cần test chống sửa mọi metadata/hash.

## Rủi ro và quyết định cần ghi nhận

- Dùng toàn bộ validation lấy ngưỡng đưa sự cố vào reference: phân biệt reference mask với metric mask.
- Refit sau calibration làm score scale đổi: giữ model train đã chọn và tau đã hiệu chỉnh.

## Kết quả cần xem

- [ ] Cung cấp bảng q/tau, lý do chọn và frozen config; kiểm tra lựa chọn độc lập test labels và phát hiện thiếu/sai input model/cột. Không cần biên bản hoặc hash chain riêng.
