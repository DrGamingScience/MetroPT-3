# PB15 So sánh mô hình và cửa sổ

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M3 |
| Phụ thuộc | [PB13](PB13-isolation-forest.md), [PB14](PB14-frozen-ecod.md) |
| Nguồn | Backlog PB15; pipeline chương 10, 12–13 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Cần bảng validation so sánh công bằng giữa mô hình/cửa sổ. Một vòng lặp cấu hình nhỏ là đủ; dùng lại score trong lần chạy khi chỉ thay ngưỡng.

## Phạm vi và ranh giới

X1/X2 bằng một script; ghi danh sách cấu hình và seed X6, X7 tùy chọn trên validation. PB18 thực hiện lựa chọn/freeze cuối; PB16 bổ sung X3–X5.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Ba model; feature builder; preprocessing; danh sách cấu hình trong Python/YAML | Train/validation hợp lệ, version dữ liệu và code rõ. |
| Đầu ra | Bảng cấu hình/kết quả; score trong bộ nhớ hoặc file chỉ định; common mask | Mỗi dòng có config_id, model/feature_set/W/seed/tham số, số mốc và coverage. |
| Đầu ra | Bảng validation X1/X2 | Có coverage riêng và chung; F7 baseline tức thời, grid F35. |

## Yêu cầu chức năng

- **PB15-FR01:** X1 dùng MAD/IF/FrozenECOD, F35 W=5; X2 dùng W=1/5/15 và F7 là 7 analog mới nhất tại t có tuổi tối đa 2×delta0, cùng split/segment và warm-up chung.
- **PB15-FR02:** Với mỗi bảng, giao valid timestamps của các cấu hình tham gia; cùng nguồn cảm biến/schema trong phép so model cùng feature_set. Không ép các W hoặc F7/F35 có tên/số feature giống nhau; công bố rõ khác biệt.
- **PB15-FR03:** Fit preprocessing/model riêng từng cấu hình từ train reference; lưu config_id, n_valid, positive_rate, số mốc loại và coverage riêng/chung. Common mask là giao timestamp, không cần hash/mask_id riêng. Không so AP khác tập mốc như cùng tập đánh giá.
- **PB15-FR04:** Lưới F35 chính tối đa 24 lượt fit: 3 W × (1 MAD + 1 ECOD + 6 IF); F7 tính riêng. Vòng lặp cấu hình và bảng kết quả đủ; không yêu cầu registry engine hoặc cache theo data/config/schema/model/code hashes.
- **PB15-FR05:** Trong một lần chạy, fit/score mỗi cấu hình một lần, dùng lại score để quét q/merge. Đổi W/feature/model phải tính lại phần liên quan. Mặc định không tái dùng cache xuyên run; score đã lưu chỉ đọc khi chọn rõ đường dẫn và config tương ứng.
- **PB15-FR06:** Ghi trước kế hoạch X6 seed 42/7/2026 cho IF và những cấu hình sẽ test trong config/bảng thí nghiệm. X7 q/merge là phân tích độ nhạy validation tùy chọn, không cần một hệ thống đăng ký.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Mỗi run lỗi có trạng thái/lý do và không được đưa vào bảng như một run thành công.
- Timing cùng điều kiện; bảng kết quả chỉ rõ cấu hình và dữ liệu. Không tự dò cache giữa các run.

## Tiêu chí nghiệm thu

- [ ] **PB15-AC01:** **Khi** chạy X1 rồi X2, **thì** có ba model/W/F7 theo kế hoạch; F7 stale bị loại và không lấy tương lai.
- [ ] **PB15-AC02:** **Khi** các cấu hình có valid mask khác nhau, **thì** bảng chính dùng giao timestamp, có số mốc/coverage riêng và chung; không cần file/hash cho mask.
- [ ] **PB15-AC03:** **Khi** quét nhiều q trên score của một cấu hình trong cùng lần chạy, **thì** không fit/score lại model; metric và alarm được tính lại đúng q.
- [ ] **PB15-AC04:** **Khi** đổi W hoặc model, **thì** chạy với feature/model tương ứng, không lấy score cấu hình trước. Không có yêu cầu tự động resume/cache giữa các run.
- [ ] **PB15-AC05:** **Trước test**, danh sách cấu hình/seed được ghi rõ; không có lựa chọn dựa trên kết quả test.

## Rủi ro và quyết định cần ghi nhận

- Yêu cầu 'cùng cột' bị áp nhầm cho so F7/F35 hoặc các W: chỉ giữ cùng schema khi đang so model trên cùng feature set.
- Khi cần đọc lại score, chọn rõ bộ kết quả/config và đối chiếu metadata; không xây cache tự động trước khi có nút thắt đã đo.

## Kết quả cần xem

- [ ] Cung cấp bảng validation X1/X2, danh sách cấu hình và coverage. Kiểm tra không fit lại khi quét q trong cùng lần chạy; không cần log cache hit/miss.
