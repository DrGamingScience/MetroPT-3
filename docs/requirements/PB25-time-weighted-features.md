# PB25 Đặc trưng có trọng số thời gian

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P2 — tùy chọn |
| Mốc | P2 — mở rộng feature |
| Phụ thuộc | [PB15](PB15-experiment-runner.md) |
| Nguồn | Backlog PB25; pipeline chương 6, 13 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

**Phạm vi hiện tại: Deferred.** Chỉ triển khai khi có câu hỏi hoặc nhu cầu cụ thể; các yêu cầu dưới đây áp dụng nếu mở lại mục này.

## Mục tiêu và nhu cầu

Người phân tích cần đo xem trọng số theo thời gian có thay đổi kết quả khi nhịp quan sát không đều hay không.

## Phạm vi và ranh giới

Nhánh feature riêng so với mean/tỷ lệ theo số mẫu của benchmark; không âm thầm thay công thức F35/F51 gốc.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Raw timestamps/quality/lineage; runner PB15 | Nhịp không đều, split/segment và quality policy đã cố định. |
| Đầu ra | Time-weighted feature schema/config | Biên giữ mẫu, max hold age, đơn vị, denominator và version riêng. |
| Đầu ra | Validation comparison runs | Model/preprocess/tau riêng; common mask; coverage và chi phí. |

## Yêu cầu chức năng

- **PB25-FR01:** Định nghĩa khoảng mà mẫu tại s_i đại diện bằng sample-and-hold chỉ tới mốc đã biết <=t; cắt ở biên cửa sổ/t, split/segment/gap và giới hạn tuổi cấu hình. Không lấy giá trị mẫu tương lai để nội suy.
- **PB25-FR02:** Chốt max_hold_seconds, xử lý mẫu trước biên trái và phần duration không được phủ trong config trước chạy; mọi nguồn dùng phải có lineage và tuân purge/warm-up. Đây là quyết định bổ sung, chưa có giá trị mặc định xác nhận trong pipeline.
- **PB25-FR03:** Mean có trọng số là sum(x_i×duration_i)/sum(duration_i); digital on fraction là covered on-duration/covered duration. Công bố observed/covered duration; denominator=0 làm invalid, không biến thành 0.
- **PB25-FR04:** Tạo feature_set/version riêng, không đặt tên kết quả như F35/F51 chuẩn; fit preprocessing/model train và calibration validation riêng, báo common mask với nhánh chuẩn.
- **PB25-FR05:** Đánh giá ảnh hưởng tới feature/metric/coverage/runtime trên validation; test xác nhận cần đăng ký trước freeze, sau khi xem test chỉ exploratory.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Tính thời lượng theo timestamp thật và đơn vị giây nhất quán; không tính thời gian không quan sát như được phủ.
- Không lấp qua gap dài hoặc dùng sample-and-hold vô hạn để đạt coverage.

## Tiêu chí nghiệm thu

- [ ] **PB25-AC01** (FR01, FR02, FR03): **Khi** fixture có giá trị/thời lượng 0 trong 10 giây và 10 trong 50 giây được phủ hợp lệ, **thì** weighted mean=500/60, khác sample mean=5; denominator và biên đúng policy.
- [ ] **PB25-AC02** (FR01, FR02): **Khi** thêm/sửa dữ liệu sau t hoặc có split/gap trong cửa sổ, **thì** feature tại t không đổi theo tương lai và không dùng nguồn qua biên.
- [ ] **PB25-AC03** (FR03): **Khi** không còn covered duration hoặc mẫu quá tuổi, **thì** invalid có reason, không score hoặc mean 0 giả.
- [ ] **PB25-AC04** (FR04, FR05): **Khi** so nhánh time-weighted với benchmark, **thì** schema/run/tau riêng, cùng comparison mask và công bố phần coverage khác.

## Rủi ro và quyết định cần ghi nhận

- Trọng số giữ mẫu lâu có thể khuếch đại giá trị cũ: giới hạn tuổi và báo covered duration.
- Thay công thức phải có tên feature_set riêng và ghi trong cấu hình để không nhầm bảng kết quả; không cần cache/hash riêng.

## Kết quả cần xem

- [ ] Cung cấp policy có giá trị cụ thể, weighted schema, test tính tay/cause và bảng validation so nhánh chuẩn.
