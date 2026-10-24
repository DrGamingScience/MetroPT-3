# Product backlog MetroPT-3

Ngày lập: 24/10/2026. Nguồn đặc tả: [Pipeline kỹ thuật phiên bản 1.0 ngày 19/10/2026](metropt3_pipeline_ky_thuat.docx), đối chiếu phạm vi với [proposal](proposal/metropt3_proposal.md).

Mục tiêu là xây dựng pipeline tái lập từ dữ liệu thô đến điểm bất thường mỗi phút, đợt cảnh báo, bảng so sánh MAD / Isolation Forest / FrozenECOD và báo cáo giải thích. Ưu tiên hoàn thành một luồng MAD trên train/validation trước, sau đó bổ sung mô hình và thí nghiệm, khóa cấu hình rồi mới đánh giá test.

Repo đã có tài liệu và khung PB01; chưa kèm dữ liệu thô. Theo dõi trạng thái, người phụ trách, hạn và PR tại [bảng quản lý công việc](requirements/README.md). Mỗi PB có file phân tích yêu cầu riêng trong `docs/requirements/`, liên kết trực tiếp ở các bảng bên dưới. Branch PB01 đã được tạo theo kế hoạch; tên branch các PB sau dùng khi bắt đầu triển khai.

## Cách tổ chức công việc

Mỗi PB tương ứng một branch và một PR có thể nghiệm thu riêng. Các task trong PB là checklist triển khai trên cùng branch. Sau khi merge PR, tạo branch tiếp theo từ `main` đã có thay đổi đó. Số PB thể hiện thứ tự triển khai đề xuất; cột phụ thuộc cho biết điều kiện thực sự để bắt đầu.

- **P0:** cần để có benchmark chính đáng tin cậy và chạy lại được.
- **P1:** hoàn thiện phần Data Mining, thí nghiệm mở rộng và replay trong pipeline.
- **P2:** phân tích bổ sung khi còn thời gian, liệt kê riêng cuối tài liệu.
- **S / M / L:** quy mô tương đối nhỏ / vừa / lớn, chưa quy đổi sang ngày khi chưa biết tốc độ triển khai và phần cứng.

Không dùng mức AP hoặc recall đặt trước làm điều kiện merge. Điều kiện hoàn thành là logic đúng, không rò rỉ dữ liệu, có đầu ra truy vết được và công bố cả kết quả kém hoặc sự cố bị bỏ sót.

## Các mốc bàn giao

| Mốc | Hạng mục | Kết quả kiểm tra được |
| --- | --- | --- |
| M1 Dữ liệu sẵn sàng | PB01–PB06 | Raw có checksum, audit, sự cố, split và EDA train; hoàn thành X0. |
| M2 Baseline chạy xuyên suốt | PB07–PB12 | F35, cửa sổ 5 phút, MAD; có score, episode và metric validation. |
| M3 So sánh và đăng ký thí nghiệm | PB13–PB17 | Ba detector, X1–X2; bổ sung X3–X5 và chế độ vận hành nếu làm phạm vi đầy đủ. |
| M4 Benchmark đã khóa | PB18–PB19 | Chọn trên validation, frozen artifacts, bảng test và kiểm tra seed X6. |
| M5 Bàn giao pipeline | PB20–PB22 | Replay, case study, báo cáo và bằng chứng chạy lại từ raw. |

Luồng lõi: **PB01 → … → PB15 → PB18 → PB19 → PB21 → PB22**. PB16, PB17 và PB20 là phần P1; để hoàn thành toàn bộ pipeline, thực hiện thêm cả ba. PB16 phải xong trước PB18 nếu muốn đưa các biến thể mở rộng vào benchmark test đã đăng ký. PB17 được fit và chốt trên train trước khi xem test để phục vụ diễn giải.

## Danh sách backlog và tên branch

| ID | Ưu tiên | Hạng mục | Branch | Phụ thuộc | Cỡ |
| --- | --- | --- | --- | --- | --- |
| [PB01](requirements/PB01-project-scaffold.md) | P0 | Khởi tạo dự án, config và hợp đồng artifact | `chore/pb01-project-scaffold` | — | S |
| [PB02](requirements/PB02-data-ingestion.md) | P0 | Nhập dữ liệu và khóa nguồn | `feat/pb02-data-ingestion` | PB01 | S |
| [PB03](requirements/PB03-data-quality-audit.md) | P0 | Audit và chia đoạn dữ liệu | `feat/pb03-data-quality-audit` | PB02 | M |
| [PB04](requirements/PB04-event-labels.md) | P0 | Bảng sự cố và quy tắc nhãn | `feat/pb04-event-labels` | PB02 | S |
| [PB05](requirements/PB05-temporal-splits.md) | P0 | Temporal split và purge | `feat/pb05-temporal-splits` | PB03, PB04 | M |
| [PB06](requirements/PB06-train-eda.md) | P0 | EDA trên train | `feat/pb06-train-eda` | PB05 | S |
| [PB07](requirements/PB07-causal-window-features.md) | P0 | Đặc trưng cửa sổ F35 nhân quả | `feat/pb07-causal-window-features` | PB05 | L |
| [PB08](requirements/PB08-train-preprocessing.md) | P0 | Preprocessing chỉ fit trên train | `feat/pb08-train-preprocessing` | PB07 | M |
| [PB09](requirements/PB09-mad-baseline.md) | P0 | Baseline MAD | `feat/pb09-mad-baseline` | PB08 | S |
| [PB10](requirements/PB10-alert-episodes.md) | P0 | Alarm, episode và ghép sự cố | `feat/pb10-alert-episodes` | PB04, PB05 | M |
| [PB11](requirements/PB11-evaluation-metrics.md) | P0 | Metric cửa sổ và sự kiện | `feat/pb11-evaluation-metrics` | PB10 | M |
| [PB12](requirements/PB12-baseline-workflow.md) | P0 | CLI baseline chạy xuyên suốt | `feat/pb12-baseline-workflow` | PB09, PB11 | M |
| [PB13](requirements/PB13-isolation-forest.md) | P0 | Isolation Forest | `feat/pb13-isolation-forest` | PB12 | S |
| [PB14](requirements/PB14-frozen-ecod.md) | P0 | FrozenECOD đúng đặc tả | `feat/pb14-frozen-ecod` | PB12 | L |
| [PB15](requirements/PB15-experiment-runner.md) | P0 | Runner thí nghiệm và đối chiếu cửa sổ | `feat/pb15-experiment-runner` | PB13, PB14 | L |
| [PB16](requirements/PB16-feature-ablations.md) | P1 | F51, F55 và ablation nhóm cảm biến | `feat/pb16-feature-ablations` | PB15 | L |
| [PB17](requirements/PB17-operating-modes.md) | P1 | PCA và K-Means cho chế độ vận hành | `feat/pb17-operating-modes` | PB06, PB08 | M |
| [PB18](requirements/PB18-validation-freeze.md) | P0 | Chọn cấu hình, ngưỡng và freeze | `feat/pb18-validation-freeze` | PB15; PB16 nếu dùng mở rộng | L |
| [PB19](requirements/PB19-frozen-test-benchmark.md) | P0 | Chấm test bằng cấu hình đã khóa | `feat/pb19-frozen-test-benchmark` | PB18 | M |
| [PB20](requirements/PB20-causal-replay.md) | P1 | Replay theo thời gian | `feat/pb20-causal-replay` | PB19 | M |
| [PB21](requirements/PB21-results-report.md) | P0 | Case study và báo cáo kết quả | `feat/pb21-results-report` | PB19; PB16, PB17 cho phân tích mở rộng | M |
| [PB22](requirements/PB22-reproducible-handoff.md) | P0 | Nghiệm thu tái lập và hướng dẫn chạy | `chore/pb22-reproducible-handoff` | PB21; PB20 nếu làm replay | M |

## Chi tiết các hạng mục

### PB01 Khởi tạo dự án và hợp đồng artifact

**Giá trị:** người triển khai có một cấu trúc và cấu hình thống nhất ngay từ đầu. Đối chiếu chương 14–15.

- [ ] Tạo `pyproject.toml`, `src/metropt3/`, `tests/`, `configs/base.yaml` và quy ước đường dẫn `data/`, `artifacts/<run_id>/`, `reports/<run_id>/` ngay tại root repo hiện tại.
- [ ] Khai báo các phụ thuộc theo pipeline; thêm pytest cho kiểm tra logic. PyOD chỉ là phụ thuộc tùy chọn phục vụ đối chiếu.
- [ ] Đưa tham số split, cửa sổ, chất lượng, ECOD, q, seed và gộp cảnh báo vào config; kiểm tra config sai ngay khi nạp.
- [ ] Định nghĩa schema artifact, `run_id`, hash config và quan hệ đầu vào/đầu ra của từng stage; thêm `.gitignore` cho dữ liệu, môi trường và đầu ra lớn.
- [ ] Khởi tạo `cli --help`; các stage được bổ sung dần cùng PB triển khai, không báo thành công cho stage chưa có logic.

**Nghiệm thu:** cài package trong môi trường riêng; import và `python -m metropt3.cli --help` chạy được. Có config mẫu và tài liệu hợp đồng cho các artifact ở bảng cuối backlog. Chốt lockfile sau smoke test thực tế tại PB12.

### PB02 Nhập dữ liệu và khóa nguồn

**Giá trị:** mọi kết quả chỉ rõ phiên bản dữ liệu đã sử dụng. Đối chiếu chương 2.

- [ ] Triển khai `ingest.py`, nhận gói tải chính thức hoặc đường dẫn local, giữ nguyên CSV và PDF mô tả trong `data/raw/`.
- [ ] Lưu `raw_manifest.json`: URL, ngày tải, tên file, byte, SHA-256, schema version; giữ `raw_row_id` và tên cột gốc.
- [ ] Kiểm tra header 15 cảm biến, `timestamp` và cột chỉ mục; giữ chính tả `DV_eletric`, `Towers`; index không vào feature.
- [ ] Đối chiếu SHA-256 CSV mà pipeline đã ghi: `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`. Nếu khác, tạo phiên bản dữ liệu mới và yêu cầu audit lại trong luồng chạy.

**Nghiệm thu:** chạy ingest hai lần với cùng nguồn không ghi đè raw hoặc nhân đôi dữ liệu. File hỏng, thiếu cột và checksum khác có thông báo rõ; số liệu trong tài liệu chỉ là giá trị đối chiếu, phải đo lại trên file nhập thực tế.

### PB03 Audit chất lượng và chia đoạn liên tục

**Giá trị:** phân biệt thiếu giá trị với thiếu thời gian quan sát, tránh chấm các cửa sổ không đủ dữ liệu. Đối chiếu chương 2–3.

- [ ] Triển khai `audit.py`: parse timestamp, numeric, missing, infinity, digital domain, số giá trị duy nhất, quantile, nhịp ghi và gap.
- [ ] Deduplicate dòng trùng hoàn toàn, lưu số bản gộp; timestamp trùng nhưng khác cảm biến vào bảng xung đột và bị loại khỏi dữ liệu hợp lệ.
- [ ] Ước lượng `delta0` từ timestamp của phần train theo ranh giới lịch đã khai báo; lưu `gap_break = 3 × delta0`, `segment_id` và bảng gap. PB05 sẽ xác nhận split đầy đủ sau đó.
- [ ] Giữ các giá trị cực đoan chưa có bằng chứng lỗi đo, giữ timestamp theo đồng hồ gốc và giữ phần dữ liệu ngày 01/09/2020 nếu có.

**Đầu ra và nghiệm thu:** cleaned rows, quality report, gap/conflict tables và `data_card.md`. Fixture có gap, duplicate, invalid numeric cho kết quả đúng; không tự gán múi giờ Asia/Saigon cho dữ liệu. Audit toàn bộ file chỉ dùng để kiểm tra cấu trúc, timestamp và chất lượng; EDA phân phối cảm biến nằm ở PB06 trên train.

### PB04 Chuẩn hóa sự cố và quy tắc nhãn

**Giá trị:** có nguồn đối chiếu thống nhất cho cả metric và lọc tập tham chiếu. Đối chiếu chương 3–4.

- [ ] Tạo `events.py` và `events.csv` có `event_id`, `start`, `end`, `failure_type`, `source`, `source_note`, `confidence_note`.
- [ ] Lưu E1: 18/04/2020 00:00–23:59; E2: 29/05/2020 23:30–30/05/2020 06:00; E3: 05/06/2020 10:00–07/06/2020 14:30; E4: 15/07/2020 14:30–19:00.
- [ ] Khoảng sự cố đóng hai đầu, giây 00 khi nguồn chỉ ghi đến phút; nhãn tại `window_end`. Lưu ghi chú nguồn mâu thuẫn thay vì tự dịch mốc.
- [ ] Tách hàm gán nhãn tại thời điểm kết thúc và hàm kiểm tra nguồn dữ liệu cửa sổ có giao sự cố; hàm thứ hai sẽ nhận cả provenance forward fill từ PB07.

**Nghiệm thu:** kiểm tra đúng ngay trước, tại và sau hai biên sự cố. Nhãn không xuất hiện trong ma trận feature; nhãn 0 được diễn giải là ngoài báo cáo.

### PB05 Temporal split và kiểm soát rò rỉ

**Giá trị:** validation/test mô phỏng dữ liệu tương lai đúng giao thức. Đối chiếu chương 4.

- [ ] Triển khai `split.py`: train trước `2020-03-01`, validation từ mốc đó đến trước `2020-05-01`, test từ `2020-05-01` đến hết file.
- [ ] Lưu `splits.json`, lưới chấm điểm một phút và mask; E1 thuộc validation, E2–E4 thuộc test theo timeline nguồn.
- [ ] Reset fill và window ở biên split/segment; warm-up chung 930 giây rồi làm tròn lên mốc phút, kể cả cấu hình W ngắn hơn.
- [ ] Định nghĩa reference mask loại mọi cửa sổ có nguồn thô giao sự cố, kể cả nguồn fill; metric mask giữ tất cả cửa sổ hợp lệ. Hoàn thiện reference mask khi PB07 cung cấp provenance.

**Nghiệm thu:** fixture xác nhận không có `raw_row_id` hoặc nguồn fill dùng chung giữa hai split; không cắt đôi sự cố. Lưu số dòng, mốc dự kiến/hợp lệ, thời lượng, dương và sự cố đánh giá được; chưa tính sensor feature để chọn theo test.

### PB06 EDA trên train

**Giá trị:** hiểu phạm vi hành vi tham chiếu và ghi nhận trạng thái hiếm trước khi xây mô hình. Đối chiếu chương 5.

- [ ] Tạo histogram, boxplot, timeline analog, tần suất digital, Pearson và Spearman trên train.
- [ ] Đối chiếu Motor_current và áp suất với COMP, DV_eletric, Towers; ghi điều có bằng chứng và điều chưa xác minh.
- [ ] Khi lấy mẫu, phân bố theo ngày, cố định seed và lưu danh sách dòng; không tự loại feature do tương quan cao.

**Nghiệm thu:** báo cáo EDA có đơn vị, phạm vi train và nguồn sample. Chưa đặt tên trạng thái COMP/cụm bằng diễn giải cơ học thiếu bằng chứng; PCA/K-Means triển khai sau tại PB17.

### PB07 Đặc trưng cửa sổ F35 nhân quả

**Giá trị:** chuyển cảm biến thành đầu vào mô hình chỉ dùng thông tin đã có tại thời điểm chấm. Đối chiếu chương 6.

- [ ] Triển khai `features.py` cho `(t-W, t]`, stride 60 giây; hỗ trợ W = 1, 5, 15 phút, khởi đầu chạy W = 5.
- [ ] Tính 7 analog × mean/std/min/max/slope; `ddof=0`, slope theo thời gian thật bằng phút, mean theo các mẫu quan sát.
- [ ] Độ phủ tính trước fill, mỗi cảm biến cần ít nhất `max(3, ceil(0.8 × W_seconds / delta0))` mẫu thật; kiểm tra gap và hai biên với dung sai `2 × delta0`.
- [ ] Nếu cần fill, chỉ forward fill tuổi tối đa 30 giây cùng split/segment, lưu thời điểm nguồn. Không tạo impute khi dữ liệu đã đầy đủ.
- [ ] Lưu toàn bộ mốc dự kiến, `valid`, reason, biên cửa sổ, min/max source time và provenance đủ kiểm tra giao sự cố/purge.
- [ ] Xuất `features.parquet`, quality mask và `feature_schema.json` gồm cột/thứ tự/công thức/đơn vị/phiên bản.

**Nghiệm thu:** sửa dữ liệu sau t không đổi feature tại t; `source_max_time <= window_end`. Fixture timestamp không đều cho slope đúng; cửa sổ qua split/gap, thiếu coverage hoặc stale sensor có reason và không được đưa vào detector. Hoàn tất reference mask của PB05.

### PB08 Preprocessing chỉ fit trên train

**Giá trị:** detector nhận cùng schema, không học thống kê từ validation/test. Đối chiếu chương 7.

- [ ] Triển khai `preprocess.py`, tạo train reference hợp lệ trước khi fit.
- [ ] Loại cột hằng/hoàn toàn thiếu trên train; lưu danh sách, giá trị hằng và cờ chất lượng nếu chúng thay đổi về sau.
- [ ] Mặc định dùng complete-case. Nếu bật median imputer, fit train, ghi số mốc đã điền và đối chiếu complete-case.
- [ ] Giữ đơn vị gốc cho ba detector; kiểm tra finite, đúng tên và thứ tự cột. Nhánh scale cho PCA/K-Means tách riêng.

**Đầu ra và nghiệm thu:** `preprocess.joblib` và schema sau lọc. Thay dữ liệu validation/test không đổi thống kê đã fit; cột thiếu/đảo thứ tự bị từ chối rõ ràng; lưu/nạp cho cùng kết quả transform.

### PB09 Baseline MAD

**Giá trị:** có mốc so sánh đơn giản và giải thích được. Đối chiếu chương 7.

- [ ] Triển khai `models/mad.py` với median, MAD và sàn theo train; score là max độ lệch chuẩn hóa.
- [ ] Sàn là `max(1e-6, 0.01 × (P99-P1))`; dùng range train khi khoảng phân vị bằng 0 ở cột không hằng. Không nhân hệ số 1.4826.
- [ ] Lưu trạng thái model, feature names/version và thông tin feature đạt max cho giải thích.

**Nghiệm thu:** fixture MAD bằng 0 vẫn có score hữu hạn; score và feature giải thích khớp phép tính tay. Model không tự chọn threshold; save/load giữ kết quả.

### PB10 Alarm, episode và ghép sự cố

**Giá trị:** biến score thành các đợt cần kiểm tra mà không làm tăng giả số sự cố được phát hiện. Đối chiếu chương 11.

- [ ] Triển khai `alerts.py` nhận score và tau; alarm khi `score > tau`, tại dấu bằng là 0; invalid giữ cả score/alarm null.
- [ ] Gộp alarm cách nhau tối đa 300 giây khi cùng segment và mọi mốc ở giữa hợp lệ; invalid/gap/split ngắt đợt.
- [ ] Giữ alarm gốc ở cấp mốc; khoảng nối giữa hai alarm chỉ phục vụ hiển thị.
- [ ] Chỉ ghép sự cố khi có alarm thật nằm trong sự cố; lưu nhiều `event_id` nếu một đợt chứa alarm khớp nhiều sự cố.

**Đầu ra và nghiệm thu:** score table đầy đủ mốc và `episodes.csv` có đầu/cuối, số alarm, peak, max score, model version, liên kết mốc gốc. Fixture có hai alarm nằm ngoài và khoảng nối qua sự cố không được tạo true positive.

### PB11 Metric cửa sổ và sự kiện

**Giá trị:** đo đồng thời khả năng phát hiện, độ trễ và gánh nặng cảnh báo. Đối chiếu chương 12.

- [ ] Triển khai `evaluate.py`: TP/FP/FN/TN, precision/recall/F1, AP từ score liên tục, PR curve và positive rate.
- [ ] Tính event recall dạng số đếm/tổng đánh giá được, delay từ lúc bắt đầu sự cố, `first_valid_time`, observational delay và danh sách bỏ sót.
- [ ] Ngày hợp lệ = số mốc một phút hợp lệ / 1440; báo ngoài báo cáo/ngày, alert fraction và tổng phút alarm.
- [ ] Quy định N/A có reason: AP thiếu một lớp; precision không có alarm; recall không có dương; F1 mẫu số 0; delay cho sự cố bỏ sót.
- [ ] Nhận explicit evaluation mask; báo coverage và các sự cố không đánh giá được. Không point adjustment hoặc biến null thành bình thường.

**Nghiệm thu:** fixture nhỏ tính tay được toàn bộ số đếm, episode, thời lượng và delay; alarm trước sự cố không tạo delay âm. Xuất `metrics.json` có cả số đếm, mẫu số và lý do N/A.

### PB12 CLI baseline chạy xuyên suốt

**Giá trị:** có bản chạy đầu tiên để kiểm tra giả định trước khi thêm mô hình. Đối chiếu chương 14–16.

- [ ] Nối ingest/audit/events/split/features/train/validate trong CLI; giữ schema và checksum giữa các stage.
- [ ] Chạy MAD F35 W=5, q=0.99 từ validation reference, `method=higher`, gộp 5 phút; đây là cấu hình baseline ban đầu, chưa là cấu hình chính đã chọn.
- [ ] Sinh score, episode, metric và timeline train/validation; tạo run manifest có config/code/data hash, seed, môi trường, thời gian và tài nguyên.
- [ ] Smoke test một đoạn train/validation nhỏ có warm-up; sau đó chạy baseline validation đầy đủ. Chốt phiên bản thực tế bằng lockfile.

**Nghiệm thu M2:** từ raw tạo được report validation của MAD bằng các lệnh đã tài liệu hóa; chạy lại cho cùng mốc và score trong dung sai đã ghi. Không mở benchmark test ở milestone này.

### PB13 Isolation Forest

**Giá trị:** so sánh detector đa biến với MAD trên cùng đầu vào. Đối chiếu chương 8.

- [ ] Triển khai `models/isolation_forest.py` qua cùng giao diện fit/score/save/load như MAD.
- [ ] Dùng `-score_samples`, không lấy `predict` làm alarm. Mặc định 200 cây, max_samples=min(256, n_train), seed 42, n_jobs=1, không bootstrap.
- [ ] Khai báo grid 100/200/400 cây × 256/1024 samples; lưu tham số, fit time, score time và throughput.

**Nghiệm thu:** score lớn hơn cùng nghĩa bất thường hơn; model tham gia workflow validation PB12 được. Chặn max_samples theo n_train, không suy contamination từ nhãn test, không giả định có `feature_importances_`.

### PB14 FrozenECOD đúng đặc tả

**Giá trị:** có ECOD chấm tương lai với reference cố định, kết quả không phụ thuộc batch. Đối chiếu chương 9 và kiểm thử chương 15.

- [ ] Triển khai `models/frozen_ecod.py`: sorted reference, dấu skewness, n/d/feature names/version fit từ train; skewness bằng 0 chọn đuôi phải.
- [ ] Hai đuôi đếm `<= x` và `>= x`, xử lý ties bằng hai phía searchsorted; floor xác suất `1/(n+1)`, dùng float64.
- [ ] Score = max của ba tổng trái/phải/tự động; contributions thuộc nhánh thắng và cộng bằng score, hòa chọn trái → phải → tự động.
- [ ] Thêm kiểm tra fitted/schema, save/load, batch size khởi đầu 4096 và bảo vệ tính skewness khi dữ liệu quá lớn.
- [ ] Theo đặc tả benchmark, không thay phần này bằng lời gọi PyOD có thể tái ước lượng phân phối theo dữ liệu được chấm. Nếu đối chiếu PyOD, lưu phiên bản/mã riêng.

**Nghiệm thu:** fixture train `[1,1,2]` đúng cả hai đuôi; điểm ngoài min/max hữu hạn; ví dụ tổng hợp cho 5.1 thay vì 10. Score một mẫu, nhiều batch hoặc batch hoán vị khớp trong `1e-12`; checksum reference/skewness không đổi; save/load tương đương. Đưa test số học vào chính branch này trước khi chạy tìm kiếm.

### PB15 Runner thí nghiệm và đối chiếu cửa sổ

**Giá trị:** so sánh công bằng, tái sử dụng score và hạn chế tìm kiếm trên validation chỉ có E1. Đối chiếu chương 10, 12–13.

- [ ] Hoàn thành X1: ba model, F35 W=5; X2: F35 W=1/5/15 và F7 mới nhất với tuổi tối đa `2 × delta0`.
- [ ] Mỗi bảng dùng giao các mốc hợp lệ, warm-up chung và cùng cột sau preprocessing trong phép so sánh; lưu `mask_id`, số mốc loại, positive rate. Báo thêm độ phủ riêng từng cấu hình ở phụ lục.
- [ ] Lưới F35 seed chính có tối đa 24 lượt fit: 3 W × (1 MAD + 1 ECOD + 6 IF); F7 và mở rộng tính riêng.
- [ ] Lưu/cache score theo data/config/model/schema hash để khảo sát q và gộp mà không fit lại; tránh dùng score cache của cấu hình khác.
- [ ] Đăng ký X6 với seed 42/7/2026 cho cấu hình IF chọn trên validation; không chọn seed theo test. Tạo kế hoạch X7 chỉ trên validation.

**Nghiệm thu:** có bảng kết quả validation X1/X2 và registry thí nghiệm; chạy lại tái sử dụng được artifact khớp hash. Test chưa được dùng để chọn W, feature set hay hyperparameter.

### PB16 F51, F55 và ablation nhóm cảm biến

**Giá trị:** đo phần đóng góp của digital, chênh lệch áp suất và từng nhóm cảm biến. Đối chiếu chương 6, 13.

- [ ] X3: F51 = F35 + 8 digital × tỷ lệ bằng 1/số chuyển trạng thái, xác nhận domain nhị phân trước.
- [ ] X4: F55 thêm mean/std của TP2−TP3 và TP3−Reservoirs, tính chênh lệch tại từng timestamp rồi tổng hợp.
- [ ] X5: bỏ lần lượt nhóm áp suất, nhiệt độ, dòng điện; ghi rõ các feature dẫn xuất bị loại cùng nhóm nguồn.
- [ ] Chạy IF/ECOD, mỗi biến thể fit lại preprocessing/model trên train và hiệu chỉnh ngưỡng riêng trên validation; không dùng chung tau khác thang score.

**Nghiệm thu:** dimension trước lọc đúng 51/55; transition không đếm qua gap hoặc dùng mẫu ngoài cửa sổ. Mỗi bảng có common mask và câu hỏi X3/X4/X5 rõ ràng. Nếu đưa vào báo cáo test xác nhận, đăng ký và freeze từng biến thể tại PB18 trước khi chạy PB19.

### PB17 PCA và K-Means cho chế độ vận hành

**Giá trị:** giúp giải thích score cao ở trạng thái hiếm hoặc chuyển chế độ hợp lệ. Đối chiếu chương 5.

- [ ] Fit nhánh StandardScaler/PCA trên train reference; vẽ PC1/PC2 và explained variance, lưu toàn bộ transformer.
- [ ] K-Means k=2..6, n_init=20, seed=42; silhouette trên tối đa 5000 mốc train lấy theo thời gian, kèm kích thước/tâm/tần suất chuyển cụm.
- [ ] Chốt k từ train và ghi lý do; dùng transformer/tâm cụm cố định khi chiếu validation/test. Ban đầu đặt tên trạng thái A/B/C.

**Nghiệm thu:** có artifact và bảng cluster_id, số mốc, trung vị cảm biến, thời lượng; bổ sung tỷ lệ alarm khi có score. Sửa dữ liệu validation/test không làm đổi scaler/PCA/tâm cụm; PCA chưa được đưa vào detector chính.

### PB18 Chọn cấu hình, ngưỡng và freeze

**Giá trị:** có quyết định mô hình và điểm vận hành review được trước khi biết kết quả test. Đối chiếu chương 10.

- [ ] Chọn W/hyperparameter của từng detector bằng AP validation trên common mask. AP hòa đến 4 chữ số: ít chiều hơn → ít cây hơn với IF → thời gian score thấp hơn; nếu còn hòa, dùng thứ tự config_id cố định và ghi đây là quy ước triển khai bổ sung.
- [ ] Tính tau từ validation reference với q = 0.95/0.975/0.99/0.995/0.999, `method=higher`, alarm dùng `>`.
- [ ] Với gộp chính 5 phút và ngân sách thí nghiệm 1 đợt ngoài báo cáo/ngày hợp lệ, chọn ngưỡng đạt ngân sách và phát hiện E1; ưu tiên event recall → delay → ít đợt → q cao hơn. Nếu không có ngưỡng đáp ứng cả hai, giữ q=0.99 và báo trade-off.
- [ ] X7 đối chiếu gộp 1/5/10 phút trên validation dưới dạng phân tích độ nhạy; gộp benchmark chính vẫn 5 phút theo đặc tả.
- [ ] Xuất `validation_results.csv`, biên bản lựa chọn và `frozen_config.json` cho từng model/cấu hình đã đăng ký: feature/schema/mask policy, preprocessing/model hash, seed, q/tau, matching, merge, code/data hash.

**Nghiệm thu:** freeze chỉ thành công khi đủ artifact và checksum; test thiếu freeze hoặc sai hash phải bị từ chối. Không refit train+validation. Thay nhãn test không đổi cấu hình đã chọn, tau hay frozen hash.

### PB19 Chấm test bằng cấu hình đã khóa

**Giá trị:** có đánh giá cuối cho E2–E4 và biết mức cải thiện so với MAD. Đối chiếu chương 11–13.

- [ ] Hoàn thiện `test --frozen ...`: chỉ nạp artifact đã khóa, không fit hoặc hiệu chỉnh trong test; ghép nhãn sau score.
- [ ] Chấm cùng mốc cho từng bảng, lưu `scores.parquet`, `episodes.csv`, `metrics.json`, bảng summary và bảng từng sự cố.
- [ ] Chạy các biến thể X1/X2 và phần mở rộng đã đăng ký; X6 báo cả seed 42/7/2026 cho IF, cấu hình chính vẫn seed đã chốt.
- [ ] Summary có model/feature_set/W/seed/mask_id/n_train/n_test_valid/positive_rate/AP/precision/recall/F1/detected_events/evaluable_events/median_delay/outside_episodes_per_day/alert_fraction/fit_seconds/score_ms_per_window.
- [ ] Bảng sự cố có event_id/valid_coverage/first_valid_time/detected/first_alarm/delay/max_score, kèm observational delay và lý do không đánh giá được nếu có.

**Nghiệm thu M4:** mọi alarm truy được model/tau/window/run; invalid còn null và có reason; hiện đủ cả sự cố bỏ sót, coverage và N/A. So thời gian cùng phần cứng/n_jobs. Kết quả test không đổi cấu hình chính đã freeze.

### PB20 Replay theo thời gian

**Giá trị:** kiểm tra hành vi khi dữ liệu đến tuần tự có khớp benchmark offline hay không. Đối chiếu chương 11.

- [ ] Triển khai buffer W + giới hạn fill, đưa bản ghi vào theo timestamp, chấm mỗi phút bằng preprocessing/model/tau đã khóa.
- [ ] Reset buffer/fill/episode theo cùng split/gap/invalid policy; giữ model_version và reason chất lượng.
- [ ] Đối chiếu replay với đầu ra batch offline; API hoặc dữ liệu đến muộn thực tế là phạm vi triển khai tiếp theo, chưa cần để nghiệm thu replay của đồ án.

**Nghiệm thu:** replay và batch trên cùng fixture/đoạn dữ liệu cho cùng mốc, valid/alarm/episode và score trong dung sai; thêm dữ liệu tương lai không sửa kết quả quá khứ. Không cập nhật ECDF trong replay.

### PB21 Case study và báo cáo kết quả

**Giá trị:** người đọc hiểu mô hình phát hiện gì, bỏ sót gì và các giới hạn của kết luận. Đối chiếu chương 13, 16.

- [ ] Tạo `explain.py` và `report --run-id ...`; ít nhất một case cho từng sự cố test, kể cả bỏ sót.
- [ ] Lấy thêm episode ngoài báo cáo có score cao và mẫu ngẫu nhiên seed cố định; ghi tiêu chí chọn, tránh chỉ chọn ví dụ đẹp.
- [ ] Mỗi case gồm cảm biến, score/tau, alarm thật, sự cố, chất lượng và trạng thái cụm nếu đã làm PB17. ECOD hiển thị top 5 feature của nhánh thắng, gộp theo sensor và có phân vị train; MAD hiển thị feature đạt max; IF dùng sensor timeline/ablation.
- [ ] Tổng hợp X0–X7 theo phạm vi thực hiện; trả lời ML có cải thiện MAD không, W nào hữu ích, phát hiện sự cố nào, delay và đợt ngoài báo cáo/ngày bao nhiêu.

**Nghiệm thu:** report có đơn vị/split/run_id, links tới bảng máy đọc được và đối chiếu đúng metrics.json. Ghi rõ chỉ có ít sự cố, nhãn chưa đầy đủ; phân loại cảnh báo ngoài báo cáo bằng mức chắc chắn, không khẳng định nguyên nhân cơ học từ feature contribution. Không thay lựa chọn mô hình từ kết quả test.

### PB22 Nghiệm thu tái lập và hướng dẫn chạy

**Giá trị:** người khác có thể cài và chạy lại toàn bộ kết quả. Đối chiếu chương 14–16.

- [ ] Rà soát bộ test đã được thêm ngay trong từng PB, không dồn kiểm tra logic tới cuối; chạy bộ kiểm tra causality, split/fill provenance, ECOD ties/batch/state, metric/episode và độc lập của test.
- [ ] Chạy lại từ raw với lockfile và config cố định trong môi trường mới; so tập mốc, quality mask, score trong dung sai, alarm, episode và metric. Runtime được phép khác.
- [ ] Kiểm tra toàn vẹn chuỗi artifact, hướng dẫn sửa lỗi thiếu raw/sai schema/sai hash/chưa freeze và thực hiện các kiểm tra tự động trên fixture nhỏ trong CI.
- [ ] Cập nhật README với cài đặt, nguồn data, trình tự lệnh, vị trí đầu ra, cấu hình mẫu và kết quả đã thực sự đo; ghi môi trường/CPU/RAM/library/code hash trong manifest.

**Nghiệm thu M5:** một lượt chạy sạch tạo được toàn bộ đầu ra của phạm vi đã chọn, không feature tương lai hay score vô hạn, mọi alarm truy vết được. README phân biệt rõ stage đã có và phần còn để sau; PB20 được kiểm tra nếu nằm trong phạm vi bàn giao.

## Artifact bắt buộc và nơi chịu trách nhiệm

| Artifact | PB tạo hoặc hoàn thiện | Nội dung kiểm tra |
| --- | --- | --- |
| `raw_manifest.json` | PB02 | URL, ngày tải, file/byte/SHA-256/schema version. |
| `data_card.md`, quality/gap/conflict reports | PB03, PB04 | Schema, thời gian, nhịp, chất lượng và nguồn nhãn. |
| `events.csv` | PB04 | E1–E4, mốc và ghi chú nguồn gốc. |
| `splits.json`, masks | PB05, PB07, PB15 | Ranh giới, purge/warm-up, reference/evaluation/common mask và số đếm. |
| `features.parquet`, `feature_schema.json` | PB07, PB15, PB16 | Feature, provenance/quality, cột/thứ tự/công thức/đơn vị/phiên bản. |
| `preprocess.joblib` | PB08 | Cột giữ/bỏ, thống kê train và imputer nếu có. |
| Model artifacts | PB09, PB13, PB14 | Trạng thái fit, tham số, feature names và version. |
| PCA/K-Means artifacts | PB17 | Nhánh scale, PCA, tâm cụm và lựa chọn k. |
| `validation_results.csv` | PB15, PB18 | Config, mask, q/tau, metric và lựa chọn cuối. |
| `frozen_config.json` | PB18 | Config chính, ngưỡng, seed, event/merge policy và các hash. |
| `scores.parquet`, `episodes.csv` | PB10, PB12, PB19 | Toàn bộ mốc kể cả invalid, alarm thật, đợt và event matching. |
| `metrics.json`, summary/event tables | PB11, PB19 | Số đếm, tỷ lệ, thời lượng, coverage và lý do N/A. |
| `run_manifest.json` | PB12 trở đi | Code/data/config hash, seed, Python/library/OS/hardware, thời gian/tài nguyên. |
| Report và case studies | PB06, PB21 | EDA, benchmark, biểu đồ và giới hạn kết luận. |

Artifact dùng chung như raw/events được phép tham chiếu bằng đường dẫn và checksum từ run manifest, không cần nhân bản file lớn vào mọi run. Đổi W, feature_set hoặc model/config tạo run_id mới; không ghi đè kết quả cũ.

## Điều kiện hoàn thành cho mọi PR

- [ ] Có chức năng hoặc đầu ra đúng phạm vi PB và hướng dẫn chạy ngắn.
- [ ] Có kiểm tra cho rủi ro logic thực sự của thay đổi bằng fixture nhỏ; tài liệu/đổi tên đơn giản không cần thêm test hình thức.
- [ ] Chỉ học thống kê từ train reference, chỉ chọn bằng validation; benchmark test yêu cầu freeze.
- [ ] Lưu config/schema/provenance/hash cần thiết và giữ null/reason cho mốc invalid.
- [ ] Không đưa dữ liệu thô hoặc artifact lớn vào Git; không báo số hiệu quả mô hình chưa thực nghiệm.

## Các quyết định cần ghi rõ khi triển khai

1. **Schema và số liệu nguồn:** pipeline ghi `Towers` và dữ liệu thực tế tới 01/09/2020, chi tiết hơn mô tả khái quát trong proposal. Dùng header/timeline của raw đã audit làm đầu vào, không tự đổi case cột hoặc cắt ngày cuối.
2. **Audit trước split:** ranh giới lịch đã cố định trong config cho phép PB03 lấy phần timestamp train để fit delta0; PB05 kiểm tra các mask và số đếm. Không có lý do để fit nhịp trên toàn bộ file.
3. **Reference khác metric:** cửa sổ kết thúc ngoài sự cố nhưng còn chứa nguồn dữ liệu trong sự cố phải bị loại khi tính ngưỡng tham chiếu, vẫn có thể thuộc tập metric với nhãn 0 tại window_end. Provenance fill cũng phải được xét.
4. **Nhánh mở rộng và test:** muốn so sánh xác nhận F51/F55/ablation thì hoàn tất chọn và đăng ký tại PB18. Ý tưởng nảy ra sau khi xem test được ghi là phân tích thăm dò hoặc cần giai đoạn đánh giá độc lập mới.
5. **Quy tắc triển khai còn thiếu:** với hòa AP và thời gian bằng nhau dùng config_id cố định như PB18; không chọn theo thứ tự chạy ngẫu nhiên. Nêu rõ valid_coverage là số mốc hợp lệ trong sự cố / số mốc dự kiến trên lưới một phút trong khoảng sự cố.

## Phần P2 nếu còn thời gian

| ID | Hạng mục | Branch đề xuất | Điều kiện |
| --- | --- | --- | --- |
| [PB23](requirements/PB23-block-bootstrap.md) | Block bootstrap theo ngày cho AP/gánh nặng cảnh báo | `feat/pb23-block-bootstrap` | Sau PB19; 1000 lần, seed cố định, ghi giả định và loại mẫu thiếu hai lớp. |
| [PB24](requirements/PB24-pyod-comparison.md) | Đối chiếu PyOD và ECOD-paper-frozen | `experiment/pb24-pyod-comparison` | Sau PB14; PB15 nếu đo metric validation; khóa phiên bản và đối chiếu thuật toán/batch. |
| [PB25](requirements/PB25-time-weighted-features.md) | Nhánh mean/tỷ lệ trạng thái có trọng số thời gian | `experiment/pb25-time-weighted-features` | Sau PB15; cấu hình riêng, fit/chọn lại trên train/validation. |
| [PB26](requirements/PB26-feature-transforms.md) | Nhánh PCA cho detector hoặc lọc tương quan | `experiment/pb26-feature-transforms` | Sau PB15 và PB17; thí nghiệm riêng, không thay benchmark chính sau khi xem test. |

## Bắt đầu từng phần

Branch triển khai đầu tiên:

```powershell
git switch main
git switch -c chore/pb01-project-scaffold
```

Làm xong PB01, kiểm tra và merge vào `main`, sau đó tạo `feat/pb02-data-ingestion` từ `main` mới. Lặp lại theo bảng backlog; không tạo sẵn cả chuỗi branch từ `main` cũ. Tên PR có thể dùng mẫu `[PB01] Khởi tạo dự án và cấu hình` để tra ngược backlog dễ dàng.

Nếu cần một bản chạy sớm, dừng phạm vi milestone đầu ở **M2 / PB12**: MAD F35 W=5 có đánh giá validation. Đây là mốc kiểm tra luồng xử lý; benchmark hoàn chỉnh cần tiếp tục PB13–PB19 và phần báo cáo/tái lập.
