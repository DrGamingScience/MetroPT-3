# PB12 CLI baseline chạy xuyên suốt

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M2 |
| Branch | `feat/pb12-baseline-workflow` |
| Phụ thuộc | [PB09](PB09-mad-baseline.md), [PB11](PB11-evaluation-metrics.md) |
| Nguồn | Backlog PB12; pipeline chương 14–16 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người triển khai cần chạy được luồng raw→MAD→đánh giá validation để phát hiện lỗi tích hợp trước khi mở rộng mô hình.

## Phạm vi và ranh giới

Nối các stage đã có thành CLI baseline và smoke test; cấu hình q=0.99 ban đầu chưa thay cho quy trình chọn/freeze PB18.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | PB02–PB11; config F35/W=5 | Raw đúng checksum, events/splits/features/preprocessing/MAD sẵn sàng. |
| Đầu ra | CLI audit/features/train/validate và bước ingest/events/split | Các lệnh có thật, kiểm tra đầu vào và artifact hash theo stage. |
| Đầu ra | Baseline validation run; lockfile; manifest | Score/episode/metric/timeline, code/data/config hashes và môi trường. |

## Yêu cầu chức năng

- **PB12-FR01:** Nối stage theo dependencies, kiểm tra artifact/schema/checksum trước khi dùng; stage lỗi phải trả mã lỗi và không đánh dấu các stage sau hoàn tất.
- **PB12-FR02:** Chạy MAD F35 W=5 trên train reference; tính tau từ validation reference, quantile 0.99 method=higher và alarm > tau; merge gap=300 giây.
- **PB12-FR03:** Tạo scores, episodes, metric và timeline train/validation với mọi mốc/quality reason; không mở benchmark test hoặc dùng nhãn test cho baseline milestone.
- **PB12-FR04:** Run manifest ghi seed, config/data/code hashes, Python/library/OS/CPU/RAM, fit/score time và tài nguyên đo được; chưa đo thì ghi rõ thay vì tạo số giả.
- **PB12-FR05:** Smoke test đoạn train/validation đủ warm-up, rồi baseline trên validation đầy đủ; chốt lockfile từ môi trường thực sự chạy qua.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Run lỗi và run hoàn tất phân biệt rõ; chạy lại không ghi đè run khác.
- CLI help/hướng dẫn dùng đúng stage đã triển khai; kết quả phải truy từ report về raw.

## Tiêu chí nghiệm thu

- [ ] **PB12-AC01** (FR01, FR02, FR03): **Khi** chạy luồng baseline từ raw bằng hướng dẫn CLI, **thì** có score/episode/metrics/timeline validation và model MAD fit từ train.
- [ ] **PB12-AC02** (FR01): **Khi** thay checksum một artifact hoặc xóa schema đầu vào, **thì** stage dùng nó dừng rõ lỗi, không sinh report thành công giả.
- [ ] **PB12-AC03** (FR02, FR03): **Khi** xem ngưỡng baseline và tập metric, **thì** tau chỉ từ validation reference; metric dùng toàn bộ validation hợp lệ.
- [ ] **PB12-AC04** (FR04, FR05): **Khi** chạy lại với lockfile/config/raw cố định, **thì** cùng grid/mask/alarm và score trong dung sai; manifest đủ môi trường/hash.

## Checklist triển khai

- [ ] Nối ingest/audit/events/split/features/train/validate trong CLI; giữ schema và checksum giữa các stage.
- [ ] Chạy MAD F35 W=5, q=0.99 từ validation reference, `method=higher`, gộp 5 phút; đây là cấu hình baseline ban đầu, chưa là cấu hình chính đã chọn.
- [ ] Sinh score, episode, metric và timeline train/validation; tạo run manifest có config/code/data hash, seed, môi trường, thời gian và tài nguyên.
- [ ] Smoke test một đoạn train/validation nhỏ có warm-up; sau đó chạy baseline validation đầy đủ. Chốt phiên bản thực tế bằng lockfile.

## Rủi ro và quyết định cần ghi nhận

- Smoke test quá ngắn không vượt warm-up sẽ không chấm được mốc nào: chọn đoạn có đủ lịch sử và ghi coverage.
- CLI gọi các bước rời mà không kiểm tra artifact cha làm dùng nhầm run: đối chiếu hashes tại mỗi stage.

## Bằng chứng để đóng PB

- [ ] Ghi chính xác chuỗi lệnh baseline, run_id, vị trí report/manifest/lockfile và kết quả smoke + validation đầy đủ.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
