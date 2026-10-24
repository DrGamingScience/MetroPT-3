# PB06 EDA trên train

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | S — tương đối, chưa quy đổi ngày |
| Mốc | M1 |
| Branch | `feat/pb06-train-eda` |
| Phụ thuộc | [PB05](PB05-temporal-splits.md) |
| Nguồn | Backlog PB06; pipeline chương 5 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người thiết kế thí nghiệm cần hiểu phân phối và trạng thái hiếm của train trước khi diễn giải score cao hoặc chọn giả thuyết mở rộng.

## Phạm vi và ranh giới

EDA có thể tái lập trên train. PCA/K-Means nằm ở PB17; EDA không tự biến tương quan thành quy tắc loại feature.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Cleaned train và quality/split masks | Không dùng phân phối validation/test để đề xuất feature chính. |
| Đầu ra | Báo cáo EDA và biểu đồ | Histogram, boxplot, timeline, digital frequency, Pearson/Spearman. |
| Đầu ra | Sample manifest; ghi chú giả thuyết | Seed, raw_row_id lấy mẫu, độ phân giải timeline và bằng chứng. |

## Yêu cầu chức năng

- **PB06-FR01:** Tạo thống kê/biểu đồ cho 7 analog và tần suất từng digital, chỉ rõ dữ liệu bị loại vì chất lượng; mọi trục có đơn vị và khoảng thời gian.
- **PB06-FR02:** Vẽ timeline mức ngày và các đoạn chi tiết; nếu downsample hoặc aggregate để vẽ thì ghi rõ quy tắc, không dùng bảng đã aggregate làm raw cho feature.
- **PB06-FR03:** Tính Pearson và Spearman trên train; trình bày tương quan cùng giới hạn, chưa tự loại cột hoặc diễn giải quan hệ nhân quả.
- **PB06-FR04:** Đối chiếu Motor_current/áp suất với COMP/DV_eletric/Towers; ghi tần suất trạng thái hiếm và điều chưa có bằng chứng về ý nghĩa vận hành.
- **PB06-FR05:** Lấy mẫu cố định theo ngày cho biểu đồ lớn, lưu seed và danh sách raw_row_id; các lần chạy lại dùng cùng sample.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Gắn dataset/split/config/run reference cho báo cáo; ghi rõ số dòng dùng.
- Không đặt tên cơ học cho COMP=1 chỉ từ tên cột hoặc suy đoán.

## Tiêu chí nghiệm thu

- [ ] **PB06-AC01** (FR01, FR02): **Khi** sinh báo cáo từ train đã audit, **thì** đủ nhóm hình, có đơn vị/thời gian và giải thích xử lý chất lượng/aggregate.
- [ ] **PB06-AC02** (FR03, FR04): **Khi** có cặp tương quan cao hoặc trạng thái hiếm, **thì** ghi bằng chứng và giả thuyết, không âm thầm sửa feature/schema.
- [ ] **PB06-AC03** (FR05): **Khi** chạy lại cùng seed và dữ liệu, **thì** danh sách sample và số dòng trong từng hình trùng nhau.
- [ ] **PB06-AC04** (FR01, FR05): **Khi** thay dữ liệu cảm biến test, **thì** thống kê, sample và nội dung EDA train không đổi.

## Checklist triển khai

- [ ] Tạo histogram, boxplot, timeline analog, tần suất digital, Pearson và Spearman trên train.
- [ ] Đối chiếu Motor_current và áp suất với COMP, DV_eletric, Towers; ghi điều có bằng chứng và điều chưa xác minh.
- [ ] Khi lấy mẫu, phân bố theo ngày, cố định seed và lưu danh sách dòng; không tự loại feature do tương quan cao.

## Rủi ro và quyết định cần ghi nhận

- Đồ thị lấy mẫu lệch theo một ngày gây bỏ sót trạng thái: lưu sampling theo ngày.
- Diễn giải COMP sai làm lệch case study: giữ tên trạng thái theo giá trị cho tới khi có bằng chứng.

## Bằng chứng để đóng PB

- [ ] Đính kèm report, sample manifest và nhận xét có nguồn về train; không cần test ảnh phản chiếu chi tiết cách vẽ.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
