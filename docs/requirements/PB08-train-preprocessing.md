# PB08 Preprocessing chỉ fit trên train

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M2 |
| Branch | `feat/pb08-train-preprocessing` |
| Phụ thuộc | [PB07](PB07-causal-window-features.md) |
| Nguồn | Backlog PB08; pipeline chương 7 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người chạy các detector cần một hợp đồng feature cố định và các phép xử lý thiếu chỉ học từ train reference.

## Phạm vi và ranh giới

Chọn cột, kiểm tra schema và xử lý thiếu theo config. Giữ đơn vị gốc cho detector; scaler/PCA phục vụ Data Mining nằm ở PB17.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Feature F35 + schema + train_reference mask | Chỉ mốc hợp lệ và không giao sự cố được fit. |
| Đầu ra | preprocess.joblib; retained feature schema | Danh sách cột giữ/bỏ, giá trị hằng, thống kê train, imputer nếu bật. |
| Bàn giao | Ma trận train/validation đúng cột | Detector nhận cùng tên/thứ tự, số chiều và giá trị hữu hạn. |

## Yêu cầu chức năng

- **PB08-FR01:** Fit cột và thống kê chỉ trên train reference; từ chối train rỗng hoặc không còn feature sau lọc, báo rõ dataset/config liên quan.
- **PB08-FR02:** Loại cột hằng và hoàn toàn missing trên train; lưu tên/lý do/giá trị hằng. Khi cột hằng đổi ở dữ liệu mới, phát cờ chất lượng riêng, không thêm nó lại vào detector.
- **PB08-FR03:** Mặc định complete-case; nếu bật median imputer thì fit median train, giữ số mốc đã điền và xuất đối chiếu complete-case. Cột toàn missing không lấy median từ split khác.
- **PB08-FR04:** Transform validation/test dùng nguyên schema train; kiểm tra tên, thiếu/thừa cột, thứ tự và số chiều, không âm thầm sắp xếp hoặc lọc cột mới.
- **PB08-FR05:** Không scale benchmark MAD/IF/ECOD mặc định; trước model phải finite. Artifact có phiên bản, schema hash và save/load giữ nguyên trạng thái.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không đổi valid mask chỉ để làm metric tốt hơn; nếu bật impute phải ghi chính sách và comparison mask riêng.
- Thông báo lỗi phải xác định cột hoặc giá trị không hợp lệ; không đẩy NaN/inf tới model.

## Tiêu chí nghiệm thu

- [ ] **PB08-AC01** (FR01, FR02): **Khi** train có một cột hằng, một cột toàn thiếu và một cột biến thiên, **thì** chỉ giữ cột biến thiên, artifact ghi đúng lý do; dữ liệu mới đổi cột hằng có flag riêng.
- [ ] **PB08-AC02** (FR01, FR03): **Khi** thay phân phối validation/test, **thì** cột giữ/bỏ và median train không đổi.
- [ ] **PB08-AC03** (FR04, FR05): **Khi** đảo thứ tự/thiếu/thừa feature hoặc còn infinity, **thì** transform từ chối rõ lý do trước khi score.
- [ ] **PB08-AC04** (FR03, FR05): **Khi** save/load preprocessing đã fit và transform cùng dữ liệu, **thì** ma trận và schema tương đương trong dung sai; số mốc impute được công bố.

## Checklist triển khai

- [ ] Triển khai `preprocess.py`, tạo train reference hợp lệ trước khi fit.
- [ ] Loại cột hằng/hoàn toàn thiếu trên train; lưu danh sách, giá trị hằng và cờ chất lượng nếu chúng thay đổi về sau.
- [ ] Mặc định dùng complete-case. Nếu bật median imputer, fit train, ghi số mốc đã điền và đối chiếu complete-case.
- [ ] Giữ đơn vị gốc cho ba detector; kiểm tra finite, đúng tên và thứ tự cột. Nhánh scale cho PCA/K-Means tách riêng.

## Rủi ro và quyết định cần ghi nhận

- Lọc cột hằng theo từng split sẽ làm đổi model input: khóa danh sách tại fit.
- Impute có thể che thiếu quan sát: chất lượng/coverage gốc phải còn nguyên.

## Bằng chứng để đóng PB

- [ ] Đính kèm preprocessing artifact metadata, danh sách cột loại và kiểm tra fit-on-train/schema/save-load.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
