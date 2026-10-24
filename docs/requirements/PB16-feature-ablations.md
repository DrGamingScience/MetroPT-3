# PB16 F51, F55 và ablation nhóm cảm biến

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P1 |
| Quy mô | L — tương đối, chưa quy đổi ngày |
| Mốc | M3 — mở rộng P1 |
| Branch | `feat/pb16-feature-ablations` |
| Phụ thuộc | [PB15](PB15-experiment-runner.md) |
| Nguồn | Backlog PB16; pipeline chương 6, 13 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người phân tích cần biết digital, chênh lệch áp suất và từng nhóm cảm biến có đóng góp gì ngoài F35.

## Phạm vi và ranh giới

X3/F51, X4/F55 và X5 ablation trên IF/ECOD. MAD với feature rời rạc là biến thể khác, chưa nằm trong PB này.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Runner PB15; schema analog/digital đã audit | Digital phải được xác nhận nhị phân; kế thừa causal quality policy. |
| Đầu ra | F51/F55 schemas; ablation configs | Dimension trước lọc, nguồn gốc feature và nhóm nguồn. |
| Đầu ra | Validation results X3–X5 | Fit/preprocess/tau riêng, common mask cho mỗi bảng; đăng ký PB18 nếu test. |

## Yêu cầu chức năng

- **PB16-FR01:** F51 = F35 + 8 digital×(tỷ lệ mẫu bằng 1,số chuyển trạng thái) = 51 chiều trước lọc; tỷ lệ theo số quan sát hợp lệ, không gọi là tỷ lệ thời lượng chính xác.
- **PB16-FR02:** Transition chỉ đếm cặp mẫu quan sát kề nhau khác trạng thái cùng nằm trong cửa sổ và không qua gap; không lấy mẫu trước biên để tăng count.
- **PB16-FR03:** F55 thêm mean/std của TP2−TP3 và TP3−Reservoirs; tính chênh lệch tại cùng timestamp trước khi tổng hợp, không lấy hiệu của thống kê khác.
- **PB16-FR04:** X5 bỏ lần lượt áp suất/nhiệt độ/dòng điện; map mọi feature dẫn xuất tới nhóm sensor nguồn, feature chứa sensor bị bỏ cũng phải bị loại.
- **PB16-FR05:** Mỗi biến thể fit lại preprocessing/model trên train, chọn tau bằng validation reference của chính nó, so trên common mask và ghi feature_set/dimension trước/sau lọc.
- **PB16-FR06:** Biến thể dùng trong test xác nhận phải có registry/freeze PB18 trước PB19; biến thể tạo sau khi xem test được ghi exploratory.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không hardcode 51/55 sau lọc cột hằng; báo cả số chiều gốc và thực giữ.
- Khi thêm digital, quality mask phải kiểm tra đúng các cột cần thiết và báo phần độ phủ bị mất.

## Tiêu chí nghiệm thu

- [ ] **PB16-AC01** (FR01, FR02): **Khi** fixture digital 0,0,1,1,0 trong cửa sổ, **thì** on fraction=2/5, transitions=2; mẫu ngoài cửa sổ/gap không cộng thêm.
- [ ] **PB16-AC02** (FR03): **Khi** fixture có hai chuỗi áp suất timestamp khớp, **thì** mean/std hai chênh lệch khớp phép tính từ từng dòng, dimension gốc F55=55.
- [ ] **PB16-AC03** (FR04): **Khi** ablation nhóm áp suất, **thì** loại mọi thống kê pressure và cả các chênh lệch liên quan; không còn feature lén dùng sensor đã bỏ.
- [ ] **PB16-AC04** (FR05, FR06): **Khi** so F35/F51/F55 và ablation, **thì** mỗi biến thể có model/tau riêng, common mask rõ và đăng ký trước test nếu dùng xác nhận.

## Checklist triển khai

- [ ] X3: F51 = F35 + 8 digital × tỷ lệ bằng 1/số chuyển trạng thái, xác nhận domain nhị phân trước.
- [ ] X4: F55 thêm mean/std của TP2−TP3 và TP3−Reservoirs, tính chênh lệch tại từng timestamp rồi tổng hợp.
- [ ] X5: bỏ lần lượt nhóm áp suất, nhiệt độ, dòng điện; ghi rõ các feature dẫn xuất bị loại cùng nhóm nguồn.
- [ ] Chạy IF/ECOD, mỗi biến thể fit lại preprocessing/model trên train và hiệu chỉnh ngưỡng riêng trên validation; không dùng chung tau khác thang score.

## Rủi ro và quyết định cần ghi nhận

- Digital hiếm làm ECOD tăng score mạnh: phân tích thay vì mặc định feature mới tốt hơn.
- Chỉ bỏ cột có tên sensor mà giữ feature chênh lệch làm ablation sai: dùng lineage nhóm nguồn.

## Bằng chứng để đóng PB

- [ ] Cung cấp feature/group schemas, test transition/chênh lệch và bảng X3–X5 kèm masks/tau theo biến thể.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
