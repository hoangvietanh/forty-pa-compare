# Khung nghiên cứu: so sánh hiện trạng rừng trong khu bảo tồn giữa các nước

*Bản đề xuất, 08/11/2026, đã cập nhật kết quả sàng lọc 34 nước, mô phỏng cỡ mẫu và các quyết định đã chốt. Dựa trên rà soát notebook `forty_compare_countries.ipynb` (VN–Mỹ–Úc, 30 khu lớn nhất mỗi nước) và một lượt kiểm tra WDPA trên GEE cho 36 nước ứng viên.*

---

## 1. Rà soát thiết kế hiện tại

| # | Vấn đề | Bằng chứng | Hệ quả |
|---|---|---|---|
| 1 | **Chọn khu theo tên `DESIG_ENG`** ("Nature Reserve", "National Park", "Cultural and Historical Site") — đây là tên loại khu của Việt Nam | Số khu đủ điều kiện: VN 127, **Mỹ 61** (chỉ National Park liên bang, 100% IUCN II), **Úc 1.729** | Cùng tên nhưng vai trò khác nhau giữa các nước. Ba “tổng thể” không tương đương nhau |
| 2 | **Top 30 theo diện tích** | Mẫu chiếm 30/61 khu của Mỹ (~50%), nhưng chỉ 30/1.729 khu của Úc (1,7%) | Mức đại diện chênh nhau. Khu lớn nhất ở Mỹ/Úc phần lớn là sa mạc, vùng khô hạn |
| 3 | **FCI chủ yếu đo khác biệt sinh cảnh (biome)** | FCI 2025 trung vị: VN 82,8 · Mỹ 24,9 · **Úc 0,98**. Riêng phần có rừng thì thứ tự đảo ngược: Mỹ 96,5 · Úc 93,5 · VN 84,8 | Việt Nam “hạng 1” chủ yếu vì khu bảo tồn VN nằm trong vùng rừng, không phải vì rừng được giữ tốt hơn |
| 4 | **Xếp hạng chỉ có 3 đơn vị** | Hạng 1–2–3. Kiểm tra độ nhạy 20/30/40 khu chỉ cho thấy thứ hạng ổn định *trong cùng một cách chọn* | Thứ hạng của 3 nước không có ý nghĩa thống kê. Thêm nước thì mới so được |
| 5 | **Không có đối chứng** ngoài khu bảo tồn | — | Không tách được tác động của bảo tồn khỏi bối cảnh vùng (khí hậu, áp lực dân số) |
| 6 | **Thay đổi rất nhỏ so với độ bất định** | ΔFCI trung vị: VN −0,04 · Mỹ −0,03 · Úc −0,18 điểm | ForTy V2 Beta chưa được kiểm định cho chuỗi thời gian; thay đổi cỡ 0,1 điểm có thể chỉ là nhiễu phân loại |

**Kết luận rà soát:** phần kỹ thuật tốt (tính diện tích, cache, bootstrap, bản đồ). Điểm yếu nằm ở **tổng thể so sánh**: chưa xác định rõ đang so cái gì với cái gì. Cần (a) định nghĩa khu đủ điều kiện như nhau giữa các nước, (b) chỉ so những khu có rừng, (c) điều chỉnh theo sinh cảnh trước khi kết luận về một nước.

---

## 2. Câu hỏi nghiên cứu (đề xuất viết lại)

- **CH1 – Hiện trạng:** Ở cùng điều kiện sinh cảnh, chất lượng rừng (FCI, tỷ lệ rừng tự nhiên) trong khu bảo tồn quốc gia trên cạn của Việt Nam cao hay thấp hơn các nước khác?
- **CH2 – Xu hướng:** Giai đoạn 2017–2025, rừng trong khu bảo tồn của các nước thay đổi thế nào, và thay đổi đó có vượt ngưỡng bất định của dữ liệu không?
- **CH3 – Hiệu quả bảo tồn (mở rộng, *để đợt sau*):** Chênh lệch giữa trong và ngoài khu bảo tồn (vùng đối chứng tương đồng) của Việt Nam so với các nước khác ra sao?

CH3 là phép so sánh “công bằng” nhất giữa các nước, vì mỗi nước được so với chính bối cảnh của nó.

---

## 3. Tổng thể khu bảo tồn (giữ nguyên tiêu chí: khu quốc gia, trên cạn)

**Giữ nguyên:**
- `DESIG_TYPE = "National"` (khu quốc gia; bỏ khu quốc tế như Ramsar, UNESCO-MAB, Di sản Thế giới)
- `REALM ≠ "Marine"`, phần đất ≥ 1 km² (`LAND_KM2 = GIS_AREA − GIS_M_AREA`)
- `STATUS` Designated / Inscribed; gộp các mảnh cùng `SITE_ID` (đã làm)

**Điều chỉnh đã chốt (08/11/2026), để tiêu chí “khu quốc gia” áp dụng như nhau giữa các nước:**

1. **Lọc bằng `DESIG_TYPE = National`** thay cho danh sách tên `DESIG_ENG` (hàm `gee.select_pas` đã có tham số `desig_types`).
2. **Chỉ giữ khu do nhà nước quản lý** (`GOV_TYPE`: trung ương, địa phương, ủy quyền, đồng quản lý, liên biên giới, và “Not Reported”). **Bỏ** khu do cá nhân, tổ chức phi lợi nhuận, doanh nghiệp, **người bản địa, cộng đồng địa phương** quản lý. Báo cáo phải ghi rõ: kết quả phản ánh *khu bảo tồn do nhà nước quản lý*. Ở Brazil điều này bỏ 487 khu do người bản địa quản lý.
3. **Chỉ giữ khu có rừng, tiêu chí chặt:** rừng ForTy 2017 (lớp 1, 2, 3, 4, 7) ≥ 10% diện tích **và** ≥ 50% diện tích nằm trong biome rừng RESOLVE (1–6, 14). Như vậy loại được khu sa mạc và phần lớn khu xavan.
4. **IUCN_CAT:** không dùng để lọc, vì 56/140 khu của VN là “Not Reported”. Chỉ đưa vào làm biến giải thích.

Với tiêu chí này, Việt Nam còn **116 khu** (trước đây 127 khu theo danh sách tên).

---

## 4. Số khu mỗi nước

### Nguyên tắc
Mục đích là ước lượng giá trị **của cả nước**, nên mẫu phải là **mẫu xác suất**, không phải top N. Mỗi nước cần đạt **cùng một độ chính xác**: sai số của ước lượng trung bình theo khu ≤ **±3 điểm** (khoảng 95%).

### Mô phỏng (`scripts/mo_phong_co_mau.py` → `outputs/mo_phong_co_mau.csv`)
- **Tổng thể:** khu đủ điều kiện của từng nước theo tiêu chí đã chốt (mục 3).
- **Cách lấy mẫu:** ngẫu nhiên phân tầng theo cỡ khu (1–10 · 10–100 · 100–1.000 · ≥ 1.000 km²), mỗi tầng ≥ 2 khu, phần còn lại chia theo tỷ lệ. Mỗi cỡ n lặp 2.000 lần.
- **Sai số** = 95% số lần lặp có ước lượng lệch khỏi giá trị thật của cả tổng thể không quá mức này.
- **Chỉ tiêu:** % rừng ForTy 2017 của từng khu, có sẵn cho mọi khu nhờ bước sàng lọc. Riêng Việt Nam có cả FCI 2025 và ΔFCI cho đủ 116 khu (từ cache diện tích).
- Ở Việt Nam, sai số của FCI chỉ lớn hơn sai số của % rừng khoảng 5%. Vì vậy dùng % rừng làm đại diện cho FCI là hợp lý.

**Sai số (± điểm) theo cỡ mẫu n** (0 = n ≥ N, tức điều tra toàn bộ):

| Nước | Chỉ tiêu | N | Độ lệch chuẩn | n = 30 | 60 | 100 | 150 | 200 | 250 | 300 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Việt Nam | % rừng | 116 | 24,5 | 6,4 | 3,7 | 1,5 | 0 | 0 | 0 | 0 |
| Việt Nam | FCI 2025 | 116 | 26,6 | 6,9 | 3,9 | 1,6 | 0 | 0 | 0 | 0 |
| Việt Nam | ΔFCI 2017→2025 | 116 | 0,7 | 0,22 | 0,12 | 0,05 | 0 | 0 | 0 | 0 |
| Lào | % rừng | 27 | 7,5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Campuchia | % rừng | 53 | 21,8 | 5,5 | 0 | 0 | 0 | 0 | 0 | 0 |
| Thái Lan | % rừng | 155 | 8,8 | 2,9 | 1,8 | 1,0 | 0,3 | 0 | 0 | 0 |
| Philippines | % rừng | 169 | 25,3 | 8,2 | 5,2 | 3,2 | 1,4 | 0 | 0 | 0 |
| Indonesia | % rừng | 390 | 22,0 | 7,5 | 5,1 | 3,8 | **2,9** | 2,2 | 1,6 | 1,2 |
| Brazil | % rừng | 1.124 | 26,4 | 9,0 | 6,3 | 4,9 | 3,9 | 3,1 | **2,8** | 2,5 |
| Madagascar | % rừng | 84 | 27,1 | 7,6 | 3,6 | 0 | 0 | 0 | 0 | 0 |
| Cameroon | % rừng | 20 | 18,2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Gabon | % rừng | 24 | 20,9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Mỹ | % rừng | 5.350 | 26,1 | 9,6 | 6,7 | 5,0 | 4,2 | 3,5 | 3,1 | **2,8** |
| Úc | % rừng | 1.786 | 18,9 | 6,6 | 4,7 | 3,7 | **2,9** | 2,5 | 2,1 | 2,0 |
| Nga | % rừng | 3.121 | 24,4 | 8,9 | 6,0 | 4,8 | 3,8 | 3,3 | **2,8** | 2,6 |

**Kết luận:**
- **n = 60 không đủ.** Với khu bảo tồn đa dạng (độ lệch chuẩn ~25 điểm), n = 60 chỉ cho sai số ±5–7 điểm. Cỡ này không đủ để phân biệt các nước chênh nhau dưới ~10 điểm.
- Phân tầng theo cỡ khu giúp rất ít, vì % rừng không phụ thuộc nhiều vào cỡ khu. Muốn đạt ±3 điểm cần khoảng 150–300 khu ở các nước có nhiều khu.
- Riêng ΔFCI của Việt Nam (−0,3 điểm, độ lệch chuẩn 0,7): n = 60 cho sai số ±0,12, đủ thấy xu hướng. Nhưng Việt Nam sẽ được điều tra toàn bộ nên không cần lấy mẫu.

### Quy tắc đề xuất (theo mô phỏng)
| Số khu đủ điều kiện | Cách lấy | Áp dụng |
|---|---|---|
| N ≤ 200 | **Điều tra toàn bộ** | Việt Nam 116, Lào 27, Campuchia 53, Thái Lan 155, Philippines 169, Madagascar 84, Cameroon 20, Gabon 24 |
| N > 200 | **Mẫu phân tầng**, n = cỡ nhỏ nhất cho sai số ≤ ±3 điểm, seed cố định | Indonesia 150, Úc 150, Brazil 250, Nga 250, Mỹ 300 |

- **Tổng cộng ~1.750 khu** (648 khu điều tra toàn bộ + 1.100 khu lấy mẫu).
- Mỗi khu mang **trọng số mẫu** (N_tầng / n_tầng); khoảng tin cậy tính bằng **bootstrap phân tầng**.
- Báo cáo hai loại ước lượng: **theo khu** (phản ánh quản lý) và **theo diện tích** (phản ánh lượng rừng).
- **Chi phí tính toán:** 1.750 khu × 9 năm không thể tính `frequencyHistogram` 10 m như hiện tại. Đề xuất: **lấy mẫu điểm ngẫu nhiên** (ví dụ 5.000 điểm/khu, cùng tập điểm cho cả 9 năm). Sai số tỷ lệ diện tích khoảng ±1,4 điểm ở mức 95%, chi phí không phụ thuộc diện tích khu. Bản đồ chỉ vẽ cho một số khu minh họa. **Đã chốt** cách kết hợp: khu < 100 km² tính toàn bộ diện tích, khu lớn hơn rút 5.000 điểm (mục 8, quyết định 7).
- **Hạn chế của mô phỏng:** dùng % rừng 2017 làm đại diện (trừ Việt Nam); chỉ phân tầng theo cỡ khu (chưa theo biome); ước lượng trung bình, chưa phải trung vị.

---

## 5. Khung chọn quốc gia

### Bước 1 – Điều kiện cần (loại)
1. **Dữ liệu WDPA công khai, đầy đủ ranh giới.** Trung Quốc chỉ có 9 khu (phần lớn dữ liệu bị hạn chế) → loại. Ấn Độ có 71.631 mảnh, 100% IUCN “Not Reported”, chủ yếu khu rất nhỏ → loại khỏi đợt này.
2. **≥ 20 khu có rừng sau khi lọc** (mục 3). Sau sàng lọc: Papua New Guinea chỉ còn 2 khu (38/40 khu do cộng đồng quản lý) → loại. Gabon (19 khu ≥ 100 km²) và Nepal (23) vừa đủ.
3. **ForTy V2 Beta phủ lãnh thổ:** cả 34 nước đều đạt. Số khu có dưới 90% diện tích có dữ liệu ForTy chỉ từ 0 đến 29 khu mỗi nước, chủ yếu khu nhỏ ven biển hoặc ven hồ.

### Bước 2 – Phân tầng theo hai trục khách quan
- **Trục sinh thái:** vùng địa sinh học: IM Indo-Malaya, AA Australasia, PA Palearctic, NA Nearctic, NT Neotropic, AT Afrotropic.
- **Trục kinh tế – quản lý:** nhóm thu nhập Ngân hàng Thế giới (đại diện cho năng lực quản lý). *Phân nhóm trong bảng ghi theo hiểu biết hiện có, cần đối chiếu bảng phân loại mới nhất của Ngân hàng Thế giới.*

### Bước 3 – Chọn theo quy tắc định trước
1. **Nhóm A – láng giềng cùng sinh cảnh:** mọi nước có chung ecoregion trên cạn với Việt Nam và đủ điều kiện ở bước 1: **Lào, Campuchia, Thái Lan** (Trường Sơn Bắc, Trường Sơn Nam, rừng khô Trung Đông Dương, rừng khô thường xanh Đông Nam Đông Dương). Trung Quốc cũng có ecoregion chung nhưng đã bị loại ở bước 1. *Cần kiểm tra lại bằng phép giao RESOLVE trên GEE.*
2. **Các ô còn lại (vùng × thu nhập):** mỗi ô chọn một nước có **nhiều khu có rừng ≥ 100 km² nhất**. Đếm khu ≥ 100 km² thay vì tổng số khu, vì đếm tổng số khu sẽ ưu tiên những nước có hàng nghìn khu rất nhỏ (Thụy Điển, Nhật Bản).

**Kết quả áp dụng quy tắc, tiêu chí rừng chặt** (số trong ngoặc = khu có rừng ≥ 100 km²):

| Ô | Được chọn | Ứng viên khác |
|---|---|---|
| IM × TB thấp | **Việt Nam** (70) + nhóm A: **Lào** (27), **Campuchia** (37); ngoài nhóm A: **Philippines** (51) | Sri Lanka (49), Myanmar (27), Nepal (13) |
| IM × TB cao | **Thái Lan** (145, nhóm A); ngoài nhóm A: **Indonesia** (154) | Malaysia (91) |
| NT × TB cao | **Brazil** (429) | Mexico (125), Colombia (123), Peru (66) |
| AT × Thấp | **Madagascar** (49) | CHDC Congo (22) |
| AT × TB thấp | **Cameroon** (15), *chọn theo quyết định* | Kenya (37), Tanzania (20) |
| AT × TB cao | **Gabon** (17) | Nam Phi (7) |
| NA × Cao | **Mỹ** (493), *cố định từ đầu* | Canada (514) |
| AA × Cao | **Úc** (201) | New Zealand (70) |
| PA × Cao | **Nga** (743) | Nhật Bản (196), Thụy Điển (92) |

→ **13 nước (đã chốt):** Việt Nam, Lào, Campuchia, Thái Lan, Philippines, Indonesia, Brazil, Madagascar, Cameroon, Gabon, Mỹ, Úc, Nga.

**Ghi chú về những chỗ lệch khỏi quy tắc (cần nêu trong báo cáo):**
- **Cameroon thay cho Kenya/Tanzania:** theo số khu thì Kenya đứng đầu ô này, nhưng khu của Kenya và Tanzania chủ yếu là xavan. Tỷ lệ rừng gộp của Kenya là 69%, Tanzania 65%, trong khi Cameroon 93%. Cameroon chỉ có 20 khu đủ điều kiện, vừa đạt ngưỡng tối thiểu.
- **Gabon** đúng theo quy tắc khi dùng tiêu chí chặt (Nam Phi chỉ còn 7 khu ≥ 100 km²). Gabon có 24 khu, 61% không báo cáo IUCN.
- **Mỹ** được giữ vì là nước so sánh cố định từ đầu. Theo quy tắc với tiêu chí chặt thì Canada có nhiều khu lớn hơn (514 so với 493), nên có thể thêm Canada như một kiểm tra.
- **Madagascar:** tỷ lệ rừng gộp 69%, tương đương Kenya. Đây là điểm cần lưu ý về tính nhất quán khi giải thích việc chọn Cameroon.
- **Nhật Bản** không được chọn (Nga có nhiều khu lớn hơn).

### Kết quả sàng lọc (GEE, 08/11/2026)
Script: `scripts/sang_loc_nuoc.py`. Kết quả từng khu: `outputs/sang_loc/<ISO3>.csv`; bảng tổng hợp: `outputs/sang_loc_nuoc.csv`.

- Đơn vị là **khu**: các mảnh cùng `SITE_ID` được gộp; bản ghi trùng `SITE_PID` bị bỏ (xem lưu ý dưới).
- **Lọc GOV:** giữ khu do nhà nước quản lý (trung ương, địa phương, ủy quyền, đồng quản lý, liên biên giới) và khu “Not Reported”. Bỏ khu do cá nhân, tổ chức phi lợi nhuận, doanh nghiệp, người bản địa, cộng đồng địa phương quản lý.
- **Có rừng (HOẶC):** rừng ForTy 2017 (lớp 1, 2, 3, 4, 7) ≥ 10% diện tích **hoặc** ≥ 50% diện tích nằm trong biome rừng RESOLVE (1–6, 14). **Cả hai:** thỏa cả hai điều kiện.
- Tỷ lệ rừng tính ở 100 m cho khu < 100 km² và 500 m cho khu lớn hơn, đủ chính xác để sàng lọc.

| Nước | Vùng | Thu nhập | Quốc gia, trên cạn | Sau lọc GOV | Có rừng (HOẶC) | Có rừng (cả hai) | Có rừng ≥ 100 km² | % rừng (gộp) | % IUCN không báo cáo |
|---|---|---|--:|--:|--:|--:|--:|--:|--:|
| Việt Nam | IM | TB thấp | 140 | 140 | 136 | 116 | **71** | 86 | 40 |
| Lào | IM | TB thấp | 27 | 27 | 27 | 27 | **27** | 94 | 0 |
| Campuchia | IM | TB thấp | 61 | 61 | 61 | 53 | **42** | 79 | 0 |
| Thái Lan | IM | TB cao | 165 | 165 | 163 | 155 | **149** | 91 | 0 |
| Myanmar | IM | TB thấp | 41 | 41 | 41 | 36 | **30** | 93 | 5 |
| Malaysia | IM | TB cao | 370 | 370 | 370 | 356 | **92** | 96 | 0 |
| Indonesia | IM/AA | TB cao | 450 | 450 | 443 | 390 | **160** | 88 | 13 |
| Philippines | IM | TB thấp | 202 | 202 | 194 | 169 | **58** | 70 | 57 |
| Papua New Guinea | AA | TB thấp | 40 | 2 | 2 | 2 | **0** | 61 | 50 |
| Nhật Bản | PA | Cao | 3.538 | 3.538 | 3.500 | 3.077 | **212** | 81 | 0 |
| Hàn Quốc | PA | Cao | 479 | 479 | 452 | 375 | **34** | 75 | 0 |
| Nepal | IM/PA | TB thấp | 32 | 28 | 23 | 13 | **23** | 53 | 0 |
| Sri Lanka | IM | TB thấp | 394 | 394 | 390 | 361 | **50** | 79 | 3 |
| Brazil | NT | TB cao | 2.413 | 1.494 | 1.456 | 1.124 | **558** | 81 | 0 |
| Peru | NT | TB cao | 199 | 110 | 84 | 76 | **69** | 97 | 10 |
| Colombia | NT | TB cao | 751 | 403 | 396 | 337 | **150** | 83 | 0 |
| Costa Rica | NT | TB cao | 112 | 102 | 101 | 95 | **27** | 87 | 0 |
| Mexico | NT/NA | TB cao | 804 | 481 | 404 | 325 | **143** | 58 | 64 |
| CHDC Congo | AT | Thấp | 47 | 47 | 43 | 22 | **43** | 82 | 47 |
| Gabon | AT | TB cao | 31 | 31 | 31 | 24 | **19** | 89 | 61 |
| Cameroon | AT | TB thấp | 30 | 30 | 28 | 20 | **22** | 82 | 4 |
| Kenya | AT | TB thấp | 274 | 274 | 215 | 137 | **52** | 60 | 93 |
| Tanzania | AT | TB thấp | 692 | 634 | 553 | 230 | **161** | 60 | 85 |
| Madagascar | AT | Thấp | 111 | 111 | 107 | 84 | **67** | 64 | 11 |
| Nam Phi | AT | TB cao | 1.476 | 599 | 303 | 38 | **52** | 41 | 100 |
| Mỹ | NA | Cao | 15.207 | 12.252 | 9.105 | 5.350 | **787** | 42 | 6 |
| Canada | NA | Cao | 6.144 | 5.978 | 5.751 | 5.380 | **541** | 54 | 1 |
| Úc | AA | Cao | 5.346 | 3.877 | 3.288 | 1.786 | **436** | 72 | 0 |
| New Zealand | AA | Cao | 1.961 | 1.961 | 1.708 | 1.272 | **111** | 75 | 0 |
| Phần Lan | PA | Cao | 951 | 951 | 922 | 785 | **41** | 43 | 1 |
| Thụy Điển | PA | Cao | 4.020 | 4.020 | 3.841 | 3.211 | **140** | 41 | 11 |
| Đức | PA | Cao | 2.517 | 2.517 | 2.493 | 2.060 | **25** | 58 | 1 |
| Pháp | PA | Cao | 1.445 | 1.445 | 1.322 | 816 | **95** | 46 | 36 |
| Nga | PA | Cao | 4.152 | 4.152 | 3.824 | 3.121 | **924** | 68 | 2 |

*Cột “Có rừng ≥ 100 km²” và hai cột % tính trên tập “Có rừng (HOẶC)”.*

**Nhận xét:**
- **Lọc GOV tác động mạnh ở châu Mỹ, châu Phi và Úc:**
  - Mỹ bỏ 2.955 khu, chủ yếu 2.830 khu do tổ chức phi lợi nhuận quản lý.
  - Úc bỏ 1.469 khu, trong đó 1.318 khu tư nhân.
  - Brazil bỏ 919 khu: 487 khu do người bản địa quản lý và 432 khu tư nhân.
  - Nam Phi bỏ 877 khu tư nhân; Peru bỏ 59 khu cộng đồng.
  - Ở châu Á, các nước hầu như không mất khu nào.
- **Bỏ khu do người bản địa và cộng đồng quản lý là một lựa chọn có hệ quả.** Ở Brazil, lãnh thổ bản địa giữ rừng rất tốt; bỏ chúng thì kết quả phản ánh “khu do nhà nước quản lý” chứ không phải “mọi khu bảo tồn quốc gia”. Cần ghi rõ trong báo cáo, hoặc phân tích riêng nhóm này như một kiểm tra độ nhạy.
- **Tiêu chí rừng “HOẶC” khá lỏng:** ở Việt Nam giữ 136/140 khu, nhưng cũng giữ nhiều khu xavan và cây bụi ở châu Phi và Úc (ForTy xếp một phần cây gỗ thưa vào rừng). Tiêu chí “cả hai” loại nhiều hơn rõ rệt ở các nước này (Úc 3.288 → 1.786, Nam Phi 303 → 38) nhưng gần như không đổi ở Đông Nam Á.
- **Lỗi dữ liệu WDPA:** một khu của Thụy Điển (`SITE_ID` 555773377) bị lặp 18 bản ghi cùng `SITE_PID`, mỗi bản ghi mang nguyên diện tích; Hàn Quốc có 1 bản ghi lặp. Script đã bỏ bản ghi trùng. Các khu đang dùng trong so sánh VN–Mỹ–Úc hiện tại không bị lỗi này (đã kiểm tra), nhưng `gee.select_pas` nên thêm bước bỏ trùng trước khi mở rộng sang nước khác.
- Tổng diện tích khu ở một số nước (Thụy Điển, Mỹ) có thể bị đếm trùng do các khu quốc gia chồng lấn nhau. Số khu thì không bị ảnh hưởng.

---

## 6. Phân tích

### 6.1 Chỉ tiêu (giữ phần lớn hiện có)
- **Hiện trạng:** FCI 2025; % rừng tự nhiên (lớp 1, 2, 7); FCI phần có rừng.
- **Xu hướng:** ΔFCI 2017→2025, Theil–Sen + Mann–Kendall; thay đổi ròng rừng tự nhiên.
- Giữ ngưỡng kết luận hiện có (|ΔFCI| ≥ 1 **và** p < 0,05).

### 6.2 So sánh có điều chỉnh bối cảnh (thay cho xếp hạng thô)
Mô hình hồi quy hỗn hợp ở cấp khu, có trọng số mẫu:

`FCI_khu ~ nước + biome + log(diện tích) + độ cao + độ dốc + năm thành lập (STATUS_YR) + khả năng tiếp cận + (1 | ecoregion)`

- Hiệu ứng “nước” = khác biệt còn lại sau khi đã trừ sinh cảnh và địa hình. Báo cáo **trung bình biên (EMM) từng nước kèm khoảng tin cậy**, không báo cáo hạng.
- Dữ liệu biến giải thích có sẵn trên GEE: RESOLVE Ecoregions 2017, SRTM/Copernicus DEM, Accessibility to Cities 2015 (Oxford MAP).
- **Phân tích trong cùng ecoregion xuyên biên giới** (VN–Lào–Campuchia–Thái Lan): cùng sinh cảnh, khác chính sách quản lý. Đây là phép so sánh thuyết phục nhất.

### 6.3 Đối chứng ngoài khu bảo tồn (CH3)
- **Cách đơn giản:** vành đai 1–10 km quanh khu (bỏ 1 km sát ranh vì rò rỉ tác động); chỉ tiêu = FCI trong − FCI vành đai.
- **Cách chặt hơn:** ghép cặp điểm ảnh (matching) trong và ngoài khu theo độ cao, độ dốc, khoảng cách tới đường/thành phố, ecoregion; chỉ tiêu = khác biệt trung bình sau ghép cặp, tính cho từng nước.

### 6.4 Độ bất định
- Đối chiếu xu hướng ForTy với nguồn độc lập: Hansen GFC (mất rừng), JRC TMF (rừng ẩm nhiệt đới, cho nhóm A, B). Nếu hướng thay đổi không nhất quán thì không kết luận về xu hướng.
- **Độ nhạy trọng số FCI:** Monte Carlo trọng số (ví dụ ±0,1 nhưng giữ thứ tự 1 > 7 > 2 > 3 > 4 > 5 > 6), xem kết luận giữa các nước có đổi không.
- Giữ kiểm tra độ nhạy theo cách chọn mẫu (nhiều seed, nhiều n).

---

## 7. Lộ trình

| Giai đoạn | Việc | Ra |
|---|---|---|
| 0. Sàng lọc | Lọc `GOV_TYPE` + lọc rừng cho ~20 nước ứng viên; kiểm tra ForTy phủ | Bảng số khu đủ điều kiện → chốt danh sách nước |
| 1. Cỡ mẫu | Mô phỏng lấy mẫu con trên 156 khu VN | Chốt n |
| 2. Chọn khu | Mẫu phân tầng biome × cỡ, seed cố định | `khu_bao_ton.csv` có trọng số |
| 3. Tính | Diện tích loại rừng 2017–2025 (điểm mẫu hoặc histogram), biến giải thích, vành đai đối chứng | Cache trong `outputs/` |
| 4. Phân tích | Ước lượng có trọng số, mô hình hỗn hợp, so sánh trong – ngoài, độ nhạy | Bảng, hình |
| 5. Báo cáo | Viết lại báo cáo HTML theo CH1–CH3 | `docs/`, bản một file |

**Thay đổi code dự kiến:** `gee.select_pas` (dùng `desig_types`, thêm lọc `GOV_TYPE`, lọc rừng); `compare.py` (lấy mẫu phân tầng, trọng số, bootstrap phân tầng, mô hình hỗn hợp, cần thêm `statsmodels`); `gee.py` (lấy mẫu điểm, biến giải thích, vành đai). Phần biểu đồ và báo cáo dùng lại được phần lớn.

---

## 8. Quyết định đã chốt (08/11/2026)

| # | Vấn đề | Quyết định |
|---|---|---|
| 1 | Cách lọc khu quốc gia | `DESIG_TYPE = National` + lọc `GOV_TYPE` (thay danh sách tên `DESIG_ENG`) |
| 2 | Khu do người bản địa / cộng đồng quản lý | **Bỏ** |
| 3 | Tiêu chí rừng | **Chặt:** rừng ≥ 10% **và** ≥ 50% trong biome rừng |
| 4 | Cỡ mẫu | Theo mô phỏng (mục 4): N ≤ 200 điều tra toàn bộ; lớn hơn thì lấy mẫu cho sai số ≤ ±3 điểm (150–300 khu) — *chờ anh/chị duyệt* |
| 5 | Danh sách nước | 13 nước; châu Phi thay xavan bằng **Gabon, Cameroon** |
| 6 | CH3 (đối chứng ngoài khu) | **Chưa làm** trong đợt này |
| 7 | Cách tính trong mỗi khu | **Kết hợp:** khu < 100 km² tính toàn bộ diện tích (`frequencyHistogram` 10 m); khu ≥ 100 km² rút **5.000 điểm** (pixel 10 m đơn lẻ) ngẫu nhiên, cùng bộ điểm cho cả 2017–2025, mỗi khu cố định 5.000 điểm, không tăng theo diện tích. VN dùng lại cache toàn bộ diện tích của 116 khu. Bản đồ thay đổi chỉ vẽ cho các khu minh họa (VN và vài khu tiêu biểu mỗi nước). Đã cân nhắc và bỏ phương án ô 5×5 pixel kèm tăng số mẫu theo diện tích. |

**Thực hiện (08/11/2026):**
1. `fortypa/screen.py` (chuyển từ `scripts/sang_loc_nuoc.py`): tổng thể khu theo DESIG_TYPE + GOV_TYPE, chỉ số rừng, `eligible()` = tiêu chí chặt. `gee.select_pas` bỏ bản ghi trùng `SITE_PID`; `gee.site_collection` lấy polygon cho danh sách SITE_ID.
2. `compare.sample_pas`: rút ngẫu nhiên phân tầng theo cỡ khu (seed cố định), trọng số W = N_h/n_h. Mọi chỉ tiêu cấp nước có trọng số (trung vị có trọng số, gộp diện tích × W); khoảng tin cậy và kiểm định từng cặp nước bằng bootstrap phân tầng (thay cho kiểm định hoán vị). Tổng cộng 1.748 khu.
3. `gee.compute_points`: khu có polygon ≥ 100 km² rút 5.000 điểm (`randomPoints` + `sampleRegions`, 10 m, hệ UTM), lưu lớp của từng điểm ở `outputs/points/<SITE_ID>.npz`. Kiểm tra trên 8 khu VN 150–1.200 km²: FCI 2025 lệch tối đa 0,77 điểm và ΔFCI lệch tối đa 0,11 điểm so với đếm toàn bộ pixel.
4. `scripts/chay_13_nuoc.py` chạy 13 nước → `outputs/so_sanh_13/`.

5. `scripts/bao_cao_13_nuoc.py` dựng báo cáo HTML 13 nước (`outputs/bao_cao_FCI_13_nuoc.html`, `docs/13-nuoc/`).

**Còn lại:** notebook cho 13 nước; mô hình hỗn hợp có điều chỉnh bối cảnh (mục 6.2), để thay bảng xếp hạng.

**Lưu ý về phân bổ mẫu:** mẫu chia theo tỷ lệ số khu nên tầng ≥ 1.000 km² có ít khu (Mỹ 5/73, Úc 3/23). Trung vị theo khu không bị ảnh hưởng, nhưng chỉ tiêu gộp theo diện tích (FCI phần có rừng gộp, thay đổi ròng rừng tự nhiên) phụ thuộc vào vài khu lớn. Nếu dùng các chỉ tiêu này nên lấy toàn bộ tầng lớn nhất.
