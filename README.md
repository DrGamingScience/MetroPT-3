# MetroPT-3 — Phát hiện bất thường trên dữ liệu cảm biến

Đồ án Machine Learning & Data Mining về phát hiện bất thường
trên dữ liệu máy nén khí đường sắt MetroPT-3 bằng MAD, Isolation Forest và ECOD.

## Tài liệu

| Tài liệu | Nội dung |
| --- | --- |
| [Proposal — Markdown](docs/proposal/metropt3_proposal.md) | Bài toán, phạm vi, phương pháp và kế hoạch đánh giá. |
| [Proposal — PDF](docs/proposal/metropt3_proposal.pdf) | Bản trình bày để đọc, chia sẻ và nộp đề xuất. |
| [Pipeline kỹ thuật — Word](docs/metropt3_pipeline_ky_thuat.docx) | Thiết kế chi tiết từng bước, công thức, cấu hình và kiểm thử. |
| [Product backlog](docs/product_backlog.md) | Thứ tự triển khai, phụ thuộc, tiêu chí nghiệm thu và tên branch cho từng phần. |
| [Phân tích yêu cầu và quản lý PB](docs/requirements/README.md) | File yêu cầu riêng cho PB01–PB26, checklist nghiệm thu và bảng theo dõi công việc. |
| [Hợp đồng cấu hình và artifact](docs/artifact_contracts.md) | Đường dẫn, config hash, schema/version, run ID và quan hệ đầu vào/đầu ra giữa các stage. |

## Cài đặt và chạy PB01

Yêu cầu Python từ 3.11. Từ root repo trên Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m metropt3.cli --help
.\.venv\Scripts\python.exe -m metropt3.cli check-config --config configs/base.yaml
```

Không cần activate môi trường. Trên macOS/Linux, dùng `.venv/bin/python` thay cho `.venv\Scripts\python.exe`. Extra `pyod` chỉ dành cho đối chiếu tùy chọn; không bắt buộc cho FrozenECOD. Chốt lockfile sau smoke test pipeline ở PB12.

Chạy kiểm tra:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

`check-config` kiểm tra [configs/base.yaml](configs/base.yaml), rồi in JSON gồm config hash và đường dẫn đã giải. Lệnh này không cần raw, không tạo run và không huấn luyện model. Config sai trả mã lỗi 2 với tên trường; ví dụ `features.window_minutes` phải là số nguyên dương, quantile thuộc `(0, 1)` và mốc validation phải sau train.

`paths.project_root` được giải từ vị trí file YAML; các đường dẫn còn lại giải từ root đó. Với config mẫu, dữ liệu ở `data/raw`, `data/interim`, `data/processed`; kết quả tương lai ở `artifacts/<run_id>` và `reports/<run_id>`. Xem hợp đồng artifact để biết các tệp cần lưu. Chỉ `check-config`, help và version đã được triển khai; các stage dữ liệu/mô hình sẽ bổ sung theo backlog.

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

Tải dữ liệu từ UCI; repo hiện lưu tài liệu và khung PB01, chưa kèm dữ liệu thô.
Pipeline ghi rõ các kiểm tra trên CSV gốc và những điểm metadata chưa thống nhất.

## Trạng thái

Đã có proposal, thiết kế pipeline và khung PB01 gồm package, config validator,
CLI ban đầu, hợp đồng artifact và bộ kiểm tra. Chưa có kết quả huấn luyện hoặc
so sánh mô hình; xem trạng thái review của từng PB trong bảng quản lý công việc.
Phạm vi là phát hiện bất thường, không phải dự đoán thời điểm hỏng
hay ước lượng tuổi thọ còn lại của thiết bị.
