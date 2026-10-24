# Yêu cầu MetroPT-3 — tập trung vào bài toán ML

Rà soát PB01–PB26 ngày **2026-10-24** theo yêu cầu giữ dự án đơn giản. Mục tiêu là trả lời: **Isolation Forest và FrozenECOD có cải thiện so với MAD không, cửa sổ thời gian có ích không, và các cảnh báo nói gì về dữ liệu?**

Các mã PB được giữ để tra cứu yêu cầu; **không phải 26 bước chạy, 26 module, hay 26 branch/PR bắt buộc**. Một thay đổi có thể hoàn thành nhiều PB liên quan. [Backlog](../product_backlog.md) quy định phạm vi hiện tại; từng file PB giữ quy tắc và kiểm tra cần thiết. [Quy ước đầu ra](../artifact_contracts.md) quy định phần lưu kết quả tối thiểu.

## Luồng làm việc

| Chặng | PB liên quan | Kết quả cần có |
| --- | --- | --- |
| 1. Hiểu và chuẩn bị dữ liệu | PB03–PB06; dùng PB01–PB02 đã có | Dữ liệu sạch, bảng sự cố, split thời gian, một notebook/báo cáo EDA. |
| 2. Có baseline chạy được | PB07–PB12 | F35 W=5 → MAD → score, cảnh báo, metric validation. |
| 3. So sánh và giải thích | PB13–PB17 | MAD/IF/FrozenECOD, W=1/5/15, bảng validation; phân tích Data Mining có câu hỏi rõ. |
| 4. Đánh giá cuối | PB18–PB19 | Chốt model/ngưỡng bằng validation, áp dụng lên test và báo cả sự cố bỏ sót. |
| 5. Báo cáo và chạy lại | PB21–PB22 | Bảng so sánh, timeline từng sự cố, kết luận/giới hạn và hướng dẫn tái lập. |

Đây là các chặng công việc, không bắt buộc xây năm tầng phần mềm. Một script Python gọi các hàm xử lý là đủ. Cài đặt/ingest hiện tại tiếp tục dùng; không viết lại phần ổn chỉ để làm nó ngắn hơn. Đích tiếp theo là chặng 1 rồi baseline MAD, không mở rộng cơ chế ingest.

## Giữ gì, giảm gì

**Giữ tính đúng của thí nghiệm:** split theo thời gian; feature chỉ dùng quá khứ; mọi thống kê/model fit từ train; chọn cấu hình/ngưỡng bằng validation; test không điều chỉnh lựa chọn; so model trên cùng mốc hợp lệ; báo coverage, thiếu nhãn và sự cố bỏ sót. Giữ test số học MAD/ECOD, biên thời gian, fill nếu dùng và metric/episode.

**Giảm hạ tầng:** không yêu cầu framework pipeline, registry service, tự động resume/retry, cache xuyên run theo nhiều tầng hash, manifest cha/con, trạng thái từng stage, hay log theo từng dòng/cửa sổ. Không thêm CLI/module chỉ vì có một mã PB. Config hiện có và checksum raw tiếp tục dùng; không mở rộng thành hệ thống version/hash mọi bảng trung gian.

**Lưu đầu ra để đọc và tái lập:** dữ liệu sạch/features khi cần dùng lại; bảng cấu hình và metric; score/episode của kết quả báo cáo; model/preprocessing đã chọn; một cấu hình đã chốt và ghi chú môi trường/code/data cho lần chạy. Mask là cột trong bảng, không bắt buộc file hoặc hash riêng. Chi tiết xem quy ước đầu ra.

**Log ngắn:** tên tác vụ đang chạy, số dòng/mốc hợp lệ, thời gian fit/score, nơi lưu kết quả, lỗi có hành động khắc phục. Thống kê chất lượng nằm trong data card/bảng kết quả. Debug chi tiết chỉ khi điều tra lỗi; không tạo thêm log để nghiệm thu mỗi PB.

**Test theo rủi ro ML:** không leakage, công thức đúng, fit/score không đổi reference, metric đúng mẫu số và một lượt chạy tích hợp. Không đặt mục tiêu số lượng test; không cần test hình thức cho cách đặt tên thư mục, hình vẽ hay nội dung log.

## Phần Data Mining và mở rộng

PB06 phân tích phân phối, tương quan và tín hiệu theo thời gian là phần cốt lõi. Proposal còn nêu PCA/K-Means và thử bỏ nhóm đặc trưng (PB16/PB17): giữ để làm gọn sau khi ba model chạy được, không bắt buộc triển khai mọi biến thể F51/F55 và mọi tổ hợp.

- **PCA/K-Means:** khảo sát các mẫu tín hiệu giống nhau, xem cảnh báo có tập trung vào trạng thái hiếm không; một notebook và bảng/biểu đồ đủ. Cụm không tự là nhãn hỏng.
- **Thử bỏ nhóm đặc trưng (ablation):** chạy lại một cấu hình khi bỏ một nhóm cảm biến để kiểm tra nhóm đó có giúp mô hình không. Chọn câu hỏi từ train/validation; nếu đánh giá test, chốt trước khi xem test.
- **PB20 và PB23–PB26:** hoãn khỏi phạm vi hiện tại. Replay, bootstrap, đối chiếu thư viện, trọng số thời gian và biến đổi feature chỉ mở khi có nhu cầu cụ thể. Chúng không chặn hoàn thành benchmark chính.

Không xóa các mục Data Mining đã nêu trong [proposal](../proposal/metropt3_proposal.md). Nếu quyết định bỏ hẳn chúng, cần điều chỉnh phạm vi proposal rõ ràng; không coi chúng là đã thực hiện. Pipeline Word là tài liệu thiết kế ban đầu; các yêu cầu hạ tầng được tinh gọn theo Markdown hiện tại, các quy tắc khoa học không đổi trừ khi ghi rõ quyết định.

## Bảng theo dõi

Giữ trạng thái đã ghi nhận của PB01/PB02; lần rà soát này không nghiệm thu lại code hoặc tự đóng việc. P1 được làm sau luồng chính; Deferred không phải Done.

| PB và yêu cầu | Ưu tiên | Trạng thái | Phụ trách | Hạn | Ngày xong | PR |
| --- | --- | --- | --- | --- | --- | --- |
| [PB01 Khởi tạo dự án, config và hợp đồng artifact](PB01-project-scaffold.md) | P0 | In review | Codex | — | — | — |
| [PB02 Nhập dữ liệu và khóa nguồn](PB02-data-ingestion.md) | P0 | In review | Codex | — | — | — |
| [PB03 Audit và chia đoạn dữ liệu](PB03-data-quality-audit.md) | P0 | Todo | — | — | — | — |
| [PB04 Bảng sự cố và quy tắc nhãn](PB04-event-labels.md) | P0 | Todo | — | — | — | — |
| [PB05 Temporal split và purge](PB05-temporal-splits.md) | P0 | Todo | — | — | — | — |
| [PB06 EDA trên train](PB06-train-eda.md) | P0 | Todo | — | — | — | — |
| [PB07 Đặc trưng cửa sổ F35 nhân quả](PB07-causal-window-features.md) | P0 | Todo | — | — | — | — |
| [PB08 Preprocessing chỉ fit trên train](PB08-train-preprocessing.md) | P0 | Todo | — | — | — | — |
| [PB09 Baseline MAD](PB09-mad-baseline.md) | P0 | Todo | — | — | — | — |
| [PB10 Alarm, episode và ghép sự cố](PB10-alert-episodes.md) | P0 | Todo | — | — | — | — |
| [PB11 Metric cửa sổ và sự kiện](PB11-evaluation-metrics.md) | P0 | Todo | — | — | — | — |
| [PB12 Baseline chạy xuyên suốt](PB12-baseline-workflow.md) | P0 | Todo | — | — | — | — |
| [PB13 Isolation Forest](PB13-isolation-forest.md) | P0 | Todo | — | — | — | — |
| [PB14 FrozenECOD đúng đặc tả](PB14-frozen-ecod.md) | P0 | Todo | — | — | — | — |
| [PB15 So sánh mô hình và cửa sổ](PB15-experiment-runner.md) | P0 | Todo | — | — | — | — |
| [PB16 Kiểm tra đóng góp nhóm đặc trưng](PB16-feature-ablations.md) | P1 | Todo | — | — | — | — |
| [PB17 PCA và K-Means cho chế độ vận hành](PB17-operating-modes.md) | P1 | Todo | — | — | — | — |
| [PB18 Chọn cấu hình, ngưỡng và freeze](PB18-validation-freeze.md) | P0 | Todo | — | — | — | — |
| [PB19 Chấm test bằng cấu hình đã khóa](PB19-frozen-test-benchmark.md) | P0 | Todo | — | — | — | — |
| [PB20 Replay theo thời gian](PB20-causal-replay.md) | P1 | Deferred | — | — | — | — |
| [PB21 Case study và báo cáo kết quả](PB21-results-report.md) | P0 | Todo | — | — | — | — |
| [PB22 Nghiệm thu tái lập và hướng dẫn chạy](PB22-reproducible-handoff.md) | P0 | Todo | — | — | — | — |
| [PB23 Block bootstrap theo ngày](PB23-block-bootstrap.md) | P2 | Deferred | — | — | — | — |
| [PB24 Đối chiếu PyOD và FrozenECOD](PB24-pyod-comparison.md) | P2 | Deferred | — | — | — | — |
| [PB25 Đặc trưng có trọng số thời gian](PB25-time-weighted-features.md) | P2 | Deferred | — | — | — | — |
| [PB26 PCA cho detector và lọc tương quan](PB26-feature-transforms.md) | P2 | Deferred | — | — | — | — |

## Cách dùng yêu cầu

- Đọc FR (quy tắc cần làm) và AC (cách kiểm tra); chúng không quy định số file hay class.
- Gộp PB cùng chặng vào một branch/PR khi thuận tiện. Các tên branch trong ghi chú lịch sử chỉ là gợi ý.
- Một lệnh kiểm tra và đường dẫn kết quả dùng chung có thể làm bằng chứng cho nhiều AC; không cần chép nhiều log/biên bản.
- Ghi vài dòng quyết định khi thay phương pháp hoặc phạm vi. Không chép lại cùng checklist ở backlog, file PB và PR.
- Done khi đầu ra cần thiết và kiểm tra liên quan đạt, đã review theo cách quản lý repo; không yêu cầu điểm AP/recall đẹp mới hoàn thành.

Các trạng thái dùng được: Todo, In progress, In review, Done, Deferred; dùng Blocked khi có vướng mắc thực sự. Phụ thuộc là nhu cầu dữ liệu/logic, không buộc chờ merge từng PB nhỏ mới làm phần tiếp theo.
