# PB18 Chọn cấu hình, ngưỡng và freeze

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | L — tương đối, chưa quy đổi ngày |
| Mốc | M4 |
| Branch | `feat/pb18-validation-freeze` |
| Phụ thuộc | [PB15](PB15-experiment-runner.md); [PB16](PB16-feature-ablations.md) nếu dùng mở rộng |
| Nguồn | Backlog PB18; pipeline chương 10 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người review benchmark cần quyết định cấu hình và ngưỡng dựa trên validation, được khóa cùng toàn bộ artifact trước khi biết kết quả test.

## Phạm vi và ranh giới

Lựa chọn, hiệu chỉnh q/tau, X7 và freeze từng cấu hình xác nhận. Không refit train+validation hoặc chọn seed theo test.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Validation registry/scores/common masks; train-fitted models | PB16 cần hoàn tất nếu đưa biến thể mở rộng vào test xác nhận. |
| Đầu ra | validation_results.csv; decision record | AP/config selection, q/tau, budget/recall/delay, trade-off. |
| Đầu ra | frozen_config.json; artifact hashes | Đủ model/preprocess/features/mask/event/merge/code/data policy cho PB19. |

## Yêu cầu chức năng

- **PB18-FR01:** Chọn W/hyperparameter của từng detector theo AP validation trên common mask đã đăng ký; AP hòa 4 chữ số ưu tiên ít chiều, ít cây với IF, rồi score time thấp; hòa tiếp dùng config_id cố định có ghi quy ước.
- **PB18-FR02:** Tau lấy từ score validation reference đã loại mọi nguồn giao sự cố, q=0.95/0.975/0.99/0.995/0.999, method=higher; alarm dùng >, không >=.
- **PB18-FR03:** Với merge chính 5 phút, budget thí nghiệm<=1 episode ngoài báo cáo/ngày hợp lệ: ưu tiên ngưỡng phát hiện E1 trong budget, rồi recall cao/delay thấp/ít đợt/q cao. Nếu không có ngưỡng đạt cả phát hiện và budget, giữ q=0.99 và công bố trade-off.
- **PB18-FR04:** X7 đối chiếu merge 1/5/10 phút chỉ trên validation như sensitivity; benchmark chính vẫn merge=5 phút, không biến sensitivity thành chọn theo test.
- **PB18-FR05:** Freeze feature_set/W/schema/retained columns/preprocessing/model/seed/q/tau/mask policy/merge/matching và hashes code/data/artifacts; đăng ký mọi biến thể/seed sẽ test.
- **PB18-FR06:** Từ chối freeze thiếu hoặc sai artifact; stage test từ chối thiếu frozen_config hoặc hash sai. Freeze không fit lại trên train+validation và thay nhãn test không được đổi lựa chọn.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Nếu validation thiếu hai lớp hoặc không có reference score, ghi không đủ điều kiện chọn chính theo AP/tau; không ngầm chọn bằng test.
- Ghi rõ budget là lựa chọn đồ án, không bảo đảm tiêu chuẩn vận hành; q=0.99 không đồng nghĩa chính xác 1% alarm.

## Tiêu chí nghiệm thu

- [ ] **PB18-AC01** (FR01): **Khi** hai config hòa AP đến 4 số, **thì** lựa chọn theo thứ tự tie-break đã ghi, không theo thứ tự hoàn tất job.
- [ ] **PB18-AC02** (FR02): **Khi** score tham chiếu có ties và có cửa sổ sau event còn giao nguồn, **thì** quantile higher/điều kiện > đúng; cửa sổ giao nguồn không vào tập lấy tau.
- [ ] **PB18-AC03** (FR03, FR04): **Khi** không ngưỡng nào vừa phát hiện E1 vừa đạt budget, **thì** giữ q=0.99, báo trade-off và kết quả X7 tách khỏi config chính.
- [ ] **PB18-AC04** (FR05, FR06): **Khi** freeze xong rồi thay nhãn test, **thì** model/tau/config hash không đổi; thiếu/sửa artifact làm test bị từ chối.

## Checklist triển khai

- [ ] Chọn W/hyperparameter của từng detector bằng AP validation trên common mask. AP hòa đến 4 chữ số: ít chiều hơn → ít cây hơn với IF → thời gian score thấp hơn; nếu còn hòa, dùng thứ tự config_id cố định và ghi đây là quy ước triển khai bổ sung.
- [ ] Tính tau từ validation reference với q = 0.95/0.975/0.99/0.995/0.999, `method=higher`, alarm dùng `>`.
- [ ] Với gộp chính 5 phút và ngân sách thí nghiệm 1 đợt ngoài báo cáo/ngày hợp lệ, chọn ngưỡng đạt ngân sách và phát hiện E1; ưu tiên event recall → delay → ít đợt → q cao hơn. Nếu không có ngưỡng đáp ứng cả hai, giữ q=0.99 và báo trade-off.
- [ ] X7 đối chiếu gộp 1/5/10 phút trên validation dưới dạng phân tích độ nhạy; gộp benchmark chính vẫn 5 phút theo đặc tả.
- [ ] Xuất `validation_results.csv`, biên bản lựa chọn và `frozen_config.json` cho từng model/cấu hình đã đăng ký: feature/schema/mask policy, preprocessing/model hash, seed, q/tau, matching, merge, code/data hash.

## Rủi ro và quyết định cần ghi nhận

- Dùng toàn bộ validation lấy ngưỡng đưa sự cố vào reference: phân biệt reference mask với metric mask.
- Refit sau calibration làm score scale đổi: giữ model train đã chọn và hash cố định.

## Bằng chứng để đóng PB

- [ ] Cung cấp bảng q/tau, biên bản chọn, frozen config và test chống dùng test labels/thiếu artifact/sai hash.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
