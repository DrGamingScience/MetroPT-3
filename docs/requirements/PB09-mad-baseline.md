# PB09 Baseline MAD

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | S — tương đối, chưa quy đổi ngày |
| Mốc | M2 |
| Branch | `feat/pb09-mad-baseline` |
| Phụ thuộc | [PB08](PB08-train-preprocessing.md) |
| Nguồn | Backlog PB09; pipeline chương 7 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người đánh giá cần baseline đơn giản để biết mô hình học máy có cải thiện so với độ lệch từng feature hay không.

## Phạm vi và ranh giới

Fit, score, lưu/nạp và giải thích MAD trên feature liên tục; threshold được hiệu chỉnh bên ngoài model.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Ma trận train reference sau PB08 | Feature liên tục hữu hạn, schema đã khóa. |
| Đầu ra | MAD model artifact | Median, MAD, floor, feature_names, schema/version. |
| Bàn giao | Score và feature đạt max | PB10 phát alarm; PB21 giải thích bằng giá trị hiện tại và median. |

## Yêu cầu chức năng

- **PB09-FR01:** Fit m_j=median(train_j), a_j=median(abs(train_j-m_j)); denominator s_j=max(a_j,epsilon_j) chỉ từ train.
- **PB09-FR02:** epsilon_j=max(1e-6,0.01×(P99-P1)); nếu P99-P1=0 ở cột không hằng thì dùng 0.01×(max-min) thay khoảng phân vị, vẫn áp sàn tuyệt đối.
- **PB09-FR03:** Score(x)=max_j abs(x_j-m_j)/s_j; không nhân hệ số 1.4826 và không diễn giải là Gaussian z-score/xác suất hỏng.
- **PB09-FR04:** Lưu feature đạt score max, giá trị hiện tại, median và độ lệch; nếu hòa thì lưu toàn bộ hoặc quy tắc tie cố định có tài liệu.
- **PB09-FR05:** Kiểm tra fitted/schema/finite; save/load không đổi score. Model chỉ tạo score, không fit threshold hoặc dùng nhãn validation/test.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Mọi denominator dương và score hữu hạn với dữ liệu đầu vào hữu hạn trong miền tính toán hỗ trợ.
- Khi toàn bộ cột đã bị loại ở preprocessing, báo không thể fit thay vì score rỗng hoặc 0.

## Tiêu chí nghiệm thu

- [ ] **PB09-AC01** (FR01, FR02, FR03): **Khi** fixture có MAD=0 nhưng feature không hằng, **thì** denominator theo floor và score hữu hạn, khớp tính tay.
- [ ] **PB09-AC02** (FR02): **Khi** fixture P99-P1 bằng 0 nhưng max-min dương, **thì** dùng range fallback đúng và lưu floor thực tế.
- [ ] **PB09-AC03** (FR03, FR04): **Khi** hai feature có cùng độ lệch cực đại, **thì** score đúng và giải thích tuân quy tắc tie đã lưu.
- [ ] **PB09-AC04** (FR05): **Khi** lưu/nạp model hoặc thay dữ liệu tương lai, **thì** score trên input cố định giữ nguyên; gọi score trước fit bị từ chối.

## Checklist triển khai

- [ ] Triển khai `models/mad.py` với median, MAD và sàn theo train; score là max độ lệch chuẩn hóa.
- [ ] Sàn là `max(1e-6, 0.01 × (P99-P1))`; dùng range train khi khoảng phân vị bằng 0 ở cột không hằng. Không nhân hệ số 1.4826.
- [ ] Lưu trạng thái model, feature names/version và thông tin feature đạt max cho giải thích.

## Rủi ro và quyết định cần ghi nhận

- MAD=0 xuất hiện nhiều ở tín hiệu ổn định: công bố số cột dùng floor và để dành sensitivity có ghi config.
- Sai hệ số scale làm thang điểm khác đặc tả: test công thức trực tiếp.

## Bằng chứng để đóng PB

- [ ] Cung cấp phép tính tay, metadata median/MAD/floor và ví dụ feature giải thích cho một cửa sổ.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
