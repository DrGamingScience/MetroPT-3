# PB14 FrozenECOD đúng đặc tả

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M3 |
| Phụ thuộc | [PB12](PB12-baseline-workflow.md) |
| Nguồn | Backlog PB14; pipeline chương 9 và 15 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người đánh giá cần ECOD có phân phối tham chiếu cố định để score tương lai không thay đổi theo các mẫu cùng batch.

## Phạm vi và ranh giới

Triển khai ECOD-paper-frozen theo đặc tả gồm lõi số học, contract model và giải thích. PyOD là nhánh đối chiếu PB24, không thay implementation chính.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Ma trận train reference hữu hạn | n>=2, d>0, cột hằng đã loại, đúng feature schema. |
| Đầu ra | FrozenECOD artifact | Sorted reference từng cột, dấu skewness, n/d/epsilon, names/version. |
| Bàn giao | Score; winning branch; contributions | PB15 benchmark, PB18 freeze, PB21 nhóm theo cảm biến. |

## Yêu cầu chức năng

- **PB14-FR01:** Fit sorted reference S_j và dấu moment bậc ba train; moment âm chọn trái, bằng 0 hoặc dương chọn phải. Khóa n,d,epsilon=1/(n+1), reference và skewness sau fit.
- **PB14-FR02:** Tính pL=count(train<=x)/n và pR=count(train>=x)/n bằng searchsorted right/left; xử lý ties ở cả hai đuôi, không dùng 1-pL thay pR.
- **PB14-FR03:** Clip xác suất vào [epsilon,1], lấy -ln; tạo L/R/A và score=max(sum(L),sum(R),sum(A)), không sum(max từng feature).
- **PB14-FR04:** Nhánh thắng hòa chọn trái, phải, tự động theo thứ tự cố định; contributions lấy đúng nhánh thắng, tổng bằng score và giữ feature names để gộp sensor.
- **PB14-FR05:** Kiểm tra fitted, n/d, cột/order/finite; save/load/version và float64; batch mặc định 4096. Nếu chuẩn hóa dương để tránh tràn moment, fit quy tắc riêng trên train và lưu artifact.
- **PB14-FR06:** Chấm validation/test không nối dữ liệu mới vào reference và không cập nhật skewness/epsilon. Batch chunking, thứ tự batch hoặc các mẫu khác cùng batch không được đổi score của một mẫu.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Score ngoài miền train hữu hạn nhờ probability floor; không có log(0).
- Chi phí sort/searchsorted được đo thực tế; không sao chép tuyên bố độ phức tạp của implementation khác.
- Test xác nhận reference/skewness không đổi trước/sau score bằng so sánh mảng; không tính checksum cho mỗi batch hoặc lần score.

## Tiêu chí nghiệm thu

- [ ] **PB14-AC01** (FR01, FR02): **Khi** train 1 chiều [1,1,2], x=1 và x=2, **thì** pL/pR lần lượt (2/3,1) và (1,1/3).
- [ ] **PB14-AC02** (FR02, FR03): **Khi** x nhỏ hơn min hoặc lớn hơn max train, **thì** score hữu hạn, xác suất được chặn đúng epsilon.
- [ ] **PB14-AC03** (FR03, FR04): **Khi** L=(5,0.1), R=(0.1,5), A=L, **thì** score=5.1 thay vì 10; contributions cộng đúng và tie có thứ tự cố định.
- [ ] **PB14-AC04** (FR05, FR06): **Khi** score một mẫu riêng, trong batch, chia/hoán vị batch và restore thứ tự, **thì** score khớp trong 1e-12, reference/skewness không đổi khi so sánh trạng thái trong test.
- [ ] **PB14-AC05** (FR01, FR05): **Khi** input chưa fit, cột hằng, schema sai hoặc save/load, **thì** input lỗi bị từ chối; save/load input hợp lệ cho score tương đương.

## Rủi ro và quyết định cần ghi nhận

- Thay bằng implementation ECOD khác có thể đổi cả aggregation và batch behavior: khóa tên paper_frozen_v1.
- Moment bậc ba có thể overflow: chỉ chuẩn hóa dương dựa trên train và không đổi thứ hạng/nhánh vô ý.

## Kết quả cần xem

- [ ] Cung cấp toàn bộ test số học ties/tails/aggregation/contribution/batch/state/save-load trước khi chạy tìm kiếm.
