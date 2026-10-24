# Cấu hình và đầu ra tối thiểu MetroPT-3

Rà soát **2026-10-24**: giữ hợp đồng config/raw đã triển khai; thay kế hoạch manifest theo stage bằng cách lưu kết quả gọn cho đồ án ML. Phần thí nghiệm bên dưới là yêu cầu cho bước chưa triển khai, không mô tả tính năng CLI đã có. Xem [phạm vi](requirements/README.md) và [backlog](product_backlog.md).

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

Config hash đã có được giữ để nhận diện cấu hình. Không yêu cầu thêm hash cho mọi bảng/mask/model hoặc cache xuyên run. Cấu hình thực dùng vẫn phải được lưu để đọc và chạy lại.

## Raw manifest PB02

`ingest` xuất `data/raw/sha256-<hash>/raw_manifest.json` cùng CSV/PDF nguyên byte. Không có con trỏ "latest" dùng chung; downstream nhận đường dẫn manifest cụ thể từ JSON của CLI. Manifest chỉ xuất hiện sau khi toàn bộ dữ liệu đã xác minh và thư mục staging được đổi tên nguyên khối. Lỗi thông thường dọn staging; nếu tiến trình bị kill, thư mục `.ingest-*` còn lại không phải version hoàn tất.

Schema raw v1 có các trường:

| Trường | Nội dung |
| --- | --- |
| `schema_version`, `status`, `dataset_version` | `1`, `completed` và hash định danh nội dung. Completed chỉ xác nhận ingest, không thay kết quả audit. |
| `source` | `kind`, `location` (URL hoặc file URI), `resolved_url` sau redirect và `url` nguồn được khai báo; URL local không biết là null. |
| `downloaded_at`, `package` | UTC lúc nhận gói hoàn tất; byte/SHA-256 của ZIP thực nhận. Với local đây là thời điểm nhập, không suy ra ngày tải lịch sử. |
| `files.csv`, `files.pdf` | `path` tương đối với manifest, `archive_member` gốc, `bytes`, `sha256`. |
| `csv` | Header nguyên gốc, index/timestamp, 7 analog, 8 digital, feature allowlist, số record thực đo và quy ước `raw_row_id`. |
| `audit` | SHA-256 CSV tham chiếu, `required` và `reason`; khác tham chiếu bắt buộc audit lại. |

Hash version là SHA-256 của JSON UTF-8 canonical (`sort_keys=True`, separators `(',', ':')`) chứa `schema_version` và `files`. Bao gồm CSV/PDF, tên file và tên thành viên ZIP; thay nội dung PDF cũng tạo version mới. Đóng gói lại cùng các thành viên không đổi version; timestamp/nguồn/byte ZIP không thuộc định danh. Khi dùng lại version, giữ nguồn và ngày nhập đầu tiên trong manifest bất biến, kiểm tra lại checksum mọi file; không ghi đè khi phát hiện sửa đổi hoặc thiếu file.

Trước khi reuse, kiểm tra đủ trường và kiểu theo schema v1, bao gồm metadata của lần nhập đầu tiên: `source` đủ kind/location/resolved_url/url; nguồn URL phải có HTTP(S) URL tuyệt đối, nguồn local có file URI tuyệt đối, `resolved_url: null`, và URL gốc có thể null. `downloaded_at` phải là ISO timestamp UTC; `package.bytes` là số nguyên dương (không nhận bool), `package.sha256` là 64 ký tự hex thường. Thiếu hoặc sai metadata trả lỗi, giữ nguyên raw và manifest. Các trường này được xác minh độc lập, không so sánh với nguồn/ngày/ZIP của lần nhập mới; các trường nội dung còn lại được đối chiếu cả giá trị và kiểu JSON.

CSV phải có đúng `timestamp`, 15 sensor đúng chính tả và một index trong `""`, `index`, `Unnamed: 0`; không đổi tên header. `feature_columns` chỉ gồm 15 sensor, không chứa timestamp/index. `row_count` đếm CSV record thực tế, không dùng số công bố. Không kiểm tra giá trị numeric, sắp xếp, deduplicate hoặc sửa dữ liệu ở bước này.

`raw_row_id` là vị trí CSV data record bắt đầu từ 0, bỏ header; phạm vi định danh là cặp `(dataset_version, raw_row_id)`. Đây là CSV record, không phải số dòng vật lý nếu giá trị được quote có newline. Index gốc có thể không liên tiếp và không thay thế `raw_row_id`. PB03/PB04 materialize ID khi đọc raw; PB02 chỉ ghi quy ước để giữ nguyên byte CSV.

PDF được kiểm tra signature `%PDF-` và marker `%%EOF`, không phân tích ngữ nghĩa nội dung. ZIP phải có đúng một CSV và một PDF; từ chối tên đường dẫn thoát thư mục hoặc symlink. CRC kiểm tra toàn bộ thành viên trước khi xuất version.

## Một thư mục cho một bộ thí nghiệm

Một lần so sánh có thể chứa nhiều model/W/seed. Dùng tên thư mục dễ đọc (ví dụ `artifacts/validation-20261024/`), phân biệt cấu hình bằng `config_id` ngắn và tham số thực tế trong bảng kết quả. Không bắt buộc UUID, run ID theo hash hay một run cho mỗi hàm. Báo lỗi nếu tên đích đã có để tránh ghi đè nhầm kết quả đã báo cáo.

Một script gọi tuần tự các hàm; khi lỗi thì dừng, không ghi bảng tổng kết như thành công. Ghi bảng kết quả cuối sau khi tính xong. Không cần state machine từng stage, manifest cha/con, tự động resume, registry hay cơ chế publish nhiều tầng.

## Các đầu ra cần giữ

| Phần | Nội dung tối thiểu | Có thể tổ chức gọn như sau |
| --- | --- | --- |
| Raw | CSV/PDF gốc, nguồn và checksum | Giữ `data/raw/<version>/raw_manifest.json` hiện tại. |
| Chuẩn bị | Cleaned rows với raw_row_id/segment; bảng 4 sự cố; thống kê chất lượng/nhịp/split | `cleaned.parquet`, `events.csv`, một `data_card.md`. Bảng dòng lỗi/gap riêng chỉ khi cần xem chi tiết. |
| Feature | Feature names/order/công thức; W/biên; mọi mốc với split/valid/reason/reference | `features.parquet` chứa cả cột metadata/mask; thông tin cột/công thức trong metadata dùng chung hoặc `feature_schema.json` gọn. |
| Thí nghiệm | Config hiệu dụng, raw version/checksum, code, seed và phiên bản môi trường | Một `run_manifest.json` gọn cho cả bộ thí nghiệm, kèm config snapshot/lockfile hoặc đường dẫn tới chúng. |
| Validation | Model/W/tham số/seed, common mask policy, số mốc, coverage, metric, q/tau, timing | `validation_results.csv`; score được giữ trong bộ nhớ khi quét q. Lưu score ra file nếu dùng cho hình/báo cáo hoặc đọc lại có chủ đích. |
| Model chọn | Preprocessing/cột đã fit, model và các tham số | Joblib hoặc định dạng phù hợp, cùng thư mục với cấu hình đã chọn. Không buộc giữ model của mọi cấu hình bị loại. |
| Chốt trước test | Cấu hình/ngưỡng/feature policy và đường dẫn đúng model đã chọn | Một `frozen_config.json` cho các detector/seed đã chọn, kèm lý do chọn ngắn hoặc tham chiếu dòng validation. |
| Đánh giá | Mọi mốc score/valid/reason/alarm; episode; metric tổng hợp và từng sự cố | `scores.parquet`, `episodes.csv`, bảng summary/events; `metrics.json` chỉ khi hữu ích cho chương trình đọc. Không sao chép cùng số liệu sang nhiều định dạng bắt buộc. |
| Diễn giải | EDA, hình/bảng kết quả, case study, giới hạn | Notebook hoặc Markdown và ảnh; không cần sample/case manifest riêng. |

Các tên file gợi ý cho phần chưa triển khai có thể gộp; nội dung cần thiết và mối liên hệ giữa cấu hình/model/kết quả phải rõ. Nhãn không nằm trong ma trận feature đưa vào detector. Metadata có thể đi cùng bảng để join theo timestamp, không dựa vào thứ tự dòng ngầm định.

## Metadata đủ để chạy lại

`run_manifest.json` chỉ cần thông tin dùng được: raw manifest/version và CSV checksum; config thực dùng (hoặc snapshot); seed; Git commit; phiên bản Python/dependencies (hoặc lockfile); tên cấu hình và đường dẫn kết quả. Config hash hiện có có thể ghi thêm. Ghi một lần cho cả bộ thí nghiệm, không lặp ở mỗi cửa sổ hay stage.

Với kết quả cuối, chạy trên source đã commit để commit nhận diện đúng code. Khi thử nghiệm còn thay đổi chưa commit, ghi `dirty: true`; chưa gọi đó là bản tái lập cuối. Không cần cơ chế tự snapshot/hash toàn bộ source. Timing fit/score nằm trong bảng thí nghiệm; ghi máy và n_jobs một lần khi so tốc độ. Không bắt buộc thu CPU/RAM sử dụng, telemetry hoặc lý do null cho mọi thông số chưa đo.

## Chốt lựa chọn và dùng test

`frozen_config.json` ghi feature_set/W, cột/thứ tự đã giữ, đường dẫn preprocessing/model, seed, q/tau, split/quality/reference/merge policy và raw version. Đây là bản ghi quyết định trước test; không phải hệ thống khóa file hoặc approval workflow.

Khi chạy test, nạp chính các model/preprocessing đã chọn; kiểm tra file tồn tại, tên/thứ tự cột, tham số/seed tương ứng và tau hữu hạn. Nếu thiếu/sai đầu vào thì dừng rõ lý do. Không tự tìm model mới nhất, tự fit lại hoặc tự hiệu chỉnh ngưỡng. Không cần checksum chuỗi artifact; model và cấu hình được lưu cùng bộ kết quả, đọc bằng đường dẫn tường minh. Chỉ thêm kiểm tra hash khác khi có nhu cầu thực tế.

Model không nhận nhãn test; chỉ ghép nhãn sau score. Giữ model/ngưỡng đã chốt khi báo test; sửa nhãn test không được đổi feature, score hoặc lựa chọn. Thêm phân tích sau khi xem test phải ghi là thăm dò.

## Mask, nguồn cửa sổ và kết quả thiếu

- `split`, `segment_id`, `valid`, `reason`, `is_reference` có thể là cột trong bảng feature/score. Common mask lấy giao timestamp hợp lệ của các cấu hình đang so và lưu policy/danh sách cấu hình cùng số đếm. Không cần `mask_id` dạng hash hoặc tệp riêng mỗi mask.
- Giữ biên cửa sổ, source_min/max và kết quả kiểm tra nguồn có giao sự cố/split. Khi fill, giữ nguồn gốc trong quá trình tính để kiểm tra đúng; không bắt buộc xuất danh sách mọi raw_row_id cho từng feature/cửa sổ. Dùng fixture kiểm tra trực tiếp nguồn được dùng; raw và code đủ để tính lại.
- Invalid vẫn hiện trên lưới mốc, score/alarm null; lý do ngắn theo thứ tự ưu tiên cố định. Coverage dùng số quan sát thật trước fill. Metric lưu mẫu số, số đếm và N/A có lý do; JSON không dùng NaN/Infinity.
- Phân biệt reference mask dùng fit/calibration và evaluation mask dùng metric. Những quy tắc này bảo vệ kết quả ML, không được bỏ để giảm số cột.

## Cache và log

Mặc định không có cache tự động giữa các lần chạy. Trong một lần chạy, fit/score mỗi cấu hình một lần rồi dùng lại score để quét q/merge. Nếu đọc lại score đã lưu, người chạy chỉ rõ thư mục/config và đối chiếu metadata; không tự suy cache hợp lệ chỉ từ tên file. Chỉ xây cache khi đo được nút thắt thời gian đáng kể.

Console chỉ cần tác vụ, số mốc hợp lệ, thời gian và nơi lưu kết quả; lỗi có nguyên nhân. Thống kê chất lượng nằm trong data card, kết quả ML nằm trong bảng. Không log từng dòng/cửa sổ, cache hit/miss hay hash mọi artifact. Debug chi tiết là tùy chọn khi điều tra lỗi.
