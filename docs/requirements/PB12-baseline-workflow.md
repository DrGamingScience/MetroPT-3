# PB12 Baseline chạy xuyên suốt

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M2 |
| Phụ thuộc | [PB09](PB09-mad-baseline.md), [PB11](PB11-evaluation-metrics.md) |
| Nguồn | Backlog PB12; pipeline chương 14–16 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người triển khai cần chạy được luồng raw→MAD→đánh giá validation để phát hiện lỗi tích hợp trước khi mở rộng mô hình.

## Phạm vi và ranh giới

Một script hoặc lệnh CLI mỏng gọi các hàm đã có và smoke test; cấu hình q=0.99 ban đầu chưa thay cho quy trình chọn/freeze PB18.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | PB02–PB11; config F35/W=5 | Raw đúng checksum, events/splits/features/preprocessing/MAD sẵn sàng. |
| Đầu ra | Một điểm chạy baseline từ raw tới validation | Gọi hàm trực tiếp, kiểm tra input; không bắt buộc một CLI cho mỗi bước. |
| Đầu ra | Baseline validation run; lockfile; manifest | Score/episode/metric/timeline, config/seed, raw version, code và phiên bản dependencies. |

## Yêu cầu chức năng

- **PB12-FR01:** Gọi tuần tự các hàm chuẩn bị, feature, fit và đánh giá từ một script/CLI. Kiểm tra input cần thiết (file, cột, split, finite); lỗi thì dừng rõ lý do, không xuất bảng kết quả cuối như thành công. Không xây engine stage/manifest cha-con.
- **PB12-FR02:** Chạy MAD F35 W=5 trên train reference; tính tau từ validation reference, quantile 0.99 method=higher và alarm > tau; merge gap=300 giây.
- **PB12-FR03:** Tạo scores, episodes, metric và timeline train/validation với mọi mốc/quality reason; không mở benchmark test hoặc dùng nhãn test cho baseline milestone.
- **PB12-FR04:** Lưu config/seed, raw version/checksum, Git commit và phiên bản Python/dependencies một lần cho bộ kết quả. Ghi fit/score time trong bảng; không cần hardware/resource logger hoặc metadata riêng từng stage.
- **PB12-FR05:** Smoke test đoạn train/validation đủ warm-up, rồi baseline trên validation đầy đủ; chốt lockfile từ môi trường thực sự chạy qua.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Run lỗi và run hoàn tất phân biệt rõ; chạy lại không ghi đè run khác.
- CLI help/hướng dẫn dùng đúng stage đã triển khai; kết quả phải truy từ report về raw.

## Tiêu chí nghiệm thu

- [ ] **PB12-AC01** (FR01, FR02, FR03): **Khi** chạy script/CLI baseline từ raw theo hướng dẫn, **thì** có score/episode/metrics/timeline validation và model MAD fit từ train.
- [ ] **PB12-AC02:** **Khi** thiếu input, sai tên/thứ tự feature hoặc dữ liệu không hữu hạn tới model, **thì** dừng rõ lỗi; không tạo summary thành công giả.
- [ ] **PB12-AC03** (FR02, FR03): **Khi** xem ngưỡng baseline và tập metric, **thì** tau chỉ từ validation reference; metric dùng toàn bộ validation hợp lệ.
- [ ] **PB12-AC04:** **Khi** chạy lại cùng raw/config/phiên bản thư viện/seed, **thì** cùng grid/mask/alarm và score trong dung sai; lưu đủ thông tin để chạy lại, không bắt buộc hash mọi artifact.

## Rủi ro và quyết định cần ghi nhận

- Smoke test quá ngắn không vượt warm-up sẽ không chấm được mốc nào: chọn đoạn có đủ lịch sử và ghi coverage.
- Dùng nhầm model/features làm sai kết quả: truyền input tường minh trong cùng lần chạy, kiểm tra cột và tham số; không xây hash graph.

## Kết quả cần xem

- [ ] Ghi lệnh baseline, vị trí bảng/hình và môi trường đã chạy; một ghi chú dùng chung cho smoke test và validation đầy đủ.
