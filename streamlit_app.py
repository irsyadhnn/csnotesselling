import streamlit as st
import mysql.connector

# Koneksi ke database
db = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="csnoteselling"
)
cursor = db.cursor()

# Inisialisasi session state jika belum ada
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

role = st.session_state.role  # Ambil nilai role dari session state
username = st.session_state.username

# Sidebar Login / Registrasi
st.sidebar.title("Login / Registrasi")

if role is None:
    with st.sidebar.form("login_form"):
        username_input = st.text_input("Nama Pengguna")
        login_btn = st.form_submit_button("Login")
    
    with st.sidebar.form("register_form"):
        new_username = st.text_input("Nama Pengguna Baru")
        email = st.text_input("Email")
        role_selection = st.radio("Pilih Peran:", ["BUYER", "SELLER"])
        register_btn = st.form_submit_button("Registrasi")
    
    if login_btn:
        cursor.execute("SELECT role FROM pengguna WHERE nama = %s", (username_input,))
        user = cursor.fetchone()
        if user:
            st.session_state.role = user[0]
            st.session_state.username = username_input
            st.rerun()
        else:
            st.sidebar.error("Nama pengguna tidak ditemukan. Silakan registrasi terlebih dahulu.")
    
    if register_btn:
        cursor.execute("SELECT pengguna_id FROM pengguna ORDER BY pengguna_id DESC LIMIT 1")
        last_id = cursor.fetchone()
        
        if last_id:
            last_num = int(last_id[0][1:])  # Ambil angka setelah "U"
            new_id = f"U{last_num + 1:04d}"  # Format ID baru, contoh: U0002, U0003
        else:
            new_id = "U0001"  # Jika belum ada user
        
        cursor.execute("SELECT * FROM pengguna WHERE nama = %s", (new_username,))
        existing_user = cursor.fetchone()
        if existing_user:
            st.sidebar.error("Nama pengguna sudah terdaftar, silakan pilih nama lain.")
        else:
            cursor.execute("INSERT INTO pengguna (pengguna_id, nama, email, role) VALUES (%s, %s, %s, %s)", (new_id, new_username, email, role_selection))
            db.commit()
            st.sidebar.success("Registrasi berhasil! Silakan login.")
            st.rerun()
else:
    st.sidebar.write(f"Login sebagai: {username} ({role})")
    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

if role == "BUYER":
    st.title("Dashboard BUYER")
    search_query = st.text_input("Cari Mata Kuliah atau Materi")
    
    cursor.execute("SELECT DISTINCT mata_kuliah FROM catatan ORDER BY mata_kuliah")
    mata_kuliah = cursor.fetchall()
    selected_mk = st.selectbox("Pilih Mata Kuliah", [mk[0] for mk in mata_kuliah])
    
    query = "SELECT catatan_id, materi, harga, file_path FROM catatan WHERE mata_kuliah = %s"
    params = (selected_mk,)
    
    if search_query:
        query += " AND (materi LIKE %s OR mata_kuliah LIKE %s)"
        params += (f"%{search_query}%", f"%{search_query}%")
    
    cursor.execute(query, params)
    materi_list = cursor.fetchall()
    
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    for materi in materi_list:
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(materi[1])  # Nama materi
        with col2:
            if st.button(f'Beli - Rp {materi[2]}', key=f'beli_{materi[0]}'):
                st.session_state.cart.append(materi)
                st.success(f'{materi[1]} ditambahkan ke keranjang!')
    
    st.sidebar.subheader("🛒 Keranjang Belanja")
    for item in st.session_state.cart:
        st.sidebar.write(f'{item[1]} - Rp {item[2]}')
    
    if st.sidebar.button("Checkout"):
        if st.session_state.cart:
            st.success("Checkout berhasil! Berikut daftar belanja Anda:")
            for item in st.session_state.cart:
                st.write(f'- {item[1]} - Rp {item[2]}')
            st.session_state.cart.clear()
        else:
            st.error("Keranjang belanja kosong!")

elif role == "SELLER":
    st.title("Dashboard SELLER")
    cursor.execute("SELECT DISTINCT mata_kuliah FROM catatan ORDER BY mata_kuliah")
    mata_kuliah = cursor.fetchall()
    
    st.subheader("Upload Materi Baru")
    mk_selected = st.selectbox("Pilih Mata Kuliah", [mk[0] for mk in mata_kuliah])
    nama_materi = st.text_input("Nama Materi")
    harga_materi = st.number_input("Harga (Rp)", min_value=0)
    file_materi = st.file_uploader("Upload File Materi")
    
    if st.button("Upload"):
        if nama_materi and harga_materi and file_materi:
            cursor.execute("SELECT catatan_id FROM catatan ORDER BY catatan_id DESC LIMIT 1")
            last_id = cursor.fetchone()
            
            if last_id:
                last_num = int(last_id[0][1:])  # Ambil angka setelah "C"
                new_id = f"C{last_num + 1:04d}"  # Format ID baru, contoh: C0002, C0003
            else:
                new_id = "C0001"  # Jika belum ada catatan
            
            cursor.execute(
                "INSERT INTO catatan (catatan_id, mata_kuliah, materi, file_path, harga) VALUES (%s, %s, %s, %s, %s)", 
                (new_id, mk_selected, nama_materi, f'/files/{file_materi.name}', harga_materi)
            )
            db.commit()
            st.success("Materi berhasil diunggah!")

# Tutup koneksi database
cursor.close()
db.close()
