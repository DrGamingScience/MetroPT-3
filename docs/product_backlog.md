# Product backlog MetroPT-3

Phạm vi thực hiện được tinh gọn ngày **2026-10-24**: một đồ án ML so sánh MAD, Isolation Forest và FrozenECOD trên chuỗi thời gian MetroPT-3. Đầu ra chính là kết quả thực nghiệm có thể giải thích và chạy lại. Trạng thái từng mục ở [requirements/README](requirements/README.md); quy tắc chi tiết ở các file PB liên kết bên dưới.

## Cách triển khai

Dùng package/config/ingest đã có. Viết các hàm xử lý dữ liệu, feature, model và đánh giá; gọi từ một script hoặc CLI mỏng. Notebook phù hợp cho EDA và báo cáo. Không xây framework điều phối, plugin model, registry service hay cache tự động khi chưa có nhu cầu thực tế.

Mã PB để tra cứu, không tương ứng bắt buộc với branch, PR, module, lệnh CLI hoặc một tệp đầu ra. Có thể triển khai nhiều PB cùng chặng. Không thêm giấy tờ nghiệm thu cho từng bước; các bảng kết quả và kiểm tra logic là bằng chứng.

| Chặng | Phạm vi | Đích hoàn thành |
| --- | --- | --- |
| Dữ liệu | PB03–PB06 trên nền PB01–PB02 | Hiểu dữ liệu, xử lý chất lượng, có nhãn sự cố và split. |
| Baseline | PB07–PB12 | MAD F35 W=5 chạy từ raw tới metric validation. |
| So sánh | PB13–PB17 | IF/ECOD, ảnh hưởng W, bảng validation và phân tích Data Mining gọn. |
| Đánh giá cuối | PB18–PB19 | Chọn trên validation; test với model/ngưỡng cố định. |
| Báo cáo | PB21–PB22 | Case study, kết luận và một lượt tái lập từ raw. |

## Overview toàn bộ PB

| PB | Quyết định | Trọng tâm và phần tinh gọn |
| --- | --- | --- |
| [PB01](requirements/PB01-project-scaffold.md) | Giữ nền đã có | Package/config/seed/đường dẫn. Không xây thêm hợp đồng cha/con hoặc version cho mọi stage. |
| [PB02](requirements/PB02-data-ingestion.md) | Giữ nền đã có | Raw, nguồn, checksum, kiểm tra đủ cột. Không mở rộng cơ chế khóa/chống sửa hoặc viết lại ingest. |
| [PB03](requirements/PB03-data-quality-audit.md) | Giữ; cùng chặng dữ liệu | Missing/trùng/timestamp/gap và quy tắc làm sạch; một data card, bảng cleaned, bảng lỗi khi cần. |
| [PB04](requirements/PB04-event-labels.md) | Giữ; cùng chặng dữ liệu | Bốn sự cố trong events.csv và hàm gán nhãn; không có lifecycle nhãn riêng. |
| [PB05](requirements/PB05-temporal-splits.md) | Giữ; cùng chặng dữ liệu | Split thời gian, reset cửa sổ/fill, warm-up; mask là cột, không hệ thống artifact riêng. |
| [PB06](requirements/PB06-train-eda.md) | Giữ; cùng chặng dữ liệu | Notebook/báo cáo hiểu train; sampling có seed/quy tắc, không bắt buộc sample manifest. |
| [PB07](requirements/PB07-causal-window-features.md) | Giữ | F35, thời gian thật, coverage, không nhìn tương lai. Fill chỉ khi dữ liệu cần; không lưu danh sách nguồn cho từng ô/cửa sổ. |
| [PB08](requirements/PB08-train-preprocessing.md) | Giữ; cùng baseline | Lọc cột theo train, finite/schema, complete-case mặc định. Chưa xây imputer/drift-monitor nhiều chế độ. |
| [PB09](requirements/PB09-mad-baseline.md) | Giữ; cùng baseline | Công thức MAD, floor và score dễ kiểm chứng. |
| [PB10](requirements/PB10-alert-episodes.md) | Giữ; cùng đánh giá | score > tau; gộp cảnh báo; chỉ alarm thật khớp sự cố. |
| [PB11](requirements/PB11-evaluation-metrics.md) | Giữ; cùng đánh giá | AP, precision/recall/F1, event recall, delay, cảnh báo/ngày và coverage. |
| [PB12](requirements/PB12-baseline-workflow.md) | Thu gọn mạnh | Script nối baseline; không triển khai engine stage, hash graph hay hardware/resource logger. |
| [PB13](requirements/PB13-isolation-forest.md) | Giữ | Wrapper nhỏ cho sklearn, score đúng dấu, grid nhỏ, seed và timing. |
| [PB14](requirements/PB14-frozen-ecod.md) | Giữ lõi số học | ECDF train cố định, ties/tails/aggregation đúng, score độc lập batch. Kiểm tra trạng thái trong test; không hash mỗi batch. |
| [PB15](requirements/PB15-experiment-runner.md) | Thu gọn mạnh | Vòng lặp cấu hình và bảng kết quả, chung mốc so sánh. Tái dùng score trong lần chạy; chưa làm cache xuyên run/registry framework. |
| [PB16](requirements/PB16-feature-ablations.md) | Phần Data Mining có giới hạn | Sau ba model, chọn một câu hỏi thử bỏ nhóm cảm biến hoặc mở rộng feature; không chạy mọi tổ hợp F51/F55/ablation. |
| [PB17](requirements/PB17-operating-modes.md) | Phần Data Mining có giới hạn | PCA/K-Means để hiểu trạng thái tín hiệu; notebook + vài hình/bảng, không thành hệ thống phân loại trạng thái. |
| [PB18](requirements/PB18-validation-freeze.md) | Giữ nguyên tắc, giảm thủ tục | Một frozen_config.json ghi lựa chọn/ngưỡng/đường dẫn model; không dịch vụ freeze hoặc chuỗi checksum. |
| [PB19](requirements/PB19-frozen-test-benchmark.md) | Giữ | Chỉ score model đã chọn, báo kết quả và các seed đã định trước; không dùng test để chọn lại. |
| [PB20](requirements/PB20-causal-replay.md) | Hoãn | Replay phục vụ hướng triển khai tuần tự; fixture nhân quả đã đủ cho benchmark offline hiện tại. |
| [PB21](requirements/PB21-results-report.md) | Giữ; cùng bàn giao | Report/notebook, mọi sự cố test và vài cảnh báo ngoài báo cáo; không xây report engine/case manifest riêng. |
| [PB22](requirements/PB22-reproducible-handoff.md) | Thu gọn | README, phiên bản dependencies, kiểm tra logic và một lượt chạy sạch. CI tùy điều kiện; không release inventory/hạ tầng vận hành. |
| [PB23](requirements/PB23-block-bootstrap.md) | Hoãn | Chỉ mở khi cần phân tích bất định; ít sự cố vẫn phải nêu là giới hạn. |
| [PB24](requirements/PB24-pyod-comparison.md) | Hoãn | Không cần benchmark thư viện để hoàn thành so sánh ba model. |
| [PB25](requirements/PB25-time-weighted-features.md) | Hoãn | Chỉ mở nếu audit cho thấy nhịp không đều đặt ra câu hỏi cụ thể. |
| [PB26](requirements/PB26-feature-transforms.md) | Hoãn | PCA cho detector/lọc tương quan là thử nghiệm mới; không tự thêm sau khi xem test. |

## Thí nghiệm đủ để trả lời bài toán

1. **Hiểu dữ liệu (X0):** schema, chất lượng, nhịp, tương quan và bối cảnh cảm biến trên train.
2. **So model (X1):** MAD/IF/FrozenECOD trên F35 W=5, cùng mốc hợp lệ.
3. **Vai trò thời gian (X2):** W=1/5/15 và F7 lấy giá trị mới nhất còn đủ tươi; giữ common mask. Chạy grid IF nhỏ đã định trước trên validation. 24 lượt fit F35 là giới hạn của grid hiện tại, không phải chỉ tiêu phải mở rộng.
4. **Giải thích/Data Mining (PB16/PB17):** một phân tích PCA/K-Means gọn và một câu hỏi về nhóm đặc trưng. F51, F55 và từng ablation là lựa chọn, không phải một tổ hợp bắt buộc. Chọn câu hỏi từ train/validation, ghi biến thể đã làm.
5. **Chốt và đánh giá:** chọn W/tham số/ngưỡng bằng validation; giữ seed chính 42, kiểm tra IF với 7/2026 theo kế hoạch trước test. Độ nhạy merge 1/5/10 phút (X7) là bổ sung validation, không chặn benchmark chính merge=5 phút.

Không báo đã hoàn tất mọi X3–X7 khi chỉ làm một phần. Proposal có PCA/K-Means và phân tích bỏ nhóm đặc trưng; giữ mục đích nghiên cứu đó. Giảm hạ tầng không đồng nghĩa bỏ nội dung ML; nếu bỏ hẳn phần đã nêu trong proposal, ghi thay đổi phạm vi rõ ràng trước bàn giao.

## Những quy tắc không giản lược

- Train trước 2020-03-01; validation từ đó đến trước 2020-05-01; test từ 2020-05-01 đến hết raw. Không random split hoặc dịch biên để tăng điểm.
- Window `(t-W,t]`, stride 60 giây; không lấy tương lai. Reset ở biên split/gap; warm-up chung 930 giây giữ theo config hiện tại.
- Fit cadence/preprocessing/model từ train. Reference loại nguồn giao sự cố; evaluation gán nhãn tại window_end. Nếu fill, tính cả nguồn gốc giá trị fill.
- Chỉ chọn cấu hình và ngưỡng từ validation. Test giữ nguyên model, cột, ngưỡng và chính sách; không refit train+validation sau calibration.
- So metric trên cùng mốc; invalid không biến thành normal. Báo cả coverage, N/A, sự cố bỏ sót và số sự cố ít. Ngoài báo cáo không mặc nhiên là lỗi thật hay cảnh báo sai đã xác nhận.
- Công thức MAD/ECOD và cách ghép alarm/sự cố có test nhỏ tính tay được. Không thay thuật toán chỉ để bớt vài dòng code.

## Đầu ra và điều kiện hoàn thành

Theo [quy ước đầu ra tối thiểu](artifact_contracts.md): raw manifest hiện có; data card + events + dữ liệu sạch; features và cột mask; cấu hình/phiên bản môi trường; model/preprocessing đã chọn; bảng validation/test, score/episode và report. Tên file có thể gộp khi cùng mục đích, không buộc một file cho mỗi khái niệm.

Một bộ kết quả cần nguồn dữ liệu, code/phiên bản thư viện, config/seed và các model đã dùng. Checksum raw có ích; không cần hash mọi bảng/mask/schema hay log mọi lần gọi hàm. Console báo tiến độ ngắn, timing fit/score và đường dẫn kết quả. Chỉ lưu debug khi điều tra lỗi.

Hoàn thành khi luồng ML chạy được, kiểm tra quan trọng đạt, kết quả trung thực và chạy lại được theo README. Không có ngưỡng AP/recall tối thiểu để ép kết quả đẹp. Không tạo thêm phase/abstraction/artifact nếu không chỉ ra được câu hỏi ML, lỗi thực tế hoặc bước phân tích sẽ dùng nó.
