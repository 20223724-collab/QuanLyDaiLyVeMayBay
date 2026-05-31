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

    # =========================
    # 1. BẢNG HÃNG BAY
    # =========================


    # Thêm hãng mẫu
    for airline in AIRLINES:
        cursor.execute(
            "INSERT OR IGNORE INTO airlines(name) VALUES(?)",
            (airline,)
        )

    # =========================
    # 2. BẢNG CHUYẾN BAY
    # =========================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        airline TEXT,
        code TEXT UNIQUE,
        destination TEXT,
        price REAL,
        seats INTEGER,
        total_seats INTEGER,
        booked_seats TEXT DEFAULT '',
        departure_time TEXT
    )
    ''')

    # =========================
    # 3. BẢNG ĐẶT VÉ
    # =========================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_phone TEXT,
        flight_code TEXT,
        seat_number TEXT,
        price_at_booking REAL,
        booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # =========================
    # 4. BẢNG USERS
    # =========================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS airlines(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        country TEXT,
        hotline TEXT,
        website TEXT
    )
    ''')
    # =========================
    # TÀI KHOẢN MẶC ĐỊNH
    # =========================
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', '123', 'Admin')
        )

    cursor.execute("SELECT * FROM users WHERE username='staff'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('staff', '123', 'Staff')
        )

    # =========================
    # DỮ LIỆU MẪU CHUYẾN BAY
    # =========================
    cursor.execute("SELECT COUNT(*) FROM flights")

    if cursor.fetchone()[0] == 0:

        now = datetime.datetime.now()

        sample_flights = [
            (
                'Vietnam Airlines',
                'VN121',
                'TP. Hồ Chí Minh (SGN)',
                1250000,
                48,
                50,
                'G1,G2',
                (now + datetime.timedelta(days=1)).strftime("%d/%m %H:%M")
            ),

            (
                'Vietnam Airlines',
                'VN234',
                'Hà Nội (HAN)',
                1500000,
                50,
                50,
                '',
                (now + datetime.timedelta(days=2)).strftime("%d/%m %H:%M")
            ),

            (
                'VietJet Air',
                'VJ456',
                'Đà Nẵng (DAD)',
                850000,
                59,
                60,
                'G5',
                (now + datetime.timedelta(hours=5)).strftime("%d/%m %H:%M")
            ),

            (
                'Bamboo Airways',
                'QH789',
                'Phú Quốc (PQC)',
                2100000,
                40,
                40,
                '',
                (now + datetime.timedelta(days=3)).strftime("%d/%m %H:%M")
            ),

            (
                'Vietnam Airlines',
                'VN999',
                'Đà Lạt (DLI)',
                950000,
                0,
                30,
                '',
                (now + datetime.timedelta(days=1)).strftime("%d/%m %H:%M")
            )
        ]

        cursor.executemany(
            '''
            INSERT INTO flights
            (
                airline,
                code,
                destination,
                price,
                seats,
                total_seats,
                booked_seats,
                departure_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            sample_flights
        )

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
            ctk.CTkButton(
                self.sidebar,
                text="👥 QUẢN LÝ USER",
                height=45,
                fg_color="#34495E",
                command=lambda: self.show_frame("users")
            ).pack(pady=5, padx=20, fill="x")
            ctk.CTkButton(
                self.sidebar,
                text="✈ QUẢN LÝ HÃNG",
                height=45,
                fg_color="#34495E",
                command=lambda: self.show_frame("airlines")
            ).pack(pady=5, padx=20, fill="x")
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

        # Main Pages
        self.main_content = ctk.CTkFrame(self.container, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.frame_flights = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.frame_customers = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.frame_stats = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.frame_users = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.frame_airlines = ctk.CTkFrame(self.main_content,fg_color="transparent"
        )
        self.setup_flight_view()
        bf = ctk.CTkFrame(
            self.frame_flights,
            fg_color="transparent"
        )

        bf.pack(fill="x", pady=20)

        # Nút đặt vé
        ctk.CTkButton(
            bf,
            text="ĐẶT VÉ",
            fg_color="#E67E22",
            height=50,
            font=("Arial", 14, "bold"),
            command=self.open_booking
        ).pack(side="left", expand=True, padx=10)

        # Chỉ Admin mới thấy
        if self.current_role == "Admin":
            ctk.CTkButton(
                bf,
                text="✏ SỬA CHUYẾN",
                fg_color="#2980B9",
                height=50,
                font=("Arial", 14, "bold"),
                command=self.edit_flight
            ).pack(side="left", expand=True, padx=10)

            ctk.CTkButton(
                bf,
                text="❌ XÓA CHUYẾN",
                fg_color="#C0392B",
                height=50,
                font=("Arial", 14, "bold"),
                command=self.delete_flight
            ).pack(side="left", expand=True, padx=10)
        self.setup_customer_view()
        self.setup_stats_view()
        self.setup_user_view()
        self.setup_airline_view()
        self.show_frame("flights")

    def show_frame(self, page):

        for f in [
            self.frame_flights,
            self.frame_customers,
            self.frame_stats,
            self.frame_users,
            self.frame_airlines
        ]:
            f.pack_forget()

        # ẨN / HIỆN FORM ADMIN
        if self.current_role == "Admin":

            if page == "flights":
                self.admin_input_frame.pack(pady=20, fill="x")
            else:
                self.admin_input_frame.pack_forget()

        if page == "flights":
            self.frame_flights.pack(fill="both", expand=True)
            self.load_data()

        elif page == "customers":
            self.frame_customers.pack(fill="both", expand=True)
            self.load_customers()

        elif page == "stats":
            self.frame_stats.pack(fill="both", expand=True)
            self.update_stats()

        elif page == "users":
            self.frame_users.pack(fill="both", expand=True)
            self.load_users()

        elif page == "airlines":
            self.frame_airlines.pack(fill="both", expand=True)
            self.load_airlines()

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

        # Lấy dữ liệu chuyến bay
        f_data = self.tree.item(sel)['values']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            "SELECT seats, total_seats, booked_seats, price FROM flights WHERE id=?",
            (f_data[0],)
        )

        res = c.fetchone()
        conn.close()

        # res:
        # 0 = seats
        # 1 = total_seats
        # 2 = booked_seats
        # 3 = price

        if res[0] <= 0:
            messagebox.showerror("Lỗi", "Chuyến bay đã hết chỗ!")
            return

        # Danh sách ghế đã đặt
        booked_list = res[2].split(',') if res[2] else []

        # Danh sách ghế còn trống
        available_seats = []

        for i in range(1, res[1] + 1):
            seat = f"G{i}"

            if seat not in booked_list:
                available_seats.append(seat)

        # ==========================
        # POPUP ĐẶT VÉ
        # ==========================
        pop = ctk.CTkToplevel(self)
        pop.title("Đặt vé nhiều ghế")
        pop.geometry("550x700")
        pop.attributes("-topmost", True)

        ctk.CTkLabel(
            pop,
            text=f"HÃNG: {f_data[1]}\nMÃ CHUYẾN: {f_data[2]}",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Tên khách hàng
        en = ctk.CTkEntry(
            pop,
            placeholder_text="Tên khách hàng",
            width=350
        )
        en.pack(pady=10)

        # SĐT
        ep = ctk.CTkEntry(
            pop,
            placeholder_text="Số điện thoại",
            width=350
        )
        ep.pack(pady=10)

        ctk.CTkLabel(
            pop,
            text="CHỌN GHẾ",
            font=("Arial", 14, "bold")
        ).pack(pady=(15, 5))

        # Frame cuộn chứa ghế
        seat_frame = ctk.CTkScrollableFrame(
            pop,
            width=450,
            height=350
        )

        seat_frame.pack(pady=10)

        # Lưu checkbox
        seat_vars = {}

        row = 0
        col = 0

        # Tạo checkbox ghế
        for seat in available_seats:

            var = ctk.BooleanVar()

            cb = ctk.CTkCheckBox(
                seat_frame,
                text=seat,
                variable=var
            )

            cb.grid(
                row=row,
                column=col,
                padx=10,
                pady=10,
                sticky="w"
            )

            seat_vars[seat] = var

            col += 1

            if col > 4:
                col = 0
                row += 1

        # ==========================
        # XÁC NHẬN ĐẶT VÉ
        # ==========================
        def confirm():

            customer_name = en.get().strip()
            customer_phone = ep.get().strip()

            if not customer_name or not customer_phone:
                messagebox.showwarning(
                    "Lỗi",
                    "Vui lòng nhập đầy đủ thông tin!"
                )
                return

            # Ghế được chọn
            selected_seats = []

            for seat, var in seat_vars.items():
                if var.get():
                    selected_seats.append(seat)

            if len(selected_seats) == 0:
                messagebox.showwarning(
                    "Lỗi",
                    "Hãy chọn ít nhất 1 ghế!"
                )
                return

            if len(selected_seats) > res[0]:
                messagebox.showerror(
                    "Lỗi",
                    "Không đủ ghế trống!"
                )
                return

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            # Gộp ghế cũ + ghế mới
            all_booked = booked_list + selected_seats

            new_booked = ",".join(all_booked)

            # Cập nhật số ghế
            c.execute(
                """
                UPDATE flights
                SET seats = seats - ?,
                    booked_seats = ?
                WHERE id=?
                """,
                (
                    len(selected_seats),
                    new_booked,
                    f_data[0]
                )
            )

            # Insert từng ghế vào bookings
            for seat in selected_seats:
                c.execute(
                    """
                    INSERT INTO bookings
                    (
                        customer_name,
                        customer_phone,
                        flight_code,
                        seat_number,
                        price_at_booking
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        customer_name,
                        customer_phone,
                        f_data[2],
                        seat,
                        res[3]
                    )
                )

            conn.commit()
            conn.close()

            self.load_data()

            pop.destroy()

            messagebox.showinfo(
                "Thành công",
                f"Đặt thành công {len(selected_seats)} ghế!\n\n"
                f"Ghế đã chọn:\n{', '.join(selected_seats)}"
            )

        # Nút xác nhận
        ctk.CTkButton(
            pop,
            text="XÁC NHẬN ĐẶT VÉ",
            fg_color="#E67E22",
            height=45,
            font=("Arial", 14, "bold"),
            command=confirm
        ).pack(pady=20)



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
    def edit_flight(self):

        sel = self.tree.selection()

        if not sel:
            messagebox.showwarning(
                "Lỗi",
                "Hãy chọn chuyến bay!"
            )
            return

        data = self.tree.item(sel)['values']

        pop = ctk.CTkToplevel(self)
        pop.title("Sửa chuyến bay")
        pop.geometry("400x500")

        ctk.CTkLabel(
            pop,
            text="CHỈNH SỬA CHUYẾN BAY",
            font=("Arial", 18, "bold")
        ).pack(pady=15)

        airline = ctk.CTkOptionMenu(
            pop,
            values=AIRLINES
        )
        airline.pack(pady=10)
        airline.set(data[1])

        ent_code = ctk.CTkEntry(pop)
        ent_code.pack(pady=10)
        ent_code.insert(0, data[2])

        ent_dest = ctk.CTkEntry(pop)
        ent_dest.pack(pady=10)
        ent_dest.insert(0, data[3])

        ent_time = ctk.CTkEntry(pop)
        ent_time.pack(pady=10)
        ent_time.insert(0, data[4])

        ent_price = ctk.CTkEntry(pop)
        ent_price.pack(pady=10)
        ent_price.insert(0, str(data[5]).replace(",", ""))

        ent_total = ctk.CTkEntry(pop)
        ent_total.pack(pady=10)
        ent_total.insert(0, str(data[7]))

        def save_edit():

            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()

                c.execute(
                    """
                    UPDATE flights
                    SET airline=?,
                        code=?,
                        destination=?,
                        departure_time=?,
                        price=?,
                        total_seats=?
                    WHERE id=?
                    """,
                    (
                        airline.get(),
                        ent_code.get().upper(),
                        ent_dest.get(),
                        ent_time.get(),
                        float(ent_price.get()),
                        int(ent_total.get()),
                        data[0]
                    )
                )

                conn.commit()
                conn.close()

                self.load_data()

                pop.destroy()

                messagebox.showinfo(
                    "Thành công",
                    "Đã cập nhật chuyến bay!"
                )

            except Exception as e:
                messagebox.showerror(
                    "Lỗi",
                    str(e)
                )

        ctk.CTkButton(
            pop,
            text="LƯU THAY ĐỔI",
            fg_color="#27AE60",
            command=save_edit
        ).pack(pady=20)

    def backup_data(self):
        if not os.path.exists('Backups'): os.makedirs('Backups')
        shutil.copy2(DB_NAME, f"Backups/backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        messagebox.showinfo("OK", "Đã sao lưu!")

    # =========================
    # QUẢN LÝ USER
    # =========================

    def setup_user_view(self):

        ctk.CTkLabel(
            self.frame_users,
            text="QUẢN LÝ TÀI KHOẢN",
            font=("Arial", 22, "bold")
        ).pack(pady=10)

        form = ctk.CTkFrame(self.frame_users)
        form.pack(fill="x", padx=20, pady=10)

        self.ent_new_user = ctk.CTkEntry(
            form,
            placeholder_text="Tên đăng nhập"
        )
        self.ent_new_user.grid(row=0, column=0, padx=10, pady=10)

        self.ent_new_pass = ctk.CTkEntry(
            form,
            placeholder_text="Mật khẩu"
        )
        self.ent_new_pass.grid(row=0, column=1, padx=10, pady=10)

        self.opt_role = ctk.CTkOptionMenu(
            form,
            values=["Admin", "Staff"]
        )
        self.opt_role.grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkButton(
            form,
            text="THÊM USER",
            fg_color="#27AE60",
            command=self.add_user
        ).grid(row=0, column=3, padx=10)

        ctk.CTkButton(
            form,
            text="RESET PASS",
            fg_color="#F39C12",
            command=self.reset_password
        ).grid(row=0, column=4, padx=10)

        ctk.CTkButton(
            form,
            text="XÓA USER",
            fg_color="#C0392B",
            command=self.delete_user
        ).grid(row=0, column=5, padx=10)

        self.tree_users = ttk.Treeview(
            self.frame_users,
            columns=("ID", "Username", "Role"),
            show='headings'
        )

        for c in ("ID", "Username", "Role"):
            self.tree_users.heading(c, text=c)
            self.tree_users.column(c, anchor="center")

        self.tree_users.pack(fill="both", expand=True, padx=20, pady=20)

    def load_users(self):

        for row in self.tree_users.get_children():
            self.tree_users.delete(row)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("SELECT id, username, role FROM users")

        for row in c.fetchall():
            self.tree_users.insert("", "end", values=row)

        conn.close()

    def add_user(self):

        username = self.ent_new_user.get().strip()
        password = self.ent_new_pass.get().strip()
        role = self.opt_role.get()

        if not username or not password:
            messagebox.showwarning("Lỗi", "Nhập đầy đủ thông tin!")
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            c.execute(
                """
                INSERT INTO users(username, password, role)
                VALUES (?, ?, ?)
                """,
                (username, password, role)
            )

            conn.commit()
            conn.close()

            self.load_users()

            self.ent_new_user.delete(0, 'end')
            self.ent_new_pass.delete(0, 'end')

            messagebox.showinfo("Thành công", "Đã thêm user!")

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete_user(self):

        sel = self.tree_users.selection()

        if not sel:
            messagebox.showwarning("Lỗi", "Chọn user!")
            return

        data = self.tree_users.item(sel)['values']

        if data[1] == "admin":
            messagebox.showwarning(
                "Lỗi",
                "Không thể xóa admin!"
            )
            return

        if messagebox.askyesno(
                "Xác nhận",
                f"Xóa user {data[1]} ?"
        ):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            c.execute(
                "DELETE FROM users WHERE id=?",
                (data[0],)
            )

            conn.commit()
            conn.close()

            self.load_users()

            messagebox.showinfo("Thành công", "Đã xóa user!")

    def reset_password(self):

        sel = self.tree_users.selection()

        if not sel:
            messagebox.showwarning("Lỗi", "Chọn user!")
            return

        data = self.tree_users.item(sel)['values']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            "UPDATE users SET password='123' WHERE id=?",
            (data[0],)
        )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Thành công",
            f"Đã reset mật khẩu user {data[1]} về 123"
        )

    # =========================
    # QUẢN LÝ HÃNG BAY
    # =========================

    def setup_airline_view(self):

        ctk.CTkLabel(
            self.frame_airlines,
            text="QUẢN LÝ HÃNG HÀNG KHÔNG",
            font=("Arial", 22, "bold")
        ).pack(pady=10)

        form = ctk.CTkFrame(self.frame_airlines)
        form.pack(fill="x", padx=20, pady=10)

        self.ent_airline = ctk.CTkEntry(
            form,
            placeholder_text="Tên hãng hàng không"
        )
        self.ent_airline.grid(row=0, column=0, padx=10, pady=10)

        self.ent_country = ctk.CTkEntry(
            form,
            placeholder_text="Quốc gia"
        )
        self.ent_country.grid(row=1, column=0, padx=10, pady=10)

        self.ent_hotline = ctk.CTkEntry(
            form,
            placeholder_text="Hotline"
        )
        self.ent_hotline.grid(row=1, column=1, padx=10, pady=10)

        self.ent_website = ctk.CTkEntry(
            form,
            placeholder_text="Website"
        )
        self.ent_website.grid(row=1, column=2, padx=10, pady=10)

        ctk.CTkButton(
            form,
            text="THÊM HÃNG",
            fg_color="#27AE60",
            command=self.add_airline
        ).grid(row=0, column=1, padx=10)

        ctk.CTkButton(
            form,
            text="XÓA HÃNG",
            fg_color="#C0392B",
            command=self.delete_airline
        ).grid(row=0, column=2, padx=10)

        self.tree_airlines = ttk.Treeview(
            self.frame_airlines,
            columns=("ID", "Name"),
            show='headings'
        )

        self.tree_airlines.heading("ID", text="ID")
        self.tree_airlines.heading("Name", text="Tên hãng")

        self.tree_airlines.column("ID", width=80, anchor="center")
        self.tree_airlines.column("Name", anchor="center")

        self.tree_airlines.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

    def load_airlines(self):

        for row in self.tree_airlines.get_children():
            self.tree_airlines.delete(row)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("SELECT id, name FROM airlines")

        rows = c.fetchall()

        conn.close()

        for row in rows:
            self.tree_airlines.insert("", "end", values=row)

    def add_airline(self):

        global AIRLINES

        name = self.ent_airline.get().strip()

        if not name:
            messagebox.showwarning(
                "Lỗi",
                "Nhập tên hãng!"
            )
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            c.execute(
                "INSERT INTO airlines(name) VALUES(?)",
                (name,)
            )

            conn.commit()
            conn.close()

            AIRLINES.append(name)

            self.opt_add_airline.configure(values=AIRLINES)

            self.opt_filter_airline.configure(
                values=["Tất cả hãng"] + AIRLINES
            )

            self.ent_airline.delete(0, 'end')

            self.load_airlines()

            messagebox.showinfo(
                "Thành công",
                "Đã thêm hãng!"
            )

        except Exception as e:
            messagebox.showerror(
                "Lỗi",
                str(e)
            )

    def delete_airline(self):

        global AIRLINES

        sel = self.tree_airlines.selection()

        if not sel:
            messagebox.showwarning(
                "Lỗi",
                "Chọn hãng!"
            )
            return

        data = self.tree_airlines.item(sel)['values']

        airline_name = data[1]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            "SELECT COUNT(*) FROM flights WHERE airline=?",
            (airline_name,)
        )

        count = c.fetchone()[0]

        if count > 0:
            conn.close()

            messagebox.showwarning(
                "Lỗi",
                "Hãng đang có chuyến bay!"
            )
            return

        if messagebox.askyesno(
                "Xác nhận",
                f"Xóa hãng {airline_name} ?"
        ):

            c.execute(
                "DELETE FROM airlines WHERE id=?",
                (data[0],)
            )

            conn.commit()
            conn.close()

            if airline_name in AIRLINES:
                AIRLINES.remove(airline_name)

            self.opt_add_airline.configure(values=AIRLINES)

            self.opt_filter_airline.configure(
                values=["Tất cả hãng"] + AIRLINES
            )

            self.load_airlines()

            messagebox.showinfo(
                "Thành công",
                "Đã xóa hãng!"
            )

if __name__ == "__main__":
    init_db()
    app = FlightApp()
    app.mainloop()