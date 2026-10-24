# PB22 Nghiệm thu tái lập và hướng dẫn chạy

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | M — tương đối, chưa quy đổi ngày |
| Mốc | M5 |
| Branch | `chore/pb22-reproducible-handoff` |
| Phụ thuộc | [PB21](PB21-results-report.md); [PB20](PB20-causal-replay.md) nếu làm replay |
| Nguồn | Backlog PB22; pipeline chương 14–16 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người tiếp nhận cần cài và chạy lại pipeline từ raw, kiểm tra được kết quả và biết chính xác phạm vi đã bàn giao.

## Phạm vi và ranh giới

Nghiệm thu tích hợp, tái lập, CI fixture nhỏ và tài liệu. Các unit/logic test quan trọng phải có ngay trong PB triển khai, không chờ tới PB22.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Các PB thuộc phạm vi đã chọn; raw; config; lockfile | Có report, frozen artifacts, tests và manifest hoàn chỉnh. |
| Đầu ra | Biên bản tái lập; CI checks; README vận hành | Lệnh thật, phiên bản, lỗi thường gặp và kết quả xác minh. |
| Đầu ra | Release/handoff inventory | Run/artifact/checksums/report và danh sách P1/P2 làm hoặc hoãn. |

## Yêu cầu chức năng

- **PB22-FR01:** Rà soát test nhân quả, split/fill provenance, ECOD ties/tails/aggregation/batch/state, metric/episode/null và test-label independence; bổ sung khoảng trống thực sự, không viết test chỉ lặp implementation.
- **PB22-FR02:** Chạy lại raw→report bằng môi trường mới từ lockfile/config/data version cố định; kiểm tra cùng grid/mask/alarm/episode/metrics và score trong dung sai đã ghi.
- **PB22-FR03:** Xác minh chuỗi checksum/schema/artifact cha và mọi alarm truy model/tau/window/source được; runtime và run_id mới có thể khác, không yêu cầu file binary serialization trùng byte.
- **PB22-FR04:** Thiết lập CI trên fixture nhỏ không cần tải/fit toàn MetroPT-3; CI báo lỗi có tác dụng chặn merge theo cách quản lý repo đã chọn.
- **PB22-FR05:** README nêu cài đặt, nguồn raw, từng stage thật, freeze/test, run/report paths, lỗi checksum/schema/missing artifact, config và phần chưa làm; kết quả công bố phải là số đã chạy.
- **PB22-FR06:** Đóng scope: P0 hoàn tất; P1/P2 được ghi Done hoặc hoãn có lý do; replay phải kiểm chứng nếu thuộc bàn giao. Lưu hardware/OS/Python/library/code/data/config trong manifest.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Dung sai phải công bố trước đối chiếu, không nới chỉ để giấu lỗi; nêu khác biệt nền tảng nếu có.
- Không commit raw/artifact lớn hoặc thông tin nhạy cảm của môi trường vào repo.

## Tiêu chí nghiệm thu

- [ ] **PB22-AC01** (FR01, FR04): **Khi** chạy suite và CI fixture, **thì** kiểm tra các bất biến quan trọng qua, lỗi fixture có thể bị phát hiện mà không cần full dataset.
- [ ] **PB22-AC02** (FR02, FR03): **Khi** người tiếp nhận làm theo README trong môi trường mới, **thì** tạo report từ raw, danh sách mốc/mask/alarm/metric khớp; score đúng dung sai.
- [ ] **PB22-AC03** (FR03, FR05): **Khi** thiếu raw, sai schema/hash hoặc chưa freeze mà chạy test, **thì** thông báo rõ hành động khắc phục, không báo thành công giả.
- [ ] **PB22-AC04** (FR05, FR06): **Khi** kiểm tra inventory và README cuối, **thì** đủ môi trường/artifacts/report, phân biệt phần đã làm/hoãn và không công bố kết quả chưa đo.

## Checklist triển khai

- [ ] Rà soát bộ test đã được thêm ngay trong từng PB, không dồn kiểm tra logic tới cuối; chạy bộ kiểm tra causality, split/fill provenance, ECOD ties/batch/state, metric/episode và độc lập của test.
- [ ] Chạy lại từ raw với lockfile và config cố định trong môi trường mới; so tập mốc, quality mask, score trong dung sai, alarm, episode và metric. Runtime được phép khác.
- [ ] Kiểm tra toàn vẹn chuỗi artifact, hướng dẫn sửa lỗi thiếu raw/sai schema/sai hash/chưa freeze và thực hiện các kiểm tra tự động trên fixture nhỏ trong CI.
- [ ] Cập nhật README với cài đặt, nguồn data, trình tự lệnh, vị trí đầu ra, cấu hình mẫu và kết quả đã thực sự đo; ghi môi trường/CPU/RAM/library/code hash trong manifest.

## Rủi ro và quyết định cần ghi nhận

- Khác OS/library có thể làm thay đổi số học: lock phiên bản và so trong dung sai, giữ metadata để điều tra.
- Chạy lại chỉ từ feature cache không chứng minh ingest/feature: ít nhất một lượt nghiệm thu phải từ raw.

## Bằng chứng để đóng PB

- [ ] Cung cấp log chạy sạch, đối chiếu hai run, kết quả test/CI và checklist bàn giao đã review.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Chưa có ghi chú. Khi triển khai, ghi quyết định bổ sung, vướng mắc và việc chuyển sang PB khác tại đây; giữ nguyên yêu cầu nguồn hoặc nêu rõ lý do thay đổi.
