# Chuỗi chỉ số tình trạng rừng hằng năm {{tong.nam_dau}}–{{tong.nam_cuoi}} cho {{tong.n_khu}} khu bảo tồn ở {{tong.n_nuoc}} quốc gia, từ bản đồ loại rừng 10 m

*Bài báo dạng mô tả dữ liệu (Data Descriptor), theo khung của tạp chí Scientific Data. Bản thảo tiếng Việt.*

## Tóm tắt

Theo dõi rừng trong khu bảo tồn thường dựa vào bản đồ độ che phủ cây, vốn không phân biệt rừng tự nhiên với rừng trồng hay cây công nghiệp. Chúng tôi giới thiệu một bộ dữ liệu về tình trạng rừng hằng năm giai đoạn {{tong.nam_dau}}–{{tong.nam_cuoi}} cho {{tong.n_khu}} khu bảo tồn quốc gia, trên cạn, có rừng ở {{tong.n_nuoc}} nước thuộc sáu vùng địa sinh học. Bộ dữ liệu được tính từ bản đồ loại rừng ForTy V2 Beta ở độ phân giải 10 m. Các khu đại diện cho {{tong.N_khu}} khu đủ điều kiện, qua thiết kế điều tra toàn bộ hoặc rút mẫu ngẫu nhiên phân tầng có trọng số. Với mỗi khu và mỗi năm, bộ dữ liệu cung cấp diện tích bảy lớp phủ và chỉ số tình trạng rừng (FCI, 0–100) có trọng số theo độ tự nhiên của lớp. Kèm theo là chỉ tiêu xu hướng, ma trận chuyển đổi lớp và các ước lượng cấp quốc gia với khoảng tin cậy bootstrap phân tầng. Bộ dữ liệu cho phép so sánh nhất quán giữa các nước về cả lượng và chất lượng rừng trong hệ thống khu bảo tồn. Nó cũng cho thấy các ước lượng phụ thuộc thế nào vào thiết kế mẫu và vào độ bất định của một sản phẩm phân loại thử nghiệm.

## Bối cảnh và tổng quan

Khu bảo tồn là trụ cột của các cam kết bảo tồn toàn cầu, trong đó có mục tiêu bảo vệ 30% diện tích đất vào năm 2030 của Khung Đa dạng sinh học toàn cầu Côn Minh – Montreal[1]. Hiệu quả của khu bảo tồn trong việc giữ rừng thường được đánh giá bằng bản đồ mất độ che phủ cây toàn cầu[2,3]. Các bản đồ này ghi nhận nơi cây bị mất, nhưng không phân biệt rừng nguyên sinh, rừng tái sinh, rừng trồng và cây công nghiệp. Hệ quả là chúng không trả lời được câu hỏi rừng trong khu bảo tồn đang thay đổi về **chất lượng** như thế nào: một khu có thể giữ nguyên độ che phủ trong khi rừng tự nhiên bị thay bằng rừng trồng, hoặc ngược lại.

Bộ bản đồ Forest Typology (ForTy) lấp một phần khoảng trống này[4]. ForTy v1 phân loại toàn bộ mặt đất năm 2020 ở độ phân giải 10 m thành sáu lớp theo định nghĩa của FAO[5] và của Quy định chống phá rừng của Liên minh châu Âu[6]. Độ chính xác tổng thể là 90,2% với sáu lớp và 95,5% với rừng / không rừng, kiểm định trên 8.190 điểm do chuyên gia giải đoán[4]. Bản V2 Beta mở rộng thành chuỗi hằng năm {{tong.nam_dau}}–{{tong.nam_cuoi}} và tách rừng nguyên sinh thành hai lớp, trưởng thành và đang phục hồi. Nhờ vậy, lần đầu tiên có thể tính một chỉ số chất lượng rừng nhất quán theo thời gian cho hàng nghìn khu bảo tồn ở nhiều nước.

Bộ dữ liệu mô tả ở đây chuyển bản đồ pixel thành các bản ghi cấp khu bảo tồn và cấp quốc gia, sẵn sàng cho phân tích thống kê. Ba lựa chọn thiết kế định hình bộ dữ liệu. (i) Tổng thể khu bảo tồn được định nghĩa thống nhất cho mọi nước từ Cơ sở dữ liệu Khu bảo tồn Thế giới (WDPA)[7]: khu cấp quốc gia, trên cạn, do nhà nước quản lý, có rừng. (ii) Ở nước có nhiều khu, một mẫu ngẫu nhiên phân tầng theo diện tích thay cho điều tra toàn bộ, với trọng số để ước lượng cấp quốc gia không chệch. (iii) Diện tích các lớp trong khu lớn được ước lượng bằng mẫu điểm cố định qua các năm, nên chi phí tính toán không phụ thuộc diện tích khu. Bộ dữ liệu phục vụ so sánh giữa các nước, phân tích xu hướng và lựa chọn khu cần kiểm tra thực địa. Nó cũng là tình huống để đánh giá độ ổn định theo thời gian của ForTy V2 Beta.

{{hinh:composition|**Hình 1.** Cơ cấu lớp phủ ForTy trong các khu bảo tồn đủ điều kiện của {{tong.n_nuoc}} nước (diện tích có trọng số W).}}

## Phương pháp

### Dữ liệu đầu vào

Bản đồ loại rừng: ForTy V2 Beta trên Google Earth Engine (`projects/nature-trace/assets/forest_typology/v2_beta/<năm>`), mỗi năm là một ImageCollection chia ô. Bảy band uint8 là xác suất tương đối (0–250) của bảy lớp. Lớp của pixel là lớp có xác suất cao nhất: (1) rừng nguyên sinh trưởng thành, (7) rừng nguyên sinh đang phục hồi, (2) rừng tái sinh tự nhiên, (3) rừng trồng, (4) rừng trồng thâm canh, (5) cây công nghiệp và nông lâm kết hợp, (6) đất khác. Rừng tự nhiên gồm lớp 1, 2 và 7.

Ranh giới khu bảo tồn: WDPA (`WCMC/WDPA/current/polygons`)[7]. Biome: RESOLVE Ecoregions 2017[8].

### Chọn nước

{{tong.n_nuoc}} nước được chọn theo hai trục: vùng địa sinh học (Indo-Malaya, Australasia, Neotropic, Afrotropic, Nearctic, Palearctic) và nhóm thu nhập của Ngân hàng Thế giới. Trong mỗi ô, nước có nhiều khu bảo tồn có rừng nhất được chọn, cộng với ba nước chung vùng sinh thái với Việt Nam (Lào, Campuchia, Thái Lan). Danh sách: Việt Nam, Lào, Campuchia, Thái Lan, Philippines, Indonesia, Brazil, Madagascar, Cameroon, Gabon, Mỹ, Úc, Nga.

### Tổng thể khu bảo tồn

Một khu thuộc tổng thể khi thỏa mãn tất cả các điều kiện sau:

- `DESIG_TYPE = National`, trạng thái Designated hoặc Inscribed;
- không phải khu thuần biển, phần đất ≥ 1 km²;
- `GOV_TYPE` là nhà nước quản lý hoặc đồng quản lý (bỏ khu tư nhân, bản địa, cộng đồng);
- rừng ForTy {{tong.nam_dau}} (lớp 1–5 và 7) chiếm ≥ {{tong.min_forest_pct}}% diện tích **và** ≥ {{tong.min_biome_pct}}% diện tích nằm trong biome rừng của RESOLVE.

Các bản ghi WDPA cùng `SITE_ID` (khu nhiều mảnh) được gộp thành một khu. Bản ghi lặp cùng `SITE_PID` chỉ tính một lần. Tổng thể có {{tong.N_khu}} khu.

### Thiết kế mẫu

Nước có ≤ {{tong.census_max}} khu đủ điều kiện được điều tra toàn bộ. Nước nhiều khu hơn được rút ngẫu nhiên phân tầng theo diện tích đất, với bốn tầng 1–10, 10–100, 100–1.000 và ≥ 1.000 km². Số khu phân bổ theo tỷ lệ số khu của tầng, mỗi tầng ít nhất 2 khu, với hạt giống ngẫu nhiên cố định. Cỡ mẫu được chọn bằng mô phỏng sao cho sai số 95% của chỉ tiêu trung bình theo khu khoảng ±3 điểm: Indonesia {{IDN.n}}, Úc {{AUS.n}}, Brazil {{BRA.n}}, Nga {{RUS.n}} và Mỹ {{USA.n}} khu (Bảng 1). Mỗi khu mang trọng số W = N(h) / n(h), với N(h) và n(h) là số khu của tầng h trong tổng thể và trong mẫu.

{{bang:tang_mau|**Bảng 1.** Số khu rút / số khu đủ điều kiện theo tầng diện tích, và số khu tính bằng mẫu điểm.}}

### Diện tích các lớp trong mỗi khu

Khu có polygon < {{tong.nguong_diem_km2}} km² được đếm toàn bộ pixel bằng `frequencyHistogram` trong hệ UTM của khu, ở 10 m. Một request tính cả {{tong.n_nam}} năm. Khi vượt giới hạn bộ nhớ, độ phân giải lùi về 20 m rồi 30 m.

Khu lớn hơn được ước lượng bằng {{tong.n_diem}} điểm ngẫu nhiên trong polygon (sau khi bỏ các thành phần không phải đa giác). Lớp của từng điểm được đọc ở 10 m cho cả {{tong.n_nam}} năm, với cùng một bộ điểm. Mỗi điểm đại diện cho diện tích khu / {{tong.n_diem}}. Các điểm được sinh một lần rồi lấy mẫu trên ảnh ForTy toàn cầu theo lô 1.000 điểm. Có {{tong.n_khu_diem}} khu được tính theo cách này.

Ma trận chuyển đổi lớp {{tong.nam_dau}}→{{tong.nam_cuoi}} được tính cùng cách. Mỗi cặp lớp được xếp vào năm nhóm: không đổi; đổi trong cùng nhóm (tự nhiên ↔ tự nhiên, trồng ↔ trồng); tăng rừng hoặc phục hồi; rừng chuyển thành đất khác; rừng tự nhiên chuyển thành rừng trồng hoặc cây công nghiệp.

### Chỉ số tình trạng rừng

FCI(t) = 100 × Σ w(c) · A(c, t) / Σ A(c, t), với A(c, t) là diện tích lớp c năm t trên toàn khu và w(c) là trọng số của lớp (Bảng 2). Trọng số phản ánh mức độ tự nhiên giả định, từ 1 cho rừng nguyên sinh trưởng thành đến 0 cho đất khác. ΔFCI = FCI {{tong.nam_cuoi}} − FCI {{tong.nam_dau}}. FCI phần có rừng tính cùng công thức nhưng chỉ trên các lớp rừng. ΔFCI tương đối (% của FCI {{tong.nam_dau}}) chỉ tính khi FCI {{tong.nam_dau}} ≥ {{tong.rel_min_fci}}.

{{bang:trong_so_fci|**Bảng 2.** Trọng số w của các lớp trong FCI.}}

Xu hướng của mỗi khu trên chuỗi {{tong.n_nam}} năm được ước lượng bằng độ dốc Theil–Sen[9] và kiểm định Mann–Kendall[10,11]. Khu được xếp **suy giảm** hoặc **phục hồi** khi |ΔFCI| ≥ {{tong.min_delta}} điểm và p < {{tong.max_p}}; còn lại là ổn định / không rõ. Năm có bước giảm lớn nhất và tỷ trọng của bước đó trong tổng mức giảm được ghi lại, để phân biệt suy giảm dồn vào một năm (cháy, bão) với suy giảm dần (chuyển đổi đất).

### Ước lượng cấp quốc gia

Hai loại ước lượng được tính cho mỗi nước. **Theo khu** gồm trung vị và trung bình có trọng số W, mỗi khu đủ điều kiện một phiếu, phản ánh tình trạng của khu điển hình. **Gộp** coi mọi khu đủ điều kiện là một vùng, với diện tích từng lớp nhân W, phản ánh lượng rừng. Khoảng tin cậy 95% của trung vị và chênh lệch giữa từng cặp nước dùng bootstrap phân tầng[12]: 2.000 lần, rút lại các khu trong từng tầng, giữ trọng số. Giá trị p hai phía bằng hai lần tỷ lệ lần rút mà chênh lệch đổi dấu.

## Bản ghi dữ liệu

Bộ dữ liệu gồm các tệp CSV (UTF-8 có BOM, dấu thập phân là dấu chấm), lưu tại thư mục `outputs/so_sanh_13/` của kho mã nguồn [hoangvietanh/forty-pa-compare](https://github.com/hoangvietanh/forty-pa-compare/tree/main/outputs/so_sanh_13) (Bảng 3). Khóa nối giữa các tệp là `SITE_ID` (mã khu của WDPA) và `ISO3`.

| Tệp | Một dòng là | Nội dung chính |
|---|---|---|
| `khu_<ISO3>.csv` | một khu trong tổng thể của nước | tên, loại, `GOV_TYPE`, diện tích đất, tỷ lệ rừng và biome rừng, cờ đủ điều kiện, tầng, N(h), n(h), W, tọa độ tâm; `OK` đánh dấu khu đã phân tích |
| `dien_tich_lop_tung_khu.csv` | một khu × một năm × một lớp | diện tích (ha), độ phân giải đếm (m) hoặc số điểm mẫu |
| `chuyen_doi_lop_tung_khu.csv` | một khu × một cặp lớp {{tong.nam_dau}}→{{tong.nam_cuoi}} | diện tích (ha), nhóm chuyển đổi, độ phân giải đếm hoặc số điểm mẫu |
| `chi_so_FCI_tung_khu.csv` | một khu đã phân tích | FCI và FCI phần có rừng {{tong.nam_dau}}, {{tong.nam_cuoi}}, ΔFCI, ΔFCI tương đối, độ dốc Theil–Sen, p Mann–Kendall, kết luận, năm và tỷ trọng bước giảm lớn nhất, thay đổi ròng rừng tự nhiên, tỷ lệ diện tích đổi lớp, FCI từng năm |
| `FCI_theo_nuoc_theo_nam.csv` | một nước × một năm | FCI gộp, FCI phần có rừng, tỷ lệ rừng, FCI trung vị các khu |
| `so_sanh_nuoc.csv` | một nước | các chỉ tiêu trạng thái và xu hướng cấp quốc gia kèm khoảng tin cậy 95% |
| `kiem_dinh_tung_cap.csv` | một cặp nước | trung vị ΔFCI của hai nước, chênh lệch, khoảng tin cậy 95%, p |
| `xep_hang_nuoc.csv` | một nước | hạng theo từng chỉ tiêu và hạng chung |

**Bảng 3.** Các tệp của bộ dữ liệu. Năm tệp cuối là kết quả dẫn xuất và có thể tính lại từ ba tệp đầu bằng mã nguồn đi kèm.

## Đánh giá kỹ thuật

### Sai số của mẫu điểm trong khu

Với {{tong.n_diem}} điểm ngẫu nhiên, sai số chuẩn của tỷ lệ diện tích một lớp tối đa khoảng 0,7 điểm phần trăm, tương ứng ±1,4 điểm ở mức 95%. Vì các điểm được giữ cố định qua các năm, sai số của ΔFCI nhỏ hơn nhiều so với sai số của FCI từng năm. Thử trên 8 khu Việt Nam 150–1.200 km² đã có kết quả đếm toàn bộ pixel: FCI {{tong.nam_cuoi}} từ mẫu điểm lệch tối đa 0,77 điểm và ΔFCI lệch tối đa 0,11 điểm.

### Sai số của mẫu khu

Khoảng tin cậy bootstrap phân tầng của ΔFCI trung vị (Hình 2) hẹp ở các nước điều tra toàn bộ và rộng hơn ở các nước rút mẫu. Ví dụ, Việt Nam có khoảng tin cậy từ {{VNM.dfci_ci_lo}} đến {{VNM.dfci_ci_hi}}, Mỹ từ {{USA.dfci_ci_lo}} đến {{USA.dfci_ci_hi}}. Ở các nước rút mẫu, tầng ≥ 1.000 km² chỉ có vài khu, nên các chỉ tiêu gộp theo diện tích (ΔFCI gộp, thay đổi ròng rừng tự nhiên) phụ thuộc mạnh vào vài khu lớn. Úc là ví dụ: ΔFCI gộp {{AUS.dfci_pooled}} điểm, trong khi ΔFCI trung vị chỉ {{AUS.dfci_median}}. Trung vị có trọng số ổn định hơn với cách rút mẫu, và là chỉ tiêu nên dùng khi so sánh giữa các nước.

{{hinh:ci|**Hình 2.** Theo nước: FCI {{tong.nam_cuoi}} trung vị có trọng số (trái), FCI phần có rừng {{tong.nam_cuoi}} gộp (giữa) và ΔFCI {{tong.nam_dau}}–{{tong.nam_cuoi}} trung vị có trọng số (phải), với khoảng tin cậy 95% bootstrap phân tầng.}}

### Độ ổn định theo thời gian của ForTy V2 Beta

Độ chính xác công bố của ForTy là của bản 2020[4] và chưa được kiểm định cho chuỗi thời gian. Hai dấu hiệu trong bộ dữ liệu cho thấy mức nhiễu giữa các năm. Thứ nhất, tỷ lệ diện tích đổi lớp gộp {{tong.nam_dau}}→{{tong.nam_cuoi}} lớn hơn nhiều so với thay đổi ròng. Ở Việt Nam, trung vị diện tích đổi lớp là {{VNM.changed_pct_median}}%, trong khi rừng tự nhiên chỉ thay đổi ròng {{VNM.natural_change_pct}}%; phần lớn là dao động qua lại giữa rừng và đất khác. Thứ hai, ở các nước ổn định, ΔFCI trung vị chỉ từ {{tong.on_dinh_dfci_min}} đến {{tong.on_dinh_dfci_max}} điểm, cùng cỡ với mức nhiễu này. Do đó, chênh lệch giữa các nước dưới khoảng 0,1 điểm không nên được diễn giải là khác biệt thực, dù kiểm định bootstrap có thể báo ý nghĩa thống kê. {{tong.n_cap_khac_biet}} trong {{tong.n_cap}} cặp nước có p < 0,05.

{{hinh:series|**Hình 3.** FCI gộp theo năm của mỗi nước. Chuỗi trơn ở hầu hết các nước. Suy giảm đều ở Campuchia và Lào khác với bước giảm đột ngột năm {{AUS.nam_giam_manh}} ở Úc.}}

### Tính nhất quán với các sự kiện đã biết

Mẫu hình thay đổi phù hợp với các sự kiện đã biết. Ở Úc, {{AUS.n_khu_giam_nam_do}} trong {{AUS.n_decline}} khu suy giảm có bước giảm lớn nhất vào năm {{AUS.nam_giam_khu}}, sau mùa cháy 2019–2020. Thay đổi chủ yếu là đổi lớp trong nhóm rừng tự nhiên ({{AUS.doi_1}}% diện tích), không phải mất rừng ({{AUS.doi_3}}%). Ngược lại, ở Campuchia, {{KHM.doi_3}}% diện tích chuyển từ rừng sang đất khác, và mức giảm trải qua nhiều năm. Các nước có rừng ẩm nhiệt đới nguyên vẹn (Cameroon, Gabon) có từ {{CMR.doi_0}}% đến {{GAB.doi_0}}% diện tích không đổi lớp. Sự phân biệt giữa xáo trộn tự nhiên và chuyển đổi đất cho thấy chuỗi ForTy V2 Beta mang tín hiệu có ý nghĩa, dù chưa được kiểm định định lượng.

## Ghi chú sử dụng

- **Trọng số.** Mọi chỉ tiêu cấp quốc gia phải dùng W. Ở nước điều tra toàn bộ, W = 1.
- **Theo khu hay gộp.** Trung vị theo khu trả lời câu hỏi về khu điển hình và ổn định với thiết kế mẫu. Chỉ tiêu gộp trả lời câu hỏi về lượng rừng, nhưng ở nước rút mẫu thì phụ thuộc vào vài khu lớn.
- **FCI toàn khu phụ thuộc sinh cảnh.** Khu có nhiều đất không phải rừng tự nhiên (đồng cỏ, núi đá, đất ngập nước) có FCI thấp dù được bảo vệ tốt. Đất khác chiếm {{USA.dat_khac_pct}}% diện tích các khu ở Mỹ nhưng chỉ {{CMR.dat_khac_pct}}% ở Cameroon. Khi so sánh trạng thái giữa các nước, nên dùng thêm FCI phần có rừng.
- **Trọng số FCI là giả định.** Người dùng có thể tính lại FCI với trọng số khác từ tệp diện tích các lớp.
- **Khu chồng lấn.** Ở một số nước, các khu trong WDPA chồng lấn nhau. Mỗi khu được tính độc lập, nên tổng diện tích của nhiều khu có thể lớn hơn diện tích được bảo vệ thực tế.
- **Không phải đánh giá hiệu quả.** Bộ dữ liệu mô tả tình trạng rừng. Muốn đánh giá hiệu quả quản lý, cần thiết kế đối chứng (khu so với vùng ngoài khu có điều kiện tương tự) và điều chỉnh theo sinh cảnh, độ cao, áp lực dân số và tuổi khu.
- **Cập nhật.** WDPA cập nhật hằng tháng và ForTy V2 đang ở bản Beta. Kết quả có thể thay đổi khi chạy lại với phiên bản mới.

## Mã nguồn

Mã Python dùng để tạo bộ dữ liệu ở kho [hoangvietanh/forty-pa-compare](https://github.com/hoangvietanh/forty-pa-compare): `src/fortypa/` (truy vấn Google Earth Engine, tính chỉ số, thống kê, hình), `scripts/chay_13_nuoc.py` (tạo bộ dữ liệu) và `scripts/bao_cao_13_nuoc.py` (chỉ tiêu cấp quốc gia và báo cáo). Cần tài khoản Google Earth Engine. Kết quả trung gian được lưu đệm theo `SITE_ID`, nên chạy lại chỉ tính phần còn thiếu.

## Tài liệu tham khảo

- [1] Convention on Biological Diversity. Kunming-Montreal Global Biodiversity Framework. Decision 15/4 (2022).
- [2] Hansen, M. C. et al. High-resolution global maps of 21st-century forest cover change. *Science* 342, 850–853 (2013).
- [3] Geldmann, J., Manica, A., Burgess, N. D., Coad, L. & Balmford, A. A global-level assessment of the effectiveness of protected areas at resisting anthropogenic pressures. *Proc. Natl Acad. Sci. USA* 116, 23209–23215 (2019).
- [4] Neumann, M., Raichuk, A., Potapov, P. et al. Global forest typology at 10-meter resolution for forest and land-use monitoring. *Sci. Data* 13, 1434 (2026). [https://doi.org/10.1038/s41597-026-08299-5](https://doi.org/10.1038/s41597-026-08299-5)
- [5] FAO. Global Forest Resources Assessment 2020: Terms and Definitions. Forest Resources Assessment Working Paper 188 (FAO, 2018).
- [6] Regulation (EU) 2023/1115 of the European Parliament and of the Council on the making available on the Union market and the export from the Union of certain commodities and products associated with deforestation and forest degradation (2023).
- [7] UNEP-WCMC & IUCN. Protected Planet: The World Database on Protected Areas (WDPA). [https://www.protectedplanet.net](https://www.protectedplanet.net) (truy cập qua Google Earth Engine, 11/2026).
- [8] Dinerstein, E. et al. An ecoregion-based approach to protecting half the terrestrial realm. *BioScience* 67, 534–545 (2017).
- [9] Sen, P. K. Estimates of the regression coefficient based on Kendall's tau. *J. Am. Stat. Assoc.* 63, 1379–1389 (1968).
- [10] Mann, H. B. Nonparametric tests against trend. *Econometrica* 13, 245–259 (1945).
- [11] Kendall, M. G. *Rank Correlation Methods* (Griffin, 1975).
- [12] Efron, B. & Tibshirani, R. J. *An Introduction to the Bootstrap* (Chapman & Hall, 1993).
