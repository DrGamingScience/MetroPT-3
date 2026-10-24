# PB19 Chấm test bằng cấu hình đã khóa

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M4 |
| Phụ thuộc | [PB18](PB18-validation-freeze.md) |
| Nguồn | Backlog PB19; pipeline chương 11–13 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người đánh giá cần kết quả test độc lập cho E2–E4 từ đúng cấu hình đã chọn trên validation, bao gồm cả bỏ sót và độ phủ.

## Phạm vi và ranh giới

Chấm các cấu hình/seed đã ghi trước test, tính metric và bảng kết quả trong cùng script đánh giá. Không chọn lại mô hình/ngưỡng từ kết quả test; ý tưởng mới được tách exploratory.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Frozen config/artifacts; test rows; events | Model/cột/tham số khớp cấu hình đã chọn; quality/mask policy cố định, labels tách khỏi score. |
| Đầu ra | scores.parquet; episodes.csv; bảng metric tổng hợp/sự cố | Toàn bộ grid, null/reason invalid, model/tau/window/run truy vết được. |
| Đầu ra | Summary/event tables; X6 seed results | Common mask, coverage/positive rate và kết quả mọi seed đã đăng ký. |

## Yêu cầu chức năng

- **PB19-FR01:** Một hàm hoặc lệnh test nạp đúng model/preprocessing và cấu hình đã chốt bằng đường dẫn tường minh; kiểm tra file/cột/tham số. Không fit/recalibrate trong test; ghép nhãn sau score. Không yêu cầu một framework freeze/test riêng.
- **PB19-FR02:** Giữ mọi mốc với split/segment/valid/reason/score/alarm. Threshold/model/config có thể ghi một lần cho bảng hoặc theo config_id khi gộp nhiều cấu hình; metric dùng valid common mask, invalid score/alarm null.
- **PB19-FR03:** Chấm các cấu hình đã chọn/định trước cho câu hỏi X1/X2 và phần mở rộng thực hiện. Không cần mang mọi cấu hình grid IF lên test. X6 báo seed 42/7/2026 đã chuẩn bị từ train/validation, giữ seed chính 42.
- **PB19-FR04:** Bảng tổng hợp có model/feature_set/W/seed, tham số hoặc config_id, n_train/n_test_valid, positive_rate/coverage, AP/precision/recall/F1, detected/evaluable events, median_delay, outside_episodes_per_day, alert_fraction và fit/score time. Common mask ghi policy/các cấu hình so sánh, không cần hash mask_id.
- **PB19-FR05:** Bảng từng sự cố có event_id,valid_coverage,first_valid_time,detected,first_alarm,delay,max_score; thêm observational_delay và N/A reasons. Valid_coverage là valid ticks/planned ticks trong event; công bố cả missed/unobservable.
- **PB19-FR06:** Ghi nguồn dữ liệu/config/model và điều kiện timing một lần cho bộ kết quả. Test chỉ bổ sung bảng đánh giá, không ghi ngược vào lựa chọn PB18; không lặp hash/metadata ở từng mốc.

## Yêu cầu chất lượng và xử lý trường hợp biên

- So thời gian cùng phần cứng/n_jobs; thời gian fit lấy từ run train tương ứng, không fit lại trong test.
- Không đặt mức AP/recall tối thiểu chưa có căn cứ làm điều kiện hoàn thành.

## Tiêu chí nghiệm thu

- [ ] **PB19-AC01:** **Khi** thiếu cấu hình đã chốt/model/preprocessing hoặc sai feature order/tham số tương ứng, **thì** test dừng trước score và nêu input cần sửa.
- [ ] **PB19-AC02:** **Khi** thay nhãn test rồi đánh giá lại, **thì** model/feature/tau/cấu hình và score không đổi; chỉ nhãn/metric đổi.
- [ ] **PB19-AC03** (FR02, FR04, FR05): **Khi** test có một sự cố bỏ sót và khoảng không quan sát, **thì** bảng hiện đầy đủ missed/unobservable/coverage; invalid không bị coi normal, delay không gán 0.
- [ ] **PB19-AC04:** **Khi** chạy các seed/cấu hình đã định trước, **thì** báo tất cả kết quả đó, giữ cấu hình chính và so cùng mốc hợp lệ.

## Rủi ro và quyết định cần ghi nhận

- Bảng test nhiều biến thể dễ dẫn tới chọn lại 'winner': phân biệt cấu hình chọn trước với mô tả hậu nghiệm.
- Dữ liệu test thiếu đầu sự cố làm delay lớn: giữ delay từ event start và báo observational_delay bổ sung.

## Kết quả cần xem

- [ ] Cung cấp cấu hình đã chọn và bảng test có coverage; kiểm tra nhãn test không làm đổi score/model. Dùng chung bảng này cho report, không thêm mask report riêng.
