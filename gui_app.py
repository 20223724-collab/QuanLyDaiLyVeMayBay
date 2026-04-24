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
DB_NAME = 'quanly_ve_v12_airline_full.db'
# Danh sách hãng hàng không
AIRLINES = ["Vietnam Airlines", "VietJet Air", "Bamboo Airways", "Vietravel Airlines", "Pacific Airlines"]


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 1. Tạo bảng Chuyến bay (Thêm cột airline)
    cursor.execute('''CREATE TABLE IF NOT EXISTS flights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        airline TEXT,
                        code TEXT UNIQUE, destination TEXT, 
                        price REAL, seats INTEGER,
                        total_seats INTEGER,
                        booked_seats TEXT DEFAULT '',
                        departure_time TEXT)''')
    # 2. Tạo bảng Đặt vé
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_name TEXT, customer_phone TEXT,
                        flight_code TEXT, seat_number TEXT, price_at_booking REAL,
                        booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # 3. Tạo bảng Người dùng
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE, password TEXT, role TEXT)''')

    # Khởi tạo tài khoản mặc định
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '123', 'Admin'))
    cursor.execute("SELECT * FROM users WHERE username='staff'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('staff', '123', 'Staff'))

    # --- THÊM DỮ LIỆU MẪU CÓ HÃNG ---
    cursor.execute("SELECT COUNT(*) FROM flights")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now()
        sample_flights = [
            ('Vietnam Airlines', 'VN121', 'TP. Hồ Chí Minh (SGN)', 1250000, 48, 50, 'G1,G2',
             (now + datetime.timedelta(days=1)).strftime("%d/%m %H:%M")),
            ('Vietnam Airlines', 'VN234', 'Hà Nội (HAN)', 1500000, 50, 50, '',
             (now + datetime.timedelta(days=2)).strftime("%d/%m %H:%M")),
            ('VietJet Air', 'VJ456', 'Đà Nẵng (DAD)', 850000, 59, 60, 'G5',
             (now + datetime.timedelta(hours=5)).strftime("%d/%m %H:%M")),
            ('Bamboo Airways', 'QH789', 'Phú Quốc (PQC)', 2100000, 40, 40, '',
             (now + datetime.timedelta(days=3)).strftime("%d/%m %H:%M")),
            ('Vietnam Airlines', 'VN999', 'Đà Lạt (DLI)', 950000, 0, 30, '',
             (now + datetime.timedelta(days=1)).strftime("%d/%m %H:%M"))
        ]
        cursor.executemany(
            "INSERT INTO flights (airline, code, destination, price, seats, total_seats, booked_seats, departure_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            sample_flights)

    conn.commit()
    conn.close()


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
            messagebox.showerror("Lỗi", "Sai tài khoản!")


class FlightApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QUẢN LÝ VÉ MÁY BAY")
        self.geometry("1300x850")
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
        ctk.CTkLabel(self.sidebar, text=f"User: {self.current_user} | Quyền: {self.current_role}",
                     font=("Arial", 12, "italic")).pack(pady=(0, 20))

        ctk.CTkButton(self.sidebar, text="✈ CHUYẾN BAY", height=45, fg_color="#34495E",
                      command=lambda: self.show_frame("flights")).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="👤 KHÁCH HÀNG", height=45, fg_color="#34495E",
                      command=lambda: self.show_frame("customers")).pack(pady=5, padx=20, fill="x")

        if self.current_role == "Admin":
            ctk.CTkButton(self.sidebar, text="📊 THỐNG KÊ", height=45, fg_color="#34495E",
                          command=lambda: self.show_frame("stats")).pack(pady=5, padx=20, fill="x")

            # Form Admin mở rộng thêm cột Hãng
            self.admin_input_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            self.admin_input_frame.pack(pady=20, fill="x")

            self.opt_add_airline = ctk.CTkOptionMenu(self.admin_input_frame, values=AIRLINES)
            self.opt_add_airline.pack(pady=5, padx=20, fill="x")

            self.ent_code = ctk.CTkEntry(self.admin_input_frame, placeholder_text="Mã chuyến")
            self.ent_code.pack(pady=5, padx=20, fill="x")
            self.ent_dest = ctk.CTkEntry(self.admin_input_frame, placeholder_text="Điểm đến")
            self.ent_dest.pack(pady=5, padx=20, fill="x")
            self.ent_time = ctk.CTkEntry(self.admin_input_frame, placeholder_text="Ngày/Giờ")
            self.ent_time.pack(pady=5, padx=20, fill="x")
            self.ent_price = ctk.CTkEntry(self.admin_input_frame, placeholder_text="Giá vé")
            self.ent_price.pack(pady=5, padx=20, fill="x")
            self.ent_total = ctk.CTkEntry(self.admin_input_frame, placeholder_text="Tổng số ghế")
            self.ent_total.pack(pady=5, padx=20, fill="x")

            ctk.CTkButton(self.sidebar, text="THÊM CHUYẾN", fg_color="#27AE60", command=self.add_flight).pack(pady=10,
                                                                                                              padx=20,
                                                                                                              fill="x")

        ctk.CTkButton(self.sidebar, text="🚪 ĐĂNG XUẤT", fg_color="#C0392B", command=self.show_login).pack(side="bottom",
                                                                                                          pady=20,
                                                                                                          padx=20,
                                                                                                          fill="x")
        if self.current_role == "Admin":
            ctk.CTkButton(self.sidebar, text="💾 SAO LƯU", fg_color="#8E44AD", command=self.backup_data).pack(
                side="bottom", pady=5, padx=20, fill="x")

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
            self.frame_flights.pack(fill="both", expand=True);
            self.load_data()
        elif page == "customers":
            self.frame_customers.pack(fill="both", expand=True);
            self.load_customers()
        elif page == "stats":
            self.frame_stats.pack(fill="both", expand=True);
            self.update_stats()

    def setup_flight_view(self):
        filter_bar = ctk.CTkFrame(self.frame_flights, fg_color="#2C3E50", corner_radius=10)
        filter_bar.pack(fill="x", pady=(0, 15), ipady=5)

        self.ent_search = ctk.CTkEntry(filter_bar, placeholder_text="Mã hoặc Điểm đến...", width=250)
        self.ent_search.grid(row=0, column=0, padx=10, pady=10)

        # Lọc theo hãng
        ctk.CTkLabel(filter_bar, text="Hãng:").grid(row=0, column=1, padx=2)
        self.opt_filter_airline = ctk.CTkOptionMenu(filter_bar, values=["Tất cả hãng"] + AIRLINES, width=130)
        self.opt_filter_airline.grid(row=0, column=2, padx=10)

        ctk.CTkLabel(filter_bar, text="Giá:").grid(row=0, column=3, padx=2)
        self.opt_price = ctk.CTkOptionMenu(filter_bar,
                                           values=["Tất cả giá", "Dưới 1 triệu", "1 - 2 triệu", "Trên 2 triệu"],
                                           width=130)
        self.opt_price.grid(row=0, column=4, padx=10)

        ctk.CTkButton(filter_bar, text="LỌC DỮ LIỆU", width=100, fg_color="#3498DB", command=self.load_data).grid(row=0,
                                                                                                                  column=5,
                                                                                                                  padx=15)

        # Thêm cột "Hãng" (Airline) vào Treeview
        self.tree = ttk.Treeview(self.frame_flights,
                                 columns=("ID", "Airline", "Code", "Dest", "Time", "Price", "Seats", "Total"),
                                 show='headings')
        cols = {"ID": 40, "Airline": 130, "Code": 80, "Dest": 180, "Time": 120, "Price": 100, "Seats": 70, "Total": 70}
        for c, w in cols.items():
            self.tree.heading(c, text=c);
            self.tree.column(c, width=w, anchor="center")

        self.tree.tag_configure('warning', foreground='#FF4444', font=('Arial', 10, 'bold'))
        self.tree.pack(fill="both", expand=True)

        bf = ctk.CTkFrame(self.frame_flights, fg_color="transparent");
        bf.pack(fill="x", pady=20)
        ctk.CTkButton(bf, text="ĐẶT VÉ", fg_color="#E67E22", height=50, font=("Arial", 14, "bold"),
                      command=self.open_booking).pack(side="left", expand=True, padx=10)
        if self.current_role == "Admin":
            ctk.CTkButton(bf, text="XÓA CHUYẾN", fg_color="#C0392B", height=50, font=("Arial", 14, "bold"),
                          command=self.delete_flight).pack(side="left", expand=True, padx=10)

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.ent_search.get()
        a_filter = self.opt_filter_airline.get()
        p_filter = self.opt_price.get()

        query = "SELECT id, airline, code, destination, departure_time, price, seats, total_seats FROM flights WHERE (code LIKE ? OR destination LIKE ?)"
        params = ['%' + q + '%', '%' + q + '%']

        if a_filter != "Tất cả hãng":
            query += " AND airline = ?"
            params.append(a_filter)

        if p_filter == "Dưới 1 triệu":
            query += " AND price < 1000000"
        elif p_filter == "1 - 2 triệu":
            query += " AND price BETWEEN 1000000 AND 2000000"
        elif p_filter == "Trên 2 triệu":
            query += " AND price > 2000000"

        conn = sqlite3.connect(DB_NAME);
        c = conn.cursor();
        c.execute(query, params)
        for r in c.fetchall():
            tag = 'warning' if 0 < r[6] < 5 else ''
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], f"{r[5]:,.0f}", r[6], r[7]), tags=(tag,))
        conn.close()

    def add_flight(self):
        try:
            conn = sqlite3.connect(DB_NAME);
            c = conn.cursor()
            c.execute(
                "INSERT INTO flights (airline, code, destination, price, seats, total_seats, departure_time) VALUES (?,?,?,?,?,?,?)",
                (self.opt_add_airline.get(), self.ent_code.get().upper(), self.ent_dest.get(),
                 float(self.ent_price.get()), int(self.ent_total.get()), int(self.ent_total.get()),
                 self.ent_time.get()))
            conn.commit();
            conn.close();
            self.load_data()
            messagebox.showinfo("Thành công", f"Đã thêm chuyến bay của {self.opt_add_airline.get()}!");
            [e.delete(0, 'end') for e in [self.ent_code, self.ent_dest, self.ent_time, self.ent_price, self.ent_total]]
        except Exception as e:
            messagebox.showerror("Lỗi", f"Dữ liệu không hợp lệ: {e}")

    def open_booking(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Chú ý", "Hãy chọn một chuyến bay!")
            return
        f_data = self.tree.item(sel)['values']  # Index: 0=ID, 1=Airline, 2=Code

        conn = sqlite3.connect(DB_NAME);
        c = conn.cursor()
        c.execute("SELECT seats, total_seats, booked_seats, price FROM flights WHERE id=?", (f_data[0],))
        res = c.fetchone();
        conn.close()

        if res[0] <= 0:
            messagebox.showerror("Lỗi", "Chuyến bay đã hết chỗ!");
            return

        booked_list = res[2].split(',') if res[2] else []
        available_seats = [f"G{i}" for i in range(1, res[1] + 1) if f"G{i}" not in booked_list]

        pop = ctk.CTkToplevel(self);
        pop.title("Đặt vé & Chọn ghế");
        pop.geometry("400x450");
        pop.attributes("-topmost", True)
        ctk.CTkLabel(pop, text=f"HÃNG: {f_data[1]}\nMÃ: {f_data[2]}", font=("Arial", 14, "bold")).pack(pady=10)
        en = ctk.CTkEntry(pop, placeholder_text="Tên khách hàng", width=300);
        en.pack(pady=10)
        ep = ctk.CTkEntry(pop, placeholder_text="Số điện thoại", width=300);
        ep.pack(pady=10)

        ctk.CTkLabel(pop, text="Chọn ghế:").pack(pady=(10, 0))
        seat_var = ctk.StringVar(value=available_seats[0])
        ctk.CTkOptionMenu(pop, values=available_seats, variable=seat_var, width=300).pack(pady=10)

        def confirm():
            if not en.get() or not ep.get():
                messagebox.showwarning("Lỗi", "Vui lòng nhập đủ thông tin!");
                return
            conn = sqlite3.connect(DB_NAME);
            c = conn.cursor()
            new_booked = (res[2] + "," + seat_var.get()).strip(',')
            c.execute("UPDATE flights SET seats = seats - 1, booked_seats = ? WHERE id=?", (new_booked, f_data[0]))
            c.execute(
                "INSERT INTO bookings (customer_name, customer_phone, flight_code, seat_number, price_at_booking) VALUES (?,?,?,?,?)",
                (en.get(), ep.get(), f_data[2], seat_var.get(), res[3]))
            conn.commit();
            conn.close();
            self.load_data();
            pop.destroy()
            messagebox.showinfo("Thành công", f"Đặt vé thành công! Ghế: {seat_var.get()}")

        ctk.CTkButton(pop, text="XÁC NHẬN ĐẶT VÉ", fg_color="#E67E22", command=confirm).pack(pady=20)

    # --- CÁC HÀM KHÁC GIỮ NGUYÊN TỪ V11 ---
    def setup_customer_view(self):
        ctk.CTkLabel(self.frame_customers, text="DANH SÁCH KHÁCH HÀNG", font=("Arial", 20, "bold")).pack(pady=10)
        self.tree_cust = ttk.Treeview(self.frame_customers, columns=("ID", "Name", "Phone", "Flight", "Seat", "Date"),
                                      show='headings')
        for c in ("ID", "Name", "Phone", "Flight", "Seat", "Date"):
            self.tree_cust.heading(c, text=c);
            self.tree_cust.column(c, anchor="center")
        self.tree_cust.pack(fill="both", expand=True, pady=10)
        ctk.CTkButton(self.frame_customers, text="❌ HỦY VÉ", fg_color="#C0392B", command=self.cancel_booking).pack(
            pady=10)

    def load_customers(self):
        for r in self.tree_cust.get_children(): self.tree_cust.delete(r)
        conn = sqlite3.connect(DB_NAME);
        c = conn.cursor()
        c.execute("SELECT id, customer_name, customer_phone, flight_code, seat_number, booking_date FROM bookings")
        for r in c.fetchall(): self.tree_cust.insert("", "end", values=r)
        conn.close()

    def cancel_booking(self):
        sel = self.tree_cust.selection()
        if not sel: return
        data = self.tree_cust.item(sel)['values']
        if messagebox.askyesno("Xác nhận", f"Hủy vé khách {data[1]}?"):
            conn = sqlite3.connect(DB_NAME);
            c = conn.cursor()
            c.execute("SELECT booked_seats FROM flights WHERE code=?", (data[3],))
            booked_str = c.fetchone()[0]
            booked_list = booked_str.split(',')
            if str(data[4]) in booked_list: booked_list.remove(str(data[4]))
            new_booked_str = ",".join(booked_list).strip(',')
            c.execute("DELETE FROM bookings WHERE id=?", (data[0],))
            c.execute("UPDATE flights SET seats = seats + 1, booked_seats = ? WHERE code=?", (new_booked_str, data[3]))
            conn.commit();
            conn.close();
            self.load_customers();
            self.load_data()

    def setup_stats_view(self):
        card = ctk.CTkFrame(self.frame_stats, fg_color="#1E272E", border_width=2, border_color="#27AE60")
        card.pack(fill="x", padx=40, pady=20)
        self.lbl_total_rev = ctk.CTkLabel(card, text="0 VNĐ", font=("Arial", 32, "bold"), text_color="#2ecc71")
        self.lbl_total_rev.pack(pady=20)
        self.tree_stats = ttk.Treeview(self.frame_stats, columns=("Code", "Sold", "Rev"), show='headings')
        for c in ("Code", "Sold", "Rev"): self.tree_stats.heading(c, text=c); self.tree_stats.column(c, anchor="center")
        self.tree_stats.pack(fill="both", expand=True, padx=40)
        ctk.CTkButton(self.frame_stats, text="📊 XUẤT CSV", command=self.export_to_csv).pack(pady=20)

    def update_stats(self):
        conn = sqlite3.connect(DB_NAME);
        c = conn.cursor()
        c.execute("SELECT SUM(price_at_booking) FROM bookings");
        self.lbl_total_rev.configure(text=f"{c.fetchone()[0] or 0:,.0f} VNĐ")
        for r in self.tree_stats.get_children(): self.tree_stats.delete(r)
        c.execute("SELECT flight_code, COUNT(*), SUM(price_at_booking) FROM bookings GROUP BY flight_code")
        for r in c.fetchall(): self.tree_stats.insert("", "end", values=(r[0], r[1], f"{r[2]:,.0f}"))
        conn.close()

    def export_to_csv(self):
        if not os.path.exists('Reports'): os.makedirs('Reports')
        path = f"Reports/BaoCao_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Flight', 'Sold', 'Revenue'])
            for row in self.tree_stats.get_children(): writer.writerow(self.tree_stats.item(row)['values'])
        messagebox.showinfo("Thành công", f"Đã lưu tại {path}")

    def delete_flight(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Xác nhận", "Xóa chuyến này?"):
            conn = sqlite3.connect(DB_NAME);
            c = conn.cursor()
            c.execute("DELETE FROM flights WHERE id=?", (self.tree.item(sel)['values'][0],))
            conn.commit();
            conn.close();
            self.load_data()

    def backup_data(self):
        if not os.path.exists('Backups'): os.makedirs('Backups')
        shutil.copy2(DB_NAME, f"Backups/backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        messagebox.showinfo("OK", "Đã sao lưu!")


if __name__ == "__main__":
    init_db()
    app = FlightApp()
    app.mainloop()