# PB03 Audit và chia đoạn dữ liệu

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M1 |
| Phụ thuộc | [PB02](PB02-data-ingestion.md) |
| Nguồn | Backlog PB03; pipeline chương 2–3 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người xây feature cần dữ liệu đã kiểm tra chất lượng, nhịp nền và các đoạn liên tục để phân biệt không có quan sát với quan sát bình thường.

## Phạm vi và ranh giới

Parse, audit, xử lý duplicate xác định được và đánh dấu chất lượng. Không loại outlier bằng z-score/IQR hoặc dùng phân phối test để thiết kế feature.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Raw + raw_manifest.json + train_end | Nguồn đúng checksum; ranh giới lịch đã có trong config. |
| Đầu ra | Cleaned rows với quality flags; bảng lỗi/gap khi cần xem chi tiết | Giữ raw_row_id, flags, duplicate counts và segment_id. |
| Đầu ra | Một data_card.md gồm thống kê chất lượng và split | Thời gian, missing, nhịp và delta0/gap_break đã fit từ timestamp train. |

## Yêu cầu chức năng

- **PB03-FR01:** Parse timestamp theo định dạng quan sát được, giữ đồng hồ gốc không múi giờ; numeric không parse được có cờ invalid_numeric. Lưu dòng không parse được để kiểm tra thay vì âm thầm mất dấu.
- **PB03-FR02:** Ổn định thứ tự theo timestamp/raw_row_id; gộp dòng trùng hoàn toàn và ghi số bản; timestamp trùng nhưng cảm biến khác nhau bị loại khỏi dữ liệu hợp lệ, có bảng xung đột.
- **PB03-FR03:** Báo schema/types, missing, infinity, domain digital, số giá trị duy nhất, thời gian đầu/cuối, phân bố delta và gaps; tách thiếu ô với thiếu mốc thời gian. Thống kê phục vụ chọn mô hình chỉ trên train.
- **PB03-FR04:** Fit delta0 là mode delta timestamp dương trên phần train đã khai báo, lưu median/quantile; gap_break=3×delta0, gap chỉ khi delta > gap_break, tạo segment_id mới.
- **PB03-FR05:** Giữ giá trị cực đoan hợp lệ và phần dữ liệu 01/09/2020 nếu tồn tại; không tự áp luật áp suất không âm. Ghi số dòng và lý do làm sạch trong data card; giữ raw_row_id để xem lại raw, không tạo nhật ký mỗi thao tác.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không đủ delta train để fit thì dừng với lý do, không lấy nhịp validation/test thay thế.
- Nếu mode bị hòa, ghi một quy tắc chọn cố định trong artifact; đây là quyết định triển khai cần ghi, không suy đoán nhịp.

## Tiêu chí nghiệm thu

- [x] **PB03-AC01** (FR01, FR02): **Khi** fixture có timestamp lỗi, numeric lỗi, exact duplicate và duplicate xung đột, **thì** mỗi loại có flag/bảng/số đếm đúng; raw_row_id truy ngược được.
- [x] **PB03-AC02** (FR03, FR04): **Khi** fixture có delta train phổ biến 10 giây, một gap 30 và một gap 31 giây, **thì** delta0=10, gap_break=30; chỉ gap 31 tạo đoạn mới.
- [x] **PB03-AC03** (FR04): **Khi** thay timestamp của phần test mà giữ train, **thì** delta0 và gap_break đã fit không đổi.
- [x] **PB03-AC04** (FR05): **Khi** dữ liệu có giá trị cực đoan và các dòng ngày 01/09, **thì** giữ chúng nếu không vi phạm quy tắc chất lượng đã xác nhận.

## Rủi ro và quyết định cần ghi nhận

- Dùng mode từ toàn file làm leakage: fit nhịp trên timestamp train rồi đóng băng.
- Loại duplicate nhầm tín hiệu ổn định: chỉ gộp bản trùng hoàn toàn cùng timestamp.

## Kết quả cần xem

- [x] Cung cấp một data card có counts trước/sau và tóm tắt gap; bảng chi tiết chỉ khi cần phân tích. Kiểm tra fixture lỗi chất lượng.

## Ghi chú thực hiện — 2026-10-25

Branch: `feat/pb03-data-quality-audit`. Trạng thái **In review**; chưa merge/đóng Done hoặc tạo PR. Đã thêm [audit.py](../../src/metropt3/audit.py), lệnh `metropt3 audit`, [test_audit.py](../../tests/test_audit.py), [hướng dẫn chạy](../../README.md#audit-chất-lượng-và-chia-đoạn-pb03) và [hợp đồng cleaned](../artifact_contracts.md#cleaned-và-data-card-pb03). Không thêm dependency.

| AC | Bằng chứng kiểm tra |
| --- | --- |
| AC01 | `test_quality_flags_duplicates_conflicts_and_raw_lineage`: flags/counts đúng, duplicate có ánh xạ đại diện, conflict giữ mọi raw row; `test_invalid_sensor_tokens_do_not_hide_conflicting_observations`: không gộp hai lỗi khác nhau thành NaN. `test_cli_real_io_parquet_metadata_and_immutable_raw` và `test_conflicting_raw_rows_survive_parquet_roundtrip` kiểm tra ghi/đọc bảng, metadata và raw nguyên byte/mtime trên ZIP synthetic. |
| AC02 | `test_strict_gap_boundary_and_stable_timestamp_order`: delta0=10, gap_break=30, gap 30 không ngắt và 31 ngắt; thứ tự timestamp/raw_row_id ổn định. |
| AC03 | `test_test_timestamp_and_sensor_distribution_cannot_change_train_fit`: thay timestamp/phân phối test không đổi toàn bộ cadence và thống kê sensor train. `test_exclusive_split_boundaries_and_cross_boundary_delta_not_fit`: không fit delta giao biên train. |
| AC04 | `test_extremes_negative_pressure_and_september_1_survive`: giữ analog âm, cực đoan và 01/09. Chạy trên raw thật giữ đủ **530 dòng 2020-09-01**. |

Quyết định triển khai: exact duplicate so timestamp và nguyên token sensor, bỏ index provenance; đại diện có ID nhỏ nhất. Dòng lỗi sensor được giữ với cờ và `valid=false`, timestamp lỗi/conflict được lưu riêng. Tối thiểu để fit là một delta dương từ hai timestamp train khác nhau; mode hòa chọn nhỏ nhất. `quality.gap_multiplier` phải bằng 3 khi audit. Segment không reset theo split; downstream phải xét cả hai biên. Các lựa chọn này được ghi trong data card/metadata, không suy nhịp từ validation/test.

Đã chạy:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_tmp/pb03-final -o cache_dir=.pytest_tmp/pb03-cache
.\.venv\Scripts\python.exe -m pip check
git diff --check
.\.venv\Scripts\python.exe -m metropt3 audit --config configs/base.yaml --manifest data/raw/sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55/raw_manifest.json --output data/interim/pb03-verified
```

Kết quả: **197 passed** (24 test PB03); `pip check` không có dependency lỗi; `git diff --check` sạch. Các test PB03 còn kiểm tra thiếu train không fallback, định dạng timestamp tường minh, raw sai checksum/manifest, từ chối ghi đè và lỗi ghi không công bố kết quả dở.

Chạy trên dữ liệu thật với CSV SHA-256 `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`: **1.516.948 raw → 1.516.948 cleaned/valid**, không có lỗi sensor/timestamp, duplicate hoặc conflict. Phạm vi **2020-02-01 00:00:00 → 2020-09-01 03:59:50**; **delta0=10 giây**, **gap_break=30 giây**, **331 gap / 332 segment**. Train/validation/test lần lượt **214.850 / 429.182 / 872.916 dòng**. Đây là thống kê lịch, chưa nghiệm thu mask/purge PB05.

Đầu ra đầy đủ ở `data/interim/pb03-verified/` (gitignore): cleaned, gaps và data card; các bảng lỗi/duplicate không sinh vì rỗng. [Bản sao data card thực tế](../examples/pb03/data_card.md) được giữ trong repo để review. Raw/manifest PB02 không bị sửa.

### Sửa P2 sau review — 2026-10-25

Regex cũ chỉ kiểm tra hình dạng timestamp; pandas tự chuẩn hóa giây 60/61 sang phút tiếp theo. Khi có dòng đúng tại thời điểm sau chuẩn hóa nhưng sensor khác, hai dòng bị loại do conflict giả và dòng sai không vào issues. Regression test `test_out_of_range_clock_cannot_normalize_into_valid_row_conflict` đã tái hiện trên code cũ: **2 failed, 2 passed**, với bốn trường hợp giây 60, giây 61, phút 60 và giờ 24.

Đã sửa: kiểm tra giờ trong `00–23`, phút/giây trong `00–59` bằng regex trước khi gọi `pd.to_datetime`; tính hợp lệ của ngày/tháng vẫn do parser kiểm tra. Dòng sai giữ nguyên timestamp/raw_row_id trong issues, có `invalid_timestamp=true` và `parsed_timestamp=NaT`; dòng đúng được giữ, không sinh duplicate/conflict giả.

Kiểm tra sau sửa: **201 passed**; `pip check` đạt và `git diff --check` sạch. Chạy lại bằng `--output data/interim/pb03-p2-fixed-20261025` giữ nguyên **1.516.948 cleaned/valid**, **delta0=10 giây**, **gap_break=30 giây**, **331 gap / 332 segment**, đủ **530 dòng 01/09**; data card trùng byte với bản trong repo, checksum CSV/PDF raw không đổi. PB03 tiếp tục **In review**, chưa nghiệm thu/đóng Done.
