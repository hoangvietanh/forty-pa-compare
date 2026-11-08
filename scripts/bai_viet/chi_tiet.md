## Tóm tắt kết quả

**Dữ liệu và chỉ số.** Nghiên cứu dùng bản đồ loại rừng ForTy V2 Beta: bản đồ toàn cầu ở độ phân giải 10 m, cho từng năm {{tong.nam_dau}}–{{tong.nam_cuoi}}, phân loại mặt đất thành rừng nguyên sinh (trưởng thành hoặc đang phục hồi), rừng tái sinh tự nhiên, rừng trồng, rừng trồng thâm canh, cây công nghiệp và nông lâm kết hợp, và đất khác. Tình trạng rừng của mỗi khu bảo tồn được tóm thành **chỉ số FCI** (0–100), là điểm trung bình của mọi pixel theo mức độ tự nhiên của lớp phủ: 100 khi toàn khu là rừng nguyên sinh trưởng thành, 0 khi không có rừng. **ΔFCI** = FCI {{tong.nam_cuoi}} − FCI {{tong.nam_dau}}; giá trị âm là mất hoặc suy thoái rừng. {{tong.n_khu}} khu được phân tích, đại diện cho {{tong.N_khu}} khu bảo tồn quốc gia, trên cạn, có rừng của {{tong.n_nuoc}} nước.

{{kpi}}

**Thế giới.** {{tong.n_on_dinh}} trong {{tong.n_nuoc}} nước gần như giữ nguyên tình trạng rừng trong khu bảo tồn: ΔFCI trung vị từ {{tong.on_dinh_dfci_min}} đến {{tong.on_dinh_dfci_max}} điểm. Ba nước suy giảm rõ: Campuchia ({{KHM.dfci_median}} điểm, rừng tự nhiên thay đổi ròng {{KHM.natural_change_pct:1}}%), Lào ({{LAO.dfci_median}} điểm, {{LAO.natural_change_pct:1}}%) và Madagascar ({{MDG.dfci_median}} điểm, {{MDG.natural_change_pct:1}}%). Xét FCI toàn khu năm {{tong.nam_cuoi}}, Cameroon ({{CMR.fci_median_2025}}), Gabon ({{GAB.fci_median_2025}}) và Thái Lan ({{THA.fci_median_2025}}) đứng đầu. Xét riêng phần có rừng, rừng tự nhiên nhất ở Cameroon ({{CMR.fci_forest_pooled_2025}}), Gabon ({{GAB.fci_forest_pooled_2025}}) và Indonesia ({{IDN.fci_forest_pooled_2025}}).

**Việt Nam** ({{VNM.n}} khu, điều tra toàn bộ): FCI {{tong.nam_cuoi}} trung vị {{VNM.fci_median_2025}}, FCI phần có rừng {{VNM.fci_forest_pooled_2025}}, ΔFCI trung vị {{VNM.dfci_median}} điểm (KTC 95% {{VNM.dfci_ci_lo}} đến {{VNM.dfci_ci_hi}}). Việt Nam thuộc nhóm ổn định, tốt hơn có ý nghĩa thống kê so với {{tong.vn_tot_hon}}, kém hơn so với {{tong.vn_kem_hon}}, nhưng chênh lệch với nhóm sau lớn nhất chỉ {{tong.vn_chenh_max}} điểm. Điểm yếu của Việt Nam là chất lượng phần rừng: tỷ lệ rừng tái sinh và rừng trồng cao.

## Dữ liệu và phương pháp

### Bản đồ loại rừng ForTy

ForTy (Forest Typology) phiên bản 1 là bản đồ toàn cầu năm 2020 ở độ phân giải 10 m, công bố trên *Scientific Data* (Neumann và cộng sự, 2026). Bản đồ xếp mọi pixel vào sáu lớp theo định nghĩa của FAO và EUDR, dự đoán bằng mô hình học sâu (Swin Transformer) từ embedding vệ tinh AlphaEarth Foundations, vốn tổng hợp Sentinel-1, Sentinel-2, Landsat và các nguồn khác thành một vectơ cho mỗi pixel mỗi năm. Kiểm định độc lập trên 8.190 điểm do chuyên gia giải đoán cho độ chính xác tổng thể 90,2% với sáu lớp, 94,8% với rừng tự nhiên / không tự nhiên và 95,5% với rừng / không rừng. Nghiên cứu này dùng bản **V2 Beta** trên Google Earth Engine (`projects/nature-trace/assets/forest_typology/v2_beta/<năm>`): bảy lớp (rừng nguyên sinh tách thành trưởng thành và đang phục hồi), mỗi năm {{tong.nam_dau}}–{{tong.nam_cuoi}}, lớp của pixel là lớp có xác suất cao nhất.

### Chọn nước

{{tong.n_nuoc}} nước được chọn theo hai trục khách quan: vùng địa sinh học (Indo-Malaya, Australasia, Neotropic, Afrotropic, Nearctic, Palearctic) và nhóm thu nhập của Ngân hàng Thế giới, cộng với các láng giềng chung vùng sinh thái với Việt Nam (Lào, Campuchia, Thái Lan). Trong mỗi ô, nước có nhiều khu bảo tồn có rừng lớn nhất được chọn. Mỹ và Úc được giữ cố định từ đợt so sánh trước; Gabon và Cameroon đại diện châu Phi rừng ẩm.

### Tổng thể khu bảo tồn

Từ WDPA (`WCMC/WDPA/current/polygons`): `DESIG_TYPE = National`, trạng thái Designated/Inscribed, bỏ khu thuần biển, phần đất ≥ 1 km². Các bản ghi cùng `SITE_ID` được gộp thành một khu, bản ghi lặp cùng `SITE_PID` chỉ tính một lần. Chỉ giữ khu do nhà nước quản lý hoặc đồng quản lý (`GOV_TYPE`; bỏ khu tư nhân, bản địa, cộng đồng). Khu được coi là **có rừng** khi rừng ForTy {{tong.nam_dau}} chiếm ≥ {{tong.min_forest_pct}}% diện tích **và** ≥ {{tong.min_biome_pct}}% diện tích nằm trong biome rừng của RESOLVE Ecoregions 2017.

### Số khu mỗi nước

Nước có ≤ {{tong.census_max}} khu đủ điều kiện được điều tra toàn bộ. Nước nhiều khu hơn được rút ngẫu nhiên phân tầng theo diện tích đất (4 tầng: 1–10, 10–100, 100–1.000 và ≥ 1.000 km²), phân bổ theo tỷ lệ số khu, mỗi tầng ít nhất 2 khu: Indonesia {{IDN.n}}, Úc {{AUS.n}}, Brazil {{BRA.n}}, Nga {{RUS.n}}, Mỹ {{USA.n}} khu. Cỡ mẫu được chọn bằng mô phỏng để sai số 95% của chỉ tiêu trung bình theo khu khoảng ±3 điểm. Mỗi khu mang trọng số **W = số khu của tầng / số khu rút từ tầng** (W = 1 khi điều tra toàn bộ); mọi chỉ tiêu cấp nước đều tính theo W. Số khu rút / số khu đủ điều kiện:

{{bang:tang_mau}}

### Diện tích các lớp trong mỗi khu

Khu có polygon < {{tong.nguong_diem_km2}} km²: đếm toàn bộ pixel ForTy (`frequencyHistogram`, hệ UTM của khu, 10 m). Khu lớn hơn: rút ngẫu nhiên {{tong.n_diem}} điểm trong polygon, đọc lớp của từng điểm ở 10 m cho cả {{tong.n_nam}} năm (cùng một bộ điểm), mỗi điểm đại diện cho diện tích khu / {{tong.n_diem}}. {{tong.n_khu_diem}} khu được tính bằng mẫu điểm. Sai số FCI của một khu do lấy mẫu điểm tối đa ±1,4 điểm (95%). Thử trên 8 khu Việt Nam 150–1.200 km², FCI {{tong.nam_cuoi}} lệch tối đa 0,77 điểm và ΔFCI lệch tối đa 0,11 điểm so với đếm toàn bộ. Việt Nam dùng kết quả đếm toàn bộ pixel cho cả {{VNM.n}} khu.

### Chỉ số FCI

FCI(t) = 100 × Σ w(c) · A(c, t) / Σ A(c, t), trong đó A(c, t) là diện tích lớp c năm t và w(c) là trọng số của lớp. ΔFCI = FCI {{tong.nam_cuoi}} − FCI {{tong.nam_dau}}.

{{bang:trong_so_fci}}

Khu được kết luận **suy giảm** hoặc **phục hồi** khi |ΔFCI| ≥ {{tong.min_delta}} điểm **và** kiểm định Mann–Kendall trên chuỗi {{tong.n_nam}} năm có p < {{tong.max_p}}; còn lại là **ổn định / không rõ**.

### So sánh giữa các nước

**Trung vị các khu** là trung vị có trọng số W (mỗi khu đủ điều kiện một phiếu). **Gộp** coi mọi khu đủ điều kiện của một nước là một vùng (diện tích từng lớp × W). ΔFCI so với FCI {{tong.nam_dau}} chỉ tính cho khu có FCI {{tong.nam_dau}} ≥ {{tong.rel_min_fci}}. Khoảng tin cậy 95% và kiểm định từng cặp nước dùng **bootstrap phân tầng** (2.000 lần, rút lại các khu trong từng tầng, giữ trọng số); p hai phía bằng hai lần tỷ lệ lần rút mà chênh lệch đổi dấu. Xếp hạng theo công thức: điểm trạng thái = trung bình FCI {{tong.nam_cuoi}} trung vị và FCI phần có rừng; điểm xu hướng = trung bình hạng của 4 chỉ tiêu xu hướng; điểm chung = trung bình hạng trạng thái và điểm xu hướng.

**Tính bất định.** ForTy V2 Beta là dữ liệu thử nghiệm. Độ chính xác công bố là của bản 2020, chưa kiểm định cho chuỗi thời gian hay cho từng nước. Ở hầu hết các nước ΔFCI trung vị chỉ vài phần trăm điểm, cùng cỡ với nhiễu phân loại giữa các năm. Trọng số FCI là giả định. So sánh chưa điều chỉnh theo sinh cảnh, độ cao, áp lực dân số hay tuổi khu, nên không phải đánh giá hiệu quả quản lý của từng nước.

## Kết quả

### Trạng thái và xu hướng của mỗi nước

{{hinh:ci|FCI {{tong.nam_cuoi}} trung vị các khu (trái), FCI phần có rừng {{tong.nam_cuoi}} gộp (giữa) và ΔFCI {{tong.nam_dau}}–{{tong.nam_cuoi}} trung vị các khu (phải), có trọng số W; vạch ngang là khoảng tin cậy 95% bootstrap phân tầng.}}

{{hinh:strip|FCI {{tong.nam_cuoi}} (trái) và ΔFCI (phải) của từng khu. Mỗi chấm là một khu; vạch đứng là trung vị có trọng số của nước; dải xám là |ΔFCI| < {{tong.min_delta}} điểm.}}

{{hinh:series|FCI gộp theo năm của mỗi nước.}}

{{hinh:composition|Cơ cấu loại rừng trong các khu đủ điều kiện của mỗi nước, có trọng số.}}

### Bảng chỉ tiêu

{{bang:chi_tieu}}

### Việt Nam so với từng nước

{{hinh:pairwise|Chênh lệch ΔFCI trung vị giữa từng cặp nước (hàng trừ cột); xanh là hàng tốt hơn, đỏ là hàng kém hơn; dấu * và ** là p < 0,05 và p < 0,01.}}

{{bang:kiem_dinh_vn}}

### Xếp hạng theo công thức

Giữ cách xếp hạng của đợt so sánh 3 nước để đối chiếu (1 = tốt nhất). Với {{tong.n_nuoc}} nước, điểm xu hướng (trung bình thứ hạng) phóng đại những chênh lệch rất nhỏ: các nước có ΔFCI từ {{tong.on_dinh_dfci_min}} đến {{tong.on_dinh_dfci_max}} điểm vẫn bị xếp cách nhau nhiều bậc. Nên đọc hình khoảng tin cậy ở trên trước bảng này.

{{bang:xep_hang}}

### Từng nước

Mỗi nước có bản đồ ΔFCI các khu, danh sách 10 khu giảm nhiều nhất và bảng tất cả các khu đã phân tích.

{{cac_nuoc}}

## Kết luận chung

### Bức tranh chung

Giai đoạn {{tong.nam_dau}}–{{tong.nam_cuoi}}, rừng trong hệ thống khu bảo tồn của {{tong.n_nuoc}} nước tách thành hai nhóm rõ rệt. {{tong.n_on_dinh}} nước gần như giữ nguyên tình trạng rừng: ΔFCI trung vị của các khu chỉ từ {{tong.on_dinh_dfci_min}} đến {{tong.on_dinh_dfci_max}} điểm. Nói cách khác, sau {{tong.so_nam}} năm, một khu điển hình mất không quá một phần mười điểm trên thang 100. Ba nước còn lại suy giảm rõ và đồng loạt: Campuchia ({{KHM.dfci_median}} điểm), Lào ({{LAO.dfci_median}} điểm) và, nhẹ hơn, Madagascar ({{MDG.dfci_median}} điểm). Khoảng cách giữa hai nhóm lớn gấp hàng chục lần khoảng cách bên trong nhóm ổn định, nên đây là kết quả vững nhất của cả phân tích. Ngược lại, thứ tự giữa các nước ổn định phần lớn nằm trong vùng nhiễu của dữ liệu, không nên đọc như một bảng xếp hạng chính xác.

### Góc độ trạng thái: rừng trong khu tự nhiên đến mức nào

Theo FCI năm {{tong.nam_cuoi}} tính trên toàn khu, Cameroon ({{CMR.fci_median_2025}}), Gabon ({{GAB.fci_median_2025}}), Thái Lan ({{THA.fci_median_2025}}), Lào ({{LAO.fci_median_2025}}) và Indonesia ({{IDN.fci_median_2025}}) dẫn đầu; các nước còn lại thấp hơn nhiều. Chỉ số này phản ánh sinh cảnh nhiều hơn là công tác bảo vệ. Đất không phải rừng chiếm {{USA.dat_khac_pct}}% diện tích khu bảo tồn ở Mỹ, {{MDG.dat_khac_pct}}% ở Madagascar và {{KHM.dat_khac_pct}}% ở Campuchia, nên FCI toàn khu của các nước này thấp dù phần rừng còn lại có thể rất tự nhiên.

Khi chỉ xét phần có rừng, thứ tự thay đổi đáng kể. Rừng trong khu bảo tồn của Cameroon ({{CMR.fci_forest_pooled_2025}}), Gabon ({{GAB.fci_forest_pooled_2025}}), Indonesia ({{IDN.fci_forest_pooled_2025}}) và Brazil ({{BRA.fci_forest_pooled_2025}}) gần như hoàn toàn là rừng nguyên sinh trưởng thành. Nga ({{RUS.fci_forest_pooled_2025}}), Thái Lan ({{THA.fci_forest_pooled_2025}}), Lào ({{LAO.fci_forest_pooled_2025}}) và Madagascar ({{MDG.fci_forest_pooled_2025}}) ở mức khá. Mỹ ({{USA.fci_forest_pooled_2025}}), Úc ({{AUS.fci_forest_pooled_2025}}), Việt Nam ({{VNM.fci_forest_pooled_2025}}), Campuchia ({{KHM.fci_forest_pooled_2025}}) và Philippines ({{PHL.fci_forest_pooled_2025}}) đứng cuối. Ở Việt Nam và Philippines, khoảng {{VNM.lop2_pct}}% diện tích là rừng tái sinh tự nhiên, ngoài ra còn một phần rừng trồng và cây công nghiệp. Đó là dấu vết của lịch sử khai thác và phục hồi từ trước, không phải mất rừng trong giai đoạn nghiên cứu.

### Góc độ xu hướng: mất rừng hay ổn định

Campuchia và Lào suy giảm nặng nhất, và suy giảm gần như ở mọi nơi: {{KHM.pct_negative}}% số khu của Campuchia và {{LAO.pct_negative}}% số khu của Lào có ΔFCI âm. {{KHM.pct_decline}}% số khu của Campuchia và {{LAO.pct_decline}}% số khu của Lào giảm từ {{tong.min_delta}} điểm trở lên với xu hướng có ý nghĩa thống kê. Chỉ trong {{tong.so_nam}} năm, diện tích rừng tự nhiên trong khu bảo tồn thay đổi ròng {{KHM.natural_change_pct:1}}% ở Campuchia và {{LAO.natural_change_pct:1}}% ở Lào. Madagascar có {{MDG.pct_decline}}% số khu suy giảm rõ và rừng tự nhiên thay đổi {{MDG.natural_change_pct:1}}%.

Ở {{tong.n_on_dinh}} nước còn lại, đa số khu cũng có ΔFCI hơi âm (từ {{tong.on_dinh_giam_min}}% đến {{tong.on_dinh_giam_max}}% số khu), nhưng mức giảm rất nhỏ: không quá {{tong.on_dinh_suy_giam_max}}% số khu suy giảm rõ. Việt Nam giảm nhiều hơn một chút so với {{tong.vn_kem_hon}}, và chênh lệch này có ý nghĩa thống kê. Tuy vậy, chênh lệch lớn nhất chỉ {{tong.vn_chenh_max}} điểm FCI, nhỏ hơn nhiều so với sai số phân loại có thể có của ForTy V2 Beta. Có ý nghĩa thống kê ở đây không có nghĩa là khác biệt đáng kể trên thực địa.

### Góc độ bản chất của thay đổi

Cùng là FCI giảm, nhưng nguyên nhân khác nhau giữa các nước. Ở Campuchia, Lào và Madagascar, rừng chuyển thành đất không phải rừng trên lần lượt {{KHM.doi_3}}%, {{LAO.doi_3}}% và {{MDG.doi_3}}% diện tích khu, và mức giảm trải ra qua nhiều năm (năm giảm mạnh nhất của FCI gộp: {{KHM.nam_giam_manh}} ở Campuchia, {{LAO.nam_giam_manh}} ở Lào, {{MDG.nam_giam_manh}} ở Madagascar). Đây là dấu hiệu của chuyển đổi sử dụng đất kéo dài, có thể do phát quang làm nông nghiệp hoặc khai thác, chứ không phải một sự kiện đơn lẻ.

Ở Úc, Nga và một phần ở Mỹ, thay đổi chủ yếu là đổi lớp trong nhóm rừng tự nhiên, phần lớn từ rừng nguyên sinh trưởng thành sang rừng nguyên sinh đang phục hồi ({{AUS.doi_1}}% diện tích ở Úc, {{RUS.doi_1}}% ở Nga, {{USA.doi_1}}% ở Mỹ); diện tích mất hẳn rừng rất nhỏ. Ở Úc, {{AUS.n_khu_giam_nam_do}} trong {{AUS.n_decline}} khu suy giảm có mức giảm lớn nhất vào năm {{AUS.nam_giam_khu}}, trùng với mùa cháy rừng 2019–2020. Đây là xáo trộn tự nhiên, chủ yếu do cháy, và rừng có thể tự phục hồi sau đó. Điều này cũng giải thích vì sao FCI gộp của Úc thay đổi {{AUS.dfci_pooled}} điểm trong khi khu điển hình gần như không đổi ({{AUS.dfci_median}}): mức giảm dồn vào một số khu bị cháy lớn.

Cameroon, Gabon và Thái Lan là nơi rừng trong khu bảo tồn ít biến động nhất: {{THA.doi_0}}–{{GAB.doi_0}}% diện tích giữ nguyên lớp trong {{tong.so_nam}} năm. Ở Việt Nam, tỷ lệ diện tích đổi lớp trung vị là {{VNM.changed_pct_median}}%, cao hơn nhóm này, nhưng phần lớn là dao động qua lại giữa rừng và đất khác, còn thay đổi ròng nhỏ.

### Góc độ khu vực: Đông Nam Á lục địa phân hóa rõ

Bốn nước cùng lưu vực Mê Kông cho kết quả trái ngược nhau. Thái Lan và Việt Nam giữ rừng trong khu bảo tồn gần như nguyên trạng, trong khi Lào và Campuchia, ngay bên cạnh và có cùng loại sinh cảnh, lại mất rừng nhanh nhất trong {{tong.n_nuoc}} nước. Vì sinh cảnh tương tự, khó giải thích khác biệt này bằng điều kiện tự nhiên. Nó gợi ý vai trò của áp lực sử dụng đất và năng lực thực thi bảo vệ, nhưng cần đối chiếu với dữ liệu mất rừng độc lập và thông tin về quản lý trước khi kết luận.

### Xếp hạng tổng hợp

Xếp hạng dưới đây đặt xu hướng lên trước trạng thái, vì xu hướng là phần mà công tác bảo tồn có thể tác động, còn trạng thái phụ thuộc nhiều vào sinh cảnh và lịch sử. Các nước được chia thành bốn nhóm. Trong mỗi nhóm, thứ tự dựa vào chất lượng phần rừng, mức đồng đều giữa các khu và bản chất của thay đổi; thứ tự này chỉ mang tính tham khảo.

**Nhóm thứ nhất, rừng gần như nguyên vẹn và ổn định:** hạng 1 Gabon, hạng 2 Cameroon, hạng 3 Thái Lan, hạng 4 Indonesia. Gabon và Cameroon có rừng tự nhiên nhất và gần như không biến động. Thái Lan có rất ít khu suy giảm rõ ({{THA.pct_decline:1}}%) và rừng khá tự nhiên. Indonesia có phần rừng rất tự nhiên nhưng {{IDN.pct_decline}}% số khu suy giảm rõ, nên đứng cuối nhóm.

**Nhóm thứ hai, ổn định nhưng có xáo trộn tự nhiên đáng kể:** hạng 5 Brazil, hạng 6 Nga, hạng 7 Mỹ, hạng 8 Úc. Các nước này có ΔFCI trung vị gần bằng 0 và phần rừng từ khá đến rất tự nhiên, nhưng một số khu bị cháy hoặc xáo trộn lớn. Úc đứng cuối nhóm vì cháy 2019–2020 làm giảm mạnh rừng nguyên sinh trưởng thành ở nhiều khu.

**Nhóm thứ ba, ổn định nhưng rừng kém tự nhiên hơn:** hạng 9 Việt Nam, hạng 10 Philippines. Cả hai có xu hướng gần như ổn định, nhưng phần rừng có nhiều rừng tái sinh, rừng trồng và cây công nghiệp. Việt Nam xếp trên vì phần rừng tự nhiên hơn Philippines khoảng {{tong.vn_phl_rung}} điểm, lớn hơn nhiều so với chênh lệch xu hướng giữa hai nước.

**Nhóm thứ tư, suy giảm rõ:** hạng 11 Madagascar, hạng 12 Lào, hạng 13 Campuchia. Lào có trạng thái tốt hơn Madagascar, nhưng ΔFCI trung vị âm gấp khoảng {{tong.lao_mdg_lan}} lần và suy giảm xảy ra ở gần như mọi khu. Campuchia đứng cuối vì có mức suy giảm và tỷ lệ mất rừng tự nhiên lớn nhất, đồng thời phần rừng kém tự nhiên.

Thứ tự này khác bảng xếp hạng theo công thức ở mục Kết quả, chủ yếu ở vị trí của Lào. Công thức xếp Lào cao hơn nhờ trạng thái tốt (FCI {{LAO.fci_median_2025}}). Phần đánh giá này xếp Lào thứ 12, vì coi việc giữ được rừng là tiêu chí hàng đầu của một hệ thống khu bảo tồn. Hai cách xếp thống nhất ở hai đầu bảng: Gabon, Cameroon và Thái Lan đứng đầu; Madagascar và Campuchia đứng cuối.

### Mức độ tin cậy

Kết luận về nhóm suy giảm (Campuchia, Lào, Madagascar) và nhóm nguyên vẹn (Gabon, Cameroon) là vững: chênh lệch lớn hơn nhiều so với sai số lấy mẫu và nhất quán qua nhiều chỉ tiêu. Thứ tự giữa các nước ổn định thì không vững, vì chênh lệch ΔFCI chỉ vài phần trăm điểm, cùng cỡ với nhiễu phân loại giữa các năm của ForTy V2 Beta, một bộ dữ liệu thử nghiệm chưa được kiểm định cho chuỗi thời gian. So sánh này cũng chưa điều chỉnh theo sinh cảnh, độ cao, áp lực dân số hay tuổi khu. Vì vậy, đây là đánh giá tình trạng rừng, chưa phải đánh giá hiệu quả quản lý của từng nước.

## Kết luận cho Việt Nam và hàm ý chính sách

### Việt Nam ở đâu

Việt Nam thuộc nhóm ổn định. Rừng chiếm {{VNM.forest_pct_pooled_2025:0}}% diện tích của {{VNM.n}} khu bảo tồn và hầu như không giảm trong {{tong.so_nam}} năm: ΔFCI trung vị {{VNM.dfci_median}} điểm, ΔFCI gộp {{VNM.dfci_pooled}} điểm, rừng tự nhiên thay đổi ròng {{VNM.natural_change_pct}}%. {{VNM.n_decline}} khu được kết luận suy giảm rõ và {{VNM.n_recovery}} khu phục hồi rõ. Điểm yếu nằm ở chất lượng rừng hơn là ở xu hướng: FCI phần có rừng {{VNM.fci_forest_pooled_2025}}, thuộc nhóm thấp, do rừng tái sinh tự nhiên chiếm {{VNM.lop2_pct}}% và rừng trồng, cây công nghiệp chiếm thêm {{VNM.lop4_pct}}% và {{VNM.lop5_pct}}% diện tích. Về xu hướng, Việt Nam kém một chút so với các nước ổn định nhất, nhưng tốt hơn rõ rệt so với hai láng giềng Lào và Campuchia.

### Hàm ý chính sách

Các gợi ý dưới đây có điều kiện: chúng dựa vào một bộ dữ liệu thử nghiệm chưa được kiểm định cho Việt Nam, và chưa xét áp lực dân số, ngân sách hay năng lực quản lý của từng khu.

- **Rừng tái sinh là tài sản cần giữ lâu dài.** Với khoảng {{VNM.lop2_pct}}% diện tích là rừng tái sinh tự nhiên, cách nâng chất lượng rừng trong khu bảo tồn Việt Nam hiệu quả nhất là bảo vệ đủ lâu để rừng tái sinh trưởng thành, thay vì can thiệp bằng trồng rừng trong phân khu bảo vệ nghiêm ngặt.
- **Bổ sung chỉ tiêu chất lượng vào giám sát.** Chỉ tiêu độ che phủ rừng hiện hành không phân biệt rừng tự nhiên với rừng trồng. Một chỉ số kiểu FCI, tính từ bản đồ loại rừng, có thể bổ sung cho kiểm kê rừng để theo dõi chất lượng rừng trong khu bảo tồn theo năm.
- **Kiểm định ForTy cho Việt Nam trước khi dùng chính thức.** Cần đối chiếu bản đồ với ô tiêu chuẩn và số liệu kiểm kê, đặc biệt ở ranh giới giữa rừng tái sinh và rừng trồng, nơi sai số phân loại lớn nhất.
- **Ưu tiên các khu có dấu hiệu suy giảm.** {{VNM.n_decline}} khu suy giảm rõ (danh sách ở mục Từng nước) là nơi nên kiểm tra thực địa trước, để phân biệt mất rừng thật với sai số của dữ liệu.
- **Hợp tác xuyên biên giới.** Rừng trong khu bảo tồn của Lào và Campuchia đang mất nhanh. Các khu bảo tồn liền kề biên giới và buôn bán gỗ, động vật hoang dã xuyên biên giới khiến hợp tác khu vực trở thành một phần của bảo tồn trong nước.
