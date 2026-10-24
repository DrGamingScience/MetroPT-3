# PB19 Chấm test bằng cấu hình đã khóa

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M4 |
| Branch | `feat/pb19-frozen-test-benchmark` |
| Phụ thuộc | [PB18](PB18-validation-freeze.md) |
| Nguồn | Backlog PB19; pipeline chương 11–13 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người đánh giá cần kết quả test độc lập cho E2–E4 từ đúng cấu hình đã chọn trên validation, bao gồm cả bỏ sót và độ phủ.

## Phạm vi và ranh giới

Chấm các run đã đăng ký và frozen, tính metric/bảng test. Không chọn lại mô hình/ngưỡng từ kết quả test; ý tưởng mới được tách exploratory.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Frozen config/artifacts; test rows; events | Hash khớp, feature/quality/mask policy đã cố định, labels tách khỏi score. |
| Đầu ra | scores.parquet; episodes.csv; metrics.json | Toàn bộ grid, null/reason invalid, model/tau/window/run truy vết được. |
| Đầu ra | Summary/event tables; X6 seed results | Common mask, coverage/positive rate và kết quả mọi seed đã đăng ký. |

## Yêu cầu chức năng

- **PB19-FR01:** Lệnh test --frozen chỉ nạp artifact đủ/đúng hash; dùng train-fitted preprocessing/model và feature policy đã khóa, không fit/recalibrate. Ghép nhãn sau khi sinh score.
- **PB19-FR02:** Giữ mọi mốc dự kiến với split/segment/valid/reason/score/threshold/alarm/model_version; metric chỉ dùng explicit valid comparison mask, invalid score/alarm là null.
- **PB19-FR03:** Chấm mọi config X1/X2/mở rộng đã đăng ký; X6 chạy IF seed 42/7/2026 đã freeze, không thay seed chính dựa trên test.
- **PB19-FR04:** Summary có model,feature_set,W,seed,mask_id,n_train,n_test_valid,positive_rate,AP,precision,recall,F1,detected_events,evaluable_events,median_delay,outside_episodes_per_day,alert_fraction,fit_seconds,score_ms_per_window.
- **PB19-FR05:** Bảng từng sự cố có event_id,valid_coverage,first_valid_time,detected,first_alarm,delay,max_score; thêm observational_delay và N/A reasons. Valid_coverage là valid ticks/planned ticks trong event; công bố cả missed/unobservable.
- **PB19-FR06:** Hiện đầy đủ dataset/code/config/model hashes và điều kiện timing; kết quả test chỉ bổ sung artifact đánh giá, không ghi ngược vào quyết định chính PB18.

## Yêu cầu chất lượng và xử lý trường hợp biên

- So thời gian cùng phần cứng/n_jobs; thời gian fit lấy từ run train tương ứng, không fit lại trong test.
- Không đặt mức AP/recall tối thiểu chưa có căn cứ làm điều kiện hoàn thành.

## Tiêu chí nghiệm thu

- [ ] **PB19-AC01** (FR01): **Khi** thiếu frozen config hoặc checksum model/schema không khớp, **thì** test dừng trước score và nêu artifact lỗi.
- [ ] **PB19-AC02** (FR01, FR06): **Khi** thay nhãn test rồi chạy đánh giá lại, **thì** model/feature selection/tau/frozen hash và score không đổi; chỉ kết quả nhãn/metric đổi.
- [ ] **PB19-AC03** (FR02, FR04, FR05): **Khi** test có một sự cố bỏ sót và khoảng không quan sát, **thì** bảng hiện đầy đủ missed/unobservable/coverage; invalid không bị coi normal, delay không gán 0.
- [ ] **PB19-AC04** (FR03, FR04, FR06): **Khi** chạy các seed/config đăng ký, **thì** báo tất cả, giữ cấu hình chính và comparison mask đúng registry.

## Checklist triển khai

- [ ] Hoàn thiện `test --frozen ...`: chỉ nạp artifact đã khóa, không fit hoặc hiệu chỉnh trong test; ghép nhãn sau score.
- [ ] Chấm cùng mốc cho từng bảng, lưu `scores.parquet`, `episodes.csv`, `metrics.json`, bảng summary và bảng từng sự cố.
- [ ] Chạy các biến thể X1/X2 và phần mở rộng đã đăng ký; X6 báo cả seed 42/7/2026 cho IF, cấu hình chính vẫn seed đã chốt.
- [ ] Summary có model/feature_set/W/seed/mask_id/n_train/n_test_valid/positive_rate/AP/precision/recall/F1/detected_events/evaluable_events/median_delay/outside_episodes_per_day/alert_fraction/fit_seconds/score_ms_per_window.
- [ ] Bảng sự cố có event_id/valid_coverage/first_valid_time/detected/first_alarm/delay/max_score, kèm observational delay và lý do không đánh giá được nếu có.

## Rủi ro và quyết định cần ghi nhận

- Bảng test nhiều biến thể dễ dẫn tới chọn lại 'winner': phân biệt cấu hình chọn trước với mô tả hậu nghiệm.
- Dữ liệu test thiếu đầu sự cố làm delay lớn: giữ delay từ event start và báo observational_delay bổ sung.

## Bằng chứng để đóng PB

- [ ] Cung cấp frozen run_id, toàn bộ test tables, mask/coverage report và kiểm tra nhãn test không làm đổi score/model.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
