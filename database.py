import sqlite3
import os

# --- 1. KHỞI TẠO CƠ SỞ DỮ LIỆU ---
def init_db():
    conn = sqlite3.connect('dai_ly_ve.db')
    cursor = conn.cursor()
    # Bảng chuyến bay
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            destination TEXT,
            price REAL,
            seats INTEGER
        )
    ''')
    # Bảng khách hàng và đặt vé
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            flight_id INTEGER,
            booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flight_id) REFERENCES flights (id)
        )
    ''')
    conn.commit()
    conn.close()

# --- 2. CÁC HÀM NGHIỆP VỤ (BACKEND) ---

def add_flight(code, destination, price, seats):
    try:
        conn = sqlite3.connect('dai_ly_ve.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO flights (code, destination, price, seats) VALUES (?, ?, ?, ?)",
                       (code, destination, price, seats))
        conn.commit()
        print(f"✔️ Đã thêm chuyến bay {code}")
    except sqlite3.IntegrityError:
        print("❌ Lỗi: Mã chuyến bay này đã tồn tại!")
    finally:
        conn.close()

def show_flights():
    conn = sqlite3.connect('dai_ly_ve.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flights")
    rows = cursor.fetchall()
    print("\n--- DANH SÁCH CHUYẾN BAY ---")
    print(f"{'ID':<5} {'Mã':<10} {'Điểm đến':<15} {'Giá':<12} {'Ghế trống':<5}")
    for r in rows:
        print(f"{r[0]:<5} {r[1]:<10} {r[2]:<15} {r[3]:<12,.0f} {r[4]:<5}")
    conn.close()

def book_ticket(customer_name, flight_id):
    conn = sqlite3.connect('dai_ly_ve.db')
    cursor = conn.cursor()

    # Kiểm tra còn ghế không
    cursor.execute("SELECT seats FROM flights WHERE id = ?", (flight_id,))
    result = cursor.fetchone()

    if result and result[0] > 0:
        # Giảm số ghế
        cursor.execute("UPDATE flights SET seats = seats - 1 WHERE id = ?", (flight_id,))
        # Thêm bản ghi đặt vé
        cursor.execute("INSERT INTO bookings (customer_name, flight_id) VALUES (?, ?)",
                       (customer_name, flight_id))
        conn.commit()
        print(f"✅ Đặt vé thành công cho khách: {customer_name}!")
    else:
        print("❌ Hết ghế hoặc chuyến bay không tồn tại!")
    conn.close()

# --- 3. GIAO DIỆN ĐIỀU KHIỂN (CLI MENU) ---

def main():
    init_db()
    while True:
        print("\n=== HỆ THỐNG QUẢN LÝ ĐẠI LÝ VÉ MÁY BAY ===")
        print("1. Xem danh sách chuyến bay")
        print("2. Thêm chuyến bay mới")
        print("3. Đặt vé cho khách")
        print("4. Thoát")

        choice = input("Chọn chức năng (1-4): ")

        if choice == '1':
            show_flights()
        elif choice == '2':
            try:
                code = input("Nhập mã chuyến bay (VD: VJ01): ")
                dest = input("Nhập điểm đến: ")
                price = float(input("Nhập giá vé: "))
                seats = int(input("Nhập số lượng ghế: "))
                add_flight(code, dest, price, seats)
            except ValueError:
                print("❌ Lỗi: Giá vé và số ghế phải là số!")
        elif choice == '3':
            show_flights()
            try:
                f_id = int(input("Nhập ID chuyến bay khách chọn: "))
                name = input("Nhập tên khách hàng: ")
                book_ticket(name, f_id)
            except ValueError:
                print("❌ Lỗi: ID phải là con số!")
        elif choice == '4':
            print("Tạm biệt!")
            break
        else:
            print("Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()