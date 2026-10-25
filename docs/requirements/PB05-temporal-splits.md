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

- [x] **PB05-AC01** (FR01): **Khi** xét timestamp đúng 2020-03-01 và 2020-05-01, **thì** lần lượt vào validation và test, không trùng train.
- [x] **PB05-AC02** (FR02, FR03): **Khi** split/segment bắt đầu đúng 00:00 và warm-up=930 giây, **thì** 00:15 chưa đủ; 00:16 mới đủ warm-up, vẫn phải qua kiểm tra chất lượng.
- [x] **PB05-AC03** (FR02, FR04): **Khi** kiểm tra lineage fixture của hai split, **thì** không chung raw_row_id hoặc fill origin; reference và evaluation được phân biệt đúng.
- [x] **PB05-AC04** (FR05): **Khi** một sự cố không có mốc hợp lệ, **thì** giữ nó trong tổng nguồn và ghi không đánh giá được, không xóa khỏi báo cáo.

## Rủi ro và quyết định cần ghi nhận

- Cho W=1 dùng warm-up ngắn hơn W=15 tạo so sánh lệch: áp dụng warm-up chung.
- Chỉ dùng biên cửa sổ để kiểm tra purge có thể bỏ sót nguồn fill: kiểm tra cả lineage.

## Kết quả cần xem

- [x] Cung cấp số mốc theo split/reason và kiểm tra ranh giới/nguồn dùng chung với PB07; không bắt buộc splits.json riêng.

## Triển khai và bằng chứng — 2026-10-25

Branch `feat/pb05-temporal-splits`, tạo từ branch PB04 và giữ nguyên các thay đổi PB04 đang có. Trạng thái **In review**, chưa commit/PR/merge.

[temporal.py](../../src/metropt3/temporal.py) cung cấp `split_timestamps`, `build_time_grid`, `apply_window_masks` và `summarize_time_grid`. Tích hợp vào lệnh `audit` hiện có: xuất `minute_grid.parquet`, tóm tắt vào data card và metadata; không thêm CLI/dependency. PB07 dùng cùng API để kiểm tra mọi raw/fill origin và kết hợp quality mask trong lúc tạo feature; PB05 không tạo F35 hay tự triển khai fill.

Phân biệt hai mức: `temporal_valid` chỉ xét thời gian/warm-up/gap; `valid` cuối cùng chỉ xuất khi caller truyền đầy đủ lineage và quality decision. Reference/evaluation mask được kiểm thử bằng fixture, chưa báo số reference thực tế trước khi PB07 có feature. Warm-up bắt đầu từ quan sát thật đầu tiên của từng `(split, segment_id)`, không từ một quan sát tương lai hoặc trước split. Mọi phút trong phạm vi dữ liệu được giữ; thiếu dữ liệu có `gap`, đoạn mới có `warmup`. Thứ tự loại khi finalize: gap → warmup → source_split → source_segment → future_source → outside_window → stale_fill → missing_source → quality (hoặc lý do cụ thể của PB07).

| AC | Bằng chứng trong [test_temporal.py](../../tests/test_temporal.py) |
| --- | --- |
| AC01 | `test_exact_split_boundaries_are_exclusive`, `test_split_resets_warmup_even_without_segment_break`: hai biên đúng split, reset dù segment PB03 không đổi. |
| AC02 | `test_warmup_930_seconds_rounds_up_to_minute_and_restarts_after_gap`, `test_warmup_includes_exact_930_seconds`, `test_all_window_lengths_have_identical_temporal_mask`: 00:15/00:16, biên đúng 930 giây, W=1/5/15 cùng mask. |
| AC03 | `test_lineage_rejects_cross_split_raw_and_fill_and_keeps_train_sources_disjoint`, `test_fill_origin_must_share_segment`, `test_reference_excludes_actual_fill_event_outside_nominal_window`: ID nguồn giữa split không dùng chung; fill qua biên bị loại; reference/evaluation khác nhau dù point label=0. |
| AC04 | `test_all_events_remain_in_summary_even_without_valid_point`, `test_final_coverage_counts_positive_points_and_retains_zero_coverage_events`: giữ đủ bốn sự cố, count=0/first=null/evaluable=false khi không có mốc. |

Kiểm thử thêm: nguồn tương lai, cửa sổ mở trái/đóng phải, tuổi fill 30/31 giây, gap >30 giây, không suy reference bằng min/max, test không làm reference, quality/index/ID sai, lưới rỗng, Parquet roundtrip, không thay mốc quá khứ khi sửa tương lai. Test tích hợp audit kiểm tra raw không đổi, grid/cleaned cùng dataset version và không công bố kết quả dở khi lỗi ghi.

Đã chạy:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
git diff --check
.\.venv\Scripts\python.exe -m metropt3 audit --config configs/base.yaml --manifest data/raw/sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55/raw_manifest.json --output data/interim/pb05-verified-20261025
```

Kết quả kiểm tra: **254 passed**, `pip check` và `git diff --check` đạt. Dựng lại lưới từ cleaned đã lưu khớp từng dòng với Parquet xuất từ audit, metadata/version và thống kê theo split đối chiếu đúng.

Chạy dữ liệu thật: **1.516.948 cleaned rows → 306.960 mốc phút**, **247.909 mốc đủ điều kiện thời gian**, **54.403 gap**, **4.648 warm-up**. Đây là coverage thời gian; chưa phải số feature/score hợp lệ của PB07/PB11.

| Split | Mốc dự kiến | Đủ điều kiện thời gian | Gap | Warm-up | Mốc dương đủ điều kiện |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 41.760 | 35.019 | 6.247 | 494 | 0 |
| Validation | 87.840 | 69.983 | 16.509 | 1.348 | 1.419 |
| Test | 177.360 | 142.907 | 31.647 | 2.806 | 3.476 |

E1 thuộc validation; E2–E4 thuộc test. Số mốc đủ điều kiện thời gian E1/E2/E3/E4: **1.419 / 391 / 2.832 / 253**; cả bốn có coverage ở mức này. Thời lượng trong summary là số mốc × 60 giây, không phải uptime/coverage sensor. Xem [data card](../examples/pb05/data_card.md) và [validation.json](../examples/pb05/validation.json); output đầy đủ ở `data/interim/pb05-verified-20261025/`.
