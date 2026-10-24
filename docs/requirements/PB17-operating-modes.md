# PB17 PCA và K-Means cho chế độ vận hành

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P1 |
| Mốc | M3 — Data Mining P1 |
| Phụ thuộc | [PB06](PB06-train-eda.md), [PB08](PB08-train-preprocessing.md) |
| Nguồn | Backlog PB17; pipeline chương 5 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người giải thích cảnh báo cần nhìn thấy các chế độ vận hành và trạng thái hiếm mà không nhầm cụm với nguyên nhân hỏng.

## Phạm vi và ranh giới

Phân tích gọn trong notebook: PCA giúp nhìn cấu trúc dữ liệu, K-Means gom cửa sổ có tín hiệu giống nhau để khảo sát trạng thái hiếm/cảnh báo. Fit trên train reference; dùng grid k=2..6 đã giới hạn. Không xây hệ thống gán nhãn chế độ hoặc tầng pipeline riêng. PCA cho detector thuộc PB26.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Train-reference features; retained schema; EDA | Không dùng test để chọn scaler, PCA hoặc k. |
| Đầu ra | Scaler/PCA/K-Means artifacts; selection note | Feature names, tập train, seed, variance và lựa chọn k trong notebook. |
| Đầu ra | Projected/cluster tables và biểu đồ | PC1/PC2, cluster_id, số mốc, median sensor, thời lượng/alarm fraction khi có. |

## Yêu cầu chức năng

- **PB17-FR01:** Fit StandardScaler và PCA riêng từ train reference; lưu transformer và explained_variance_ratio_, vẽ PC1/PC2 nhưng không khẳng định 2 PC giữ đủ thông tin.
- **PB17-FR02:** Khảo sát K-Means k=2..6 với n_init=20/seed=42 trên dữ liệu đã scale; có thể MiniBatchKMeans nếu cấu hình và lý do được lưu.
- **PB17-FR03:** Silhouette tính trên sample tối đa 5000 cửa sổ train lấy theo thời gian, ghi seed/cách lấy sample; chọn k dựa cả silhouette, kích thước, tâm và tần suất chuyển cụm.
- **PB17-FR04:** Chốt k và ý nghĩa mô tả từ train trước test; validation/test chỉ transform/predict bằng artifacts cố định, không refit.
- **PB17-FR05:** Gán tên A/B/C... ban đầu, lưu cluster_id/số mốc/median sensor/thời lượng theo split; bổ sung alarm fraction khi có score mà không dùng nó để chọn lại k theo test.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Sample và seed tái lập; dữ liệu nhỏ không đủ k/silhouette phải có reason thay vì crash hoặc số giả.
- Không nối chuyển cụm qua gap/invalid; thời lượng dùng mốc hợp lệ.

## Tiêu chí nghiệm thu

- [ ] **PB17-AC01** (FR01): **Khi** fit PCA trên train và sinh biểu đồ, **thì** có variance ratios, schema và transformer; số PC giữ thông tin được công bố đúng.
- [ ] **PB17-AC02** (FR02, FR03): **Khi** chạy k grid hai lần cùng train/seed/sample, **thì** có bảng lựa chọn với chỉ số, kích thước/tâm và cách lấy mẫu và kết quả nhất quán.
- [ ] **PB17-AC03** (FR04): **Khi** thay sensor values validation/test, **thì** scaler/PCA/tâm cụm và k đã chọn không đổi.
- [ ] **PB17-AC04** (FR05): **Khi** ghép cluster với alarm sau benchmark, **thì** tỷ lệ theo đúng split/mask; không đổi cluster fit và không gọi cluster là lỗi cơ học.

## Rủi ro và quyết định cần ghi nhận

- Train không bao phủ mọi chế độ hợp lệ: cụm hiếm/xa tâm là tín hiệu cần kiểm tra, không nhãn hỏng.
- Chọn k chỉ từ silhouette dễ bỏ qua cụm quá nhỏ: ghi đầy đủ các căn cứ.

## Kết quả cần xem

- [ ] Cung cấp notebook với bảng chọn k, một hình PCA và mô tả nhóm tín hiệu; lưu transformer nếu dùng lại trên validation/test. Không cần sample manifest hoặc report riêng.
