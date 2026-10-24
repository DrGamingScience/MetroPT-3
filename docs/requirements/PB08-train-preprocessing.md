# PB08 Preprocessing chỉ fit trên train

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M2 |
| Phụ thuộc | [PB07](PB07-causal-window-features.md) |
| Nguồn | Backlog PB08; pipeline chương 7 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người chạy các detector cần một hợp đồng feature cố định và các phép xử lý thiếu chỉ học từ train reference.

## Phạm vi và ranh giới

Chọn cột, kiểm tra input hữu hạn và dùng complete-case mặc định. Median imputer chỉ bổ sung nếu dữ liệu thực tế cần, có kết quả đối chiếu. Giữ đơn vị gốc cho detector; scaler/PCA phục vụ Data Mining nằm ở PB17.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Feature F35 + schema + train_reference mask | Chỉ mốc hợp lệ và không giao sự cố được fit. |
| Đầu ra | preprocess.joblib; retained feature schema | Danh sách cột giữ/bỏ, giá trị hằng, thống kê train, imputer nếu bật. |
| Bàn giao | Ma trận train/validation đúng cột | Detector nhận cùng tên/thứ tự, số chiều và giá trị hữu hạn. |

## Yêu cầu chức năng

- **PB08-FR01:** Fit cột và thống kê chỉ trên train reference; từ chối train rỗng hoặc không còn feature sau lọc, báo rõ dataset/config liên quan.
- **PB08-FR02:** Loại cột hằng và hoàn toàn missing trên train; ghi tên/lý do/giá trị hằng cùng preprocessing. Nếu chúng đổi ở dữ liệu mới thì ghi nhận trong phân tích chất lượng khi cần, không thêm lại vào detector hoặc xây hệ thống drift monitoring.
- **PB08-FR03:** Mặc định complete-case. Chưa triển khai nhiều chế độ impute. Nếu quan sát thực tế đòi hỏi median imputer, fit chỉ trên train, ghi số mốc điền và đối chiếu với complete-case; cột toàn missing không lấy median split khác.
- **PB08-FR04:** Transform validation/test dùng nguyên schema train; kiểm tra tên, thiếu/thừa cột, thứ tự và số chiều, không âm thầm sắp xếp hoặc lọc cột mới.
- **PB08-FR05:** Không scale benchmark MAD/IF/ECOD mặc định; trước model phải finite. Lưu cột/thứ tự và thống kê cùng preprocessing; save/load giữ nguyên trạng thái, không cần schema hash riêng.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không đổi valid mask chỉ để làm metric tốt hơn; nếu bật impute phải ghi chính sách và comparison mask riêng.
- Thông báo lỗi phải xác định cột hoặc giá trị không hợp lệ; không đẩy NaN/inf tới model.

## Tiêu chí nghiệm thu

- [ ] **PB08-AC01:** **Khi** train có cột hằng, toàn thiếu và biến thiên, **thì** chỉ giữ cột biến thiên, ghi lý do; danh sách cột không tự đổi trên validation/test.
- [ ] **PB08-AC02:** **Khi** thay phân phối validation/test, **thì** cột giữ/bỏ và mọi thống kê train không đổi; kiểm tra median nếu có imputer.
- [ ] **PB08-AC03** (FR04, FR05): **Khi** đảo thứ tự/thiếu/thừa feature hoặc còn infinity, **thì** transform từ chối rõ lý do trước khi score.
- [ ] **PB08-AC04:** **Khi** save/load preprocessing và transform cùng input, **thì** ma trận/cột tương đương; nếu dùng imputer thì công bố số mốc điền.

## Rủi ro và quyết định cần ghi nhận

- Lọc cột hằng theo từng split sẽ làm đổi model input: khóa danh sách tại fit.
- Impute có thể che thiếu quan sát: chất lượng/coverage gốc phải còn nguyên.

## Kết quả cần xem

- [ ] Đính kèm preprocessing artifact metadata, danh sách cột loại và kiểm tra fit-on-train/schema/save-load.
