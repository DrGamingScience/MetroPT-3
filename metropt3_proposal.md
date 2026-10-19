# ĐỀ XUẤT ĐỒ ÁN MACHINE LEARNING & DATA MINING

## Phát hiện bất thường trên dữ liệu cảm biến máy nén khí MetroPT-3

**Tên tiếng Anh:** Anomaly Detection in Railway Air Compressor Sensor Data Using MetroPT-3.

### 1. Bài toán, mục tiêu và ứng dụng

Máy nén khí trên tàu điện ngầm hoạt động ở nhiều chế độ, khiến các cảm biến thay đổi ngay cả khi thiết bị vẫn bình thường. Một giá trị khác thường chưa đủ để kết luận có sự cố. Đề tài khai thác quan hệ giữa nhiều cảm biến và diễn biến theo thời gian để phát hiện những khoảng vận hành lệch khỏi dữ liệu tham chiếu, sau đó đối chiếu với báo cáo sự cố.

- **Đầu vào:** các phép đo cảm biến và timestamp đến thời điểm hiện tại; đặc trưng được tổng hợp từ cửa sổ 1, 5 hoặc 15 phút gần nhất.
- **Đầu ra:** điểm bất thường cho từng cửa sổ, trạng thái bình thường/bất thường theo ngưỡng, danh sách đợt cảnh báo và các cảm biến có biến động hoặc sai số đáng chú ý. Điểm số thể hiện mức lệch so với dữ liệu tham chiếu, không phải xác suất hỏng hóc.
- **Mục tiêu:** so sánh baseline thống kê dùng MAD, Isolation Forest và ECOD; đánh giá khả năng phát hiện các khoảng sự cố, mức cảnh báo ngoài báo cáo và ảnh hưởng của đặc trưng thời gian.
- **Ứng dụng tương lai:** hỗ trợ bảng giám sát tình trạng máy nén khí, khoanh vùng thời điểm cần kiểm tra và cung cấp thông tin cho quyết định bảo trì. Hệ thống thực tế cần được xác minh trên thêm thiết bị và sự cố.

**Phạm vi:** anomaly detection trên chuỗi thời gian đa biến bằng học máy cổ điển. Các mô hình học từ giai đoạn tham chiếu được xem là bình thường; báo cáo sự cố phục vụ kiểm tra dữ liệu, hiệu chỉnh khi phù hợp và đánh giá. Đề tài không đặt mục tiêu dự đoán thời điểm hỏng trong tương lai hoặc ước lượng tuổi thọ còn lại.

### 2. Bộ dữ liệu sử dụng

Sử dụng **MetroPT-3** từ [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset), DOI: [10.24432/C5VW3R](https://doi.org/10.24432/C5VW3R). Theo UCI, bộ dữ liệu có **1.516.948 bản ghi và 15 biến cảm biến**, thu thập từ tháng 2 đến tháng 8/2020; tệp CSV khoảng 208 MB. Dữ liệu là bảng chuỗi thời gian đa biến, gồm timestamp, 7 tín hiệu analog liên tục và 8 tín hiệu digital.

| Nhóm dữ liệu | Ví dụ và vai trò |
|---|---|
| Áp suất | TP2, TP3, H1, DV_pressure, Reservoirs: mô tả trạng thái hệ thống khí nén. |
| Nhiệt độ và dòng điện | Oil_temperature, Motor_current: mô tả nhiệt và tải động cơ. |
| Tín hiệu trạng thái | COMP, TOWERS, MPG: cung cấp bối cảnh chế độ vận hành. |
| Thời gian và chỉ mục | Timestamp dùng để tạo cửa sổ và chia tập; cột chỉ mục không dùng làm đặc trưng. |

Dữ liệu chưa có nhãn lỗi cho từng dòng; UCI cung cấp **bốn khoảng sự cố rò rỉ khí** để đối chiếu. Nhãn đánh giá sẽ được xây dựng từ những khoảng này sau khi kiểm tra mốc bắt đầu/kết thúc. Bản ghi ngoài khoảng sự cố chỉ được xem là bình thường theo báo cáo, không bảo đảm hoàn toàn không có bất thường.

Trước khi thực nghiệm, kiểm tra schema, dữ liệu thiếu/trùng, khoảng ngắt và tần suất timestamp. Mô tả UCI chưa thống nhất giữa 1 Hz và 0,1 Hz, nên độ dài cửa sổ được xác định theo thời gian thực. Lưu nguồn tải, cấu trúc dữ liệu và quyết định tiền xử lý trong một data card.

### 3. Phương pháp và thuật toán

Đề tài so sánh các phương pháp dựa trên độ lệch thống kê, khả năng cô lập mẫu và xác suất ở đuôi phân phối thực nghiệm. Mỗi phương pháp tạo điểm bất thường cho dữ liệu mới; ngưỡng cảnh báo được hiệu chỉnh trên validation. Các mô hình sử dụng cùng nguồn cảm biến, cùng các mốc chấm điểm hợp lệ và cùng quy tắc đánh giá.

**Baseline thống kê.** Với đặc trưng liên tục, tính độ lệch tuyệt đối so với median của train, chia cho độ lệch tuyệt đối trung vị (MAD) có giá trị sàn để tránh chia cho 0. Lấy độ lệch chuẩn hóa lớn nhất làm điểm bất thường. Phương pháp dễ kiểm tra và giúp xác định lợi ích của các mô hình phức tạp hơn; hạn chế là chưa mô tả được đầy đủ quan hệ giữa cảm biến.

**Isolation Forest.** Dùng các phép chia ngẫu nhiên trong không gian đặc trưng để cô lập quan sát; mẫu dễ bị cô lập hơn được xem là đáng nghi hơn. Huấn luyện trên train tham chiếu và chấm điểm cửa sổ mới. Khảo sát số cây, kích thước mẫu mỗi cây và nhóm đặc trưng. Đây là mô hình chính để đánh giá bất thường đa biến; cần phân tích khả năng cảnh báo nhầm khi một chế độ vận hành hợp lệ ít xuất hiện trong train.

**ECOD (Empirical-Cumulative-distribution-based Outlier Detection).** Ước lượng hàm phân phối tích lũy thực nghiệm (ECDF) cho đuôi trái và đuôi phải của từng đặc trưng trên train tham chiếu. Theo bài báo, cộng các giá trị âm log xác suất đuôi theo ba cách: toàn bộ đuôi trái, toàn bộ đuôi phải và chọn đuôi theo độ lệch phân phối; lấy điểm lớn nhất làm điểm bất thường. Đề tài áp dụng ECOD với ECDF và độ lệch phân phối cố định từ train khi chấm validation/test, có giá trị sàn cho xác suất để tránh log(0). ECOD không cần nhãn lỗi hoặc tinh chỉnh tham số cho bước tính điểm; ngưỡng cảnh báo vẫn chọn trên validation. Phân tích đóng góp của từng đặc trưng giúp giải thích cảnh báo. Hạn chế là mô hình hóa từng đặc trưng riêng, nên có thể bỏ sót bất thường chỉ thể hiện qua quan hệ giữa cảm biến và cảnh báo nhầm ở chế độ vận hành hợp lệ ít gặp.

**Hiệu chỉnh và so sánh.** Thống nhất chiều điểm số để giá trị lớn hơn luôn thể hiện bất thường hơn. Chọn ngưỡng và cấu hình bằng validation. Báo cáo hiệu quả phát hiện cùng chi phí tính toán của tất cả phương pháp.

**Data Mining và diễn giải.** Phân tích tương quan, PCA và K-Means để khảo sát các chế độ vận hành. Đối chiếu biến động cảm biến quanh đợt cảnh báo, đóng góp của từng đặc trưng trong điểm ECOD và kết quả khi loại từng nhóm đặc trưng. Các cụm và mức đóng góp của đặc trưng hỗ trợ diễn giải hành vi mô hình, không trực tiếp xác định nguyên nhân sự cố.

### 4. Quy trình xử lý và thiết kế thực nghiệm

1. **Tiền xử lý:** sắp xếp timestamp, kiểm tra trùng/thiếu và lập bảng sự cố. Sửa lỗi xác định được, giữ giá trị cực đoan hợp lệ. Điền thiếu bằng thống kê train hoặc forward fill có giới hạn; không nội suy bằng dữ liệu tương lai qua khoảng ngắt dài.
2. **Tạo đặc trưng:** tính mean, standard deviation, min/max, xu hướng cho tín hiệu liên tục; tỷ lệ bật và số lần chuyển trạng thái cho tín hiệu digital. Thử cửa sổ 1, 5, 15 phút, chấm điểm mỗi phút; kiểm tra độ đầy đủ của cửa sổ theo timestamp.
3. **Chia theo thời gian:** train ở giai đoạn đầu, validation kế tiếp, test cuối. Chốt ranh giới theo timeline trước khi chạy mô hình; báo cáo số sự cố từng tập, giữ mỗi sự cố trọn trong một tập và loại cửa sổ dùng chung dữ liệu thô qua ranh giới.
4. **Huấn luyện:** loại cửa sổ giao với sự cố khỏi train tham chiếu. Fit imputer, scaler, PCA và mô hình trên train; chọn cấu hình bằng validation. Với ECOD, giữ cố định ECDF và độ lệch phân phối từ train; kiểm tra cách triển khai để việc chấm điểm không tái ước lượng phân phối bằng validation/test.
5. **Khóa cấu hình:** chọn ngưỡng phân vị trên validation tham chiếu, đối chiếu với sự cố validation nếu có. Khóa ngưỡng và quy tắc gộp cảnh báo trước test.
6. **Đánh giá test:** áp dụng cấu hình đã khóa, tạo bảng metric và timeline; lưu seed, phiên bản thư viện, thời gian chạy và cấu hình để tái lập.

### 5. Độ đo và cách đánh giá

**Nhãn đối chiếu:** y = 1 khi thời điểm kết thúc cửa sổ nằm trong khoảng sự cố được báo cáo, y = 0 ở các thời điểm còn lại. So sánh nhãn này với cảnh báo tại ngưỡng đã chọn trên validation. TP là cửa sổ được cảnh báo và khớp sự cố; FP là cửa sổ được cảnh báo ngoài sự cố; FN là cửa sổ trong sự cố bị bỏ sót; TN là cửa sổ ngoài sự cố không bị cảnh báo.

**Độ đo ở cấp cửa sổ:**

| Độ đo | Công thức và ý nghĩa |
|---|---|
| Precision | TP / (TP + FP): tỷ lệ cửa sổ cảnh báo khớp với sự cố được báo cáo; càng cao càng tốt. |
| Recall | TP / (TP + FN): tỷ lệ cửa sổ trong sự cố được phát hiện; càng cao càng tốt. |
| F1-score | 2 * TP / (2 * TP + FP + FN): tổng hợp precision và recall tại ngưỡng đã khóa; càng cao càng tốt. |
| Average Precision (AP) | AP = sum_k (R_k - R_(k-1)) * P_k, với P_k và R_k là precision/recall tại các ngưỡng theo thứ tự recall tăng. Đánh giá thứ hạng điểm bất thường qua nhiều ngưỡng; càng cao càng tốt. |

Báo cáo thêm **confusion matrix (TP, FP, FN, TN)** và tỷ lệ mẫu dương. AP được tính bằng `average_precision_score`; không đồng nhất AP với diện tích đường precision-recall tính bằng quy tắc hình thang. Accuracy chỉ là thông tin bổ sung vì tỷ lệ sự cố nhỏ. Các chỉ số đo mức khớp với báo cáo, không xác nhận mọi bất thường đều là lỗi.

**Độ đo ở cấp sự kiện:** dự kiến gộp các cảnh báo cách nhau không quá 5 phút thành một đợt; chốt quy tắc trên validation trước khi đánh giá test.

| Độ đo | Công thức và ý nghĩa |
|---|---|
| Event recall | Số sự cố có ít nhất một cảnh báo trong khoảng sự cố / tổng số sự cố có thể đánh giá. Báo cáo cả số đếm và tỷ lệ; càng cao càng tốt. |
| Detection delay | Thời điểm cảnh báo đầu tiên trong sự cố - thời điểm bắt đầu sự cố, tính bằng phút. Báo cáo từng sự cố và trung vị; càng thấp càng tốt. Liệt kê sự cố bị bỏ sót riêng. |
| Đợt cảnh báo ngoài báo cáo/ngày | Số đợt không giao với khoảng sự cố / tổng thời lượng quan sát hợp lệ quy đổi sang ngày. Thể hiện gánh nặng cảnh báo; càng thấp càng tốt, nhưng cần xét cùng event recall. |

**Chỉ số ưu tiên:** AP cho khả năng xếp hạng; event recall, detection delay và đợt cảnh báo ngoài báo cáo/ngày cho giá trị giám sát. Precision, recall và F1 bổ sung đánh giá ở ngưỡng đã khóa. Do báo cáo sự cố chưa phải nhãn bất thường đầy đủ, FP và đợt cảnh báo ngoài báo cáo không mặc nhiên là cảnh báo sai đã xác nhận.

**Đánh giá bổ sung:** thời gian huấn luyện/chấm điểm và phân tích cảnh báo đại diện. Ghi N/A khi mẫu số bằng 0 hoặc nhãn không đủ để diễn giải.


### Nguồn tham khảo

1. [UCI: MetroPT-3 Dataset](https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset) - dữ liệu và báo cáo sự cố, DOI 10.24432/C5VW3R.
2. [scikit-learn: IsolationForest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) - thuật toán và tham số Isolation Forest.
3. Li và cộng sự (2022), [ECOD: Unsupervised Outlier Detection Using Empirical Cumulative Distribution Functions](https://arxiv.org/abs/2201.00382) - thuật toán ECOD; đề tài dùng ECDF tham chiếu cố định từ train để đánh giá theo thời gian.
4. [PyOD: Mã nguồn ECOD](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/ecod.html) - tham khảo triển khai; cần kiểm tra cách tính ECDF và tổng hợp điểm so với bài báo trước khi sử dụng.
5. scikit-learn: [Average Precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) và [Precision, Recall, F-score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html) - định nghĩa và cách tính độ đo.

