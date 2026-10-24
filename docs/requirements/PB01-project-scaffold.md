# PB01 Khởi tạo dự án, config và hợp đồng artifact

[Mục lục và bảng theo dõi](README.md) · [Product backlog](../product_backlog.md)

| Thuộc tính | Giá trị |
| --- | --- |
| Ưu tiên | P0 |
| Quy mô | S — tương đối, chưa quy đổi ngày |
| Mốc | M1 |
| Branch | `chore/pb01-project-scaffold` |
| Phụ thuộc | — |
| Nguồn | Backlog PB01; pipeline chương 14–15 |

Trạng thái, người phụ trách, hạn hoàn thành và PR được cập nhật tại bảng theo dõi trong README của folder này. Checklist dưới đây dùng để theo dõi chi tiết trong PB.

## Mục tiêu và nhu cầu

Người triển khai cần cài và chạy dự án theo một cách thống nhất để các PB sau dùng chung config, schema và quy ước lưu kết quả.

## Phạm vi và ranh giới

Thiết lập package, CLI khung, cấu hình và hợp đồng dữ liệu giữa các stage. Logic ingest, feature, detector và metric được triển khai trong các PB tương ứng.

## Đầu vào và đầu ra

| Loại | Dữ liệu hoặc sản phẩm | Hợp đồng cần đáp ứng |
| --- | --- | --- |
| Đầu vào | Pipeline và product backlog | Các giá trị mặc định và thứ tự stage; chưa yêu cầu raw. |
| Đầu ra | pyproject.toml; src/metropt3/; tests/; configs/base.yaml | Package cài được, CLI có help, config có kiểm tra kiểu/miền. |
| Đầu ra | Tài liệu hợp đồng artifact; .gitignore | Stage sau tra được schema/version, đường dẫn và quy tắc hash. |

## Yêu cầu chức năng

- **PB01-FR01:** Tổ chức source layout ngay tại root repo; lệnh `python -m metropt3.cli --help` hoạt động sau khi cài package trong môi trường riêng.
- **PB01-FR02:** Config chứa nhóm dataset/split/features/quality/ecod/selection/alerts/reproducibility; ranh giới split tăng dần, W và stride dương, quantile trong (0,1), batch size nguyên dương.
- **PB01-FR03:** Config mẫu phản ánh pipeline: W=5, stride=60 giây, W ứng viên 1/5/15, warm-up=930 giây, seed=42, gộp=300 giây và timezone=null.
- **PB01-FR04:** Định nghĩa cách tạo run_id, canonical config hash, manifest và schema version; ghi quan hệ artifact cha/con và quy tắc không ghi đè run đã hoàn tất.
- **PB01-FR05:** Khai báo dependencies; PyOD là tùy chọn. Ignore môi trường/raw/artifact lớn; lệnh chưa có logic phải báo chưa hỗ trợ hoặc không đăng ký, không trả kết quả giả.

## Yêu cầu chất lượng và xử lý trường hợp biên

- Không cố định đường dẫn tuyệt đối theo máy cá nhân; mọi đường dẫn giải được từ root/config.
- Config sai phải nêu trường và lý do; help không cần tải dữ liệu hoặc fit model.

## Tiêu chí nghiệm thu

- [x] **PB01-AC01** (FR01, FR03): **Khi** cài package trong môi trường sạch và gọi help, **thì** lệnh thoát thành công, liệt kê đúng tính năng đã có và đọc được config mẫu.
- [x] **PB01-AC02** (FR02): **Khi** nạp config có W=0, q=1 hoặc split đảo ngược, **thì** bị từ chối với tên trường, không tạo run thành công.
- [x] **PB01-AC03** (FR04): **Khi** hash hai config có cùng nội dung nhưng khác thứ tự khóa, **thì** nhận cùng config hash; đổi giá trị có ý nghĩa làm hash đổi.
- [x] **PB01-AC04** (FR05): **Khi** kiểm tra ignore và các stage khung, **thì** raw/môi trường không bị theo dõi ngoài ý muốn; stage chưa làm không giả báo thành công.

## Checklist triển khai

- [x] Tạo `pyproject.toml`, `src/metropt3/`, `tests/`, `configs/base.yaml` và quy ước đường dẫn `data/`, `artifacts/<run_id>/`, `reports/<run_id>/` ngay tại root repo hiện tại.
- [x] Khai báo các phụ thuộc theo pipeline; thêm pytest cho kiểm tra logic. PyOD chỉ là phụ thuộc tùy chọn phục vụ đối chiếu.
- [x] Đưa tham số split, cửa sổ, chất lượng, ECOD, q, seed và gộp cảnh báo vào config; kiểm tra config sai ngay khi nạp.
- [x] Định nghĩa schema artifact, `run_id`, hash config và quan hệ đầu vào/đầu ra của từng stage; thêm `.gitignore` cho dữ liệu, môi trường và đầu ra lớn.
- [x] Khởi tạo `cli --help`; các stage được bổ sung dần cùng PB triển khai, không báo thành công cho stage chưa có logic.

## Rủi ro và quyết định cần ghi nhận

- Hash phụ thuộc định dạng YAML sẽ làm mất cache: canonical hóa giá trị đã parse trước khi hash.
- Đặt sẵn lockfile chưa chạy thử có thể gây hiểu nhầm: chỉ chốt môi trường sau smoke test PB12.

## Bằng chứng để đóng PB

- [x] Ghi lệnh cài/import/help, ví dụ config bị từ chối và đường dẫn tài liệu hợp đồng artifact.
- [ ] Ghi kết quả từng AC, vị trí artifact hoặc log và commit/PR có thể kiểm tra; không chỉ đánh dấu đã làm.
- [ ] Cập nhật trạng thái, PR và ngày hoàn thành trong bảng theo dõi sau khi review đạt yêu cầu.

## Ghi chú thực hiện

Ngày triển khai và kiểm tra: 2026-10-24. Branch `chore/pb01-project-scaffold`; thay đổi đã được kiểm tra và ghi nhận trong lịch sử Git của branch. Chưa có PR/merge nên trạng thái là In review và chưa điền ngày hoàn thành.

| AC | Bằng chứng | Kết quả |
| --- | --- | --- |
| AC01 | Cài editable `.[dev]` vào `.venv` mới, Python 3.13.9; import đủ dependencies; help/check-config từ CLI. | Đạt. Config mẫu W=5, stride=60, warm-up=930, seed=42, merge=300. |
| AC02 | `tests/test_config.py` và `tests/test_cli.py`: W=0, q=0/1, split bằng/đảo, sai kiểu, thiếu/lạ/trùng key, NaN/inf. | Đạt. Lỗi có tên trường, CLI exit 2, không tạo run. |
| AC03 | Test đổi thứ tự khóa/comment, timestamp/số tương đương, seed khác và di chuyển repo. | Đạt. Hash ổn định cho config tương đương, đổi khi seed đổi; resolved paths không phụ thuộc cwd. |
| AC04 | Test gọi các stage chưa có; kiểm tra `git check-ignore` cho `.venv`, raw/interim/processed, artifacts/reports và egg-info. | Đạt. Stage chưa có exit 2; dữ liệu/đầu ra lớn được ignore. |

Lệnh xác minh từ root repo:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m metropt3.cli --help
.\.venv\Scripts\python.exe -m metropt3.cli check-config --config configs/base.yaml
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Kết quả: **63 passed**; pip check không có dependency lỗi. Config hash mẫu: `5682fdfd2397ea08bf85dd24e85921b3693b9b33012c16ffe561002b991a881b`.

Tệp triển khai: [pyproject](../../pyproject.toml), [config mẫu](../../configs/base.yaml), [config loader](../../src/metropt3/config.py), [CLI](../../src/metropt3/cli.py), [tests config](../../tests/test_config.py), [tests CLI](../../tests/test_cli.py), [hợp đồng artifact](../artifact_contracts.md).

Các quyết định bổ sung đã ghi trong hợp đồng: `paths.project_root` tương đối với YAML; từ chối unknown/duplicate keys; canonical hash chuẩn hóa số/timestamp và không bao gồm absolute paths giải lúc chạy. PB01 định nghĩa run ID/manifest, bộ tạo run thực tế thuộc PB12. Lockfile vẫn để PB12 sau smoke test pipeline.

Môi trường đã xác minh: Python 3.13.9; numpy 2.5.4; pandas 3.1.0; scipy 1.18.1; scikit-learn 1.9.1; pyarrow 26.0.0; PyYAML 6.0.3; joblib 1.6.0; matplotlib 3.11.2; seaborn 0.13.2; pytest 9.1.1. Đây là ghi nhận cài đặt PB01, không phải lockfile.
