# PB05 Temporal split và purge

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M1 |
| Phụ thuộc | [PB03](PB03-data-quality-audit.md), [PB04](PB04-event-labels.md) |
| Nguồn | Backlog PB05; pipeline chương 4 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người chạy benchmark cần train/validation/test theo thời gian, với mốc chấm công bằng và không dùng chung nguồn quan sát qua biên.

## Phạm vi và ranh giới

Chia tập và tạo mask trong cùng luồng chuẩn bị/feature. PB07 kiểm tra nguồn thực dùng; không cần một stage hay lệnh split độc lập.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Cleaned timestamps/segments; events; config | delta0/gap_break từ train; biên split đã cố định. |
| Đầu ra | Cột split/warm-up trên lưới phút; tóm tắt split trong data card/config | Mốc một phút, thời lượng/số dòng/sự cố theo split. |
| Bàn giao | Reference/evaluation mask policy | PB07 bổ sung provenance; PB15 tạo common comparison mask. |

## Yêu cầu chức năng

- **PB05-FR01:** Train trước 2020-03-01 00:00, validation từ đó đến trước 2020-05-01 00:00, test từ đó đến hết tệp; không dịch biên theo score hoặc hiệu quả mô hình.
- **PB05-FR02:** Mỗi mốc thuộc đúng một split; mỗi cửa sổ chỉ dùng raw và fill origin cùng split/segment. Biên split hoặc gap reset trạng thái.
- **PB05-FR03:** Warm-up chung bằng Wmax + max fill age = 930 giây; mốc đầu đủ điều kiện nằm trên lưới phút tại hoặc sau thời điểm đủ warm-up, áp dụng lại mỗi đoạn liên tục.
- **PB05-FR04:** Train/validation reference loại cửa sổ có nguồn giao sự cố; evaluation giữ mọi mốc hợp lệ và gán nhãn tại window_end. Dùng contract provenance để bổ sung mask khi feature sẵn sàng.
- **PB05-FR05:** Lưu mốc dự kiến, hợp lệ, loại theo lý do, thời lượng, dương và số sự cố đánh giá được; E1 thuộc validation, E2–E4 test nếu dữ liệu nguồn đúng phiên bản.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Bảng mốc dự kiến vẫn giữ warm-up/invalid để đo coverage; không chỉ xuất những mốc đẹp.
- Audit timestamp của test được phép; phân phối cảm biến/score test không tham gia lựa chọn.

## Tiêu chí nghiệm thu

- [ ] **PB05-AC01** (FR01): **Khi** xét timestamp đúng 2020-03-01 và 2020-05-01, **thì** lần lượt vào validation và test, không trùng train.
- [ ] **PB05-AC02** (FR02, FR03): **Khi** split/segment bắt đầu đúng 00:00 và warm-up=930 giây, **thì** 00:15 chưa đủ; 00:16 mới đủ warm-up, vẫn phải qua kiểm tra chất lượng.
- [ ] **PB05-AC03** (FR02, FR04): **Khi** kiểm tra lineage fixture của hai split, **thì** không chung raw_row_id hoặc fill origin; reference và evaluation được phân biệt đúng.
- [ ] **PB05-AC04** (FR05): **Khi** một sự cố không có mốc hợp lệ, **thì** giữ nó trong tổng nguồn và ghi không đánh giá được, không xóa khỏi báo cáo.

## Rủi ro và quyết định cần ghi nhận

- Cho W=1 dùng warm-up ngắn hơn W=15 tạo so sánh lệch: áp dụng warm-up chung.
- Chỉ dùng biên cửa sổ để kiểm tra purge có thể bỏ sót nguồn fill: kiểm tra cả lineage.

## Kết quả cần xem

- [ ] Cung cấp số mốc theo split/reason và kiểm tra ranh giới/nguồn dùng chung với PB07; không bắt buộc splits.json riêng.
