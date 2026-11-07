# So sánh chỉ số tình trạng rừng (FCI) trong khu bảo tồn Việt Nam, Mỹ và Úc (ForTy V2 Beta, 2017–2025)

Notebook `notebooks/forty_compare_countries.ipynb` so sánh FCI 2017 → 2025 và ΔFCI trong hai nhóm khu bảo tồn của mỗi
nước: 20 khu lớn nhất và 10 khu cỡ vừa (WDPA, `DESIG_ENG` thuộc Nature Reserve, National Park, Cultural and Historical Site).

- **Báo cáo:** `docs/index.html` (ảnh trong `docs/img/`, dùng cho GitHub Pages).
- **Kết quả dạng bảng:** `outputs/*.csv` (`chi_so_FCI.csv` từng khu, `so_sanh_nuoc.csv`, `xep_hang_nuoc.csv`,
  `kiem_dinh_hoan_vi.csv`, `FCI_theo_nuoc_theo_nam.csv`, diện tích và chuyển đổi lớp).

## Phương pháp tóm tắt

- **Dữ liệu:** ForTy V2 Beta (`projects/nature-trace/assets/forest_typology/v2_beta/<năm>`, lớp = argmax của 7 band xác
  suất) và `WCMC/WDPA/current/polygons`.
- **Chọn khu:** trạng thái Designated/Inscribed, bỏ khu thuần biển, lọc `DESIG_ENG`, gộp các mảnh cùng `SITE_ID`, rồi
  xếp theo diện tích đất liền. Nhóm lớn nhất: 20 khu đứng đầu. Nhóm cỡ vừa: chia danh sách thành 4 nhóm có số khu bằng
  nhau, lấy 10 khu lớn nhất của nhóm thứ 2 (bỏ qua khu đã thuộc nhóm lớn nhất). Hai nhóm được so sánh riêng.
- **Diện tích:** `frequencyHistogram` trong hệ UTM của khu, 10 m. Khu rất lớn (Mỹ, Úc) được tính ở 20–60 m.
- **FCI:** FCI = 100 × Σ w·A / ΣA, trọng số từ 1,0 (nguyên sinh trưởng thành) đến 0 (đất khác); ΔFCI = FCI 2025 − FCI
  2017. Một khu là suy giảm/phục hồi khi |ΔFCI| ≥ 1 điểm và Mann–Kendall p < 0,05.
- **So sánh nước:** tách chỉ tiêu trạng thái (FCI 2025, FCI phần có rừng) và chỉ tiêu xu hướng (ΔFCI, ΔFCI tương đối,
  % khu có ΔFCI âm, thay đổi ròng rừng tự nhiên). Kèm khoảng tin cậy bootstrap, kiểm định hoán vị và xếp hạng theo
  trung bình thứ hạng.

ForTy V2 Beta là dữ liệu thử nghiệm. Độ chính xác công bố là của bản 2020, chưa được kiểm định cho chuỗi thời gian hay
cho từng nước, nên kết quả chỉ mang tính sàng lọc.

## Chạy lại

```bash
uv venv .venv --python 3.12
```

```bash
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
```

Earth Engine đã đăng nhập (project `ee-hoangvietanh`). Kết quả trung gian được lưu trong `outputs/`; khi chạy lại,
notebook chỉ tính những phần còn thiếu.
