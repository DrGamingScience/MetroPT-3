# Hợp đồng cấu hình và artifact MetroPT-3

PB01 triển khai nạp/kiểm tra config và canonical config hash. Tài liệu này quy định hợp đồng cho các stage sẽ được triển khai trong PB02–PB22; chưa có stage huấn luyện, tạo run, freeze hoặc test benchmark ở PB01.

## Cấu hình và đường dẫn

`configs/base.yaml` dùng `schema_version: 1`. Tất cả trường trong mẫu là bắt buộc; tên trường lạ, YAML trùng khóa, sai kiểu hoặc giá trị không hợp lệ bị từ chối. Các quy tắc benchmark như timezone null, biên phải, ddof=0, ECOD-paper-frozen, quantile higher, alarm greater_than và ngắt episode ở invalid được kiểm tra theo schema này.

Các mốc split dùng đồng hồ gốc không offset; chỉ được khai báo ở PB01, việc chia dữ liệu thuộc PB05. Warm-up phải ít nhất bằng cửa sổ ứng viên lớn nhất cộng tuổi forward fill tối đa. `window_minutes` phải có trong `candidate_windows`.

YAML timestamp được giữ dưới dạng chuỗi để validator của từng trường kiểm tra ngày/giờ. Giá trị sai có hoặc không có dấu nháy đều phải báo tên trường và lý do, CLI trả mã 2 thay vì traceback. Cả `reproducibility.seed` và từng phần tử `stability_seeds` phải là số nguyên trong `0..4294967295`, phù hợp miền seed RandomState dùng bởi Isolation Forest.

`paths.project_root` giải từ thư mục chứa YAML. Các đường dẫn còn lại giải từ project_root, không phụ thuộc thư mục đang chạy lệnh. Với `configs/base.yaml` hiện tại, `project_root: ".."` trỏ root repo. Đường dẫn tuyệt đối được cho phép khi cố ý đặt dữ liệu ngoài repo. Đọc/kiểm tra config không tạo thư mục hoặc ghi kết quả.

| Trường | Mặc định | Dùng để lưu |
| --- | --- | --- |
| `paths.raw` | `data/raw` | CSV/PDF gốc và manifest nguồn, không sửa raw. |
| `paths.interim` | `data/interim` | Cleaned rows, events, segments, audit. |
| `paths.processed` | `data/processed` | Features và các split/quality/reference masks. |
| `paths.artifacts` | `artifacts` | Model, score, cấu hình và metric theo run_id. |
| `paths.reports` | `reports` | Report, biểu đồ, case study theo run_id. |

## Canonical config hash

`load_config()` trả snapshot `ProjectConfig`; `as_dict()` trả bản sao để bên gọi không sửa trạng thái đã kiểm tra. Chuẩn hóa số thực và timestamp trước khi serialize JSON UTF-8, sort keys, không khoảng trắng thừa và không cho NaN/Infinity. `config_hash` là SHA-256 đầy đủ của canonical JSON này.

Đổi thứ tự khóa hoặc comment YAML không đổi hash; thay seed/W/tham số có ý nghĩa làm hash đổi. Thứ tự phần tử list được giữ. Đường dẫn source và đường dẫn tuyệt đối được giải lúc chạy không tự thêm vào canonical config, nên di chuyển nguyên repo không đổi hash. Nếu người dùng ghi đường dẫn tuyệt đối trực tiếp trong YAML thì giá trị đó là một phần config hash.

Config hash không thay thế code hash, data hash hoặc model hash. Cache chỉ hợp lệ khi toàn bộ các hash đầu vào liên quan khớp.

## Run ID và tính bất biến

Khi bổ sung bộ tạo run ở PB12, dùng định dạng `YYYYMMDDTHHMMSSffffffZ-<config_hash_12>-<uuid_8>`, trong đó thời gian UTC chỉ định danh lần chạy, không chuyển múi giờ timestamp cảm biến. UUID tránh va chạm cho hai lần chạy cùng thời điểm/config.

- Mỗi run có `artifacts/<run_id>/` và `reports/<run_id>/`; tạo thư mục theo chế độ độc quyền, không ghi đè run đã có.
- Lưu canonical config thành `config.snapshot.json`, cùng hash đầy đủ trong run manifest. Thư mục ví dụ trong tài liệu không phải kết quả thí nghiệm thật.
- Các trạng thái stage gồm `created`, `running`, `completed`, `failed`; chỉ completed mới được downstream sử dụng. Ghi tệp tạm rồi hoàn tất manifest sau khi xác minh output.
- Run completed bất biến. Thay W, feature_set, model/config hoặc chạy lại tạo run_id mới; không sửa artifact hoàn tất tại chỗ.
- Raw dùng checksum làm phiên bản dữ liệu. File dùng chung được tham chiếu bằng đường dẫn + SHA-256, không cần nhân bản vào mỗi run.

## Phiên bản và manifest

Config, manifest và từng loại artifact có schema version riêng, khởi đầu là 1 khi stage đó triển khai. Version không hỗ trợ phải bị từ chối. Thay đổi cách hiểu trường/công thức/cột tăng version và ghi trong manifest; không tái sử dụng cache khác schema.

`run_manifest.json` cần các trường sau khi có runner PB12:

| Trường | Nội dung |
| --- | --- |
| `schema_version`, `run_id`, `stage`, `status` | Phiên bản hợp đồng, định danh và trạng thái thực tế. |
| `config_hash`, `config_snapshot` | SHA-256 và đường dẫn config đã dùng. |
| `code` | Git commit, cờ working tree dirty và SHA-256 snapshot source/config liên quan; commit đơn lẻ không đủ khi có thay đổi chưa commit. |
| `dataset` | Dataset version, raw manifest và raw SHA-256. |
| `parents` | Danh sách artifact đầu vào với đường dẫn, SHA-256 và schema version. |
| `outputs` | Danh sách artifact đầu ra với loại, đường dẫn, SHA-256 và schema version. |
| `seed`, `environment` | Python, library versions, OS, CPU, RAM, số luồng. |
| `started_at`, `finished_at`, `timing`, `resources` | Thời điểm/thời gian/tài nguyên đã đo; thiếu thì null với lý do. |

SHA-256 luôn tính từ byte file thực tế sau khi ghi. Đường dẫn artifact trong manifest giải từ thư mục chứa manifest; tham chiếu raw dùng chung có thể đi ra ngoài thư mục run. Downstream kiểm tra file tồn tại, schema, completed status và checksum trước khi dùng.

## Quan hệ giữa các stage

| Stage hoặc PB | Đầu vào chính | Đầu ra cần có |
| --- | --- | --- |
| Ingest PB02 | Gói UCI/local | Raw CSV/PDF, `raw_manifest.json`. |
| Audit/events PB03–PB04 | Raw đã xác minh và nguồn sự cố | Cleaned rows, quality report, data card, `events.csv`, fitted cadence. |
| Split/features PB05–PB07 | Cleaned/events/config | `splits.json`, masks, features, `feature_schema.json`, source provenance. |
| Preprocess/train PB08–PB14 | Train reference và schema | `preprocess.joblib`, model artifact/metadata. |
| Validate PB12/PB15/PB18 | Train-fitted artifacts + validation | Scores, `validation_results.csv`, comparison masks, quyết định lựa chọn. |
| Freeze PB18 | Kết quả lựa chọn + model/schema | `frozen_config.json` và hash toàn bộ artifacts đã chọn. |
| Test PB19 | Frozen bundle hợp lệ + test | `scores.parquet`, `episodes.csv`, `metrics.json`, bảng tổng hợp/từng sự cố. |
| Report PB21 | Completed metrics/scores/cases | Report/biểu đồ/bảng có run_id, split, đơn vị và nguồn dữ liệu. |

Feature schema lưu cột/thứ tự/công thức/đơn vị/W/biên/version. Scores giữ mọi mốc dự kiến với timestamp, split, segment, valid, reason, score, threshold, alarm, model_version; invalid có score/alarm null. Metric lưu số đếm, mẫu số, mask_id, coverage và lý do N/A; JSON dùng null thay cho NaN/Infinity.

Test stage phải từ chối khi thiếu frozen config hoặc artifact hash sai. Không refit train+validation sau calibration. Model và feature schema không nhận nhãn test; ghép nhãn sau score.

## Tài liệu kỹ thuật tham khảo

Khai báo package theo [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/), CLI dùng [argparse](https://docs.python.org/3.13/library/argparse.html), YAML dùng SafeLoader theo [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation) và bổ sung kiểm tra trùng khóa.
