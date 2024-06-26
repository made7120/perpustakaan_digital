import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import os
import sqlite3

# Ensure folders for storing book covers and digital books exist
if not os.path.exists("sampul_buku"):
    os.makedirs("sampul_buku")

if not os.path.exists("buku_digital"):
    os.makedirs("buku_digital")

# Initialize SQLite database for user credentials
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
conn.commit()

# Function to register a new user
def register_user(username, password):
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

# Function to check user credentials
def check_login(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()

# Display the login page
def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    if st.button("Register"):
        st.session_state['show_register'] = True

# Display the registration page
def register_page():
    st.title("Register")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")
    if st.button("Register"):
        if username and password:
            register_user(username, password)
            st.success("User registered successfully!")
            st.session_state['show_register'] = False
        else:
            st.error("Please provide a username and password")
    if st.button("Back to Login"):
        st.session_state['show_register'] = False

# Check if the user is logged in or wants to register
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'show_register' not in st.session_state:
    st.session_state['show_register'] = False

if st.session_state['show_register']:
    register_page()
elif not st.session_state['logged_in']:
    login_page()
else:
    st.title(f"Welcome, {st.session_state['username']}")

    # Class Buku yang dimodifikasi untuk menyertakan atribut foto sampul
    class Buku:
        def __init__(self, judul, penulis, tahun_terbit, foto_sampul=None, status="tersedia"):
            self.judul = judul
            self.penulis = penulis
            self.tahun_terbit = tahun_terbit
            self.foto_sampul = foto_sampul
            self.status = status

        def info_buku(self):
            status_display = "tidak tersedia" if self.status == "dipinjam" else "tersedia"
            return f"Judul: {self.judul}, Penulis: {self.penulis}, Tahun Terbit: {self.tahun_terbit}, Status: {status_display}, Foto Sampul: {self.foto_sampul}"

    class BukuDigital(Buku):
        def __init__(self, judul, penulis, tahun_terbit, ukuran_file, format_file, file_path, foto_sampul=None, status="tersedia"):
            super().__init__(judul, penulis, tahun_terbit, foto_sampul, status)
            self.ukuran_file = ukuran_file
            self.format_file = format_file
            self.file_path = file_path

        def info_buku(self):
            info = super().info_buku()
            return f"{info}, Ukuran File: {self.ukuran_file}MB, Format: {self.format_file}, Path: {self.file_path}"

    class BukuFisik(Buku):
        def __init__(self, judul, penulis, tahun_terbit, jumlah_halaman, berat, foto_sampul=None, status="tersedia"):
            super().__init__(judul, penulis, tahun_terbit, foto_sampul, status)
            self.jumlah_halaman = jumlah_halaman
            self.berat = berat

        def info_buku(self):
            info = super().info_buku()
            return f"{info}, Jumlah Halaman: {self.jumlah_halaman}, Berat: {self.berat} gram"

    class Perpustakaan:
        def __init__(self):
            self.daftar_buku = []
            self.load_data()

        def tambah_buku(self, buku):
            self.daftar_buku.append(buku)
            self.simpan_data()

        def cari_buku(self, judul):
            for buku in self.daftar_buku:
                if buku.judul.lower() == judul.lower():
                    return buku
            return None

        def tampilkan_semua_buku(self):
            return [buku.info_buku() for buku in self.daftar_buku]

        def tampilkan_semua_buku_df(self):
            data = [{
                'Judul': buku.judul,
                'Penulis': buku.penulis,
                'Tahun Terbit': buku.tahun_terbit,
                'Status': "tidak tersedia" if buku.status == "dipinjam" else "tersedia",
                'Ukuran File (MB)': getattr(buku, 'ukuran_file', None),
                'Format File': getattr(buku, 'format_file', None),
                'Jumlah Halaman': getattr(buku, 'jumlah_halaman', None),
                'Berat (gram)': getattr(buku, 'berat', None),
                'Foto Sampul': buku.foto_sampul,
                'File Path': getattr(buku, 'file_path', None)
            } for buku in self.daftar_buku]

            df = pd.DataFrame(data)
            return df

        def pinjam_buku(self, judul):
            buku = self.cari_buku(judul)
            if buku and buku.status == "tersedia":
                buku.status = "dipinjam"
                self.simpan_data()
                return f"Buku '{judul}' berhasil dipinjam."
            else:
                return f"Buku '{judul}' tidak tersedia untuk dipinjam."

        def kembalikan_buku(self, judul):
            buku = self.cari_buku(judul)
            if buku and buku.status == "dipinjam":
                buku.status = "tersedia"
                self.simpan_data()
                return f"Buku '{judul}' berhasil dikembalikan."
            else:
                return f"Buku '{judul}' tidak sedang dipinjam."

        def hapus_buku(self, judul):
            buku = self.cari_buku(judul)
            if buku:
                self.daftar_buku.remove(buku)
                self.simpan_data()
                return f"Buku '{judul}' berhasil dihapus."
            else:
                return f"Buku '{judul}' tidak ditemukan."

        def simpan_data(self):
            data = [{
                'Judul': buku.judul,
                'Penulis': buku.penulis,
                'Tahun Terbit': buku.tahun_terbit,
                'Status': buku.status,
                'Ukuran File (MB)': getattr(buku, 'ukuran_file', None),
                'Format File': getattr(buku, 'format_file', None),
                'Jumlah Halaman': getattr(buku, 'jumlah_halaman', None),
                'Berat (gram)': getattr(buku, 'berat', None),
                'Foto Sampul': buku.foto_sampul,
                'File Path': getattr(buku, 'file_path', None)
            } for buku in self.daftar_buku]

            df = pd.DataFrame(data)
            df.to_excel('data_perpustakaan.xlsx', index=False)

        def load_data(self):
            try:
                df = pd.read_excel('data_perpustakaan.xlsx')
                for _, row in df.iterrows():
                    if pd.notna(row['Ukuran File (MB)']):
                        buku = BukuDigital(row['Judul'], row['Penulis'], row['Tahun Terbit'], row['Ukuran File (MB)'], row['Format File'], row['File Path'], row['Foto Sampul'], row['Status'])
                    else:
                        buku = BukuFisik(row['Judul'], row['Penulis'], row['Tahun Terbit'], row['Jumlah Halaman'], row['Berat (gram)'], row['Foto Sampul'], row['Status'])
                    self.daftar_buku.append(buku)
            except FileNotFoundError:
                pass

    # Initialize library
    perpustakaan = Perpustakaan()

    # Streamlit Interface
    st.title("Sistem Perpustakaan Sederhana")

    tabs = st.tabs(["Tambah Buku", "Cari Buku", "Tampilkan Semua Buku", "Pinjam Buku", "Kembalikan Buku", "Hapus Buku"])

    with tabs[0]:
        st.subheader("Tambah Buku Baru")
        tipe_buku = st.selectbox("Tipe Buku", ["Buku Fisik", "Buku Digital"])
        judul = st.text_input("Judul Buku")
        penulis = st.text_input("Penulis Buku")
        tahun_terbit = st.number_input("Tahun Terbit", min_value=1500, max_value=2024, step=1)
        foto_sampul = st.file_uploader("Unggah Foto Sampul", type=["jpg", "png", "jpeg"])

        if foto_sampul is not None:
            foto_sampul_path = os.path.join("sampul_buku", foto_sampul.name)
            with open(foto_sampul_path, "wb") as f:
                f.write(foto_sampul.getbuffer())

        if tipe_buku == "Buku Digital":
            ukuran_file = st.number_input("Ukuran File (MB)", min_value=0.1)
            format_file = st.selectbox("Format File", ["PDF", "EPUB", "MOBI"])
            file_buku = st.file_uploader("Unggah File Buku", type=["pdf", "epub", "mobi"])

            if file_buku is not None:
                file_path = os.path.join("buku_digital", file_buku.name)
                with open(file_path, "wb") as f:
                    f.write(file_buku.getbuffer())

            if st.button("Tambah Buku Digital"):
                buku = BukuDigital(judul, penulis, tahun_terbit, ukuran_file, format_file, file_path, foto_sampul_path)
                perpustakaan.tambah_buku(buku)
                st.success(f"Buku digital '{judul}' berhasil ditambahkan.")
        else:
            jumlah_halaman = st.number_input("Jumlah Halaman", min_value=1)
            berat = st.number_input("Berat (gram)", min_value=1)
            if st.button("Tambah Buku Fisik"):
                buku = BukuFisik(judul, penulis, tahun_terbit, jumlah_halaman, berat, foto_sampul_path)
                perpustakaan.tambah_buku(buku)
                st.success(f"Buku fisik '{judul}' berhasil ditambahkan.")

    with tabs[1]:
        st.subheader("Cari Buku")
        judul = st.text_input("Masukkan Judul Buku")
        if st.button("Cari"):
            buku = perpustakaan.cari_buku(judul)
            if buku:
                st.write(buku.info_buku())
                if buku.foto_sampul:
                    st.image(buku.foto_sampul, caption=buku.judul)
            else:
                st.warning("Buku tidak ditemukan.")

    with tabs[2]:
        st.subheader("Daftar Semua Buku")
        df_buku = perpustakaan.tampilkan_semua_buku_df()
        st.dataframe(df_buku)

    with tabs[3]:
        st.subheader("Pinjam Buku")
        judul = st.text_input("Masukkan Judul Buku yang Akan Dipinjam")
        if st.button("Pinjam"):
            pesan = perpustakaan.pinjam_buku(judul)
            st.write(pesan)

    with tabs[4]:
        st.subheader("Kembalikan Buku")
        judul = st.text_input("Masukkan Judul Buku yang Akan Dikembalikan")
        if st.button("Kembalikan"):
            pesan = perpustakaan.kembalikan_buku(judul)
            st.write(pesan)

    with tabs[5]:
        st.subheader("Hapus Buku")
        judul = st.text_input("Masukkan Judul Buku yang Akan Dihapus")
        if st.button("Hapus"):
            pesan = perpustakaan.hapus_buku(judul)
            st.write(pesan)

#css
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://i.ibb.co.com/dDYYLWp/cccc.png");
        background-size: cover;

    </style>
    """,
    unsafe_allow_html=True
)
