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

Lệnh kiểm tra checksum/schema raw rồi xuất `cleaned.parquet`, `events.csv` và `data_card.md` vào `paths.interim/pb03-audit`. Nếu thư mục đã có, dùng `--output data/interim/pb03-rerun` để tạo kết quả mới. `--output` tương đối giải từ thư mục chạy lệnh; đường dẫn mặc định giải theo config. Lỗi đầu vào, thiếu delta train hoặc lỗi ghi trả mã 2.

Cleaned giữ index gốc, `raw_row_id`, timestamp không múi giờ, 15 sensor dạng số, quality flags, `valid`, `duplicate_count`, `segment_id` và split lịch. Nhịp `delta0` là mode delta dương của timestamp train trước `train_end_exclusive`; hòa chọn mode nhỏ nhất. Gap chỉ khi `delta > 3 × delta0`. Giá trị analog âm/cực đoan hợp lệ và dữ liệu ngày 01/09 được giữ.

Dòng lỗi cảm biến được giữ với `valid=false`; dòng lỗi timestamp và timestamp xung đột được lưu riêng để kiểm tra. Các bảng chi tiết chỉ xuất khi có nội dung. Thống kê, nguồn raw và config thực dùng nằm trong metadata Parquet, đọc bằng `pd.read_parquet(path).attrs["audit"]`. Split ở đây chỉ là thống kê lịch; mask/purge cửa sổ thuộc PB05/PB07.

Xem [hợp đồng cleaned](docs/artifact_contracts.md#cleaned-và-data-card-pb03), [nghiệm thu PB03](docs/requirements/PB03-data-quality-audit.md) và [data card dữ liệu thật](docs/examples/pb03/data_card.md).

## Bảng sự cố và nhãn PB04

Lệnh `audit` xuất thêm `events.csv` trong cùng bộ kết quả chuẩn bị dữ liệu; không cần một stage/CLI riêng. Ví dụ chạy trên version đã nhập:

```powershell
.\.venv\Scripts\python.exe -m metropt3 audit --config configs/base.yaml --manifest data/raw/sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55/raw_manifest.json --output data/interim/pb04-verified-20261025
```

Nếu thư mục đã có, chọn `--output` mới. JSON kết quả có đường dẫn `events`. [Bảng mẫu để review](docs/examples/pb04/events.csv) chứa E1–E4 và nguồn UCI, loại lỗi, ghi chú gốc và ghi chú độ tin cậy. E2 giữ nguyên `Maintenance on 30Apr at 12:00` dù sự cố ở tháng 5; không tự đổi ngày. Khoảng sự cố đóng cả hai đầu; mốc chỉ ghi đến phút có giây đúng `00`, không kéo dài đến `59`. Toàn bộ dùng đồng hồ gốc không múi giờ.

Các hàm trong [events.py](src/metropt3/events.py) dùng lại khi tạo cửa sổ và đánh giá:

```python
from metropt3.events import event_coverage, label_timestamps, read_events, reference_status

events = read_events("data/interim/pb04-verified-20261025/events.csv")
labels = label_timestamps(["2020-04-19 00:00:00"], events, valid=[True])
assert labels.label.iloc[0] == 0  # Điểm kết thúc nằm ngoài E1.

status = reference_status(
    ["2020-04-18 23:59:20", "2020-04-19 00:00:00"], events,
    fill_origin_timestamps=["2020-04-18 23:59:00"],
)
assert status["source_event_ids"] == ["E1"]
assert not status["is_reference"]  # Nguồn giá trị fill vẫn thuộc E1.

coverage = event_coverage(labels.window_end, events, valid=labels.valid)
```

`label_timestamps` trả bảng riêng gồm `window_end`, `valid`, `label` kiểu nullable `Int8` và danh sách `event_ids`. Mốc invalid có nhãn null, không phải 0; nhãn 0 chỉ có nghĩa ngoài các sự cố đã báo cáo. Nếu truyền Series `valid`, index phải trùng `window_end`; không tự ghép theo thứ tự hàng khi index lệch. Chỉ ghép nhãn với kết quả sau bước score; không đưa cột nhãn vào ma trận feature/detector.

`reference_status` nhận **mọi timestamp nguồn thực dùng**, cộng timestamp gốc của các giá trị fill. Không thay bằng nhãn ở cuối cửa sổ, biên danh nghĩa hay min/max nguồn. Hàm chỉ kiểm tra giao sự cố; PB05/PB07 còn phải kiểm tra quality/split/segment trước khi truyền `valid=True`.

`event_coverage` giữ tất cả sự cố, báo số mốc hợp lệ, mốc đầu và `evaluable=false` nếu không có mốc nào. PB11 phải dùng mốc score hợp lệ/common mask. Metadata `cleaned.parquet.attrs['audit']['reported_events']` và data card chỉ thống kê độ phủ **dòng cleaned**, chưa phải độ phủ cửa sổ cuối cùng. Xem [nghiệm thu PB04](docs/requirements/PB04-event-labels.md) và [bằng chứng dữ liệu thật](docs/examples/pb04/validation.json).

## Temporal split và purge PB05

Lệnh `audit` xuất thêm `minute_grid.parquet` trong cùng bộ chuẩn bị dữ liệu, không thêm CLI riêng:

```powershell
.\.venv\Scripts\python.exe -m metropt3 audit --config configs/base.yaml --manifest data/raw/sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55/raw_manifest.json --output data/interim/pb05-rerun
```

Lưới giữ mọi phút từ `ceil(first_timestamp)` đến `floor(last_timestamp)`, kể cả gap/warm-up. Train trước 01/03/2020; validation từ 01/03 đến trước 01/05; test từ 01/05. Mỗi cặp `(split, segment_id)` bắt đầu warm-up từ quan sát thật đầu tiên; warm-up chung 930 giây cho W=1/5/15. Bắt đầu 00:00 thì 00:15 chưa đủ, 00:16 mới đủ. `segment_id` của PB03 không bị sửa; trạng thái cửa sổ/fill của PB07 phải reset theo cả hai cột.

`temporal_valid` chỉ xác nhận điều kiện thời gian. `temporal_reason` nhận `gap`, `warmup` hoặc null; gap ưu tiên trước warm-up. Mốc cách quan sát quá khứ gần nhất hơn `gap_break` bị đánh dấu gap; không đọc quan sát tương lai để quyết định tại mốc hiện tại. Chất lượng sensor, coverage và kiểm tra biên cửa sổ vẫn thuộc PB07. Vì vậy bảng lịch chưa có `valid` hoặc `is_reference` cuối cùng. Data card và metadata `attrs['temporal']` báo rõ phạm vi thống kê; thời lượng biểu diễn bằng số mốc × 60 giây, không phải thời gian sensor hoạt động thực tế.

API trong [temporal.py](src/metropt3/temporal.py) dùng chung khi xây feature:

```python
import pandas as pd
from metropt3.config import load_config
from metropt3.events import read_events
from metropt3.temporal import build_time_grid, summarize_time_grid

config = load_config("configs/base.yaml")
cleaned = pd.read_parquet("data/interim/pb05-verified-20261025/cleaned.parquet")
events = read_events("data/interim/pb05-verified-20261025/events.csv")
grid = build_time_grid(cleaned, config,
                       gap_break_seconds=cleaned.attrs["audit"]["cadence"]["gap_break_seconds"])
summary = summarize_time_grid(grid, events)
```

PB07 gọi `apply_window_masks(grid, cleaned, events, config, sources=..., quality_valid=..., fill_origins=..., quality_reason=...)` một lần cho bảng cửa sổ. `sources` chứa **toàn bộ** cặp `window_end,raw_row_id` thực dùng; `fill_origins` chứa `window_end,raw_row_id,target_timestamp`, ID trỏ tới quan sát gốc của từng giá trị fill. Không cần xuất bảng lineage này ra đĩa. `quality_valid` là Series boolean cùng index với grid, do PB07 kiểm tra theo sensor thực dùng. Hàm kiểm tra split/segment, nguồn tương lai, biên `(t-W,t]`, tuổi fill, nguồn giao sự cố và nguồn rỗng. Nó không thực hiện fill hoặc tạo F35.

Kết quả có `valid/reason`, `is_evaluation`, `is_reference`, `source_event_ids`, `source_min_time/source_max_time` và nhãn tại `window_end`. Reference chỉ áp dụng train/validation, loại mọi nguồn giao sự cố kể cả fill origin ngoài biên danh nghĩa. Evaluation giữ sự cố khi cửa sổ hợp lệ; invalid có label null. Nhãn/mask là metadata, không đưa vào ma trận sensor/feature của detector. `summarize_time_grid` tự dùng mask `valid` sau bước này, giữ cả sự cố không có mốc hợp lệ; PB11 vẫn phải tính lại trên common score mask.

Xem [nghiệm thu PB05](docs/requirements/PB05-temporal-splits.md), [data card thật](docs/examples/pb05/data_card.md) và [thống kê để review](docs/examples/pb05/validation.json).

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

Đã có proposal, thiết kế pipeline, khung PB01, ingest PB02, audit PB03, bảng sự cố/nhãn PB04 và temporal split/purge PB05 gồm khóa nguồn,
manifest/checksum/version, chất lượng dữ liệu, chia đoạn, nhãn đối chiếu và kiểm tra nguồn giao sự cố. Chưa có kết quả huấn luyện hoặc
so sánh mô hình; xem trạng thái review của từng PB trong bảng quản lý công việc.
Phạm vi là phát hiện bất thường, không phải dự đoán thời điểm hỏng
hay ước lượng tuổi thọ còn lại của thiết bị.
