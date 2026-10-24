# PB20 Replay theo thời gian

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P1 |
| Mốc | M5 — replay P1 |
| Phụ thuộc | [PB19](PB19-frozen-test-benchmark.md) |
| Nguồn | Backlog PB20; pipeline chương 11 |

Áp dụng [phạm vi tinh gọn](README.md) và [quy ước đầu ra](../artifact_contracts.md). PB là nhóm yêu cầu; có thể triển khai cùng các PB liên quan trong một script/branch. Không bắt buộc artifact riêng cho từng mục.

**Phạm vi hiện tại: Deferred.** Chỉ triển khai khi có câu hỏi hoặc nhu cầu cụ thể; các yêu cầu dưới đây áp dụng nếu mở lại mục này.

## Mục tiêu và nhu cầu

Người triển khai cần chứng minh việc xử lý tuần tự dữ liệu cho cùng kết quả với pipeline offline nhân quả.

## Phạm vi và ranh giới

Replay timestamp có thứ tự bằng model đã khóa. Cơ chế nhận dữ liệu trễ thực tế, API/service và lịch retrain chưa nằm trong replay đồ án.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Raw/interim rows theo timestamp; frozen artifacts | Đủ preprocessing/model/tau/schema/quality policy đã đánh giá. |
| Đầu ra | Replay scores/alarms/episodes | Mỗi mốc có valid/reason/version và lineage nhất quán offline. |
| Đầu ra | Báo cáo so replay với batch | Cùng grid/mask/score/alarm/episode, có dung sai công bố. |

## Yêu cầu chức năng

- **PB20-FR01:** Đưa bản ghi vào theo timestamp; tại mỗi phút t chỉ buffer dữ liệu tới t, đủ W+giới hạn fill, không đọc trước cho feature/quality.
- **PB20-FR02:** Nạp preprocessing/model/tau/schema một lần từ frozen artifact; mọi trạng thái model và ECDF giữ nguyên trong phiên replay.
- **PB20-FR03:** Reset buffer/fill/rolling/episode tại split hoặc gap; invalid xử lý đúng policy offline, không sinh score 0 thay null.
- **PB20-FR04:** Giữ model_version/run/source provenance; không âm thầm chỉnh cảnh báo quá khứ khi thêm quan sát tương lai. Nếu input ngoài thứ tự, từ chối rõ hoặc tạo phiên bản tính lại riêng có policy, không lẫn run chính.
- **PB20-FR05:** So từng mốc với batch reference cùng config: scheduled ticks, valid/reason, score, alarm và membership episode.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Buffer giải phóng dữ liệu không còn dùng nhưng vẫn giữ đủ fill lineage; không tích toàn bộ raw vào RAM để giả replay.
- Benchmark replay dùng cùng clock convention, biên và warm-up với offline.

## Tiêu chí nghiệm thu

- [ ] **PB20-AC01** (FR01, FR03, FR05): **Khi** replay fixture có thiếu mẫu, gap và biên split, **thì** grid/mask/reason/alarm/episode khớp batch.
- [ ] **PB20-AC02** (FR01, FR02, FR05): **Khi** đối chiếu score replay và batch, **thì** sai lệch trong dung sai model đã công bố; reference không đổi khi so trạng thái trong test.
- [ ] **PB20-AC03** (FR01, FR04): **Khi** thêm dữ liệu tương lai sau mốc đã phát alarm, **thì** score/alarm quá khứ không đổi.
- [ ] **PB20-AC04** (FR04): **Khi** đưa bản ghi cũ vào sau mốc đã xử lý, **thì** hành vi đúng policy đã ghi, không âm thầm sửa kết quả đã công bố.

## Rủi ro và quyết định cần ghi nhận

- Cách offline resample nhìn cả file có thể lén dùng tương lai: kiểm tra cùng fixture sửa tương lai.
- Reset thiếu một trạng thái như fill/episode khiến replay khác batch: kiểm tra từng loại biên.

## Kết quả cần xem

- [ ] Cung cấp lệnh replay, bảng đối chiếu từng mốc và test buffer/gap/future invariance.
