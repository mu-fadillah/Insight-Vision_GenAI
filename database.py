import mysql.connector

def get_connection():
    """Fungsi pembantu untuk membuat koneksi ke MySQL."""
    return mysql.connector.connect(
        host="localhost",
        user="root",      # User default XAMPP
        password="",      # Password default XAMPP (kosong)
        database="insight_vision"
    )

def simpan_ke_db(nama_file, hasil):
    """Menyimpan hasil analisis ke tabel analisis_log."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO analisis_log (nama_file, hasil_analisis) VALUES (%s, %s)"
        val = (nama_file, hasil)
        
        cursor.execute(sql, val)
        conn.commit()
        print(f"✅ Data {nama_file} berhasil disimpan ke database.")
        
    except mysql.connector.Error as err:
        print(f"❌ Error Database (Simpan): {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def ambil_riwayat(limit=5):
    """Mengambil riwayat analisis terbaru untuk ditampilkan di UI."""
    try:
        conn = get_connection()
        # Menggunakan dictionary=True agar hasil query berupa list of dictionary
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT nama_file, hasil_analisis, waktu_simpan FROM analisis_log ORDER BY waktu_simpan DESC LIMIT %s"
        cursor.execute(sql, (limit,))
        
        return cursor.fetchall()
        
    except mysql.connector.Error as err:
        print(f"❌ Error Database (Ambil): {err}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def hapus_semua_riwayat():
    """Menghapus semua data dari tabel analisis_log."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE analisis_log")
        conn.commit()
        print("✅ Semua riwayat telah dihapus.")
    except mysql.connector.Error as err:
        print(f"❌ Error Database (Hapus): {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()