# PB04 Bảng sự cố và quy tắc nhãn

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M1 |
| Phụ thuộc | [PB02](PB02-data-ingestion.md) |
| Nguồn | Backlog PB04; pipeline chương 3–4 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người đánh giá cần một bảng sự cố có nguồn và hai phép kiểm tra tách biệt: nhãn tại mốc chấm và giao dữ liệu của cả cửa sổ với sự cố.

## Phạm vi và ranh giới

Chuẩn hóa E1–E4 và logic nhãn/giao khoảng. Không tự đổi ngày sự cố từ ghi chú bảo trì mâu thuẫn, không đưa nhãn vào feature.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Nguồn sự cố và quy ước timestamp | Dùng cùng đồng hồ gốc với cảm biến; bảo lưu ghi chú gốc. |
| Đầu ra | events.csv | event_id/start/end/failure_type/source/source_note/confidence_note. |
| Bàn giao | Logic nhãn tại mốc và kiểm tra nguồn giao sự cố | PB05/PB07 lọc reference; PB10/PB11 ghép và đánh giá. |

## Yêu cầu chức năng

- **PB04-FR01:** Ghi E1: 2020-04-18 00:00–23:59; E2: 2020-05-29 23:30–2020-05-30 06:00; E3: 2020-06-05 10:00–2020-06-07 14:30; E4: 2020-07-15 14:30–19:00; kiểm tra start<=end, ID không trùng.
- **PB04-FR02:** Khoảng sự cố đóng cả hai đầu, giây=00 khi nguồn chỉ ghi đến phút. Lưu provenance và ghi chú mâu thuẫn nguyên nghĩa, không dùng chúng để tự dịch mốc.
- **PB04-FR03:** Nhãn y(t)=1 nếu window_end thuộc ít nhất một sự cố, còn lại là 0 đối với mốc hợp lệ; invalid không tham gia metric. Trả danh sách event_id nếu có nhiều giao.
- **PB04-FR04:** Kiểm tra reference dựa trên mọi timestamp nguồn thực sự dùng trong cửa sổ, kể cả timestamp gốc của fill; nhãn tại window_end không thay cho phép kiểm tra này.
- **PB04-FR05:** Tách nhãn đối chiếu khỏi feature matrix và bước score; label 0 chỉ có nghĩa ngoài các khoảng đã báo cáo.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Chỉ áp dụng quy ước timestamp nhất quán; không tự chuyển timezone một phía.
- Có kiểm tra sự cố không có mốc hợp lệ để PB11 báo không đánh giá được.

## Tiêu chí nghiệm thu

- [x] **PB04-AC01** (FR01, FR02, FR03): **Khi** chấm ngay trước, đúng start, đúng end và ngay sau end E1, **thì** nhãn lần lượt 0/1/1/0 theo độ chính xác timestamp.
- [x] **PB04-AC02** (FR03, FR04): **Khi** cửa sổ kết thúc sau E1 nhưng còn dùng quan sát trong E1, **thì** y(window_end)=0 nhưng bị loại khỏi reference.
- [x] **PB04-AC03** (FR04): **Khi** giá trị được fill có timestamp gốc nằm trong sự cố ngoài biên danh nghĩa cửa sổ, **thì** vẫn phát hiện giao nguồn với sự cố.
- [x] **PB04-AC04** (FR02, FR05): **Khi** nguồn có ghi chú bảo trì lệch tháng, **thì** mốc chuẩn không tự đổi; ghi chú được lưu và feature không chứa nhãn.

## Rủi ro và quyết định cần ghi nhận

- Nhầm end ghi 23:59 thành 23:59:59 sẽ đổi nhãn: giữ giây=00 theo đặc tả.
- Dùng nhãn pointwise để lọc reference bỏ sót phần đuôi cửa sổ sau sự cố: kiểm tra nguồn thực dùng trong lúc tạo feature. Không cần xuất danh sách nguồn riêng cho từng cửa sổ.

## Kết quả cần xem

- [x] Đính kèm events.csv, nguồn/ghi chú và các test biên sự cố, đặc biệt cửa sổ còn giao sau end.

## Ghi chú thực hiện — 2026-10-25

Branch: `feat/pb04-event-labels`, tách từ trạng thái PB03 hiện tại. Trạng thái **In review**; chưa commit, tạo PR hoặc merge. Không thêm dependency hay CLI riêng: lệnh `audit` hiện có xuất thêm `events.csv`, metadata nguồn/coverage trong cleaned và ghi chú trong data card của cùng bộ dữ liệu.

Đã triển khai [events.py](../../src/metropt3/events.py): bảng bốn sự cố có provenance, kiểm tra schema/biên/ID, nhãn pointwise nullable, kiểm tra mọi nguồn thực dùng gồm fill origin, và coverage giữ cả sự cố không có mốc hợp lệ. Nhãn nằm ở bảng trả về riêng, không thêm vào cleaned hoặc đầu vào detector. Xem [hướng dẫn sử dụng](../../README.md#bảng-sự-cố-và-nhãn-pb04) và [hợp đồng](../artifact_contracts.md#bảng-sự-cố-và-nhãn-pb04).

| AC | Bằng chứng trong [test_events.py](../../tests/test_events.py) |
| --- | --- |
| AC01 | `test_closed_boundaries_at_nanosecond_precision` kiểm tra trước/start/end/sau cho cả E1–E4; `test_e1_end_is_not_extended_to_end_of_minute` giữ end=23:59:00. |
| AC02 | `test_zero_point_label_does_not_make_post_event_window_a_reference`: label=0 sau E1 nhưng nguồn còn giao E1 nên không được là reference. |
| AC03 | `test_fill_origin_outside_nominal_window_still_excludes_reference`: thời điểm fill ngoài sự cố, nguồn gốc thuộc E1 và nằm ngoài cửa sổ vẫn bị phát hiện. |
| AC04 | `test_reported_intervals_and_provenance`, `test_events_csv_roundtrip_and_review_copy_match`, `test_labels_are_separate_and_never_mutate_sensor_features`: giữ ghi chú 30Apr/mốc tháng 5, CSV đọc lại đúng và input feature không bị thêm nhãn. |

Các kiểm tra bổ sung bao gồm nhiều sự cố chồng lấp, timestamp có timezone, ID trùng, biên đảo, thiếu mốc, mask sai index/kiểu, invalid label null và sự cố không có mốc đánh giá. [Test tích hợp audit](../../tests/test_audit.py) kiểm tra CSV/metadata liên kết manifest cụ thể, raw nguyên byte/mtime và lỗi ghi events không công bố kết quả dở.

Đã chạy:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_tmp/pb04-full -o cache_dir=.pytest_tmp/pb04-full-cache
.\.venv\Scripts\python.exe -m pip check
git diff --check
.\.venv\Scripts\python.exe -m metropt3 audit --config configs/base.yaml --manifest data/raw/sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55/raw_manifest.json --output data/interim/pb04-rerun
```

Kết quả: **229 passed**, `pip check` đạt. Chạy tích hợp qua API `audit_dataset` trên dữ liệu thật ở `data/interim/pb04-verified-20261025/`: **1.516.948 cleaned/valid**, 4 sự cố, **29.954 dòng trong sự cố** và **1.486.994 dòng ngoài báo cáo**. Số dòng hợp lệ theo E1/E2/E3/E4 lần lượt **8.657 / 2.360 / 17.315 / 1.622**. Đây là nhãn trên dòng cleaned để xác minh PB04, chưa phải số cửa sổ hợp lệ của benchmark. PB11 phải tính lại coverage/evaluable trên score timestamps/common mask sau PB05/PB07.

[events.csv mẫu](../examples/pb04/events.csv) và [validation.json](../examples/pb04/validation.json) được giữ để review; CSV trùng byte với đầu ra thật. Kiểm tra toàn bộ checksum và mtime CSV/PDF/manifest raw trước/sau không thay đổi. Nguồn đối chiếu là bảng Failure Information trên [UCI MetroPT-3](https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset), kiểm tra ngày 2026-10-25. Nguồn lặp Nr. #1 tại E2; local ID E1–E4 theo thứ tự dòng. Không tự sửa ghi chú bảo trì hoặc suy ra timezone/nhãn bình thường tuyệt đối.
