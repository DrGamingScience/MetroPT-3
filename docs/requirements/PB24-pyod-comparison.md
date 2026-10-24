# PB24 Đối chiếu PyOD và FrozenECOD

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P2 — tùy chọn |
| Mốc | P2 — đối chiếu thuật toán |
| Phụ thuộc | [PB14](PB14-frozen-ecod.md); [PB15](PB15-experiment-runner.md) nếu đo metric validation |
| Nguồn | Backlog PB24; pipeline chương 9, 13 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

**Phạm vi hiện tại: Deferred.** Chỉ triển khai khi có câu hỏi hoặc nhu cầu cụ thể; các yêu cầu dưới đây áp dụng nếu mở lại mục này.

## Mục tiêu và nhu cầu

Người nghiên cứu cần hiểu khác biệt giữa FrozenECOD và một phiên bản PyOD cụ thể, đặc biệt aggregation và batch behavior.

## Phạm vi và ranh giới

Thí nghiệm đối chiếu có version pin; không thay detector chính hoặc khẳng định mọi phiên bản PyOD đều cùng hành vi.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | FrozenECOD PB14; PyOD version/source snapshot | Ghi phiên bản và link/tag/commit mã được đối chiếu, preprocess/schema chung. |
| Đầu ra | Comparison configs/results | Score, batch sensitivity, aggregation example và trạng thái reference. |
| Đầu ra | Báo cáo khác biệt có bằng chứng | Phân biệt lựa chọn frozen adaptation và implementation được kiểm tra. |

## Yêu cầu chức năng

- **PB24-FR01:** Khóa phiên bản PyOD và ghi link/tag/commit mã ECOD được đọc; ghi phụ thuộc/môi trường riêng nếu cần, tránh thay lockfile chính mà không chủ đích.
- **PB24-FR02:** Kiểm tra mã phiên bản đó và ghi nó có tái ước lượng ECDF/skewness theo query batch không, aggregation là max-of-sums hay sum-of-feature-max; dùng ví dụ số học xác nhận.
- **PB24-FR03:** Trên cùng train/schema/query, chấm một mẫu riêng/trong batch/batch có thêm điểm cực đoan/hoán vị batch, lưu score differences và mọi trạng thái thay đổi.
- **PB24-FR04:** So bằng input và preprocessing cố định; nếu đo metric, mỗi implementation có threshold lấy từ validation riêng, không dùng chung tau do khác score scale.
- **PB24-FR05:** Phân loại kết quả là đối chiếu bổ sung; muốn test xác nhận phải đăng ký/freeze trước khi xem test, nếu không chỉ báo train/validation hoặc exploratory.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không hardcode kết luận dựa trên một phiên bản cũ; báo hành vi thực đo ở version đã pin.
- Khác score không tự chứng minh implementation sai; giải thích khác đặc tả/thuật toán/hợp đồng tương lai.

## Tiêu chí nghiệm thu

- [ ] **PB24-AC01** (FR01, FR02): **Khi** mở report đối chiếu, **thì** truy được version/source và phép tính aggregation/reference của bản đã kiểm tra.
- [ ] **PB24-AC02** (FR02, FR03): **Khi** chạy ties/tails/aggregation và batch probes, **thì** bảng ghi cả hai outputs, giữ kết quả kể cả khi không có khác biệt ở probe cụ thể.
- [ ] **PB24-AC03** (FR03, FR04): **Khi** đo metric validation, **thì** cùng input/mask, threshold riêng và không chọn từ test.
- [ ] **PB24-AC04** (FR05): **Khi** thí nghiệm tạo sau khi xem benchmark test, **thì** report gắn nhãn exploratory, không đổi model chính.

## Rủi ro và quyết định cần ghi nhận

- Phiên bản thư viện thay đổi làm nhận định cũ hết đúng: version/source là đầu vào bắt buộc.
- Dùng chung threshold làm so sánh sai: calibration riêng, mask chung.

## Kết quả cần xem

- [ ] Cung cấp source/version metadata, probe fixtures, score differences và report có giới hạn kết luận.
