import sqlite3
import streamlit as st
from datetime import datetime, timedelta
import time
import os
import pandas as pd

# Koneksi ke database SQLite dengan timeout
def get_connection():
    return sqlite3.connect('perpustakaan8.db', check_same_thread=False, timeout=10)

# Perbarui skema tabel buku jika belum ada
conn = get_connection()
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS buku (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT,
    penulis TEXT,
    tahun_terbit INTEGER,
    status TEXT,
    jenis TEXT,
    ukuran_file REAL,
    format_file TEXT,
    jumlah_halaman INTEGER,
    berat REAL,
    nama_peminjam TEXT,
    tanggal_peminjaman DATE,
    tanggal_pengembalian DATE,
    denda INTEGER,
    file_path TEXT,
    link_download TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS akun (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
''')

# Tambahkan kolom yang mungkin belum ada
columns = [desc[1] for desc in c.execute('PRAGMA table_info(buku)').fetchall()]
if 'nama_peminjam' not in columns:
    c.execute('ALTER TABLE buku ADD COLUMN nama_peminjam TEXT')
if 'tanggal_peminjaman' not in columns:
    c.execute('ALTER TABLE buku ADD COLUMN tanggal_peminjaman DATE')
if 'tanggal_pengembalian' not in columns:
    c.execute('ALTER TABLE buku ADD COLUMN tanggal_pengembalian DATE')
if 'denda' not in columns:
    c.execute('ALTER TABLE buku ADD COLUMN denda INTEGER')
if 'file_path' not in columns:
    c.execute('ALTER TABLE buku ADD COLUMN file_path TEXT')
if 'link_download' not in columns:
    c.execute('ALTER TABLE buku ADD COLUMN link_download TEXT')
conn.commit()

# Fungsi untuk menambah akun superadmin
def tambah_superadmin():
    try:
        c.execute('INSERT INTO akun (username, password, role) VALUES (?, ?, ?)', ('supermade', 'made', 'superadmin'))
        conn.commit()
        print("Akun superadmin 'supermade' berhasil ditambahkan.")
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed' in str(e):
            print("Akun superadmin 'supermade' sudah ada.")
        else:
            print(f"Terjadi kesalahan saat menambahkan akun superadmin: {e}")

# Panggil fungsi untuk menambah akun superadmin
tambah_superadmin()

conn.close()

# Fungsi untuk menambah buku ke database
def tambah_buku_ke_db(buku):
    conn = get_connection()
    c = conn.cursor()
    try:
        if isinstance(buku, BukuDigital):
            c.execute('''
            INSERT INTO buku (judul, penulis, tahun_terbit, status, jenis, ukuran_file, format_file, file_path, link_download)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (buku.judul, buku.penulis, buku.tahun_terbit, buku.status, 'digital', buku.ukuran_file, buku.format_file, buku.file_path, buku.link_download))
        elif isinstance(buku, BukuFisik):
            c.execute('''
            INSERT INTO buku (judul, penulis, tahun_terbit, status, jenis, jumlah_halaman, berat)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (buku.judul, buku.penulis, buku.tahun_terbit, buku.status, 'fisik', buku.jumlah_halaman, buku.berat))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Terjadi kesalahan saat menambah buku: {e}")
    finally:
        conn.close()

# Kelas-kelas perpustakaan
class Buku:
    def __init__(self, judul, penulis, tahun_terbit):
        self.judul = judul
        self.penulis = penulis
        self.tahun_terbit = tahun_terbit
        self.status = "tersedia"

    def info_buku(self):
        return f"Judul: {self.judul}, Penulis: {self.penulis}, Tahun Terbit: {self.tahun_terbit}, Status: {self.status}"

class BukuDigital(Buku):
    def __init__(self, judul, penulis, tahun_terbit, ukuran_file, format_file, file_path, link_download):
        super().__init__(judul, penulis, tahun_terbit)
        self.ukuran_file = ukuran_file
        self.format_file = format_file
        self.file_path = file_path
        self.link_download = link_download

    def info_buku(self):
        info = super().info_buku()
        return f"{info}, Ukuran File: {self.ukuran_file}MB, Format: {self.format_file}"

class BukuFisik(Buku):
    def __init__(self, judul, penulis, tahun_terbit, jumlah_halaman, berat):
        super().__init__(judul, penulis, tahun_terbit)
        self.jumlah_halaman = jumlah_halaman
        self.berat = berat

    def info_buku(self):
        info = super().info_buku()
        return f"{info}, Jumlah Halaman: {self.jumlah_halaman}, Berat: {self.berat} gram"

# Fungsi untuk menambah buku digital
def tambah_buku_digital():
    st.subheader("Tambah Buku Digital")
    judul = st.text_input("Judul")
    penulis = st.text_input("Penulis")
    tahun_terbit = st.number_input("Tahun Terbit", min_value=1500, max_value=datetime.now().year, format="%d")
    ukuran_file = st.number_input("Ukuran File (MB)")
    format_file = st.selectbox("Format File", ["PDF", "EPUB", "MOBI"])
    uploaded_file = st.file_uploader("Upload File Buku", type=["pdf", "epub", "mobi"])

    if st.button("Tambah Buku Digital"):
        if uploaded_file is not None:
            # Buat direktori 'uploads' jika belum ada
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            file_path = f"uploads/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            link_download = file_path
            buku = BukuDigital(judul, penulis, tahun_terbit, ukuran_file, format_file, file_path, link_download)
            tambah_buku_ke_db(buku)
            st.success(f"Buku digital '{judul}' berhasil ditambahkan.")
        else:
            st.error("Harap upload file buku.")

# Fungsi untuk menambah buku fisik
def tambah_buku_fisik():
    st.subheader("Tambah Buku Fisik")
    judul = st.text_input("Judul")
    penulis = st.text_input("Penulis")
    tahun_terbit = st.number_input("Tahun Terbit", min_value=1500, max_value=datetime.now().year, format="%d")
    jumlah_halaman = st.number_input("Jumlah Halaman", min_value=1, format="%d")
    berat = st.number_input("Berat (gram)", min_value=1, format="%d")

    if st.button("Tambah Buku Fisik"):
        buku = BukuFisik(judul, penulis, tahun_terbit, jumlah_halaman, berat)
        tambah_buku_ke_db(buku)
        st.success(f"Buku fisik '{judul}' berhasil ditambahkan.")

# Fungsi untuk menampilkan semua buku
def ambil_semua_buku_dari_db():
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM buku')
        return c.fetchall()
    finally:
        conn.close()

# Fungsi untuk menampilkan semua buku
def tampilkan_semua_buku():
    st.subheader("Daftar Semua Buku")
    buku_list = ambil_semua_buku_dari_db()
    buku_dict_list = []
    for buku in buku_list:
        if buku[5] == 'fisik':
            buku_obj = BukuFisik(buku[1], buku[2], buku[3], buku[7], buku[8])
        else:
            buku_obj = BukuDigital(buku[1], buku[2], buku[3], buku[6], buku[7], buku[14], buku[15])

        buku_dict = {
            "ID": buku[0],
            "Judul Buku": buku[1],
            "Nama Pembuat": buku_obj.penulis,
            "Tahun Terbit": buku_obj.tahun_terbit,
            "Status": buku[4],  # Menggunakan status dari database
            "Jenis": buku[5],
            "Ukuran File": buku_obj.ukuran_file if isinstance(buku_obj, BukuDigital) else 'N/A',
            "Format File": buku_obj.format_file if isinstance(buku_obj, BukuDigital) else 'N/A',
            "Jumlah Halaman": buku_obj.jumlah_halaman if isinstance(buku_obj, BukuFisik) else 'N/A',
            "Berat": buku_obj.berat if isinstance(buku_obj, BukuFisik) else 'N/A',
            "Nama Peminjam": buku[10] if buku[10] else 'N/A',
            "Tanggal Peminjaman": buku[11] if buku[11] else 'N/A',
            "Tanggal Pengembalian": buku[12] if buku[12] else 'N/A',
            "Denda": buku[13] if buku[13] else 'N/A'
        }
        buku_dict_list.append(buku_dict)

    df_buku = pd.DataFrame(buku_dict_list)
    
    st.table(df_buku)

    # Tampilkan tombol atau link download buku untuk setiap buku digital
    for index, row in df_buku.iterrows():
        if row["Jenis"] == "digital":
            file_path = buku_list[index][14]
            with open(file_path, "rb") as file:
                st.download_button(
                    label=f"Download {row['Judul Buku']}",
                    data=file,
                    file_name=os.path.basename(file_path),
                    mime='application/octet-stream'
                )

# Fungsi untuk menjalankan query dengan retry
def execute_query_with_retry(query, params, commit=False):
    attempts = 3
    for attempt in range(attempts):
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute(query, params)
            if commit:
                conn.commit()
            result = c.fetchall()
            conn.close()
            return result
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                time.sleep(1)  # Tunggu 1 detik sebelum mencoba lagi
            else:
                raise

# Fungsi untuk meminjam buku
def pinjam_buku():
    st.subheader("Pinjam Buku")
    judul = st.text_input("Judul Buku yang Ingin Dipinjam")
    nama_peminjam = st.text_input("Nama Peminjam")

    if st.button("Pinjam Buku"):
        try:
            query = 'SELECT * FROM buku WHERE judul=? AND status="tersedia" AND jenis="fisik"'
            buku = execute_query_with_retry(query, (judul,))
            if buku:
                tanggal_peminjaman = datetime.now().date()
                tanggal_pengembalian = tanggal_peminjaman + timedelta(days=7)
                query = 'UPDATE buku SET status="dipinjam", nama_peminjam=?, tanggal_peminjaman=?, tanggal_pengembalian=? WHERE judul=?'
                execute_query_with_retry(query, (nama_peminjam, tanggal_peminjaman, tanggal_pengembalian, judul), commit=True)
                st.success(f"Buku '{judul}' berhasil dipinjam oleh {nama_peminjam}.")
            else:
                st.error(f"Buku '{judul}' tidak tersedia untuk dipinjam atau bukan buku fisik.")
        except sqlite3.Error as e:
            st.error(f"Terjadi kesalahan saat meminjam buku: {e}")

# Fungsi untuk mengembalikan buku
def kembalikan_buku():
    st.subheader("Kembalikan Buku")
    judul = st.text_input("Judul Buku yang Ingin Dikembalikan")
    nama_peminjam = st.text_input("Nama Peminjam")

    if st.button("Kembalikan Buku"):
        try:
            query = 'SELECT * FROM buku WHERE judul=? AND status="dipinjam" AND nama_peminjam=?'
            buku = execute_query_with_retry(query, (judul, nama_peminjam))
            if buku:
                query = 'UPDATE buku SET status="tersedia", nama_peminjam=NULL, tanggal_peminjaman=NULL, tanggal_pengembalian=NULL, denda=NULL WHERE judul=?'
                execute_query_with_retry(query, (judul,), commit=True)
                st.success(f"Buku '{judul}' berhasil dikembalikan oleh {nama_peminjam}.")
            else:
                st.error(f"Buku '{judul}' tidak ditemukan atau tidak sedang dipinjam oleh {nama_peminjam}.")
        except sqlite3.Error as e:
            st.error(f"Terjadi kesalahan saat mengembalikan buku: {e}")

# Fungsi untuk menghitung denda
def hitung_denda():
    st.subheader("Hitung Denda Buku")
    judul = st.text_input("Judul Buku")
    nama_peminjam = st.text_input("Nama Peminjam")

    if st.button("Hitung Denda"):
        try:
            query = 'SELECT tanggal_pengembalian FROM buku WHERE judul=? AND nama_peminjam=?'
            result = execute_query_with_retry(query, (judul, nama_peminjam))
            if result:
                tanggal_pengembalian = datetime.strptime(result[0][0], "%Y-%m-%d").date()
                hari_terlambat = (datetime.now().date() - tanggal_pengembalian).days
                if hari_terlambat > 0:
                    denda = hari_terlambat * 5000
                    query = 'UPDATE buku SET denda=? WHERE judul=? AND nama_peminjam=?'
                    execute_query_with_retry(query, (denda, judul, nama_peminjam), commit=True)
                    st.success(f"Buku '{judul}' terlambat dikembalikan selama {hari_terlambat} hari. Denda: Rp {denda}")
                else:
                    st.success(f"Buku '{judul}' tidak terlambat dikembalikan. Tidak ada denda.")
            else:
                st.error(f"Buku '{judul}' tidak ditemukan atau tidak sedang dipinjam oleh {nama_peminjam}.")
        except sqlite3.Error as e:
            st.error(f"Terjadi kesalahan saat menghitung denda: {e}")

# Fungsi untuk menghapus buku berdasarkan judul dan pembuat
def hapus_buku():
    st.subheader("Hapus Buku")
    judul = st.text_input("Judul Buku yang Ingin Dihapus")
    penulis = st.text_input("Penulis Buku")

    if st.button("Hapus Buku"):
        try:
            query = 'DELETE FROM buku WHERE judul=? AND penulis=?'
            execute_query_with_retry(query, (judul, penulis), commit=True)
            urutkan_id_buku()
            st.success(f"Buku '{judul}' berhasil dihapus.")
        except sqlite3.Error as e:
            st.error(f"Terjadi kesalahan saat menghapus buku: {e}")

# Fungsi untuk mengurutkan ulang ID buku
def urutkan_id_buku():
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
        CREATE TABLE IF NOT EXISTS buku_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT,
            penulis TEXT,
            tahun_terbit INTEGER,
            status TEXT,
            jenis TEXT,
            ukuran_file REAL,
            format_file TEXT,
            jumlah_halaman INTEGER,
            berat REAL,
            nama_peminjam TEXT,
            tanggal_peminjaman DATE,
            tanggal_pengembalian DATE,
            denda INTEGER,
            file_path TEXT,
            link_download TEXT
        )
        ''')
        c.execute('''
        INSERT INTO buku_temp (judul, penulis, tahun_terbit, status, jenis, ukuran_file, format_file, jumlah_halaman, berat, nama_peminjam, tanggal_peminjaman, tanggal_pengembalian, denda, file_path, link_download)
        SELECT judul, penulis, tahun_terbit, status, jenis, ukuran_file, format_file, jumlah_halaman, berat, nama_peminjam, tanggal_peminjaman, tanggal_pengembalian, denda, file_path, link_download
        FROM buku
        ''')
        c.execute('DROP TABLE buku')
        c.execute('ALTER TABLE buku_temp RENAME TO buku')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Terjadi kesalahan saat mengurutkan ulang ID buku: {e}")
    finally:
        conn.close()

# Fungsi untuk menampilkan daftar akun
def tampilkan_daftar_akun():
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT username, password, role FROM akun')
        akun_list = c.fetchall()
        akun_dict_list = [{"Username": akun[0], "Password": akun[1], "Role": akun[2]} for akun in akun_list]
        df_akun = pd.DataFrame(akun_dict_list)
        st.table(df_akun)
    finally:
        conn.close()

# Fungsi untuk menambah akun admin
def tambah_akun_admin():
    st.subheader("Tambah Akun Admin")
    username = st.text_input("Username Admin Baru", key="admin_username")
    password = st.text_input("Password Admin Baru", type="password", key="admin_password")
    konfirmasi_password = st.text_input("Konfirmasi Password", type="password", key="admin_konfirmasi_password")

    if st.button("Tambah Akun Admin", key="tambah_admin"):
        if password == konfirmasi_password:
            try:
                conn = get_connection()
                c = conn.cursor()
                c.execute('INSERT INTO akun (username, password, role) VALUES (?, ?, ?)', (username, password, 'admin'))
                conn.commit()
                conn.close()
                st.success(f"Akun admin '{username}' berhasil ditambahkan.")
            except sqlite3.IntegrityError as e:
                if 'UNIQUE constraint failed' in str(e):
                    st.error(f"Username '{username}' sudah ada.")
                else:
                    st.error(f"Terjadi kesalahan saat mendaftarkan akun: {e}")
        else:
            st.error("Password dan konfirmasi password tidak sesuai.")

# Fungsi untuk menghapus akun dari semua jenis
def hapus_akun():
    st.subheader("Hapus Akun")
    username_hapus = st.text_input("Username yang Ingin Dihapus", key="hapus_akun")

    if st.button("Hapus Akun", key="hapus_akun_button"):
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute('DELETE FROM akun WHERE username=?', (username_hapus,))
            conn.commit()
            conn.close()
            st.success(f"Akun '{username_hapus}' berhasil dihapus.")
        except sqlite3.Error as e:
            st.error(f"Terjadi kesalahan saat menghapus akun: {e}")

# Fungsi untuk menambah akun superadmin
def tambah_akun_superadmin():
    st.subheader("Tambah Akun Superadmin")
    username_superadmin = st.text_input("Username Superadmin Baru", key="superadmin_username")
    password_superadmin = st.text_input("Password Superadmin Baru", type="password", key="superadmin_password")
    konfirmasi_password_superadmin = st.text_input("Konfirmasi Password", type="password", key="superadmin_konfirmasi_password")

    if st.button("Tambah Akun Superadmin", key="tambah_superadmin"):
        if password_superadmin == konfirmasi_password_superadmin:
            try:
                conn = get_connection()
                c = conn.cursor()
                c.execute('INSERT INTO akun (username, password, role) VALUES (?, ?, ?)', (username_superadmin, password_superadmin, 'superadmin'))
                conn.commit()
                conn.close()
                st.success(f"Akun superadmin '{username_superadmin}' berhasil ditambahkan.")
            except sqlite3.IntegrityError as e:
                if 'UNIQUE constraint failed' in str(e):
                    st.error(f"Username '{username_superadmin}' sudah ada.")
                else:
                    st.error(f"Terjadi kesalahan saat mendaftarkan akun superadmin: {e}")
        else:
            st.error("Password dan konfirmasi password tidak sesuai.")

# Fungsi untuk login
def login():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM akun WHERE username=? AND password=?', (username, password))
            akun = c.fetchone()
            conn.close()
            if akun:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = akun[3]  # Role dari akun
                st.experimental_rerun()
                st.success(f"Selamat datang, {username}!")
                return True
            else:
                st.error("Username atau password salah.")
        except sqlite3.Error as e:
            st.error(f"Terjadi kesalahan saat login: {e}")
    return False

# Fungsi untuk mendaftarkan akun user baru
def daftar_akun():
    st.subheader("Daftar Akun Baru")
    username = st.text_input("Username Baru", key="daftar_username")
    password = st.text_input("Password Baru", type="password", key="daftar_password")
    konfirmasi_password = st.text_input("Konfirmasi Password", type="password", key="daftar_konfirmasi_password")

    if st.button("Daftar"):
        if password == konfirmasi_password:
            try:
                conn = get_connection()
                c = conn.cursor()
                c.execute('INSERT INTO akun (username, password, role) VALUES (?, ?, ?)', (username, password, 'user'))
                conn.commit()
                conn.close()
                st.success(f"Akun user '{username}' berhasil didaftarkan.")
            except sqlite3.IntegrityError as e:
                if 'UNIQUE constraint failed' in str(e):
                    st.error(f"Username '{username}' sudah ada.")
                else:
                    st.error(f"Terjadi kesalahan saat mendaftarkan akun: {e}")
        else:
            st.error("Password dan konfirmasi password tidak sesuai.")

# Fungsi untuk logout
def logout():
    st.session_state["logged_in"] = False
    st.session_state.pop("username", None)
    st.session_state.pop("role", None)
    st.experimental_rerun()

# Tambahkan CSS untuk latar belakang gambar dan sidebar biru
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://i.ibb.co.com/0jpYBCB/walpaperr.png");
        background-size: cover;
    }
    .st-emotion-cache-6qob1r {  /* CSS class untuk sidebar */
        background-color: #ADD8E6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 style='text-align: center; color: green;'>Perpustakaan Digital</h1>", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    st.sidebar.image("https://i.ibb.co.com/Jsjdns1/5e7040a5-d888-4418-a7af-48446282402c.webp", use_column_width=True)
    
    if st.session_state["role"] == "admin":
        menu = ["Tambah Buku Digital", "Tambah Buku Fisik", "Tampilkan Semua Buku", "Pinjam Buku", "Kembalikan Buku", "Hitung Denda", "Hapus Buku", "Logout"]
    elif st.session_state["role"] == "superadmin":
        menu = ["Kelola Akun", "Tambah Akun Admin", "Hapus Akun", "Tambah Akun Superadmin", "Logout"]
    else:
        menu = ["Tampilkan Semua Buku", "Pinjam Buku", "Kembalikan Buku", "Logout"]

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Tambah Buku Digital" and (st.session_state["role"] == "admin" or st.session_state["role"] == "superadmin"):
        tambah_buku_digital()
    elif choice == "Tambah Buku Fisik" and (st.session_state["role"] == "admin" or st.session_state["role"] == "superadmin"):
        tambah_buku_fisik()
    elif choice == "Tampilkan Semua Buku":
        tampilkan_semua_buku()
    elif choice == "Pinjam Buku":
        pinjam_buku()
    elif choice == "Kembalikan Buku":
        kembalikan_buku()
    elif choice == "Hitung Denda" and (st.session_state["role"] == "admin" or st.session_state["role"] == "superadmin"):
        hitung_denda()
    elif choice == "Hapus Buku" and (st.session_state["role"] == "admin" or st.session_state["role"] == "superadmin"):
        hapus_buku()
    elif choice == "Kelola Akun" and st.session_state["role"] == "superadmin":
        tampilkan_daftar_akun()
    elif choice == "Tambah Akun Admin" and st.session_state["role"] == "superadmin":
        tambah_akun_admin()
    elif choice == "Hapus Akun" and st.session_state["role"] == "superadmin":
        hapus_akun()
    elif choice == "Tambah Akun Superadmin" and st.session_state["role"] == "superadmin":
        tambah_akun_superadmin()
    elif choice == "Logout":
        logout()
else:
    st.sidebar.image("https://i.ibb.co.com/Jsjdns1/5e7040a5-d888-4418-a7af-48446282402c.webp", use_column_width=True)
    menu = ["Login", "Daftar Akun"]
    choice = st.sidebar.selectbox("Menu", menu)    

    if choice == "Login":
        login()
    elif choice == "Daftar Akun":
        daftar_akun()

# Tambahkan teks hak cipta di bagian bawah aplikasi
st.markdown("<div style='text-align: center; margin-top: 50px;'>© 2024 Made Arya</div>", unsafe_allow_html=True)
