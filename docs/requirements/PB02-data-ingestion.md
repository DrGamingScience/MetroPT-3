# PB02 Nhập dữ liệu và khóa nguồn

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | S — tương đối, chưa quy đổi ngày |
| Mốc | M1 |
| Branch | `feat/pb02-data-ingestion` |
| Phụ thuộc | [PB01](PB01-project-scaffold.md) |
| Nguồn | Backlog PB02; pipeline chương 2 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Phạm vi sau rà soát 2026-10-24

Giữ implementation và bằng chứng đã có; không yêu cầu viết lại config/ingest. Các quy ước run/manifest cho bước ML tương lai theo [quy ước đầu ra đã tinh gọn](../artifact_contracts.md); ghi chú triển khai phía dưới là lịch sử. Không mở rộng chống sửa metadata, cạnh tranh nhiều tiến trình hoặc log nếu không có lỗi ảnh hưởng công việc thực tế.

## Mục tiêu và nhu cầu

Người chạy thí nghiệm cần biết chính xác dữ liệu gốc nào tạo ra kết quả, đồng thời có thể nhập lại cùng nguồn mà không làm thay đổi raw.

## Phạm vi và ranh giới

Tải/nhập gói MetroPT-3 và xác minh nguồn, tệp, header. Chưa sửa dữ liệu, deduplicate hay phân tích giá trị cảm biến.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | URL gói chính thức hoặc đường dẫn gói local | Ghi rõ nguồn; không suy ra nguồn từ tên file đơn thuần. |
| Đầu ra | data/raw/ và raw_manifest.json | Giữ CSV/PDF gốc; URL, ngày tải, file, byte, SHA-256, schema version. |
| Bàn giao | Raw cho PB03/PB04 | Giữ cột gốc, quy ước raw_row_id và dataset version. |

## Yêu cầu chức năng

- **PB02-FR01:** Hỗ trợ nhập gói chính thức hoặc gói local; phát hiện tải dở, ZIP lỗi, thiếu CSV hoặc thiếu PDF mô tả trước khi công bố ingest thành công.
- **PB02-FR02:** Kiểm tra header gồm timestamp, 7 analog và 8 digital; analog: TP2/TP3/H1/DV_pressure/Reservoirs/Oil_temperature/Motor_current; digital: COMP/DV_eletric/Towers/MPG/LPS/Pressure_switch/Oil_level/Caudal_impulses.
- **PB02-FR03:** Giữ tên cột và cột index gốc để truy vết; timestamp/index không được tự xem là feature. Chốt quy ước raw_row_id ổn định theo vị trí dòng gốc.
- **PB02-FR04:** Tính checksum/byte từ tệp thực nhận và ghi manifest. SHA-256 tham chiếu của CSV là `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`; khác checksum tạo phiên bản mới cần audit lại.
- **PB02-FR05:** Nhập lại đúng nội dung là thao tác idempotent; không ghi đè raw đã khóa, không nhân đôi phiên bản, không lấy số dòng công bố làm số đo thực tế.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Tải/ghi qua tệp tạm rồi xác minh trước khi công bố manifest hoàn tất.
- Manifest dùng checksum của dữ liệu, không chỉ thời gian sửa file; lỗi không để lại trạng thái ready giả.

## Tiêu chí nghiệm thu

- [x] **PB02-AC01** (FR01): **Khi** gói bị cắt hoặc thiếu CSV/PDF, **thì** ingest thất bại rõ lý do và không phát hành manifest thành công.
- [x] **PB02-AC02** (FR02, FR03): **Khi** header có DV_eletric và Towers đúng tên, **thì** giữ nguyên tên; thiếu sensor hoặc đổi tên ngoài ánh xạ được báo rõ.
- [x] **PB02-AC03** (FR04): **Khi** nhập một CSV có checksum khác bản tham chiếu, **thì** lưu version mới và yêu cầu audit; raw cũ giữ nguyên.
- [x] **PB02-AC04** (FR05): **Khi** ingest cùng một gói hai lần, **thì** version/checksum raw không đổi và không sinh bản sao dữ liệu.

## Checklist triển khai

- [x] Triển khai `ingest.py`, nhận gói tải chính thức hoặc đường dẫn local, giữ nguyên CSV và PDF mô tả trong `data/raw/`.
- [x] Lưu `raw_manifest.json`: URL, ngày tải, tên file, byte, SHA-256, schema version; giữ `raw_row_id` và tên cột gốc.
- [x] Kiểm tra header 15 cảm biến, `timestamp` và cột chỉ mục; giữ chính tả `DV_eletric`, `Towers`; index không vào feature.
- [x] Đối chiếu SHA-256 CSV mà pipeline đã ghi: `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`. Nếu khác, tạo phiên bản dữ liệu mới và yêu cầu audit lại trong luồng chạy.

## Rủi ro và quyết định cần ghi nhận

- Tên file giống nhau không bảo đảm cùng dataset: dùng checksum làm bằng chứng.
- Mạng ngắt có thể để lại tệp dở: phân biệt trạng thái tạm và trạng thái đã xác minh.

## Bằng chứng để đóng PB

- [x] Đính kèm manifest mẫu, kết quả hai lần ingest và ví dụ xử lý checksum/header lỗi.
- [x] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Ngày triển khai: **2026-10-24**. Branch: `feat/pb02-data-ingestion`. Trạng thái **In review**, chưa merge/đóng Done và chưa tạo PR.

Đã triển khai [ingest.py](../../src/metropt3/ingest.py), lệnh `metropt3 ingest`, [test_ingest.py](../../tests/test_ingest.py), hướng dẫn trong [README](../../README.md#nhập-và-khóa-dữ-liệu-pb02) và [hợp đồng raw v1](../artifact_contracts.md#raw-manifest-pb02). Không thêm dependency.

| AC | Kết quả và bằng chứng |
| --- | --- |
| AC01 | Đạt: test `test_invalid_package_never_publishes_manifest`, `test_corrupt_zip_fails_without_ready_state`, `test_incomplete_csv_fails`, `test_url_download_verifies_transport_and_preserves_url`, `test_publish_failure_removes_staging_and_leaves_previous_version`. Thiếu CSV/PDF, CRC lỗi, ZIP cắt, tải dở và publish lỗi đều không công bố version mới. |
| AC02 | Đạt: test `test_preserves_bytes_header_and_records_measured_provenance`, `test_invalid_header_reports_original_names`, `test_explicit_index_headers_are_preserved`, `test_row_id_uses_csv_records_in_original_order`. Giữ nguyên spelling/header/index và byte, không kiểm tra/sửa giá trị cảm biến. |
| AC03 | Đạt: test `test_changed_csv_creates_auditable_version_without_touching_old`, `test_changed_description_versions_the_source_package`, `test_matching_reference_does_not_request_checksum_audit`. CSV synthetic khác tham chiếu tạo version mới với lý do `csv_checksum_differs_from_reference`; raw cũ không đổi. |
| AC04 | Đạt: test `test_idempotence_preserves_files_manifest_and_timestamp`, `test_concurrent_same_package_publishes_one_version`, `test_locked_version_tampering_is_not_overwritten`. Bằng chứng nhập lại dữ liệu UCI thật được lưu tại [validation.json](../examples/pb02/validation.json). |

Lệnh kiểm tra trên Windows (thư mục tạm nằm trong workspace):

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_tmp/pb02-check -o cache_dir=.pytest_tmp/cache
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

Kết quả: **124 passed**, `pip check`: **No broken requirements found**, `git diff --check` sạch. Bộ test chạy bằng ZIP synthetic, không cần mạng. Test CLI kiểm tra cả trả JSON thành công, reuse, và lỗi mã 2 không traceback.

Gói [UCI chính thức](https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset) đã được tải qua CLI; đo được CSV **218.300.507 byte**, **1.516.948 record**, SHA-256 khớp tham chiếu. Hai lần nhập lại cùng CSV/PDF (đóng gói lại, giữ nguyên tên thành viên ZIP) đều trả `reused: true`, manifest không đổi và chỉ có một thư mục version. [Manifest mẫu thực tế](../examples/pb02/raw_manifest.json) và [kết quả nhập lại](../examples/pb02/validation.json) là bằng chứng; dữ liệu raw lớn nằm trong `data/raw/`, được gitignore.

Quyết định bổ sung:

- Mỗi version có manifest riêng tại `data/raw/sha256-<hash>/raw_manifest.json`; CLI trả đường dẫn chính xác, không chọn version mới nhất ngầm định. Version bao gồm cả CSV/PDF, tên file và thành viên ZIP; metadata đóng gói/nguồn/ngày tải không đổi định danh.
- Local không biết URL thì lưu null và file URI; `--source-url` chỉ ghi nguồn người dùng khai báo, không biến gói local thành nguồn đã được chứng thực.
- Chấp nhận đúng một index nguyên gốc trong `""`, `index`, `Unnamed: 0`. `raw_row_id` là vị trí CSV record bắt đầu từ 0, theo version; chưa thêm cột vào raw để giữ nguyên byte.
- `completed` xác nhận nhập/xác minh gói, không thay audit PB03. Checksum khác tham chiếu được nhận vào version riêng và trả `audit_required: true` cùng lý do; không tự chấp thuận để huấn luyện.
- Nhập lại xác minh manifest/file đã khóa; dữ liệu bị thay đổi hoặc mất sẽ báo lỗi thay vì sửa. Xử lý hai tiến trình cùng nhập một gói được kiểm thử; rename thư mục staging là điểm công bố version.

Bước tiếp theo: review/merge Pb02, cập nhật PR/ngày xong trong bảng theo dõi; PB03 audit chất lượng và PB04 đọc sự cố theo manifest cụ thể.

### Sửa P2 sau audit commit `ff662ae` — 2026-10-24

Audit phát hiện `_verify_locked()` bỏ qua `source`, `downloaded_at`, `package`. Đã tái hiện bằng ba regression test xóa lần lượt từng trường: cả ba thất bại trên code cũ vì ingest không báo lỗi.

Đã sửa: bắt buộc đầy đủ schema manifest đã khóa; kiểm tra trường con, kiểu và giá trị hợp lệ của thông tin nguồn, timestamp UTC, byte/SHA-256 ZIP gốc. Metadata lần đầu được xác minh độc lập, không đối chiếu với lần nhập mới. Đối chiếu nội dung bằng kiểu JSON để chặn cả các trường hợp bool/int/float bị thay thế lẫn nhau. Manifest lỗi trả mã 2 qua CLI và không bị tự sửa.

Bằng chứng bổ sung trong [test_ingest.py](../../tests/test_ingest.py): `test_locked_manifest_requires_provenance`, `test_locked_manifest_requires_nested_provenance`, `test_locked_manifest_rejects_invalid_provenance`, `test_locked_url_receipt_requires_http_urls`, `test_locked_manifest_rejects_nested_schema_type_changes`, `test_cli_rejects_missing_locked_provenance`. Test `test_reimport_keeps_original_receipt_when_source_and_zip_change` xác nhận nguồn URL/local, thời điểm và gói ZIP mới khác vẫn reuse hợp lệ, giữ nguyên manifest đầu tiên.

Kiểm tra sau sửa: **174 passed**, không cảnh báo pytest cache khi dùng `-o cache_dir=.pytest_tmp/pb02-p2-cache`; `pip check` đạt và `git diff --check` sạch. Đã nhập lại CSV/PDF thật từ ZIP đóng gói lại: `reused: true`, một version duy nhất, toàn bộ byte/checksum/mtime raw và manifest giữ nguyên; thông tin nguồn đầu tiên vẫn là URL UCI. Xem [p2-validation.json](../examples/pb02/p2-validation.json). Manifest mẫu và raw thật không bị sửa; trạng thái tiếp tục **In review**.
