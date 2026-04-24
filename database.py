import customtkinter as ctk
from tkinter import messagebox, ttk
import sqlite3
import datetime
import shutil
import os
import csv

# --- CẤU HÌNH HỆ THỐNG ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
DB_NAME = 'quanly_ve_v9_full.db'


# --- 1. KHỞI TẠO CƠ SỞ DỮ LIỆU ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS flights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE, destination TEXT, 
                        price REAL, seats INTEGER,
                        departure_time TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT, customer_phone TEXT,
                        flight_code TEXT, price_at_booking REAL,
                        booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE, password TEXT, role TEXT)''')

    # Tạo tài khoản mặc định nếu chưa có
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '123', 'Admin'))

    cursor.execute("SELECT * FROM users WHERE username='staff'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('staff', '123', 'Staff'))

    conn.commit()
    conn.close()


# --- 2. GIAO DIỆN ĐĂNG NHẬP ---
class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, login_callback):
        super().__init__(parent, fg_color="transparent")
        self.login_callback = login_callback

        ctk.CTkLabel(self, text="HỆ THỐNG ĐẠI LÝ VÉ", font=("Arial", 30, "bold"), text_color="#3498DB").pack(
            pady=(100, 20))

        self.ent_user = ctk.CTkEntry(self, placeholder_text="Tên đăng nhập", width=300, height=45)
        self.ent_user.pack(pady=10)

        self.ent_pass = ctk.CTkEntry(self, placeholder_text="Mật khẩu", width=300, height=45, show="*")
        self.ent_pass.pack(pady=10)

        ctk.CTkButton(self, text="ĐĂNG NHẬP", width=300, height=50, font=("Arial", 14, "bold"),
                      command=self.check_login).pack(pady=20)

    def check_login(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE username=? AND password=?",
                       (self.ent_user.get(), self.ent_pass.get()))
        user = cursor.fetchone()
        conn.close()
        if user:
            self.login_callback(user[0], user[1])
        else:
            messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu!")


# --- 3. GIAO DIỆN CHÍNH ---
class FlightApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QUẢN LÝ VÉ MÁY BAY v9.0 - FULL SYSTEM")
        self.geometry("1280x850")

        self.current_user = None
        self.current_role = None

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def show_login(self):
        for w in self.container.winfo_children(): w.destroy()
        LoginFrame(self.container, self.login_success).pack(fill="both", expand=True)

    def login_success(self, username, role):
        self.current_user, self.current_role = username, role
        self.show_main_ui()

    def show_main_ui(self):
        for w in self.container.winfo_children(): w.destroy()
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self.container, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="AIRLINE PRO", font=("Arial", 22, "bold"), text_color="#3498DB").pack(
            pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text=f"User: {self.current_user} | {self.current_role}",
                     font=("Arial", 12, "italic")).pack(pady=(0, 20))

        # Menu Buttons
        ctk.CTkButton(self.sidebar, text="✈ CHUYẾN BAY", height=45, fg_color="#34495E",
                      command=lambda: self.show_frame("flights")).pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(self.sidebar, text="👤 KHÁCH HÀNG", height=45, fg_color="#34495E",
                      command=lambda: self.show_frame("customers")).pack(pady=5, padx=20, fill="x")

        if self.current_role == "Admin":
            ctk.CTkButton(self.sidebar, text="📊 THỐNG KÊ", height=45, fg_color="#34495E",
                          command=lambda: self.show_frame("stats")).pack(pady=5, padx=20, fill="x")

            # Form thêm chuyến bay nhanh
            self.admin_form = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            self.admin_form.pack(pady=20, fill="x")
            self.ent_code = ctk.CTkEntry(self.admin_form, placeholder_text="Mã chuyến")
            self.ent_code.pack(pady=5, padx=20, fill="x")
            self.ent_dest = ctk.CTkEntry(self.admin_form, placeholder_text="Điểm đến")
            self.ent_dest.pack(pady=5, padx=20, fill="x")
            self.ent_time = ctk.CTkEntry(self.admin_form, placeholder_text="Ngày/Giờ")
            self.ent_time.pack(pady=5, padx=20, fill="x")
            self.ent_price = ctk.CTkEntry(self.admin_form, placeholder_text="Giá vé")
            self.ent_price.pack(pady=5, padx=20, fill="x")
            self.ent_seats = ctk.CTkEntry(self.admin_form, placeholder_text="Số ghế")
            self.ent_seats.pack(pady=5, padx=20, fill="x")

            ctk.CTkButton(self.sidebar, text="THÊM CHUYẾN", fg_color="#27AE60", command=self.add_flight).pack(pady=10,
                                                                                                              padx=20,
                                                                                                              fill="x")

        ctk.CTkButton(self.sidebar, text="🚪 ĐĂNG XUẤT", fg_color="#C0392B", command=self.show_login).pack(side="bottom",
                                                                                                          pady=20,
                                                                                                          padx=20,
                                                                                                          fill="x")

        # Main Pages
        self.main_content = ctk.CTkFrame(self.container, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.frame_flights = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.frame_customers = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.frame_stats = ctk.CTkFrame(self.main_content, fg_color="transparent")

        self.setup_flight_view()
        self.setup_customer_view()
        self.setup_stats_view()
        self.show_frame("flights")

    def show_frame(self, page):
        for f in [self.frame_flights, self.frame_customers, self.frame_stats]: f.pack_forget()
        if page == "flights":
            self.frame_flights.pack(fill="both", expand=True)
            self.load_data()
        elif page == "customers":
            self.frame_customers.pack(fill="both", expand=True)
            self.load_customers()
        elif page == "stats":
            self.frame_stats.pack(fill="both", expand=True)
            self.update_stats()

    # --- PHẦN 1: QUẢN LÝ CHUYẾN BAY ---
    def setup_flight_view(self):
        filter_bar = ctk.CTkFrame(self.frame_flights, fg_color="#2C3E50", corner_radius=10)
        filter_bar.pack(fill="x", pady=(0, 15), ipady=5)

        self.ent_search = ctk.CTkEntry(filter_bar, placeholder_text="Tìm mã chuyến hoặc nơi đến...", width=300)
        self.ent_search.grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkButton(filter_bar, text="TÌM KIẾM", command=self.load_data).grid(row=0, column=1, padx=10)

        self.tree = ttk.Treeview(self.frame_flights, columns=("ID", "Code", "Dest", "Time", "Price", "Seats"),
                                 show='headings')
        cols = {"ID": 50, "Code": 100, "Dest": 200, "Time": 150, "Price": 120, "Seats": 80}
        for c, w in cols.items():
            self.tree.heading(c, text=c);
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)

        btn_box = ctk.CTkFrame(self.frame_flights, fg_color="transparent")
        btn_box.pack(fill="x", pady=20)
        ctk.CTkButton(btn_box, text="ĐẶT VÉ MỚI", fg_color="#E67E22", height=50, command=self.open_booking).pack(
            side="left", expand=True, padx=10)
        if self.current_role == "Admin":
            ctk.CTkButton(btn_box, text="XÓA CHUYẾN", fg_color="#C0392B", height=50, command=self.delete_flight).pack(
                side="left", expand=True, padx=10)

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.ent_search.get()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM flights WHERE code LIKE ? OR destination LIKE ?", ('%' + q + '%', '%' + q + '%'))
        for r in c.fetchall():
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[5], f"{r[3]:,.0f}", r[4]))
        conn.close()

    def add_flight(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO flights (code, destination, price, seats, departure_time) VALUES (?,?,?,?,?)",
                      (self.ent_code.get().upper(), self.ent_dest.get(), float(self.ent_price.get()),
                       int(self.ent_seats.get()), self.ent_time.get()))
            conn.commit();
            conn.close()
            self.load_data()
            messagebox.showinfo("Thành công", "Đã thêm chuyến bay mới!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Dữ liệu không đúng: {e}")

    def open_booking(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Hãy chọn một chuyến bay!")
            return

        f_data = self.tree.item(sel)['values']
        pop = ctk.CTkToplevel(self)
        pop.title("Form Đặt Vé")
        pop.geometry("400x350")
        pop.attributes("-topmost", True)

        ctk.CTkLabel(pop, text=f"ĐẶT VÉ: {f_data[1]}", font=("Arial", 18, "bold")).pack(pady=20)
        en = ctk.CTkEntry(pop, placeholder_text="Tên khách hàng", width=300);
        en.pack(pady=10)
        ep = ctk.CTkEntry(pop, placeholder_text="Số điện thoại", width=300);
        ep.pack(pady=10)

        def confirm():
            if not en.get() or not ep.get(): return
            conn = sqlite3.connect(DB_NAME);
            c = conn.cursor()
            c.execute("SELECT seats, price FROM flights WHERE id=?", (f_data[0],))
            res = c.fetchone()
            if res and res[0] > 0:
                c.execute("UPDATE flights SET seats = seats - 1 WHERE id=?", (f_data[0],))
                c.execute(
                    "INSERT INTO bookings (customer_name, customer_phone, flight_code, price_at_booking) VALUES (?,?,?,?)",
                    (en.get(), ep.get(), f_data[1], res[1]))
                conn.commit();
                conn.close()
                self.load_data();
                pop.destroy()
                messagebox.showinfo("Thành công", "Đặt vé hoàn tất!")
            else:
                messagebox.showerror("Lỗi", "Đã hết ghế trống!");
                conn.close()

        ctk.CTkButton(pop, text="XÁC NHẬN ĐẶT VÉ", fg_color="#27AE60", command=confirm).pack(pady=20)

    # --- PHẦN 2: QUẢN LÝ KHÁCH HÀNG ---
    def setup_customer_view(self):
        ctk.CTkLabel(self.frame_customers, text="DANH SÁCH KHÁCH HÀNG ĐẶT VÉ", font=("Arial", 22, "bold"),
                     text_color="#3498DB").pack(pady=20)

        self.tree_cust = ttk.Treeview(self.frame_customers, columns=("ID", "Name", "Phone", "Flight", "Price", "Date"),
                                      show='headings')
        cols = {"ID": 50, "Name": 180, "Phone": 120, "Flight": 100, "Price": 120, "Date": 180}
        for c, w in cols.items():
            self.tree_cust.heading(c, text=c);
            self.tree_cust.column(c, width=w, anchor="center")
        self.tree_cust.pack(fill="both", expand=True, padx=20)

        btn_cust = ctk.CTkFrame(self.frame_customers, fg_color="transparent")
        btn_cust.pack(fill="x", pady=20)
        ctk.CTkButton(btn_cust, text="HỦY VÉ & HOÀN GHẾ", fg_color="#C0392B", command=self.cancel_booking).pack(
            side="left", expand=True, padx=20)

    def load_customers(self):
        for r in self.tree_cust.get_children(): self.tree_cust.delete(r)
        conn = sqlite3.connect(DB_NAME);
        c = conn.cursor()
        c.execute("SELECT id, customer_name, customer_phone, flight_code, price_at_booking, booking_date FROM bookings")
        for r in c.fetchall():
            self.tree_cust.insert("", "end", values=(r[0], r[1], r[2], r[3], f"{r[4]:,.0f}", r[5]))
        conn.close()

    def cancel_booking(self):
        sel = self.tree_cust.selection()
        if not sel: return
        data = self.tree_cust.item(sel)['values']
        if messagebox.askyesno("Xác nhận", f"Hủy vé của khách {data[1]}?"):
            conn = sqlite3.connect(DB_NAME);
            c = conn.cursor()
            c.execute("DELETE FROM bookings WHERE id=?", (data[0],))
            c.execute("UPDATE flights SET seats = seats + 1 WHERE code=?", (data[3],))
            conn.commit();
            conn.close()
            self.load_customers();
            self.load_data()
            messagebox.showinfo("Xong", "Đã hủy vé thành công!")

    # --- PHẦN 3: THỐNG KÊ ---
    def setup_stats_view(self):
        ctk.CTkLabel(self.frame_stats, text="BÁO CÁO DOANH THU", font=("Arial", 22, "bold"), text_color="#3498DB").pack(
            pady=20)
        self.lbl_total = ctk.CTkLabel(self.frame_stats, text="TỔNG: 0 VNĐ", font=("Arial", 30, "bold"),
                                      text_color="#27AE60")
        self.lbl_total.pack(pady=20)

        self.tree_stats = ttk.Treeview(self.frame_stats, columns=("Flight", "Tickets", "Revenue"), show='headings')
        for c in ("Flight", "Tickets", "Revenue"):
            self.tree_stats.heading(c, text=c);
            self.tree_stats.column(c, anchor="center")
        self.tree_stats.pack(fill="both", expand=True, padx=40)

        ctk.CTkButton(self.frame_stats, text="XUẤT BÁO CÁO CSV", command=self.export_csv).pack(pady=20)

    def update_stats(self):
        conn = sqlite3.connect(DB_NAME);
        c = conn.cursor()
        c.execute("SELECT SUM(price_at_booking) FROM bookings")
        total = c.fetchone()[0] or 0
        self.lbl_total.configure(text=f"TỔNG: {total:,.0f} VNĐ")

        for r in self.tree_stats.get_children(): self.tree_stats.delete(r)
        c.execute("SELECT flight_code, COUNT(*), SUM(price_at_booking) FROM bookings GROUP BY flight_code")
        for r in c.fetchall():
            self.tree_stats.insert("", "end", values=(r[0], r[1], f"{r[2]:,.0f}"))
        conn.close()

    def export_csv(self):
        if not os.path.exists('Reports'): os.makedirs('Reports')
        filename = f"Reports/BaoCao_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Chuyến bay', 'Số vé bán', 'Doanh thu'])
            for row in self.tree_stats.get_children():
                writer.writerow(self.tree_stats.item(row)['values'])
        messagebox.showinfo("Thành công", f"Đã xuất báo cáo tại: {filename}")

    def delete_flight(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Xác nhận", "Xóa chuyến bay này sẽ xóa toàn bộ dữ liệu liên quan?"):
            conn = sqlite3.connect(DB_NAME);
            c = conn.cursor()
            c.execute("DELETE FROM flights WHERE id=?", (self.tree.item(sel)['values'][0],))
            conn.commit();
            conn.close()
            self.load_data()


# --- CHƯƠNG TRÌNH CHÍNH ---
if __name__ == "__main__":
    init_db()
    app = FlightApp()
    app.mainloop()