# MetroPT-3 — Phát hiện bất thường trên dữ liệu cảm biến

Đề xuất đồ án Machine Learning & Data Mining về phát hiện bất thường
trên dữ liệu máy nén khí đường sắt MetroPT-3 bằng MAD, Isolation Forest và ECOD.

## Tài liệu

| Tài liệu | Nội dung |
| --- | --- |
| [Proposal — Markdown](metropt3_proposal.md) | Bài toán, phạm vi, phương pháp và kế hoạch đánh giá. |
| [Proposal — PDF](metropt3_proposal.pdf) | Bản trình bày để đọc, chia sẻ và nộp đề xuất. |
| [Pipeline kỹ thuật — Word](docs/metropt3_pipeline_ky_thuat.docx) | Thiết kế chi tiết từng bước, công thức, cấu hình và kiểm thử. |

## Hướng tiếp cận

1. Kiểm tra schema, timestamp, dữ liệu thiếu và các khoảng ngắt.
2. Chia train/validation/test theo thời gian để tránh rò rỉ dữ liệu.
3. Tạo đặc trưng từ cửa sổ 1, 5 và 15 phút; chấm điểm mỗi phút.
4. So sánh MAD, Isolation Forest và ECOD với phân phối tham chiếu cố định.
5. Chọn cấu hình, ngưỡng và quy tắc gộp cảnh báo trên validation.
6. Đánh giá AP, precision/recall/F1, event recall, độ trễ và số đợt cảnh báo.

## Dữ liệu và tài liệu tham khảo

- [MetroPT-3 trên UCI](https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset)
  — 1.516.948 bản ghi, 15 cảm biến và bốn khoảng sự cố được báo cáo.
- [Bài báo ECOD](https://arxiv.org/abs/2201.00382)
  — phát hiện ngoại lệ bằng hàm phân phối tích lũy thực nghiệm.

Tải dữ liệu từ UCI; repo chỉ lưu tài liệu đề xuất và thiết kế kỹ thuật.
Pipeline ghi rõ các kiểm tra trên CSV gốc và những điểm metadata chưa thống nhất.

## Trạng thái

Đã hoàn thành proposal và thiết kế pipeline; chưa có mã triển khai đầy đủ
hoặc kết quả huấn luyện, so sánh mô hình trong repo.
Phạm vi là phát hiện bất thường, không phải dự đoán thời điểm hỏng
hay ước lượng tuổi thọ còn lại của thiết bị.
