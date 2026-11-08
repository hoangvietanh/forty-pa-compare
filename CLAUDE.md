# ForTy × khu bảo tồn Việt Nam

Biến động loại rừng 2017–2025 trong 156 khu bảo tồn Việt Nam, từ ForTy V2 Beta (GEE) và WDPA. Kết quả: notebook, báo cáo HTML, GitHub Pages (repo `hoangvietanh/forty-pa-vietnam`, Pages từ `main` `/docs`: https://hoangvietanh.github.io/forty-pa-vietnam/).

## Cấu trúc
- `src/fortypa/gee.py`: lớp rừng, chọn khu, diện tích, chuyển đổi lớp, bản đồ (GEE).
- `src/fortypa/index.py`: chỉ số FCI, Theil–Sen, Mann–Kendall (không dùng scipy).
- `src/fortypa/charts.py`, `report.py`, `llm.py`: hình, báo cáo HTML, nhận xét Gemini.
- `notebooks/forty_pa_timeseries.ipynb`: chạy toàn bộ. Kết quả trung gian được cache trong `outputs/` (areas, transitions, thumbs, llm_cache); chạy lại chỉ tính phần thiếu.
- `docs/`: bản Pages (`index.html` + `img/` ảnh 256 màu, lazy-load). `outputs/`: chỉ commit các file CSV.
- Python: `.venv/Scripts/python.exe` (uv, 3.12). Không có nbconvert/scipy; chạy notebook bằng `nbclient`. In tiếng Việt ra console cần `PYTHONIOENCODING=utf-8`.

## Dữ liệu (những điểm dễ sai)
- **ForTy V2 Beta:** `projects/nature-trace/assets/forest_typology/v2_beta/<năm>` là **ImageCollection chia ô**, không phải Image → `ee.ImageCollection(path).filterBounds(region).mosaic()`. 7 band uint8 `B0`–`B6` = xác suất 0–250. Lớp = `toArray().arrayArgmax().arrayGet([0]).add(1)`.
  - 1 B0 nguyên sinh trưởng thành · 2 B1 tái sinh tự nhiên · 3 B2 rừng trồng (planted) · 4 B3 rừng trồng thâm canh (plantation) · 5 B4 cây công nghiệp/nông lâm kết hợp · 6 B5 đất khác · 7 B6 nguyên sinh đang phục hồi.
  - Rừng tự nhiên = lớp 1, 2, 7. Bản Beta: thứ tự band có thể đổi.
  - `listAssets` trên collection này rất chậm hoặc treo: đọc asset trực tiếp.
- **WDPA** `WCMC/WDPA/current/polygons` dùng **schema mới**: `SITE_ID` (trước `WDPAID`), `REALM` (Terrestrial/Coastal/Marine, trước `MARINE`), `SITE_TYPE`. Lọc hiện tại: `ISO3 = VNM`, `STATUS` Designated/Inscribed, bỏ khu thuần biển, phần đất ≥ 1 km² → 156 khu.
  - `DESIG_ENG` (VN): Nature Reserve 68, National Park 30, Cultural and Historical Site 29, Marine Protected Area 13 (quốc gia); UNESCO-MAB 8, Ramsar 6, World Heritage 2 (quốc tế). Khu quốc gia và quốc tế chồng lấn nhau.

## Phương pháp
- **Diện tích:** `frequencyHistogram` trong hệ UTM của từng khu ở 10 m (1 pixel = 100 m²); mỗi khu một request cho cả 9 năm; nếu lỗi thì tự lùi về 20 m rồi 30 m.
- **Bản đồ thay đổi 2017→2025:** gộp 4 loại (`gee.CHANGES`). Một request 10 m cho cả khu vượt giới hạn bộ nhớ GEE → tải theo ô bằng `ee.data.computePixels`, gộp dần 4×4 bằng `reduceResolution` (mode + tỷ lệ). Màu = loại thay đổi chiếm ưu thế, độ đậm = sqrt(tỷ lệ pixel đổi lớp). Dùng max sẽ phóng đại thay đổi.
- Thay đổi gộp (~6% diện tích ở nhiều khu) lớn hơn nhiều so với thay đổi ròng (~1%): phần lớn là dao động rừng ↔ đất khác.
- **FCI:** trọng số 1→1,0; 7→0,8; 2→0,6; 3→0,3; 4→0,2; 5→0,1; 6→0. FCI_t = 100·Σw·A/ΣA (trên toàn khu), ΔFCI = FCI2025 − FCI2017. Kết luận suy giảm/phục hồi khi |ΔFCI| ≥ 1 điểm **và** Mann–Kendall p < 0,05 trên chuỗi 9 năm; còn lại "ổn định / không rõ". ΔFCI cùng dấu với xu hướng Theil–Sen ở ~96% số khu (chuỗi ForTy mượt, hai năm đầu/cuối không bất thường).
- **Gemini:** `gemini-3.8-flash` (google-genai), key ở biến môi trường `GEMINI_API_KEY`, **không bao giờ ghi key vào file**. Notebook mặc định `RUN_GEMINI = False` (đọc `outputs/nhan_xet_AI.csv`); chỉ người dùng sửa tay thành True.

## Môi trường
- GEE project `ee-hoangvietanh` (credential dùng chung với dự án Vegetation-Monitoring).

## Quy ước làm việc
- Người dùng viết tiếng Việt; trả lời tiếng Việt. Số theo kiểu Việt Nam (`12.345,6`, `charts.fmt_ha`).
- Khi được yêu cầu chỉ sửa văn bản hoặc chỉ vẽ lại, không đổi số liệu, bản đồ hay phần khác.
- Chỉ commit/push khi người dùng yêu cầu.
- Báo cáo nêu rõ tính bất định: ForTy V2 Beta là dữ liệu thử nghiệm, độ chính xác công bố (90%/95%) là của bản 2020, chưa kiểm định cho chuỗi thời gian hay cho Việt Nam.

## So sánh 3 nước (dự án này)
- Repo riêng `hoangvietanh/forty-pa-compare`, Pages từ `main` `/docs`: https://hoangvietanh.github.io/forty-pa-compare/. Không push vào `forty-pa-vietnam` (sẽ đè trang VN).
- Notebook `notebooks/forty_compare_countries.ipynb` → hai bản: `docs/index.html` + `docs/img/` (ảnh riêng, cho GitHub Pages; mở riêng file html thì không thấy ảnh) và `outputs/bao_cao_FCI_3_nuoc.html` (một file, ảnh nhúng base64, ~15 MB, để gửi/mở ở bất cứ đâu). Module mới: `compare.py` (chỉ tiêu, bootstrap, hoán vị, xếp hạng), `compare_report.py` (HTML); `charts.py` có thêm hình so sánh và bản đồ ΔFCI.
- Chọn khu: `gee.select_pas(iso3, desig_eng=[...], pick=compare.select_top)`: RANK theo `LAND_KM2` trên toàn bộ khu đủ điều kiện; lấy `TOP_N` = 30 khu lớn nhất mỗi nước (người dùng đã bỏ nhóm 10 khu cỡ vừa). `results` trong notebook chỉ còn một nhóm. **WDPA Úc có khu nhiều mảnh cùng `SITE_ID`** (`SITE_PID` `<id>_1`, `_2`): phải gộp, nếu không `pa_feature().first()` chỉ lấy một mảnh.
- Khu Mỹ/Úc rộng tới 36.000 km²: một request 10 m chạy >20 phút. `MAX_PIXELS` (2e7) cho khu lớn bắt đầu ở 20/30/60 m (30 m cho 36 triệu pixel ≈ 9 phút). Bản đồ thay đổi của khu > 3.000 km² tính từ pixel 30 m.
- Cache VN chép từ dự án cũ (`REUSE_CACHE_FROM`), cùng tên file theo `SITE_ID`: **chỉ areas và transitions, không chép ảnh** (dự án cũ dùng bảng màu khác).
- Màu (ColorBrewer, người dùng chọn): lớp rừng Greens/Blues/Oranges (`gee.CLASSES`), bản đồ ΔFCI tổng quát RdYlBu 5 (`charts.DFCI_BINS`), bản đồ thay đổi = **ΔFCI từng điểm ảnh** RdYlBu 11 (`gee.DFCI_PIXEL_BINS`, `dfci_image`). Mảng ΔFCI lưu `outputs/thumbs/*_dfci_*.npz` → đổi màu chỉ cần vẽ lại. Màu lớp được nướng sẵn trong thumbnail GEE: đổi `CLASSES.color` thì phải xóa `outputs/thumbs/*_<năm>.png`.
- `report._png_256` giữ chính xác các màu khóa (`_key_colors`) khi giảm 256 màu; median cut thường làm lệch màu ô chú giải và lớp hiếm. Thêm màu có nghĩa mới thì thêm vào `_key_colors`.
- Xếp hạng (`compare.ranking`): điểm trạng thái = trung bình **giá trị** FCI 2025 trung vị và FCI phần có rừng (không dùng trung bình hạng, vì bỏ mất độ lớn chênh lệch), xếp thành hạng trạng thái; điểm xu hướng = trung bình hạng 4 chỉ tiêu; điểm chung = trung bình hạng trạng thái và điểm xu hướng. Số thứ tự hiển thị `NO` = `RANK` (1–30). Kiểm tra độ nhạy với `SENS_TOP_N` = 20/30/40 khu lớn nhất (`kiem_tra_do_nhay.csv`).
- ΔFCI tương đối chỉ tính khi FCI 2017 ≥ 5 (khu sa mạc FCI ≈ 0). Một số khu (sa mạc) không có pixel rừng nào → không có biểu đồ đường.
- Chạy: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe` với `nbclient` (kernel `python3`).

## Khung 13 nước (KHUNG_NGHIEN_CUU.md, mục 8)
- 13 nước: VNM, LAO, KHM, THA, PHL, IDN, BRA, MDG, CMR, GAB, USA, AUS, RUS. Tổng thể = `screen.eligible`: `DESIG_TYPE = National`, trên cạn, `GOV_TYPE` nhà nước (bỏ tư nhân, bản địa, cộng đồng), rừng ForTy 2017 ≥ 10% **và** ≥ 50% trong biome rừng RESOLVE. Chỉ số sàng lọc cache ở `outputs/sang_loc/<ISO3>.csv`.
- WDPA có bản ghi lặp cùng `SITE_PID` (mỗi bản ghi mang nguyên `GIS_AREA`): luôn `drop_duplicates("SITE_PID")` trước khi cộng diện tích.
- Cỡ mẫu: ≤ 200 khu thì lấy hết; IDN/AUS 150, BRA/RUS 250, USA 300 (`compare.SAMPLE_N`), rút phân tầng theo cỡ khu, trọng số `W`. Mọi chỉ tiêu cấp nước phải dùng `W`.
- Trong khu: polygon < 100 km² đếm toàn bộ pixel; lớn hơn rút 5.000 điểm (`gee.compute_points`), ghi vào cùng cache areas/transitions (cột `n_points`). Khu đã có bảng đếm toàn bộ thì giữ.
- Chạy: `scripts/chay_13_nuoc.py` → `outputs/so_sanh_13/` (CSV, cache). Rồi `scripts/bao_cao_13_nuoc.py` → `outputs/bao_cao_FCI_13_nuoc.html` (một file, ~4 MB) và `docs/13-nuoc/` (Pages, trang 3 nước ở `docs/index.html` giữ nguyên). HTML: `compare13_report.py`; hình mới trong `charts.py` (`ci_figure`, `pairwise_figure`, `series_grid_figure`). Không vẽ bản đồ từng khu; bản đồ tổng quan mỗi nước có chấm ở tâm khu (khu nhỏ không thấy ở tỉ lệ cả nước).
- Trang 13 nước có 3 tab, mỗi tab một bài viết markdown trong `scripts/bai_viet/`: `tom_tat.md` (đại chúng, văn phong báo chí), `chi_tiet.md` (báo cáo đầy đủ), `bai_bao.md` (khung Scientific Data, tiếng Việt). `## ` tạo một mục trong thanh mục lục ngang của tab.
- **Số trong bài viết luôn viết bằng `{{khóa}}`, không gõ tay.** Khóa lấy từ `compare13_report.facts()`: `ISO3.<cột của so_sanh_nuoc.csv>`, các chỉ tiêu dẫn xuất (`dat_khac_pct`, `lop<v>_pct`, `doi_<mã CHANGES>`, `nam_giam_manh`…) và `tong.*`. `{{khóa:d}}` đổi số chữ số thập phân, `{{khóa|abs}}` bỏ dấu. Hình, bảng là khối trên một đoạn riêng: `{{hinh:ci|chú thích}}`, `{{ban_do:VNM|…}}`, `{{bang:chi_tieu}}`, `{{kpi}}`, `{{cac_nuoc}}`. Khóa sai thì dựng báo cáo dừng với lỗi. Số gõ tay chỉ dành cho hằng số phương pháp, số liệu bên ngoài (độ chính xác ForTy) và thứ hạng nhận định.
- Thứ tự xếp hạng 4 nhóm trong `chi_tiet.md` và các câu so sánh bằng lời (ai đứng đầu, ai suy giảm) là nhận định viết tay: đổi dữ liệu thì đọc lại.
- Bài báo trỏ tới các CSV trong `outputs/so_sanh_13/` (được commit, kể cả `dien_tich_lop_tung_khu.csv` và `chuyen_doi_lop_tung_khu.csv`); cache JSON/npz không commit.
- GEE treo không báo lỗi: `ee.data.setDeadline` không cắt được, nên mọi `getInfo` dài đi qua `gee._call` (luồng daemon, hết giờ thì bỏ). `randomPoints` treo trên GeometryCollection có LineString (BRA 556323287): dùng `gee._polygons_only`. Rút điểm: lấy tọa độ một lần rồi `sampleRegions` trên ảnh ForTy toàn cầu theo lô 1.000 điểm (ảnh lọc theo vùng + điểm sinh trên server làm khu vài nghìn km² vượt 5 phút).
- Tên khu: `NAME` của WDPA là tên bản địa (Khmer, Thái, Lào); báo cáo dùng `NAME_ENG` khi tên không viết bằng chữ Latin.
- Notebook vẫn là bản 3 nước, top 30 khu.
