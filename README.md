# Olist E-Commerce Data Analysis

Proyek ini menganalisis data Brazilian E-Commerce Public Dataset dari Olist untuk memahami performa penjualan, kontribusi kategori produk, serta pengalaman pelanggan terkait pengiriman dan ulasan.

Pastikan Python telah terpasang. Disarankan menggunakan virtual environment.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Menjalankan dashboard Streamlit

Pastikan file `dashboard/main_data.csv` tersedia. Dari direktori utama proyek, jalankan:

```bash
cd dashboard
python -m streamlit run dashboard.py
```

Streamlit akan menjalankan aplikasi secara lokal. Buka alamat yang ditampilkan di terminal, biasanya:

```text
http://localhost:8501
```

Untuk menghentikan aplikasi, tekan `Ctrl + C` pada terminal.

## Catatan dataset

- CSV pada direktori utama merupakan dataset sumber yang digunakan notebook.
- `dashboard/main_data.csv` merupakan data hasil penggabungan/pengolahan yang dibaca oleh dashboard.
- Jangan mengganti nama atau memindahkan `main_data.csv` tanpa menyesuaikan path pada `dashboard.py`.
