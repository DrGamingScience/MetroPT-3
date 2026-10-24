# Phân tích yêu cầu và theo dõi công việc MetroPT-3

Folder này chứa **26 file phân tích yêu cầu**, tương ứng PB01–PB22 trong kế hoạch chính và PB23–PB26 tùy chọn. Dùng bảng dưới đây làm nơi duy nhất cập nhật trạng thái tổng thể, người phụ trách, hạn, ngày hoàn thành và PR. Trong từng file PB, đánh dấu checklist triển khai/tiêu chí nghiệm thu và ghi quyết định, vướng mắc, bằng chứng.

Nguồn đối chiếu: [Product backlog](../product_backlog.md), [pipeline kỹ thuật](../metropt3_pipeline_ky_thuat.docx) và [proposal](../proposal/metropt3_proposal.md). Yêu cầu mô tả công việc dự kiến; bằng chứng triển khai nằm trong từng PB và trạng thái hiện tại được theo dõi ở bảng dưới.

## Bảng theo dõi

Các ô `—` chưa được phân công hoặc chưa có thông tin. Không tự suy hạn hoàn thành từ quy mô S/M/L. Cập nhật đúng một dòng khi trạng thái PB thay đổi.

| PB và yêu cầu | Ưu tiên | Trạng thái | Phụ trách | Hạn | Ngày xong | PR |
| --- | --- | --- | --- | --- | --- | --- |
| [PB01 Khởi tạo dự án, config và hợp đồng artifact](PB01-project-scaffold.md) | P0 | In review | Codex | — | — | — |
| [PB02 Nhập dữ liệu và khóa nguồn](PB02-data-ingestion.md) | P0 | Todo | — | — | — | — |
| [PB03 Audit và chia đoạn dữ liệu](PB03-data-quality-audit.md) | P0 | Todo | — | — | — | — |
| [PB04 Bảng sự cố và quy tắc nhãn](PB04-event-labels.md) | P0 | Todo | — | — | — | — |
| [PB05 Temporal split và purge](PB05-temporal-splits.md) | P0 | Todo | — | — | — | — |
| [PB06 EDA trên train](PB06-train-eda.md) | P0 | Todo | — | — | — | — |
| [PB07 Đặc trưng cửa sổ F35 nhân quả](PB07-causal-window-features.md) | P0 | Todo | — | — | — | — |
| [PB08 Preprocessing chỉ fit trên train](PB08-train-preprocessing.md) | P0 | Todo | — | — | — | — |
| [PB09 Baseline MAD](PB09-mad-baseline.md) | P0 | Todo | — | — | — | — |
| [PB10 Alarm, episode và ghép sự cố](PB10-alert-episodes.md) | P0 | Todo | — | — | — | — |
| [PB11 Metric cửa sổ và sự kiện](PB11-evaluation-metrics.md) | P0 | Todo | — | — | — | — |
| [PB12 CLI baseline chạy xuyên suốt](PB12-baseline-workflow.md) | P0 | Todo | — | — | — | — |
| [PB13 Isolation Forest](PB13-isolation-forest.md) | P0 | Todo | — | — | — | — |
| [PB14 FrozenECOD đúng đặc tả](PB14-frozen-ecod.md) | P0 | Todo | — | — | — | — |
| [PB15 Runner thí nghiệm và đối chiếu cửa sổ](PB15-experiment-runner.md) | P0 | Todo | — | — | — | — |
| [PB16 F51, F55 và ablation nhóm cảm biến](PB16-feature-ablations.md) | P1 | Todo | — | — | — | — |
| [PB17 PCA và K-Means cho chế độ vận hành](PB17-operating-modes.md) | P1 | Todo | — | — | — | — |
| [PB18 Chọn cấu hình, ngưỡng và freeze](PB18-validation-freeze.md) | P0 | Todo | — | — | — | — |
| [PB19 Chấm test bằng cấu hình đã khóa](PB19-frozen-test-benchmark.md) | P0 | Todo | — | — | — | — |
| [PB20 Replay theo thời gian](PB20-causal-replay.md) | P1 | Todo | — | — | — | — |
| [PB21 Case study và báo cáo kết quả](PB21-results-report.md) | P0 | Todo | — | — | — | — |
| [PB22 Nghiệm thu tái lập và hướng dẫn chạy](PB22-reproducible-handoff.md) | P0 | Todo | — | — | — | — |
| [PB23 Block bootstrap theo ngày](PB23-block-bootstrap.md) | P2 | Todo | — | — | — | — |
| [PB24 Đối chiếu PyOD và FrozenECOD](PB24-pyod-comparison.md) | P2 | Todo | — | — | — | — |
| [PB25 Đặc trưng có trọng số thời gian](PB25-time-weighted-features.md) | P2 | Todo | — | — | — | — |
| [PB26 PCA cho detector và lọc tương quan](PB26-feature-transforms.md) | P2 | Todo | — | — | — | — |

## Cách dùng từng file

Mỗi file có mục tiêu/người dùng hưởng lợi, phạm vi, đầu vào/đầu ra, yêu cầu chức năng mã FR, yêu cầu chất lượng/trường hợp biên, tiêu chí nghiệm thu mã AC, checklist triển khai, rủi ro và bằng chứng đóng việc.

- **FR** xác định hệ thống cần làm gì và quy tắc xử lý; ví dụ `PB07-FR03`.
- **AC** là tình huống kiểm tra được để xác nhận FR; ví dụ `PB07-AC03` chỉ rõ đầu vào/thao tác và kết quả kỳ vọng.
- **Checklist** là các bước xây dựng; đánh dấu xong task chưa đồng nghĩa tất cả yêu cầu đã đạt.
- **Bằng chứng** ghi lệnh đã chạy, kết quả AC, đường dẫn artifact/log và commit/PR; chỉ đánh dấu nghiệm thu khi có bằng chứng.
- **Ghi chú thực hiện** chứa quyết định bổ sung, blocker và phần chuyển sang PB khác; khi cần sửa phạm vi, cập nhật cả backlog và file yêu cầu liên quan.

## Quy ước trạng thái

| Trạng thái | Khi sử dụng |
| --- | --- |
| Todo | Đã có yêu cầu, chưa chuẩn bị hoặc bắt đầu. |
| Ready | Phụ thuộc cần thiết đã đạt, đầu vào sẵn sàng, có thể bắt đầu. |
| In progress | Đang triển khai hoặc kiểm tra trong branch của PB. |
| In review | Có thay đổi và bằng chứng để review theo AC. |
| Blocked | Không thể tiến tiếp do vướng mắc đã ghi rõ trong file PB. |
| Done | AC đạt, bằng chứng đủ, thay đổi đã review và merge theo cách quản lý repo. |
| Deferred | Chủ động hoãn P1/P2, có lý do và ảnh hưởng phạm vi được ghi. |

Nếu làm một mình, tự review theo AC và lưu bằng chứng trước khi Done. P0 chưa đạt thì mốc bàn giao tương ứng chưa hoàn thành; Deferred không thay thế nghiệm thu. Ngày trong bảng dùng YYYY-MM-DD để dễ sắp xếp.

## Trình tự triển khai

| Mốc | PB | Điều kiện bàn giao |
| --- | --- | --- |
| M1 Dữ liệu | PB01–PB06 | Package/config, raw có checksum, audit, sự cố, split và EDA train. |
| M2 Baseline | PB07–PB12 | F35 W=5, MAD, episode/metric và CLI validation chạy xuyên suốt. |
| M3 Mô hình và thí nghiệm | PB13–PB17 | IF/FrozenECOD, X1/X2; mở rộng PB16/PB17 theo phạm vi. |
| M4 Đánh giá cuối | PB18–PB19 | Chọn bằng validation, freeze rồi mới chấm test. |
| M5 Bàn giao | PB20–PB22 | Replay nếu chọn, case study, report và kiểm chứng tái lập. |
| P2 Bổ sung | PB23–PB26 | Chỉ làm theo giả thuyết rõ và điều kiện phụ thuộc trong từng file. |

Luồng lõi theo backlog: **PB01 → … → PB15 → PB18 → PB19 → PB21 → PB22**. Đọc phụ thuộc trong file trước khi bắt đầu, vì một số PB có thể chuẩn bị độc lập. PB05 định nghĩa policy; PB07 hoàn thiện mask với lineage dữ liệu. PB16 cần xong trước freeze nếu muốn đưa biến thể vào test xác nhận. PB17 phải fit/chốt trên train trước khi diễn giải test. Thêm ý tưởng sau khi xem test được ghi exploratory hoặc cần tập đánh giá độc lập.

## Bắt đầu một PB

1. Mở file PB, đọc FR/AC, kiểm tra phụ thuộc; điền người phụ trách/hạn nếu đã có kế hoạch và chuyển Ready.
2. Từ `main` đã merge các phụ thuộc, tạo branch ghi trong file; chuyển In progress.
3. Triển khai theo checklist, thêm kiểm tra logic phù hợp ngay trong PB; lưu quyết định và blocker khi phát sinh.
4. Chạy các tình huống AC, ghi kết quả thực tế và bằng chứng; chuyển In review và điền PR.
5. Review/merge đạt yêu cầu thì chuyển Done, điền ngày xong. Tạo branch tiếp theo từ `main` đã cập nhật.

PB đầu tiên: [PB01 Khởi tạo dự án](PB01-project-scaffold.md), branch `chore/pb01-project-scaffold`.

## Nguyên tắc quản lý yêu cầu

- Các giá trị split, W, coverage, warm-up, threshold/merge và ECOD lấy theo pipeline/backlog; không đổi để tăng metric test.
- Những chi tiết được ghi “đề xuất” hoặc “cần ghi quyết định” là phần làm rõ khi triển khai, ví dụ bootstrap interval, mode tie-break hoặc thời gian giữ mẫu cho PB25. Chốt trong file/PR và config trước chạy thí nghiệm, không để thành mặc định ngầm.
- Mức chất lượng mô hình chưa có ngưỡng nghiệm thu AP/recall đặt trước. Nghiệm thu logic, tính nhân quả, tái lập, độ phủ và sự trung thực của báo cáo.
- Mọi PB giữ nguyên null/reason của mốc invalid và contract schema/hash của stage; không dùng test để fit/chọn cấu hình.
- Các nhánh PB23–PB26 là P2; trạng thái Todo không có nghĩa chúng bắt buộc để hoàn thành benchmark chính.

## Mẫu ghi chú khi thực hiện

Dán vào mục “Ghi chú thực hiện” của PB khi cần:

```text
Ngày:
Việc đã hoàn thành:
AC đã kiểm tra và kết quả:
Bằng chứng hoặc artifact:
Vướng mắc:
Quyết định và lý do:
Bước tiếp theo:
```
