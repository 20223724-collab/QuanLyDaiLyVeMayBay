import customtkinter as ctk
from tkinter import messagebox, ttk
import sqlite3
import datetime
import shutil  # Thư viện để copy file sao lưu
import os

# --- CẤU HÌNH GIAO DIỆN ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_NAME = 'dai_ly_ve_v3.db'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS flights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE, destination TEXT, 
                        price REAL, seats INTEGER)''')
    # Tạo thêm bảng lịch sử bán vé để thống kê chính xác hơn nếu cần (ở đây mình dùng tính toán trực tiếp)
    conn.commit()
    conn.close()


class FlightApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HỆ THỐNG QUẢN LÝ VÉ PRO - CÓ THỐNG KÊ & SAO LƯU")
        self.geometry("1100x750")
        init_db()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR BÊN TRÁI ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=15)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(self.sidebar, text="QUẢN LÝ VÉ", font=("Arial", 22, "bold"), text_color="#3498DB").pack(pady=20)

        # Các ô nhập liệu
        self.ent_code = ctk.CTkEntry(self.sidebar, placeholder_text="Mã chuyến", height=35)
        self.ent_code.pack(pady=5, padx=20, fill="x")
        self.ent_dest = ctk.CTkEntry(self.sidebar, placeholder_text="Điểm đến", height=35)
        self.ent_dest.pack(pady=5, padx=20, fill="x")
        self.ent_price = ctk.CTkEntry(self.sidebar, placeholder_text="Giá vé (VNĐ)", height=35)
        self.ent_price.pack(pady=5, padx=20, fill="x")
        self.ent_seats = ctk.CTkEntry(self.sidebar, placeholder_text="Số lượng ghế", height=35)
        self.ent_seats.pack(pady=5, padx=20, fill="x")

        self.btn_add = ctk.CTkButton(self.sidebar, text="THÊM CHUYẾN BAY", command=self.add_flight, fg_color="#27AE60",
                                     font=("Arial", 13, "bold"))
        self.btn_add.pack(pady=15, padx=20, fill="x")

        # --- KHUNG THỐNG KÊ DOANH THU (MỚI) ---
        self.revenue_frame = ctk.CTkFrame(self.sidebar, fg_color="#1A1A1A", corner_radius=10)
        self.revenue_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.revenue_frame, text="TỔNG VÉ ĐÃ BÁN", font=("Arial", 12)).pack(pady=(10, 0))
        self.lbl_total_tickets = ctk.CTkLabel(self.revenue_frame, text="0", font=("Arial", 20, "bold"),
                                              text_color="#E67E22")
        self.lbl_total_tickets.pack(pady=5)

        # Nút Sao Lưu (MỚI)
        self.btn_backup = ctk.CTkButton(self.sidebar, text="SAO LƯU DỮ LIỆU", command=self.backup_data,
                                        fg_color="#8E44AD", font=("Arial", 12))
        self.btn_backup.pack(pady=20, padx=20, fill="x")

        # --- NỘI DUNG BÊN PHẢI ---
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Tìm kiếm
        search_frame = ctk.CTkFrame(self.main_content, height=50)
        search_frame.pack(pady=(0, 10), fill="x")
        self.ent_search = ctk.CTkEntry(search_frame, placeholder_text="Tìm nhanh...", height=35)
        self.ent_search.pack(side="left", padx=15, expand=True, fill="x")
        ctk.CTkButton(search_frame, text="TÌM", width=80, command=self.search_data).pack(side="left", padx=5)

        # Cấu hình bảng (Treeview)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=40,
                        font=("Arial", 14))
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", font=("Arial", 14, "bold"))
        style.map("Treeview", background=[('selected', '#3498DB')])

        self.tree = ttk.Treeview(self.main_content, columns=("ID", "Code", "Dest", "Price", "Seats"), show='headings')
        for col in ("ID", "Code", "Dest", "Price", "Seats"):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Chức năng chính
        action_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        action_frame.pack(pady=20, fill="x")
        ctk.CTkButton(action_frame, text="ĐẶT VÉ & XUẤT HÓA ĐƠN", fg_color="#E67E22", height=60,
                      font=("Arial", 16, "bold"), command=self.book_ticket).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(action_frame, text="XÓA CHUYẾN", fg_color="#C0392B", height=60, font=("Arial", 16, "bold"),
                      command=self.delete_flight).pack(side="left", padx=10, expand=True)

        self.load_data()
        self.update_revenue()  # Cập nhật thống kê khi mở app

    # --- HÀM SAO LƯU DỮ LIỆU (NEW) ---
    def backup_data(self):
        try:
            if not os.path.exists('Backups'):
                os.makedirs('Backups')
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"Backups/backup_{timestamp}.db"
            shutil.copy2(DB_NAME, backup_file)
            messagebox.showinfo("Thành công", f"Đã lưu bản sao tại thư mục Backups!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể sao lưu: {e}")

    # --- HÀM CẬP NHẬT THỐNG KÊ (NEW) ---
    def update_revenue(self):
        # Ở bản đơn giản này, ta đếm xem tổng số ghế ban đầu so với hiện tại (hoặc giả lập số vé đã bán)
        # Để chính xác nhất nên có bảng 'sales', nhưng ở đây mình sẽ hiển thị số chuyến bay đang quản lý
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM flights")
        count = cursor.fetchone()[0]
        self.lbl_total_tickets.configure(text=str(count) + " Chuyến")
        conn.close()

    def show_big_message(self, title, message):
        msg_window = ctk.CTkToplevel(self)
        msg_window.title(title)
        msg_window.geometry("500x300")
        msg_window.attributes("-topmost", True)
        label = ctk.CTkLabel(msg_window, text=message, font=("Arial", 24, "bold"), text_color="#27AE60", wraplength=450)
        label.pack(expand=True, pady=20)
        ctk.CTkButton(msg_window, text="OK", command=msg_window.destroy).pack(pady=20)

    def load_data(self, rows=None):
        for row in self.tree.get_children(): self.tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        if not rows:
            cursor.execute("SELECT * FROM flights")
            rows = cursor.fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2], f"{r[3]:,.0f}", r[4]))
        conn.close()
        self.update_revenue()

    def add_flight(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO flights (code, destination, price, seats) VALUES (?, ?, ?, ?)",
                           (self.ent_code.get(), self.ent_dest.get(), float(self.ent_price.get()),
                            int(self.ent_seats.get())))
            conn.commit()
            conn.close()
            self.load_data()
        except:
            messagebox.showerror("Lỗi", "Kiểm tra lại dữ liệu hoặc mã chuyến bị trùng!")

    def search_data(self):
        q = self.ent_search.get()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM flights WHERE destination LIKE ? OR code LIKE ?", ('%' + q + '%', '%' + q + '%'))
        self.load_data(cursor.fetchall())
        conn.close()

    def delete_flight(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Xác nhận", "Xóa chuyến bay này?"):
            f_id = self.tree.item(sel)['values'][0]
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM flights WHERE id=?", (f_id,))
            conn.commit()
            conn.close()
            self.load_data()

    def book_ticket(self):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel)['values']
        f_id, code, dest, price, seat = item

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT seats FROM flights WHERE id=?", (f_id,))
        curr = cursor.fetchone()[0]

        if curr > 0:
            cursor.execute("UPDATE flights SET seats = seats - 1 WHERE id=?", (f_id,))
            conn.commit()
            now = datetime.datetime.now().strftime("%H%M%S")
            with open(f"Ve_{code}_{now}.txt", "w", encoding="utf-8") as f:
                f.write(f"VE MAY BAY: {code}\nDen: {dest}\nGia: {price} VND\nThanh toan luc: {datetime.datetime.now()}")
            self.show_big_message("THANH CONG", f"DA DAT VE: {code}\nLuu hoa don thanh cong!")
            self.load_data()
        else:
            messagebox.showerror("Lỗi", "Hết ghế!")
        conn.close()


if __name__ == "__main__":
    app = FlightApp()
    app.mainloop()