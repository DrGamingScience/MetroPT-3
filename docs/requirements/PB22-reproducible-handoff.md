# PB22 Nghiệm thu tái lập và hướng dẫn chạy

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Mốc | M5 |
| Phụ thuộc | [PB21](PB21-results-report.md); [PB20](PB20-causal-replay.md) nếu làm replay |
| Nguồn | Backlog PB22; pipeline chương 14–16 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

## Mục tiêu và nhu cầu

Người tiếp nhận cần cài và chạy lại pipeline từ raw, kiểm tra được kết quả và biết chính xác phạm vi đã bàn giao.

## Phạm vi và ranh giới

Một lượt chạy lại từ raw, kiểm tra logic quan trọng và hướng dẫn ngắn; CI fixture nhỏ là tiện ích tùy chọn. Các unit/logic test quan trọng phải có ngay trong PB triển khai, không chờ tới PB22.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Các PB thuộc phạm vi đã chọn; raw; config; lockfile | Có report, cấu hình/model đã chọn, tests và thông tin môi trường. |
| Đầu ra | README với lệnh thật; ghi kết quả lần chạy lại | Lệnh thật, phiên bản, lỗi thường gặp và kết quả xác minh. |
| Đầu ra | Các đầu ra báo cáo và phạm vi đã làm | Đường dẫn config/model/bảng/report; nêu phần làm hoặc hoãn ngay trong README. |

## Yêu cầu chức năng

- **PB22-FR01:** Rà soát test nhân quả, split/fill provenance, ECOD ties/tails/aggregation/batch/state, metric/episode/null và test-label independence; bổ sung khoảng trống thực sự, không viết test chỉ lặp implementation.
- **PB22-FR02:** Chạy lại raw→report bằng môi trường mới từ lockfile/config/data version cố định; kiểm tra cùng grid/mask/alarm/episode/metrics và score trong dung sai đã ghi.
- **PB22-FR03:** Đối chiếu grid/mask/score/alarm/metric với bộ kết quả đã báo cáo. Biết mỗi bảng dùng model/tau/config và raw nào; không kiểm tra chuỗi hash artifact cha/con hoặc đòi binary serialization trùng byte.
- **PB22-FR04:** Chạy các test nhỏ quan trọng bằng pytest. Có thể thêm một CI job khi repo cần, nhưng CI, branch protection và release automation không phải điều kiện nghiệm thu đồ án.
- **PB22-FR05:** README nêu cài đặt, nguồn raw, lệnh chạy thực sự có, cấu hình/model đã chọn, vị trí bảng/report và phạm vi chưa làm. Nêu cách xử lý lỗi thiếu file/sai cột khi cần; không viết tài liệu vận hành nhiều tầng.
- **PB22-FR06:** Xác nhận luồng ML chính hoàn tất và ghi phần Data Mining đã làm. PB20/PB23–PB26 hoãn không chặn bàn giao. Giữ config/seed, raw version, code và phiên bản dependencies; ghi máy/n_jobs một lần nếu so timing.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Dung sai phải công bố trước đối chiếu, không nới chỉ để giấu lỗi; nêu khác biệt nền tảng nếu có.
- Không commit raw/artifact lớn hoặc thông tin nhạy cảm của môi trường vào repo.

## Tiêu chí nghiệm thu

- [ ] **PB22-AC01:** **Khi** chạy pytest, **thì** các kiểm tra số học, nhân quả, train-only, episode/metric và tích hợp liên quan đạt trên fixture nhỏ; CI không bắt buộc.
- [ ] **PB22-AC02** (FR02, FR03): **Khi** người tiếp nhận làm theo README trong môi trường mới, **thì** tạo report từ raw, danh sách mốc/mask/alarm/metric khớp; score đúng dung sai.
- [ ] **PB22-AC03:** **Khi** thiếu raw/model/cấu hình đã chọn hoặc sai feature schema, **thì** lỗi nêu input cần sửa; không tự fit lại bằng test hoặc báo thành công giả.
- [ ] **PB22-AC04:** **Khi** làm theo README, **thì** tìm được config/model/bảng/report và thông tin môi trường; phần chưa làm được nêu đúng, không công bố kết quả chưa đo.

## Rủi ro và quyết định cần ghi nhận

- Khác OS/library có thể làm thay đổi số học: lock phiên bản và so trong dung sai, giữ metadata để điều tra.
- Chạy lại chỉ từ feature cache không chứng minh ingest/feature: ít nhất một lượt nghiệm thu phải từ raw.

## Kết quả cần xem

- [ ] Ghi lệnh chạy sạch, kết quả đối chiếu và kiểm tra logic trong README hoặc ghi chú kết quả. Không cần log chi tiết/biên bản/inventory riêng.
