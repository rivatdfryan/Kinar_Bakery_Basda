import psycopg2
from tabulate import tabulate
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'postgres',
    'password': 'a.1056.A',
    'database': 'Kinar_Bakery_B'
}

def connection():
    try:
        return psycopg2.connect(**db_config)
    except psycopg2.OperationalError as e:
        print(f"Error koneksi database: {e}")
        return None

def Login():
    print("\n=== Login Sistem Kinar Bakery ===".center(50))
    username = input("Username\t: ")
    password = input("Password\t: ")
    
    conn = connection()
    if not conn:
        return None, None
    
    try:
        query = conn.cursor()
        query.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = query.fetchone()
        query.close()
        conn.close()
        
        if user:
            return user[0], user[3] 
        else:
            print("Login gagal, username atau password salah")
            return None, None
    except psycopg2.Error as e:
        print(f"Error query: {e}")
        query.close()
        conn.close()
        return None, None

def dashboard_owner(id_user):
    conn = connection()
    query = conn.cursor()
    
    query.execute("SELECT SUM(pendapatan) as Total_Pendapatan FROM outlets")
    Total_Pendapatan = query.fetchone()[0] or 0
    
    query.execute("SELECT SUM(pengeluaran) as Total_Pengeluaran FROM outlets")
    Total_Pengeluaran = query.fetchone()[0] or 0
    
    Saldo = Total_Pendapatan - Total_Pengeluaran
    
    query.execute("SELECT COUNT(*) as Jumlah_Outlet FROM outlets")
    Jumlah_Outlet = query.fetchone()[0]
    
    query.execute("SELECT COUNT(*) as Jumlah_Karyawan FROM karyawan")
    Jumlah_Karyawan = query.fetchone()[0]
    
    print("\n=== Dashboard Owner ===".center(50))
    data = [
        ["Total Pendapatan", f"Rp {Total_Pendapatan:,.2f}"],
        ["Total Pengeluaran", f"Rp {Total_Pengeluaran:,.2f}"],
        ["Saldo", f"Rp {Saldo:,.2f}"],
        ["Jumlah Outlet", Jumlah_Outlet],
        ["Jumlah Karyawan", Jumlah_Karyawan]
    ]
    print(tabulate(data, headers=["Metrik", "Nilai"], tablefmt="pretty"))
    
    query.close()
    conn.close()
    
    while True:
        print("\n=== Menu Owner ===".center(50))
        print("1. Kelola Produk")
        print("2. Kelola Bahan Baku")
        print("3. Kelola Outlet")
        print("4. Kelola Katalog Produk")
        print("5. Kelola Akun")
        print("6. Kelola Karyawan")
        print("7. Rekapitulasi Absensi")
        print("8. Laporan Penjualan")
        print("9. Laporan Pembelian")
        print("10. Rekapitulasi Keuangan")
        print("11. Ajuan Karyawan")
        print("12. Keluar")
        choice = input("Masukkan pilihan (1-12)\t: ")
        if choice == "1":
            Kelola_Produk()
        elif choice == "2":
            Kelola_Bahan_Baku()
        elif choice == "3":
            Kelola_Outlet()
        elif choice == "4":
            Kelola_Katalog()
        elif choice == "5":
            Kelola_Akun()
        elif choice == "6":
            Kelola_Karyawan()
        elif choice == "7":
            Rekap_absensi()
        elif choice == "8":
            Laporan_Penjualan()
        elif choice == "9":
            Laporan_Pembelian()
        elif choice == "10":
            Rekap_Keuangan()
        elif choice == "11":
            Pengajuan()
        elif choice == "12":
            break
        else:
            print("Pilihan tidak valid, coba lagi")

def Kelola_Produk():
    conn = connection()
    if not conn:
        return
    
    try:
        query = conn.cursor()
        while True:
            print("\n=== Kelola Produk ===".center(50))
            query.execute("""
                SELECT p.id_produk, p.nama, p.jenis, p.stok,
                       STRING_AGG(b.nama || ': ' || r.jumlah::TEXT || ' unit', ', ') as bahan_baku
                FROM produk p
                LEFT JOIN resep r ON p.id_produk = r.id_produk
                LEFT JOIN bahan_baku b ON r.id_bahan = b.id_bahan
                GROUP BY p.id_produk
            """)
            produk = query.fetchall()
        
            table_data = [[p[0], p[1], p[2], p[3], p[4] or ''] for p in produk]
            print(tabulate(table_data, headers=["ID", "Nama", "Jenis", "Stok", "Bahan Baku"], tablefmt="pretty"))
            
            print("\nPilih aksi:")
            print("1. Tambah produk baru")
            print("2. Tambah stok produk")
            print("3. Kurangi stok produk")
            print("4. Edit produk")
            print("5. Kembali")
            choice = input("Masukkan pilihan (1-5)\t: ")
            
            if choice == '1':
                nama = input("Masukkan nama produk: ")
                if not nama.strip():
                    print("Nama produk tidak boleh kosong!")
                    continue
                jenis = input("Masukkan jenis produk: ")
                if not jenis.strip():
                    print("Jenis produk tidak boleh kosong!")
                    continue
                
                query.execute("INSERT INTO produk (nama, jenis, stok) VALUES (%s, %s, 0) RETURNING id_produk", 
                             (nama, jenis))
                id_produk = query.fetchone()[0]
                
                while True:
                    id_bahan = input("Masukkan ID bahan baku (kosongkan untuk selesai): ")
                    if not id_bahan:
                        break
                    try:
                        id_bahan = int(id_bahan)
                    except ValueError:
                        print("ID bahan baku harus berupa angka!")
                        continue
                    
                    jumlah = input("Masukkan jumlah bahan baku per unit produk: ")
                    try:
                        jumlah = float(jumlah)
                        if jumlah <= 0:
                            print("Jumlah harus lebih dari 0!")
                            continue
                    except ValueError:
                        print("Jumlah harus berupa angka!")
                        continue
                    
                    query.execute("SELECT id_bahan FROM bahan_baku WHERE id_bahan = %s", (id_bahan,))
                    if not query.fetchone():
                        print(f"Bahan baku dengan ID {id_bahan} tidak ditemukan!")
                        continue
                    
                    query.execute("INSERT INTO resep (id_produk, id_bahan, jumlah) VALUES (%s, %s, %s)", 
                                 (id_produk, id_bahan, jumlah))
                conn.commit()
                print(f"Produk {nama} berhasil ditambahkan.")
            
            elif choice == '2':
                id_produk = input("Masukkan ID produk: ")
                try:
                    id_produk = int(id_produk)
                except ValueError:
                    print("ID produk harus berupa angka!")
                    continue
                
                jumlah = input("Masukkan jumlah stok yang ditambahkan: ")
                try:
                    jumlah = int(jumlah)
                    if jumlah <= 0:
                        print("Jumlah harus lebih dari 0!")
                        continue
                except ValueError:
                    print("Jumlah harus berupa angka!")
                    continue
                
                query.execute("SELECT id_bahan, jumlah FROM resep WHERE id_produk = %s", (id_produk,))
                bahan = query.fetchall()
                if not bahan:
                    print(f"Produk dengan ID {id_produk} tidak ditemukan atau tidak memiliki resep!")
                    continue
                
                can_produce = True
                for bahan_item in bahan:
                    query.execute("SELECT stok FROM bahan_baku WHERE id_bahan = %s", (bahan_item[0],))
                    bahan_stok = query.fetchone()
                    if not bahan_stok or bahan_stok[0] < bahan_item[1] * jumlah:
                        can_produce = False
                        print(f"Stok bahan baku ID {bahan_item[0]} tidak cukup!")
                        break
                
                if can_produce:
                    query.execute("UPDATE produk SET stok = stok + %s WHERE id_produk = %s", (jumlah, id_produk))
                    for bahan_item in bahan:
                        query.execute("UPDATE bahan_baku SET stok = stok - %s WHERE id_bahan = %s", 
                                     (bahan_item[1] * jumlah, bahan_item[0]))
                    conn.commit()
                    print(f"Stok produk ID {id_produk} berhasil ditambahkan sebanyak {jumlah}.")
            
            elif choice == '3':
                id_produk = input("Masukkan ID produk: ")
                try:
                    id_produk = int(id_produk)
                except ValueError:
                    print("ID produk harus berupa angka!")
                    continue
                
                jumlah = input("Masukkan jumlah stok yang dikurangi: ")
                try:
                    jumlah = int(jumlah)
                    if jumlah <= 0:
                        print("Jumlah harus lebih dari 0!")
                        continue
                except ValueError:
                    print("Jumlah harus berupa angka!")
                    continue
                
                query.execute("SELECT stok FROM produk WHERE id_produk = %s", (id_produk,))
                stok = query.fetchone()
                if not stok:
                    print(f"Produk dengan ID {id_produk} tidak ditemukan!")
                    continue
                if stok[0] < jumlah:
                    print("Stok tidak cukup untuk dikurangi!")
                    continue
                
                query.execute("UPDATE produk SET stok = stok - %s WHERE id_produk = %s", (jumlah, id_produk))
                conn.commit()
                print(f"Stok produk ID {id_produk} berhasil dikurangi sebanyak {jumlah}.")
            
            elif choice == '4':
                id_produk = input("Masukkan ID produk: ")
                try:
                    id_produk = int(id_produk)
                except ValueError:
                    print("ID produk harus berupa angka!")
                    continue
                
                query.execute("SELECT id_produk FROM produk WHERE id_produk = %s", (id_produk,))
                if not query.fetchone():
                    print(f"Produk dengan ID {id_produk} tidak ditemukan!")
                    continue
                
                nama = input("Masukkan nama baru (kosongkan jika tidak diubah): ")
                jenis = input("Masukkan jenis baru (kosongkan jika tidak diubah): ")
                
                update_query = "UPDATE produk SET "
                update_params = []
                if nama:
                    update_query += "nama = %s, "
                    update_params.append(nama)
                if jenis:
                    update_query += "jenis = %s, "
                    update_params.append(jenis)
                
                if update_params:
                    update_query = update_query.rstrip(", ") + " WHERE id_produk = %s"
                    update_params.append(id_produk)
                    query.execute(update_query, update_params)
                    conn.commit()
                    print(f"Produk ID {id_produk} berhasil diupdate.")
                else:
                    print("Tidak ada perubahan dilakukan.")
            
            elif choice == '5':
                break
            else:
                print("Pilihan tidak valid!")
    except psycopg2.Error as e:
        print(f"Error query: {e}")
    finally:
        query.close()
        conn.close()

def Kelola_Bahan_Baku():
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Kelola Bahan Baku ===".center(50))
        query.execute("SELECT id_bahan, nama, stok, harga_unit FROM bahan_baku")
        bahan = query.fetchall()
        
        table_data = [[b[0], b[1], b[2], f"Rp {b[3]:,.2f}"] for b in bahan]
        print(tabulate(table_data, headers=["ID", "Nama", "Stok", "Harga per Unit"], tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Tambah bahan baku baru")
        print("2. Tambah stok bahan baku")
        print("3. Kurangi stok bahan baku")
        print("4. Kembali")
        choice = input("Masukkan pilihan (1-4)\t: ")
        
        if choice == '1':
            nama = input("Masukkan nama bahan baku: ")
            harga = float(input("Masukkan harga per unit: "))
            query.execute("INSERT INTO bahan_baku (nama, stok, harga_unit) VALUES (%s, 0, %s)", 
                         (nama, harga))
            conn.commit()
            print(f"Bahan baku {nama} berhasil ditambahkan.")
        
        elif choice == '2':
            id_bahan = input("Masukkan ID bahan baku: ")
            jumlah = float(input("Masukkan jumlah stok yang ditambahkan: "))
            query.execute("SELECT harga_unit FROM bahan_baku WHERE id_bahan = %s", (id_bahan,))
            harga = query.fetchone()[0]
            total_biaya = harga * jumlah
            
            query.execute("UPDATE bahan_baku SET stok = stok + %s WHERE id_bahan = %s", 
                         (jumlah, id_bahan))
            query.execute("""
                INSERT INTO transaksi_pembelian (id_bahan, jumlah, total_biaya, tanggal_pembelian)
                VALUES (%s, %s, %s, NOW())
            """, (id_bahan, jumlah, total_biaya))
            query.execute("UPDATE outlets SET pengeluaran = pengeluaran + %s WHERE id_outlet = 1", (total_biaya,))
            query.execute("""
                INSERT INTO rekapitulasi_keuangan (id_outlet, jenis, jumlah, deskripsi, tanggal)
                VALUES (1, 'pembelian_bahan', %s, %s, NOW())
            """, (total_biaya, f"Pembelian bahan baku ID {id_bahan} sebanyak {jumlah}"))
            conn.commit()
            print(f"Stok bahan baku ID {id_bahan} berhasil ditambahkan sebanyak {jumlah}.")
        
        elif choice == '3':
            id_bahan = input("Masukkan ID bahan baku: ")
            jumlah = float(input("Masukkan jumlah stok yang dikurangi: "))
            query.execute("UPDATE bahan_baku SET stok = stok - %s WHERE id_bahan = %s", 
                         (jumlah, id_bahan))
            conn.commit()
            print(f"Stok bahan baku ID {id_bahan} berhasil dikurangi sebanyak {jumlah}.")
        
        elif choice == '4':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def Kelola_Outlet():
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Kelola Outlet ===".center(50))
        query.execute("""
            SELECT o.id_outlet, o.nama, o.lokasi, o.pendapatan, o.pengeluaran, 
                   COUNT(k.id_karyawan) as karyawan_count
            FROM outlets o
            LEFT JOIN karyawan k ON o.id_outlet = k.id_outlet
            GROUP BY o.id_outlet, o.nama, o.lokasi, o.pendapatan, o.pengeluaran
        """)
        outlets = query.fetchall()
        
        table_data = [[o[0], o[1], o[2], f"Rp {o[3]:,.2f}", f"Rp {o[4]:,.2f}", o[5]] for o in outlets]
        print(tabulate(table_data, headers=["ID", "Nama", "Lokasi", "Pendapatan", "Pengeluaran", "Jml Karyawan"], 
                      tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Tambah outlet")
        print("2. Edit outlet")
        print("3. Kembali")
        choice = input("Masukkan pilihan (1-3)\t: ")
        
        if choice == '1':
            nama = input("Masukkan nama outlet: ")
            lokasi = input("Masukkan lokasi outlet: ")
            query.execute("INSERT INTO outlets (nama, lokasi, pendapatan, pengeluaran) VALUES (%s, %s, 0, 0)", 
                         (nama, lokasi))
            conn.commit()
            print(f"Outlet {nama} berhasil ditambahkan.")
        
        elif choice == '2':
            id_outlet = input("Masukkan ID outlet: ")
            nama = input("Masukkan nama outlet baru (kosongkan jika tidak diubah): ")
            lokasi = input("Masukkan lokasi baru (kosongkan jika tidak diubah): ")
            
            update_query = "UPDATE outlets SET "
            update_params = []
            if nama:
                update_query += "nama = %s, "
                update_params.append(nama)
            if lokasi:
                update_query += "lokasi = %s, "
                update_params.append(lokasi)
            
            if update_params:
                update_query = update_query.rstrip(", ") + " WHERE id_outlet = %s"
                update_params.append(id_outlet)
                query.execute(update_query, update_params)
                conn.commit()
                print(f"Outlet ID {id_outlet} berhasil diupdate.")
            else:
                print("Tidak ada perubahan dilakukan.")
        
        elif choice == '3':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def Kelola_Katalog():
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Kelola Katalog Produk ===".center(50))
        query.execute("""
            SELECT p.id_produk, p.nama, p.stok, k.harga
            FROM katalog k
            JOIN produk p ON k.id_produk = p.id_produk
        """)
        katalog = query.fetchall()
        
        table_data = [[k[0], k[1], k[2], f"Rp {k[3]:,.2f}"] for k in katalog]
        print(tabulate(table_data, headers=["ID", "Nama", "Stok", "Harga"], tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Tambah produk ke katalog")
        print("2. Edit harga produk")
        print("3. Kembali")
        choice = input("Masukkan pilihan (1-3)\t: ")
        
        if choice == '1':
            id_produk = input("Masukkan ID produk: ")
            harga = float(input("Masukkan harga produk: "))
            query.execute("INSERT INTO katalog (id_produk, harga) VALUES (%s, %s)", 
                         (id_produk, harga))
            conn.commit()
            print(f"Produk ID {id_produk} berhasil ditambahkan ke katalog.")
        
        elif choice == '2':
            id_produk = input("Masukkan ID produk: ")
            harga = float(input("Masukkan harga baru: "))
            query.execute("UPDATE katalog SET harga = %s WHERE id_produk = %s", 
                         (harga, id_produk))
            conn.commit()
            print(f"Harga produk ID {id_produk} berhasil diupdate.")
        
        elif choice == '3':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def Kelola_Akun():
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Kelola Akun ===".center(50))
        query.execute("SELECT id_user, username, role FROM users")
        akun = query.fetchall()
        
        table_data = [[a[0], a[1], a[2]] for a in akun]
        print(tabulate(table_data, headers=["ID", "Username", "Role"], tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Tambah akun")
        print("2. Hapus akun")
        print("3. Kembali")
        choice = input("Masukkan pilihan (1-3)\t: ")
        
        if choice == '1':
            username = input("Masukkan username: ")
            password = input("Masukkan password: ")
            role = input("Masukkan role (owner/karyawan): ")
            query.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                         (username, password, role))
            if role == 'karyawan':
                nama = input("Masukkan nama karyawan: ")
                no_telepon = input("Masukkan nomor telepon: ")
                alamat = input("Masukkan alamat: ")
                tanggal_diterima = input("Masukkan tanggal mulai (YYYY-MM-DD): ")
                id_outlet = input("Masukkan ID outlet: ")
                jabatan = input("Masukkan jabatan: ")
                gaji_perjam = float(input("Masukkan gaji per jam: "))
                query.execute("SELECT id_user FROM users WHERE username = %s", (username,))
                id_user = query.fetchone()[0]
                query.execute("""
                    INSERT INTO karyawan (id_user, id_outlet, nama, no_telepon, alamat, tanggal_diterima, jabatan, gaji_perjam)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (id_user, id_outlet, nama, no_telepon, alamat, tanggal_diterima, jabatan, gaji_perjam))
            conn.commit()
            print(f"Akun {username} berhasil ditambahkan.")
        
        elif choice == '2':
            id_user = input("Masukkan ID akun yang akan dihapus: ")
            query.execute("DELETE FROM users WHERE id_user = %s", (id_user,))
            conn.commit()
            print(f"Akun ID {id_user} berhasil dihapus.")
        
        elif choice == '3':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def Kelola_Karyawan():
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Kelola Karyawan ===".center(50))
        query.execute("""
            SELECT k.id_karyawan, k.nama, k.no_telepon, k.alamat, k.tanggal_diterima, 
                   o.nama as outlet_nama, k.jabatan
            FROM karyawan k
            JOIN outlets o ON k.id_outlet = o.id_outlet
        """)
        karyawan = query.fetchall()
        
        table_data = [[k[0], k[1], k[2], k[3], k[4], k[5], k[6]] for k in karyawan]
        print(tabulate(table_data, headers=["ID", "Nama", "Telepon", "Alamat", "Tgl Mulai", 
                                           "Outlet", "Jabatan"], tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Edit karyawan")
        print("2. Kembali")
        choice = input("Masukkan pilihan (1-2)\t: ")
        
        if choice == '1':
            id_karyawan = input("Masukkan ID karyawan: ")
            nama = input("Masukkan nama baru (kosongkan jika tidak diubah): ")
            no_telepon = input("Masukkan telepon baru (kosongkan jika tidak diubah): ")
            alamat = input("Masukkan alamat baru (kosongkan jika tidak diubah): ")
            id_outlet = input("Masukkan ID outlet baru (kosongkan jika tidak diubah): ")
            jabatan = input("Masukkan jabatan baru (kosongkan jika tidak diubah): ")
            gaji_perjam = input("Masukkan gaji per jam baru (kosongkan jika tidak diubah): ")
            
            update_query = "UPDATE karyawan SET "
            update_params = []
            if nama:
                update_query += "nama = %s, "
                update_params.append(nama)
            if no_telepon:
                update_query += "no_telepon = %s, "
                update_params.append(no_telepon)
            if alamat:
                update_query += "alamat = %s, "
                update_params.append(alamat)
            if id_outlet:
                update_query += "id_outlet = %s, "
                update_params.append(id_outlet)
            if jabatan:
                update_query += "jabatan = %s, "
                update_params.append(jabatan)
            if gaji_perjam:
                update_query += "gaji_perjam = %s, "
                update_params.append(float(gaji_perjam))
            
            if update_params:
                update_query = update_query.rstrip(", ") + " WHERE id_karyawan = %s"
                update_params.append(id_karyawan)
                query.execute(update_query, update_params)
                conn.commit()
                print(f"Karyawan ID {id_karyawan} berhasil diupdate.")
            else:
                print("Tidak ada perubahan dilakukan.")
        
        elif choice == '2':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def Rekap_absensi():
    conn = connection()
    query = conn.cursor()
    
    start_date = input("Masukkan tanggal mulai (YYYY-MM-DD, kosongkan untuk default): ") or '2000-01-01'
    end_date = input("Masukkan tanggal akhir (YYYY-MM-DD, kosongkan untuk hari ini): ") or datetime.now().strftime('%Y-%m-%d')
    
    query.execute("""
        SELECT k.id_karyawan, k.nama, p.tanggal, p.jam_masuk, p.jam_keluar, 
               k.gaji_perjam, 
               (EXTRACT(EPOCH FROM (p.jam_keluar - p.jam_masuk)) / 3600 * k.gaji_perjam) as gaji
        FROM presensi p
        JOIN karyawan k ON p.id_karyawan = k.id_karyawan
        WHERE p.tanggal BETWEEN %s AND %s
        ORDER BY p.tanggal
    """, (start_date, end_date))
    presensi = query.fetchall()
    
    table_data = [[p[0], p[1], p[2], p[3], p[4], f"Rp {p[5]:,.2f}", f"Rp {p[6]:,.2f}"] for p in presensi]
    print(tabulate(table_data, headers=["ID", "Nama", "Tanggal", "Masuk", "Keluar", "Gaji/Jam", "Total Gaji"], 
                  tablefmt="pretty"))
    
    query.execute("""
        SELECT SUM(EXTRACT(EPOCH FROM (p.jam_keluar - p.jam_masuk)) / 3600 * k.gaji_perjam) as total_gaji
        FROM presensi p
        JOIN karyawan k ON p.id_karyawan = k.id_karyawan
        WHERE p.tanggal BETWEEN %s AND %s
    """, (start_date, end_date))
    total_gaji = query.fetchone()[0] or 0
    print(f"\nTotal Gaji (Periode {start_date} s/d {end_date}): Rp {total_gaji:,.2f}")
    
    query.close()
    conn.close()

def Laporan_Penjualan():
    conn = connection()
    query = conn.cursor()
    
    start_date = input("Masukkan tanggal mulai (YYYY-MM-DD, kosongkan untuk default): ") or '2000-01-01'
    end_date = input("Masukkan tanggal akhir (YYYY-MM-DD, kosongkan untuk hari ini): ") or datetime.now().strftime('%Y-%m-%d')
    
    query.execute("""
        SELECT t.id_transaksi, o.nama as outlet, p.nama as produk, t.jumlah, t.total_harga, t.tanggal_transaksi
        FROM transaksi_penjualan t
        JOIN outlets o ON t.id_outlet = o.id_outlet
        JOIN produk p ON t.id_produk = p.id_produk
        WHERE t.tanggal_transaksi BETWEEN %s AND %s
        ORDER BY t.tanggal_transaksi
    """, (start_date, end_date))
    transaksi = query.fetchall()
    
    table_data = [[t[0], t[1], t[2], t[3], f"Rp {t[4]:,.2f}", t[5]] for t in transaksi]
    print(tabulate(table_data, headers=["ID", "Outlet", "Produk", "Jumlah", "Total", "Tanggal"], 
                  tablefmt="pretty"))
    
    query.execute("SELECT SUM(total_harga) FROM transaksi_penjualan WHERE tanggal_transaksi BETWEEN %s AND %s", 
                 (start_date, end_date))
    total_pendapatan = query.fetchone()[0] or 0
    print(f"\nTotal Pendapatan (Periode {start_date} s/d {end_date}): Rp {total_pendapatan:,.2f}")
    
    query.close()
    conn.close()

def Laporan_Pembelian():
    conn = connection()
    query = conn.cursor()
    
    start_date = input("Masukkan tanggal mulai (YYYY-MM-DD, kosongkan untuk default): ") or '2000-01-01'
    end_date = input("Masukkan tanggal akhir (YYYY-MM-DD, kosongkan untuk hari ini): ") or datetime.now().strftime('%Y-%m-%d')
    
    query.execute("""
        SELECT t.id_pembelian, b.nama, t.jumlah, t.total_biaya, t.tanggal_pembelian
        FROM transaksi_pembelian t
        JOIN bahan_baku b ON t.id_bahan = b.id_bahan
        WHERE t.tanggal_pembelian BETWEEN %s AND %s
        ORDER BY t.tanggal_pembelian
    """, (start_date, end_date))
    pembelian = query.fetchall()
    
    table_data = [[p[0], p[1], p[2], f"Rp {p[3]:,.2f}", p[4]] for p in pembelian]
    print(tabulate(table_data, headers=["ID", "Bahan Baku", "Jumlah", "Total Biaya", "Tanggal"], 
                  tablefmt="pretty"))
    
    query.execute("SELECT SUM(total_biaya) FROM transaksi_pembelian WHERE tanggal_pembelian BETWEEN %s AND %s", 
                 (start_date, end_date))
    total_biaya = query.fetchone()[0] or 0
    print(f"\nTotal Pengeluaran (Periode {start_date} s/d {end_date}): Rp {total_biaya:,.2f}")
    
    query.close()
    conn.close()

def Rekap_Keuangan():
    conn = connection()
    query = conn.cursor()
    
    start_date = input("Masukkan tanggal mulai (YYYY-MM-DD, kosongkan untuk default): ") or '2000-01-01'
    end_date = input("Masukkan tanggal akhir (YYYY-MM-DD, kosongkan untuk hari ini): ") or datetime.now().strftime('%Y-%m-%d')
    
    query.execute("""
        SELECT o.nama, r.jenis, r.jumlah, r.deskripsi, r.tanggal
        FROM rekapitulasi_keuangan r
        JOIN outlets o ON r.id_outlet = o.id_outlet
        WHERE r.tanggal BETWEEN %s AND %s
        ORDER BY r.tanggal
    """, (start_date, end_date))
    rekap = query.fetchall()
    
    table_data = [[r[0], r[1], f"Rp {r[2]:,.2f}", r[3], r[4]] for r in rekap]
    print(tabulate(table_data, headers=["Outlet", "Jenis", "Jumlah", "Deskripsi", "Tanggal"], 
                  tablefmt="pretty"))
    
    query.execute("""
        SELECT SUM(jumlah) 
        FROM rekapitulasi_keuangan 
        WHERE tanggal BETWEEN %s AND %s AND jenis = 'penjualan'
    """, (start_date, end_date))
    total_pendapatan = query.fetchone()[0] or 0
    
    query.execute("""
        SELECT SUM(jumlah) 
        FROM rekapitulasi_keuangan 
        WHERE tanggal BETWEEN %s AND %s AND jenis != 'penjualan'
    """, (start_date, end_date))
    total_pengeluaran = query.fetchone()[0] or 0
    
    print(f"\nTotal Pendapatan (Periode {start_date} s/d {end_date}): Rp {total_pendapatan:,.2f}")
    print(f"Total Pengeluaran (Periode {start_date} s/d {end_date}): Rp {total_pengeluaran:,.2f}")
    print(f"Saldo: Rp {(total_pendapatan - total_pengeluaran):,.2f}")
    
    query.close()
    conn.close()

def Pengajuan():
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Ajuan Karyawan ===".center(50))
        query.execute("""
            SELECT p.id_pengajuan, k.nama, o.nama, p.jenis, 
                   COALESCE(pr.nama, b.nama) as item_nama, 
                   p.jumlah, p.tanggal_pengajuan, p.status, p.catatan
            FROM pengajuan_karyawan p
            JOIN karyawan k ON p.id_karyawan = k.id_karyawan
            JOIN outlets o ON p.id_outlet = o.id_outlet
            LEFT JOIN produk pr ON p.id_item = pr.id_produk AND p.jenis = 'produk'
            LEFT JOIN bahan_baku b ON p.id_item = b.id_bahan AND p.jenis = 'bahan'
        """)
        pengajuan = query.fetchall()
        
        table_data = [[p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8] or ''] for p in pengajuan]
        print(tabulate(table_data, headers=["ID", "Karyawan", "Outlet", "Jenis", "Item", "Jumlah", 
                                           "Tanggal", "Status", "Catatan"], tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Setujui ajuan")
        print("2. Tolak ajuan")
        print("3. Kembali")
        choice = input("Masukkan pilihan (1-3)\t: ")
        
        if choice == '1':
            id_pengajuan = input("Masukkan ID ajuan: ")
            query.execute("SELECT jenis, id_item, jumlah FROM pengajuan_karyawan WHERE id_pengajuan = %s", 
                         (id_pengajuan,))
            pengajuan_data = query.fetchone()
            if pengajuan_data:
                jenis, id_item, jumlah = pengajuan_data
                if jenis == 'produk':
                    query.execute("SELECT id_bahan, jumlah FROM resep WHERE id_produk = %s", 
                                 (id_item,))
                    bahan = query.fetchall()
                    can_produce = True
                    for bahan_item in bahan:
                        query.execute("SELECT stok FROM bahan_baku WHERE id_bahan = %s", (bahan_item[0],))
                        bahan_stok = query.fetchone()[0]
                        if bahan_stok < bahan_item[1] * jumlah:
                            can_produce = False
                            print(f"Stok bahan baku ID {bahan_item[0]} tidak cukup!")
                            break
                    
                    if can_produce:
                        query.execute("UPDATE produk SET stok = stok + %s WHERE id_produk = %s", 
                                     (jumlah, id_item))
                        for bahan_item in bahan:
                            query.execute("UPDATE bahan_baku SET stok = stok - %s WHERE id_bahan = %s", 
                                         (bahan_item[1] * jumlah, bahan_item[0]))
                        query.execute("UPDATE pengajuan_karyawan SET status = 'disetujui' WHERE id_pengajuan = %s", 
                                     (id_pengajuan,))
                        conn.commit()
                        print(f"Ajuan ID {id_pengajuan} disetujui.")
                else:  # bahan
                    query.execute("SELECT harga_unit FROM bahan_baku WHERE id_bahan = %s", (id_item,))
                    harga = query.fetchone()[0]
                    total_biaya = harga * jumlah
                    query.execute("UPDATE bahan_baku SET stok = stok + %s WHERE id_bahan = %s", 
                                 (jumlah, id_item))
                    query.execute("""
                        INSERT INTO transaksi_pembelian (id_bahan, jumlah, total_biaya, tanggal_pembelian)
                        VALUES (%s, %s, %s, NOW())
                    """, (id_item, jumlah, total_biaya))
                    query.execute("UPDATE outlets SET pengeluaran = pengeluaran + %s WHERE id_outlet = 1", (total_biaya,))
                    query.execute("""
                        INSERT INTO rekapitulasi_keuangan (id_outlet, jenis, jumlah, deskripsi, tanggal)
                        VALUES (1, 'pembelian_bahan', %s, %s, NOW())
                    """, (total_biaya, f"Pembelian bahan baku ID {id_item} dari ajuan karyawan"))
                    query.execute("UPDATE pengajuan_karyawan SET status = 'disetujui' WHERE id_pengajuan = %s", 
                                 (id_pengajuan,))
                    conn.commit()
                    print(f"Ajuan ID {id_pengajuan} disetujui.")
        
        elif choice == '2':
            id_pengajuan = input("Masukkan ID ajuan: ")
            query.execute("UPDATE pengajuan_karyawan SET status = 'ditolak' WHERE id_pengajuan = %s", 
                         (id_pengajuan,))
            conn.commit()
            print(f"Ajuan ID {id_pengajuan} ditolak.")
        
        elif choice == '3':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def dashboard_karyawan(id_user):
    conn = connection()
    query = conn.cursor()
    query.execute("""
        SELECT k.nama, k.jabatan, o.nama as outlet_nama
        FROM karyawan k
        JOIN outlets o ON k.id_outlet = o.id_outlet
        WHERE k.id_user = %s
    """, (id_user,))
    karyawan = query.fetchone()
    
    start_date = input("Masukkan tanggal (YYYY-MM-DD, kosongkan untuk default): ") or '2000-01-01'
    end_date = input("Masukkan tanggal akhir (YYYY-MM-DD, kosongkan untuk hari ini): ") or datetime.now().strftime('%Y-%m-%d')
    
    query.execute("""
        SELECT SUM(gaji_perjam * EXTRACT(EPOCH FROM (p.jam_keluar - p.jam_masuk)) / 3600) as total_gaji
        FROM presensi p
        JOIN karyawan k ON p.id_karyawan = k.id_karyawan
        WHERE k.id_karyawan = (SELECT id_karyawan FROM karyawan WHERE id_user = %s)
        AND tanggal BETWEEN %s AND %s
    """, (id_user, start_date, end_date))
    total_gaji = query.fetchone()[0] or 0
    
    print("\n=== Dashboard Karyawan ===".center(50))
    data = [
        ["Nama", karyawan[0]],
        ["Jabatan", karyawan[1]],
        ["Outlet", karyawan[2]],
        ["Total Gaji", f"Rp {total_gaji:,.2f}"]
    ]
    print(tabulate(data, headers=["Metrik", "Nilai"], tablefmt="pretty"))
    
    query.close()
    conn.close()

def Presensi(id_user):
    conn = connection()
    if not conn:
        return
    
    try:
        query = conn.cursor()
        
        tanggal = input("Masukkan tanggal (YYYY-MM-DD): ")
        try:
            datetime.strptime(tanggal, "%Y-%m-%d")
        except ValueError:
            print("Format tanggal tidak valid! Gunakan YYYY-MM-DD.")
            return
        
        jam_masuk = input("Masukkan jam masuk (HH:MM): ")
        try:
            datetime.strptime(jam_masuk, "%H:%M")
            jam_masuk_time = f"{tanggal} {jam_masuk}:00"  
        except ValueError:
            print("Format jam masuk tidak valid! Gunakan HH:MM.")
            return
        
        jam_keluar = input("Masukkan jam keluar (HH:MM:SS, kosongkan jika belum keluar): ")
        jam_keluar_time = None
        if jam_keluar:
            try:
                datetime.strptime(jam_keluar, "%H:%M")
                jam_keluar_time = f"{tanggal} {jam_keluar}:00" 
            except ValueError:
                print("Format jam keluar tidak valid! Gunakan format HH:MM:SS.")
                return
        
        query.execute("SELECT id_karyawan FROM karyawan WHERE id_user = %s", (id_user,))
        id_karyawan = query.fetchone()
        if not id_karyawan:
            print("Error: Karyawan tidak ditemukan!")
            return
        id_karyawan = id_karyawan[0]
        
        query.execute("""
            INSERT INTO presensi (id_karyawan, tanggal, jam_masuk, jam_keluar)
            VALUES (%s, %s, %s, %s)
        """, (id_karyawan, tanggal, jam_masuk_time, jam_keluar_time))
        conn.commit()
        print("Presensi telah berhasil dicatat.")
        
    except psycopg2.Error as e:
        print(f"Query error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        query.close()
        conn.close()

def Lihat_Produk(id_user):
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Lihat Produk ===".center(50))
        query.execute("""
            SELECT p.id_produk, p.nama, p.jenis, p.stok, 
                   STRING_AGG(b.nama || ': ' || r.jumlah::TEXT || ' unit', ', ') as bahan_baku
            FROM produk p 
            LEFT JOIN resep r ON p.id_produk = r.id_produk
            LEFT JOIN bahan_baku b ON r.id_bahan = b.id_bahan
            GROUP BY p.id_produk
        """)
        produk = query.fetchall()
        
        table_data = [[p[0], p[1], p[2], p[3], p[4] or ''] for p in produk]
        print(tabulate(table_data, headers=["ID", "Nama", "Jenis", "Stok", "Bahan Baku"], 
                       tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Ajukan penambahan stok produk")
        print("2. Kembali")
        choice = input("Masukkan pilihan (1-2): ")
        
        if choice == '1':
            id_produk = input("Masukkan ID produk: ")
            jumlah = int(input("Masukkan jumlah stok yang diajukan: "))
            catatan = input("Masukkan catatan (opsional): ")
            
            query.execute("SELECT id_karyawan, id_outlet FROM karyawan WHERE id_user = %s", (id_user,))
            karyawan = query.fetchone()
            query.execute("""
                INSERT INTO pengajuan_karyawan (id_karyawan, id_outlet, jenis, id_item, jumlah, tanggal_pengajuan, catatan)
                VALUES (%s, %s, 'produk', %s, %s, NOW(), %s)
            """, (karyawan[0], karyawan[1], id_produk, jumlah, catatan))
            conn.commit()
            print(f"Ajuan untuk produk ID {id_produk} sebanyak {jumlah} berhasil dikirim.")
        
        elif choice == '2':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def Lihat_Bahan_Baku(id_user):
    conn = connection()
    if not conn:
        return
    
    try:
        query = conn.cursor()
        while True:
            print("\n=== Lihat Bahan Baku ===".center(50))
            query.execute("SELECT id_bahan, nama, stok, harga_unit FROM bahan_baku")
            bahan = query.fetchall()
            
            table_data = [[b[0], b[1], b[2], f"Rp {b[3]:,.2f}"] for b in bahan]
            print(tabulate(table_data, headers=["ID", "Nama", "Stok", "Harga per Unit"], tablefmt="pretty"))
            
            print("\nPilih aksi:")
            print("1. Ajukan penambahan stok bahan baku")
            print("2. Kembali")
            choice = input("Masukkan pilihan (1-2): ")
            
            if choice == '1':
                id_bahan = input("Masukkan ID bahan baku: ")
                try:
                    id_bahan = int(id_bahan)
                except ValueError:
                    print("ID bahan baku harus berupa angka!")
                    continue
                
                jumlah = input("Masukkan jumlah stok yang diajukan: ")
                try:
                    jumlah = float(jumlah)
                    if jumlah <= 0:
                        print("Jumlah harus lebih dari 0!")
                        continue
                except ValueError:
                    print("Jumlah harus berupa angka!")
                    continue
                
                catatan = input("Masukkan catatan (opsional): ")
                
                query.execute("SELECT id_karyawan, id_outlet FROM karyawan WHERE id_user = %s", (id_user,))
                karyawan = query.fetchone()
                if not karyawan:
                    print("Data karyawan tidak ditemukan!")
                    continue
                
                query.execute("SELECT id_bahan FROM bahan_baku WHERE id_bahan = %s", (id_bahan,))
                if not query.fetchone():
                    print(f"Bahan baku dengan ID {id_bahan} tidak ditemukan!")
                    continue
                
                query.execute("""
                    INSERT INTO pengajuan_karyawan (id_karyawan, id_outlet, jenis, id_item, jumlah, tanggal_pengajuan, catatan)
                    VALUES (%s, %s, 'bahan', %s, %s, NOW(), %s)
                """, (karyawan[0], karyawan[1], id_bahan, jumlah, catatan))
                conn.commit()
                print(f"Ajuan untuk bahan baku ID {id_bahan} sebanyak {jumlah} berhasil dikirim.")
            
            elif choice == '2':
                break
            else:
                print("Pilihan tidak valid!")
    except psycopg2.Error as e:
        print(f"Error query: {e}")
    finally:
        query.close()
        conn.close()

def Jaga_Kasir(id_user):
    conn = connection()
    query = conn.cursor()
    
    while True:
        print("\n=== Jaga Kasir ===".center(50))
        query.execute("""
            SELECT p.id_produk, p.nama, p.stok, k.harga
            FROM katalog k
            JOIN produk p ON k.id_produk = p.id_produk
            WHERE p.stok > 0
        """)
        katalog = query.fetchall()
        
        table_data = [[k[0], k[1], k[2], f"Rp {k[3]:,.2f}"] for k in katalog]
        print(tabulate(table_data, headers=["ID", "Nama", "Stok", "Harga"], tablefmt="pretty"))
        
        print("\nPilih aksi:")
        print("1. Tambah transaksi")
        print("2. Kembali")
        choice = input("Masukkan pilihan (1-2)\t: ")
        
        if choice == '1':
            id_produk = input("Masukkan ID produk: ")
            jumlah = int(input("Masukkan jumlah yang dibeli: "))
            
            query.execute("SELECT harga FROM katalog WHERE id_produk = %s", (id_produk,))
            harga = query.fetchone()[0]
            total_harga = harga * jumlah
            
            query.execute("SELECT id_outlet, id_karyawan FROM karyawan WHERE id_user = %s", (id_user,))
            karyawan = query.fetchone()
            id_outlet, id_karyawan = karyawan[0], karyawan[1]
            
            query.execute("""
                INSERT INTO transaksi_penjualan (id_outlet, id_karyawan, id_produk, jumlah, total_harga, 
tanggal_transaksi)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (id_outlet, id_karyawan, id_produk, jumlah, total_harga))
            
            query.execute("UPDATE produk SET stok = stok - %s WHERE id_produk = %s", (jumlah, id_produk))
            
            query.execute("UPDATE outlets SET pendapatan = pendapatan + %s WHERE id_outlet = %s", (total_harga, 
id_outlet))
            
            query.execute("""
                INSERT INTO rekapitulasi_keuangan (id_outlet, jenis, jumlah, deskripsi, tanggal)
                VALUES (%s, 'penjualan', %s, %s, NOW())
            """, (id_outlet, total_harga, f"Penjualan produk ID {id_produk} sebanyak {jumlah}"))
            conn.commit()
            print(f"Transaksi berhasil! Total: Rp {total_harga:,.2f}")
        
        elif choice == '2':
            break
        else:
            print("Pilihan tidak valid!")
    
    query.close()
    conn.close()

def menu_karyawan(id_user):
    while True:
        print("\n=== Menu Karyawan ===".center(50))
        print("1. Dashboard")
        print("2. Presensi")
        print("3. Lihat Produk")
        print("4. Lihat Bahan Baku")
        print("5. Jaga Kasir")
        print("6. Keluar")
        choice = input("Masukkan pilihan (1-6)\t: ")
        
        if choice == '1':
            dashboard_karyawan(id_user)
        elif choice == '2':
            Presensi(id_user)
        elif choice == '3':
            Lihat_Produk(id_user)
        elif choice == '4':
            Lihat_Bahan_Baku(id_user)
        elif choice == '5':
            Jaga_Kasir(id_user)
        elif choice == '6':
            print("Keluar dari menu karyawan.")
            break
        else:
            print("Pilihan tidak valid!")


def main():
    while True:
        id_user, role = Login()
        if id_user:
            if role == 'owner':
                dashboard_owner(id_user)
            elif role == 'karyawan':
                menu_karyawan(id_user)
        else:
            print("Coba lagi, atau enter sekali lagi untuk berhenti")
            if input() == '':
                break

if __name__ == "__main__":
    main()