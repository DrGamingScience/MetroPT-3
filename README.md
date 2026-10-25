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

## Cài đặt và chạy

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

`paths.project_root` được giải từ vị trí file YAML; các đường dẫn còn lại giải từ root đó. Với config mẫu, dữ liệu ở `data/raw`, `data/interim`, `data/processed`; kết quả tương lai ở `artifacts/<run_id>` và `reports/<run_id>`. Xem hợp đồng artifact để biết các tệp cần lưu. Đã triển khai `check-config`, `ingest`, `audit`, help và version; các stage tiếp theo sẽ bổ sung theo backlog.

## Nhập và khóa dữ liệu PB02

```powershell
# Tải gói chính thức từ UCI (khoảng 208 MB)
.\.venv\Scripts\python.exe -m metropt3 ingest --config configs/base.yaml

# Hoặc nhập ZIP đã tải; chỉ khai báo URL gốc nếu biết rõ nguồn
.\.venv\Scripts\python.exe -m metropt3 ingest --config configs/base.yaml --source "D:\Downloads\metropt3.zip" --source-url "https://archive.ics.uci.edu/static/public/791/metropt%2B3%2Bdataset.zip"
```

Mỗi lần thành công trả JSON với đường dẫn `data/raw/sha256-<hash>/raw_manifest.json`, dataset version, `reused` và `audit_required`. CSV/PDF giữ nguyên byte và tên file; manifest chỉ công bố cùng thư mục version sau khi kiểm tra ZIP/CRC, header, cấu trúc CSV và dấu đầu/cuối PDF. Không sửa timestamp, index hay cảm biến trong PB02.

Nhập lại cùng CSV/PDF với cùng tên/thành viên ZIP chỉ xác minh và dùng lại bản đã khóa, không sửa manifest hay ngày tải đầu tiên. Checksum CSV khác bản tham chiếu vẫn được lưu thành version riêng với `audit_required: true`; cần audit PB03 trước khi dùng tiếp. Lỗi tải, gói thiếu/hỏng, header sai hoặc raw đã bị sửa trả mã 2. Nguồn local được ghi bằng URI thực; không tự suy nguồn từ tên file.

Xem [hợp đồng raw](docs/artifact_contracts.md#raw-manifest-pb02) và [bằng chứng PB02](docs/requirements/PB02-data-ingestion.md).

## Audit chất lượng và chia đoạn PB03

Chỉ rõ manifest của version cần xử lý:

```powershell
.\.venv\Scripts\python.exe -m metropt3 audit --config configs/base.yaml --manifest data/raw/sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55/raw_manifest.json
```

Lệnh kiểm tra checksum/schema raw rồi xuất `cleaned.parquet` và `data_card.md` vào `paths.interim/pb03-audit`. Nếu thư mục đã có, dùng `--output data/interim/pb03-rerun` để tạo kết quả mới. `--output` tương đối giải từ thư mục chạy lệnh; đường dẫn mặc định giải theo config. Lỗi đầu vào, thiếu delta train hoặc lỗi ghi trả mã 2.

Cleaned giữ index gốc, `raw_row_id`, timestamp không múi giờ, 15 sensor dạng số, quality flags, `valid`, `duplicate_count`, `segment_id` và split lịch. Nhịp `delta0` là mode delta dương của timestamp train trước `train_end_exclusive`; hòa chọn mode nhỏ nhất. Gap chỉ khi `delta > 3 × delta0`. Giá trị analog âm/cực đoan hợp lệ và dữ liệu ngày 01/09 được giữ.

Dòng lỗi cảm biến được giữ với `valid=false`; dòng lỗi timestamp và timestamp xung đột được lưu riêng để kiểm tra. Các bảng chi tiết chỉ xuất khi có nội dung. Thống kê, nguồn raw và config thực dùng nằm trong metadata Parquet, đọc bằng `pd.read_parquet(path).attrs["audit"]`. Split ở đây chỉ là thống kê lịch; mask/purge cửa sổ thuộc PB05/PB07.

Xem [hợp đồng cleaned](docs/artifact_contracts.md#cleaned-và-data-card-pb03), [nghiệm thu PB03](docs/requirements/PB03-data-quality-audit.md) và [data card dữ liệu thật](docs/examples/pb03/data_card.md).

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

Tải dữ liệu từ UCI bằng lệnh `ingest`; dữ liệu thô và kết quả sinh ra được gitignore.
Pipeline ghi rõ các kiểm tra trên CSV gốc và những điểm metadata chưa thống nhất.

## Trạng thái

Đã có proposal, thiết kế pipeline, khung PB01, ingest PB02 và audit PB03 gồm khóa nguồn,
manifest/checksum/version, chất lượng dữ liệu, chia đoạn, CLI và bộ kiểm tra. Chưa có kết quả huấn luyện hoặc
so sánh mô hình; xem trạng thái review của từng PB trong bảng quản lý công việc.
Phạm vi là phát hiện bất thường, không phải dự đoán thời điểm hỏng
hay ước lượng tuổi thọ còn lại của thiết bị.
