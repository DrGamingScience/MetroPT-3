# PB06 EDA trên train

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M1 |
| Phụ thuộc | [PB05](PB05-temporal-splits.md) |
| Nguồn | Backlog PB06; pipeline chương 5 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người thiết kế thí nghiệm cần hiểu phân phối và trạng thái hiếm của train trước khi diễn giải score cao hoặc chọn giả thuyết mở rộng.

## Phạm vi và ranh giới

EDA có thể tái lập trên train. PCA/K-Means nằm ở PB17; EDA không tự biến tương quan thành quy tắc loại feature.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Cleaned train và quality/split masks | Không dùng phân phối validation/test để đề xuất feature chính. |
| Đầu ra | Báo cáo EDA và biểu đồ | Histogram, boxplot, timeline, digital frequency, Pearson/Spearman. |
| Đầu ra | Ghi chú lấy mẫu và giả thuyết ngay trong notebook/report | Seed, cách lấy mẫu, số dòng và độ phân giải timeline. |

## Yêu cầu chức năng

- **PB06-FR01:** Tạo thống kê/biểu đồ cho 7 analog và tần suất từng digital, chỉ rõ dữ liệu bị loại vì chất lượng; mọi trục có đơn vị và khoảng thời gian.
- **PB06-FR02:** Vẽ timeline mức ngày và các đoạn chi tiết; nếu downsample hoặc aggregate để vẽ thì ghi rõ quy tắc, không dùng bảng đã aggregate làm raw cho feature.
- **PB06-FR03:** Tính Pearson và Spearman trên train; trình bày tương quan cùng giới hạn, chưa tự loại cột hoặc diễn giải quan hệ nhân quả.
- **PB06-FR04:** Đối chiếu Motor_current/áp suất với COMP/DV_eletric/Towers; ghi tần suất trạng thái hiếm và điều chưa có bằng chứng về ý nghĩa vận hành.
- **PB06-FR05:** Lấy mẫu theo ngày với seed cố định khi biểu đồ lớn; lưu code/quy tắc và số dòng trong notebook. Có thể tính lại cùng sample, không bắt buộc lưu danh sách raw_row_id ra file.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Ghi dữ liệu/split và số dòng dùng ở đầu notebook/report; không lặp metadata ở mỗi hình.
- Không đặt tên cơ học cho COMP=1 chỉ từ tên cột hoặc suy đoán.

## Tiêu chí nghiệm thu

- [ ] **PB06-AC01** (FR01, FR02): **Khi** sinh báo cáo từ train đã audit, **thì** đủ nhóm hình, có đơn vị/thời gian và giải thích xử lý chất lượng/aggregate.
- [ ] **PB06-AC02** (FR03, FR04): **Khi** có cặp tương quan cao hoặc trạng thái hiếm, **thì** ghi bằng chứng và giả thuyết, không âm thầm sửa feature/schema.
- [ ] **PB06-AC03:** **Khi** chạy lại notebook cùng dữ liệu/seed/quy tắc, **thì** sample và thống kê nhất quán; kiểm tra trực tiếp, không cần file sample manifest.
- [ ] **PB06-AC04** (FR01, FR05): **Khi** thay dữ liệu cảm biến test, **thì** thống kê, sample và nội dung EDA train không đổi.

## Rủi ro và quyết định cần ghi nhận

- Đồ thị lấy mẫu lệch theo một ngày gây bỏ sót trạng thái: lưu sampling theo ngày.
- Diễn giải COMP sai làm lệch case study: giữ tên trạng thái theo giá trị cho tới khi có bằng chứng.

## Kết quả cần xem

- [ ] Cung cấp notebook/report có code lấy mẫu, seed và nhận xét về train; không cần sample manifest hay test ảnh.
