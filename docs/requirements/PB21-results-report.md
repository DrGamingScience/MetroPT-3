# PB21 Case study và báo cáo kết quả

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M5 |
| Branch | `feat/pb21-results-report` |
| Phụ thuộc | [PB19](PB19-frozen-test-benchmark.md); [PB16](PB16-feature-ablations.md), [PB17](PB17-operating-modes.md) cho phân tích mở rộng |
| Nguồn | Backlog PB21; pipeline chương 13, 16 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người đọc cần hiểu mô hình phát hiện hay bỏ sót gì, chi phí cảnh báo ra sao và bằng chứng cảm biến nào hỗ trợ giải thích.

## Phạm vi và ranh giới

Report/case study từ artifacts đã có; PB16/PB17 bổ sung ablation/cụm khi được thực hiện. Không sửa cấu hình chính theo case test.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | PB19 scores/episodes/metrics/frozen; train quantiles | Có thể thêm clusters PB17 và ablations PB16; giữ nguồn theo run/mask. |
| Đầu ra | Report, summary/PR/timeline/case artifacts | Đơn vị, split, run_id, links tới dữ liệu máy đọc và hạn chế kết luận. |
| Đầu ra | Case selection manifest; explanations | Các event, episode chọn thêm, seed, feature/sensor contributions. |

## Yêu cầu chức năng

- **PB21-FR01:** Tạo ít nhất một case cho từng sự cố test nguồn, gồm detected/missed và ghi rõ unobservable nếu có; không chỉ chọn sự cố dễ phát hiện.
- **PB21-FR02:** Chọn thêm episode ngoài báo cáo score cao và sample ngẫu nhiên cố định từ các episode khác; lưu seed, tiêu chí và danh sách chọn, tránh trùng case không cần thiết.
- **PB21-FR03:** Timeline mỗi case gồm sensor/score/tau/actual alarms/event/quality; thêm cluster nếu PB17 có, nếu thiếu thì ghi phần đó chưa triển khai thay vì tạo nhãn cụm giả.
- **PB21-FR04:** ECOD giải thích top 5 feature từ winning branch, tổng contribution đúng score, nhóm sensor và kèm giá trị/quantile train; MAD nêu feature max/median/deviation; IF dùng timeline và ablation, không causal attribution.
- **PB21-FR05:** Tổng hợp X0–X7 theo phần đã làm, so với MAD trên cùng mask, công bố coverage/AP/event counts/delay/outside episodes và timing. Chỉ báo con số có trong artifacts thực tế.
- **PB21-FR06:** Phân loại khả năng cho episode ngoài báo cáo: chuyển chế độ, train thiếu trạng thái, drift, vấn đề dữ liệu hoặc chưa xác minh; ghi độ chắc chắn và hạn chế ít sự cố/nhãn chưa đầy đủ.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Report --run-id đọc đúng chuỗi artifacts và không fit detector; số trên report phải khớp metrics.json.
- Ảnh/bảng có tên model/feature/W/split/run và đơn vị; lưu bảng máy đọc được để kiểm tra.

## Tiêu chí nghiệm thu

- [ ] **PB21-AC01** (FR01, FR02): **Khi** sinh report cho test đầy đủ, **thì** có case mọi event kể cả missed/unobservable, cùng manifest các episode bổ sung.
- [ ] **PB21-AC02** (FR03, FR04): **Khi** mở case ECOD/MAD/IF, **thì** đúng bằng chứng mô hình tương ứng; cluster chỉ xuất nếu có artifact thực.
- [ ] **PB21-AC03** (FR04, FR05): **Khi** đối chiếu bảng report với metric và contributions, **thì** số đếm/score/tau khớp artifact, không dùng mask khác để tuyên bố cải thiện.
- [ ] **PB21-AC04** (FR05, FR06): **Khi** test cho kết quả ML kém MAD hoặc nhiều episode ngoài báo cáo, **thì** report vẫn hiện kết quả và giới hạn, không đổi mô hình chính hoặc gọi mọi episode là lỗi thật.

## Checklist triển khai

- [ ] Tạo `explain.py` và `report --run-id ...`; ít nhất một case cho từng sự cố test, kể cả bỏ sót.
- [ ] Lấy thêm episode ngoài báo cáo có score cao và mẫu ngẫu nhiên seed cố định; ghi tiêu chí chọn, tránh chỉ chọn ví dụ đẹp.
- [ ] Mỗi case gồm cảm biến, score/tau, alarm thật, sự cố, chất lượng và trạng thái cụm nếu đã làm PB17. ECOD hiển thị top 5 feature của nhánh thắng, gộp theo sensor và có phân vị train; MAD hiển thị feature đạt max; IF dùng sensor timeline/ablation.
- [ ] Tổng hợp X0–X7 theo phạm vi thực hiện; trả lời ML có cải thiện MAD không, W nào hữu ích, phát hiện sự cố nào, delay và đợt ngoài báo cáo/ngày bao nhiêu.

## Rủi ro và quyết định cần ghi nhận

- Chỉ chọn ví dụ đẹp dẫn tới kết luận thiên lệch: lưu danh sách case có quy tắc.
- Contribution theo feature tương quan dễ bị hiểu như nhiều nguyên nhân: nhóm theo sensor và tránh suy nhân quả.

## Bằng chứng để đóng PB

- [ ] Cung cấp report, case selection manifest, links tới dữ liệu gốc của hình/bảng và đối chiếu số liệu.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
