# PB17 PCA và K-Means cho chế độ vận hành

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P1 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M3 — Data Mining P1 |
| Branch | `feat/pb17-operating-modes` |
| Phụ thuộc | [PB06](PB06-train-eda.md), [PB08](PB08-train-preprocessing.md) |
| Nguồn | Backlog PB17; pipeline chương 5 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người giải thích cảnh báo cần nhìn thấy các chế độ vận hành và trạng thái hiếm mà không nhầm cụm với nguyên nhân hỏng.

## Phạm vi và ranh giới

Nhánh StandardScaler/PCA/K-Means phục vụ khám phá, fit trên train reference; PCA cho detector thuộc PB26.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Train-reference features; retained schema; EDA | Không dùng test để chọn scaler, PCA hoặc k. |
| Đầu ra | Scaler/PCA/K-Means artifacts; selection note | Feature names, train hash, seed, variance và lựa chọn k. |
| Đầu ra | Projected/cluster tables và biểu đồ | PC1/PC2, cluster_id, số mốc, median sensor, thời lượng/alarm fraction khi có. |

## Yêu cầu chức năng

- **PB17-FR01:** Fit StandardScaler và PCA riêng từ train reference; lưu transformer và explained_variance_ratio_, vẽ PC1/PC2 nhưng không khẳng định 2 PC giữ đủ thông tin.
- **PB17-FR02:** Khảo sát K-Means k=2..6 với n_init=20/seed=42 trên dữ liệu đã scale; có thể MiniBatchKMeans nếu cấu hình và lý do được lưu.
- **PB17-FR03:** Silhouette tính trên sample tối đa 5000 cửa sổ train lấy theo thời gian, lưu sample; chọn k dựa cả silhouette, kích thước, tâm và tần suất chuyển cụm.
- **PB17-FR04:** Chốt k và ý nghĩa mô tả từ train trước test; validation/test chỉ transform/predict bằng artifacts cố định, không refit.
- **PB17-FR05:** Gán tên A/B/C... ban đầu, lưu cluster_id/số mốc/median sensor/thời lượng theo split; bổ sung alarm fraction khi có score mà không dùng nó để chọn lại k theo test.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Sample và seed tái lập; dữ liệu nhỏ không đủ k/silhouette phải có reason thay vì crash hoặc số giả.
- Không nối chuyển cụm qua gap/invalid; thời lượng dùng mốc hợp lệ.

## Tiêu chí nghiệm thu

- [ ] **PB17-AC01** (FR01): **Khi** fit PCA trên train và sinh biểu đồ, **thì** có variance ratios, schema và transformer; số PC giữ thông tin được công bố đúng.
- [ ] **PB17-AC02** (FR02, FR03): **Khi** chạy k grid hai lần cùng train/seed/sample, **thì** có bảng lựa chọn với chỉ số, kích thước/tâm và sample list nhất quán.
- [ ] **PB17-AC03** (FR04): **Khi** thay sensor values validation/test, **thì** scaler/PCA/tâm cụm và k đã chọn không đổi.
- [ ] **PB17-AC04** (FR05): **Khi** ghép cluster với alarm sau benchmark, **thì** tỷ lệ theo đúng split/mask; không đổi cluster fit và không gọi cluster là lỗi cơ học.

## Checklist triển khai

- [ ] Fit nhánh StandardScaler/PCA trên train reference; vẽ PC1/PC2 và explained variance, lưu toàn bộ transformer.
- [ ] K-Means k=2..6, n_init=20, seed=42; silhouette trên tối đa 5000 mốc train lấy theo thời gian, kèm kích thước/tâm/tần suất chuyển cụm.
- [ ] Chốt k từ train và ghi lý do; dùng transformer/tâm cụm cố định khi chiếu validation/test. Ban đầu đặt tên trạng thái A/B/C.

## Rủi ro và quyết định cần ghi nhận

- Train không bao phủ mọi chế độ hợp lệ: cụm hiếm/xa tâm là tín hiệu cần kiểm tra, không nhãn hỏng.
- Chọn k chỉ từ silhouette dễ bỏ qua cụm quá nhỏ: ghi đầy đủ các căn cứ.

## Bằng chứng để đóng PB

- [ ] Cung cấp train-fit artifacts, sample manifest, bảng chọn k và ví dụ projection dùng model cố định.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
