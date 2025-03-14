import streamlit as st
import mysql.connector

# Koneksi ke database
db = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="noteselling-wirpl"
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
        password_input = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

    with st.sidebar.form("register_form"):
        new_username = st.text_input("Nama Pengguna Baru")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role_selection = st.radio("Pilih Peran:", ["BUYER", "SELLER"])
        register_btn = st.form_submit_button("Registrasi")

    if login_btn:
        cursor.execute("SELECT role, password, is_verified FROM users WHERE username = %s", (username_input,))
        user = cursor.fetchone()
        if user and user[1] == password_input:
            if user[2] == 'TRUE':
                st.session_state.update({
                    "role": user[0],
                    "username": username_input
                })
                st.rerun()
            else:
                st.sidebar.error("Akun belum diverifikasi. Silakan cek email Anda.")
        else:
            st.sidebar.error("Nama pengguna atau password salah. Silakan coba lagi.")

    if register_btn:
        cursor.execute("SELECT * FROM users WHERE username = %s", (new_username,))
        existing_user = cursor.fetchone()
        if existing_user:
            st.sidebar.error("Nama pengguna sudah terdaftar, silakan pilih nama lain.")
        else:
            cursor.execute("INSERT INTO users (username, email, password, role, is_verified) VALUES (%s, %s, %s, %s, 'FALSE')", (new_username, email, password, role_selection))
            db.commit()
            st.sidebar.success("Registrasi berhasil! Silakan cek email untuk verifikasi.")
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
    
    cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
    courses = cursor.fetchall()
    course_dict = {course[0]: course[1] for course in courses}
    selected_course_id = st.selectbox("Pilih Mata Kuliah", list(course_dict.keys()), format_func=lambda x: course_dict[x])
    
    query = "SELECT material_id, title, price, file_path FROM materials WHERE course_id = %s"
    params = (selected_course_id,)
    
    if search_query:
        query += " AND (title LIKE %s)"
        params += (f"%{search_query}%",)
    
    cursor.execute(query, params)
    materials_list = cursor.fetchall()
    
    if "cart" not in st.session_state:
        st.session_state.cart = []
    
    for material in materials_list:
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(material[1])  # Nama materi
        with col2:
            if st.button(f'Beli - Rp {material[2]}', key=f'beli_{material[0]}'):
                st.session_state.cart.append(material)
                st.success(f'{material[1]} ditambahkan ke keranjang!')
    
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
    cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
    courses = cursor.fetchall()
    course_dict = {course[0]: course[1] for course in courses}
    
    st.subheader("Upload Materi Baru")
    course_selected_id = st.selectbox("Pilih Mata Kuliah", list(course_dict.keys()), format_func=lambda x: course_dict[x])
    material_title = st.text_input("Judul Materi")
    material_price = st.number_input("Harga (Rp)", min_value=0)
    file_material = st.file_uploader("Upload File Materi")
    
    if st.button("Upload"):
        if material_title and material_price and file_material:
            cursor.execute("INSERT INTO materials (course_id, title, file_path, price) VALUES (%s, %s, %s, %s)", (course_selected_id, material_title, f'/files/{file_material.name}', material_price))
            db.commit()
            st.success("Materi berhasil diunggah!")

# Debugging Session State
st.sidebar.write("DEBUG:", st.session_state)

# Tutup koneksi database
cursor.close()
db.close()
