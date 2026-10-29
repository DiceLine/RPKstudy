import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
import os

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Если код запускается не как файл (например, в Jupyter), используем текущую директорию
    BASE_DIR = os.getcwd()

DB_NAME = os.path.join(BASE_DIR, 'extruder_app.db')


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.seed_data()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                role TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS polymers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS coefficients (
                polymer_id INTEGER,
                a0 REAL, a1 REAL, a2 REAL, a3 REAL, a4 REAL, a5 REAL,
                a6 REAL, a7 REAL, a8 REAL, a9 REAL, a10 REAL,
                FOREIGN KEY(polymer_id) REFERENCES polymers(id)
            )
        ''')
        self.conn.commit()

    def seed_data(self):
        # Добавление пользователей по умолчанию
        try:
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', 'admin', 'admin'))
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('researcher', 'researcher', 'researcher'))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

        # Добавление Полистирола из задания
        self.cursor.execute("SELECT COUNT(*) FROM polymers")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO polymers (name) VALUES (?)", ('Полистирол',))
            poly_id = self.cursor.lastrowid
            coefs = (0.765, 0.030, -0.003, 1.88e-5, 3.09e-5, -1.47e-6, 8.14e-4, 7.04e-6, 7.27e-8, -7.45e-10, -4e-11)
            self.cursor.execute('''
                INSERT INTO coefficients (polymer_id, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (poly_id,) + coefs)
            self.conn.commit()

    def verify_user(self, username, password):
        self.cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_polymers(self):
        self.cursor.execute("SELECT id, name FROM polymers")
        return self.cursor.fetchall()

    def get_coefficients(self, polymer_id):
        self.cursor.execute("SELECT a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10 FROM coefficients WHERE polymer_id=?", (polymer_id,))
        return self.cursor.fetchone()

    def update_coefficients(self, polymer_id, coefs):
        self.cursor.execute('''
            UPDATE coefficients SET a0=?, a1=?, a2=?, a3=?, a4=?, a5=?, a6=?, a7=?, a8=?, a9=?, a10=?
            WHERE polymer_id=?
        ''', coefs + (polymer_id,))
        self.conn.commit()

    def add_polymer(self, name, coefs):
        try:
            self.cursor.execute("INSERT INTO polymers (name) VALUES (?)", (name,))
            poly_id = self.cursor.lastrowid
            self.cursor.execute('''
                INSERT INTO coefficients (polymer_id, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (poly_id,) + coefs)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_polymer(self, polymer_id):
        self.cursor.execute("DELETE FROM coefficients WHERE polymer_id=?", (polymer_id,))
        self.cursor.execute("DELETE FROM polymers WHERE id=?", (polymer_id,))
        self.conn.commit()

    def get_all_full_data(self):
        self.cursor.execute('''
            SELECT p.id, p.name, c.a0, c.a1, c.a2, c.a3, c.a4, c.a5, c.a6, c.a7, c.a8, c.a9, c.a10
            FROM polymers p
            JOIN coefficients c ON p.id = c.polymer_id
        ''')
        return self.cursor.fetchall()

    def get_users(self):
        self.cursor.execute("SELECT username, role FROM users")
        return self.cursor.fetchall()

    def add_user(self, username, password, role):
        try:
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_user(self, username):
        if username == 'admin': return False
        self.cursor.execute("DELETE FROM users WHERE username=?", (username,))
        self.conn.commit()
        return True


class LoginWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.root.title("Авторизация")
        self.root.geometry("300x200")
        self.root.resizable(False, False)

        ttk.Label(root, text="Логин:").pack(pady=5)
        self.username_entry = ttk.Entry(root)
        self.username_entry.pack(pady=5)

        ttk.Label(root, text="Пароль:").pack(pady=5)
        self.password_entry = ttk.Entry(root, show="*")
        self.password_entry.pack(pady=5)

        ttk.Button(root, text="Войти", command=self.login).pack(pady=15)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.db.verify_user(username, password)

        if role == 'admin':
            self.root.withdraw()
            AdminWindow(tk.Toplevel(), self.db, self.root)
        elif role == 'researcher':
            self.root.withdraw()
            ResearcherWindow(tk.Toplevel(), self.db, self.root)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")


class AdminWindow:
    def __init__(self, root, db, login_root):
        self.root = root
        self.db = db
        self.login_root = login_root
        self.root.title("Панель администратора")
        self.root.geometry("800x600")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.create_users_tab()
        self.create_coefs_tab()
        self.create_all_data_tab()

        ttk.Button(root, text="Выйти", command=self.logout).pack(pady=5)
    
    def create_users_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Пользователи")

        self.tree = ttk.Treeview(frame, columns=("Username", "Role"), show='headings')
        self.tree.heading("Username", text="Логин")
        self.tree.heading("Role", text="Роль")
        self.tree.pack(fill='both', expand=True, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=5)

        ttk.Button(btn_frame, text="Добавить", command=self.add_user_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_user).pack(side='left', padx=5)

        self.load_users()

    def load_users(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for user in self.db.get_users():
            self.tree.insert("", "end", values=user)

    def add_user_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить пользователя")
        dialog.geometry("250x250")

        ttk.Label(dialog, text="Логин:").pack(pady=5)
        u_entry = ttk.Entry(dialog)
        u_entry.pack()

        ttk.Label(dialog, text="Пароль:").pack(pady=5)
        p_entry = ttk.Entry(dialog)
        p_entry.pack()

        ttk.Label(dialog, text="Роль (admin/researcher):").pack(pady=5)
        r_combo = ttk.Combobox(dialog, values=["admin", "researcher"])
        r_combo.pack()

        def save():
            if self.db.add_user(u_entry.get(), p_entry.get(), r_combo.get()):
                self.load_users()
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Пользователь уже существует")

        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=10)

    def delete_user(self):
        selected = self.tree.selection()
        if selected:
            username = self.tree.item(selected[0])['values'][0]
            if self.db.delete_user(username):
                self.load_users()
            else:
                messagebox.showwarning("Внимание", "Нельзя удалить администратора по умолчанию")

    def create_coefs_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Редактор коэффициентов")

        ttk.Label(frame, text="Выберите материал:").grid(row=0, column=0, pady=5, sticky='w')
        self.poly_combo = ttk.Combobox(frame, width=30)
        self.poly_combo.grid(row=0, column=1, pady=5, sticky='ew')
        self.poly_combo.bind("<<ComboboxSelected>>", self.load_coefs)

        self.polymers = self.db.get_polymers()
        if self.polymers:
            self.poly_combo['values'] = [p[1] for p in self.polymers]
            self.poly_combo.current(0)

        self.coef_entries = []
        for i in range(11):
            ttk.Label(frame, text=f"a{i}:").grid(row=i+1, column=0, padx=5, pady=2, sticky='e')
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=i+1, column=1, padx=5, pady=2, sticky='ew')
            self.coef_entries.append(entry)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=13, column=0, columnspan=2, pady=15)

        ttk.Button(btn_frame, text="Сохранить изменения", command=self.save_coefs).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Добавить материал", command=self.add_polymer_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Удалить материал", command=self.delete_polymer).pack(side='left', padx=5)

        self.load_coefs()

    def load_coefs(self, event=None):
        idx = self.poly_combo.current()
        if idx == -1: return
        poly_id = self.polymers[idx][0]
        coefs = self.db.get_coefficients(poly_id)
        if coefs:
            for entry, val in zip(self.coef_entries, coefs):
                entry.delete(0, tk.END)
                entry.insert(0, str(val))

    def save_coefs(self):
        idx = self.poly_combo.current()
        if idx == -1: return
        poly_id = self.polymers[idx][0]
        try:
            coefs = tuple(float(entry.get()) for entry in self.coef_entries)
            self.db.update_coefficients(poly_id, coefs)
            messagebox.showinfo("Успех", "Коэффициенты успешно обновлены")
            self.refresh_all_data()
        except ValueError:
            messagebox.showerror("Ошибка", "Все коэффициенты должны быть числами")

    def add_polymer_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить новый материал")
        dialog.geometry("350x500")

        ttk.Label(dialog, text="Название материала:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)

        ttk.Label(dialog, text="Коэффициенты (a0 - a10):").pack(pady=5)

        coef_frame = ttk.Frame(dialog)
        coef_frame.pack(pady=5)

        entries = []
        for i in range(11):
            ttk.Label(coef_frame, text=f"a{i}:").grid(row=i, column=0, padx=5, pady=2, sticky='e')
            entry = ttk.Entry(coef_frame, width=15)
            entry.insert(0, "0.0")
            entry.grid(row=i, column=1, padx=5, pady=2)
            entries.append(entry)

        def save_new():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название материала")
                return
            try:
                coefs = tuple(float(entry.get()) for entry in entries)
                if self.db.add_polymer(name, coefs):
                    messagebox.showinfo("Успех", f"Материал '{name}' добавлен")
                    self.refresh_polymer_list()
                    self.refresh_all_data()
                    dialog.destroy()
                else:
                    messagebox.showerror("Ошибка", "Материал с таким названием уже существует")
            except ValueError:
                messagebox.showerror("Ошибка", "Коэффициенты должны быть числами")

        ttk.Button(dialog, text="Сохранить", command=save_new).pack(pady=15)

    def delete_polymer(self):
        idx = self.poly_combo.current()
        if idx == -1: return
        poly_id = self.polymers[idx][0]
        name = self.polymers[idx][1]

        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить материал '{name}'?"):
            self.db.delete_polymer(poly_id)
            self.refresh_polymer_list()
            self.refresh_all_data()
            messagebox.showinfo("Успех", "Материал удален")

    def refresh_polymer_list(self):
        self.polymers = self.db.get_polymers()
        self.poly_combo['values'] = [p[1] for p in self.polymers]
        if self.polymers:
            self.poly_combo.current(0)
            self.load_coefs()
        else:
            self.poly_combo.set('')
            for entry in self.coef_entries:
                entry.delete(0, tk.END)

    def create_all_data_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Все данные в БД")

        columns = ["ID", "Название"] + [f"a{i}" for i in range(11)]
        self.all_data_tree = ttk.Treeview(frame, columns=columns, show='headings')

        for col in columns:
            self.all_data_tree.heading(col, text=col)
            self.all_data_tree.column(col, width=60, anchor='center')
        self.all_data_tree.column("Название", width=150, anchor='w')

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.all_data_tree.yview)
        self.all_data_tree.configure(yscrollcommand=scrollbar.set)

        self.all_data_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)

        ttk.Button(frame, text="Обновить таблицу", command=self.refresh_all_data).pack(pady=5)
        self.refresh_all_data()

    def refresh_all_data(self):
        for i in self.all_data_tree.get_children():
            self.all_data_tree.delete(i)
        data = self.db.get_all_full_data()
        for row in data:
            formatted_row = [row[0], row[1]] + [round(val, 5) for val in row[2:]]
            self.all_data_tree.insert("", "end", values=formatted_row)

    def logout(self):
        self.root.destroy()
        self.login_root.deiconify()


class ResearcherWindow:
    def __init__(self, root, db, login_root):
        self.root = root
        self.db = db
        self.login_root = login_root
        self.root.title("Исследовательский комплекс")
        self.root.geometry("1100x700")

        # --- Левая панель: Ввод данных ---
        input_frame = ttk.LabelFrame(root, text="Параметры исследования")
        input_frame.pack(side='left', fill='y', padx=10, pady=10)

        ttk.Label(input_frame, text="Тип полимера:").grid(row=0, column=0, pady=5, sticky='w')
        self.poly_combo = ttk.Combobox(input_frame, state="readonly")
        self.poly_combo.grid(row=0, column=1, pady=5)
        self.polymers = self.db.get_polymers()
        self.poly_combo['values'] = [p[1] for p in self.polymers]
        if self.polymers: self.poly_combo.current(0)

        # Параметры G
        ttk.Label(input_frame, text="--- Расход сырья (G) ---").grid(row=1, column=0, columnspan=2, pady=10)
        ttk.Label(input_frame, text="G min (кг/ч):").grid(row=2, column=0, sticky='w')
        self.g_min = ttk.Entry(input_frame); self.g_min.insert(0, "2"); self.g_min.grid(row=2, column=1)

        ttk.Label(input_frame, text="G max (кг/ч):").grid(row=3, column=0, sticky='w')
        self.g_max = ttk.Entry(input_frame); self.g_max.insert(0, "10"); self.g_max.grid(row=3, column=1)

        ttk.Label(input_frame, text="Шаг ΔG:").grid(row=4, column=0, sticky='w')
        self.g_step = ttk.Entry(input_frame); self.g_step.insert(0, "0.5"); self.g_step.grid(row=4, column=1)

        # Параметры N
        ttk.Label(input_frame, text="--- Частота вращения (N) ---").grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Label(input_frame, text="N min (об/мин):").grid(row=6, column=0, sticky='w')
        self.n_min = ttk.Entry(input_frame); self.n_min.insert(0, "40"); self.n_min.grid(row=6, column=1)

        ttk.Label(input_frame, text="N max (об/мин):").grid(row=7, column=0, sticky='w')
        self.n_max = ttk.Entry(input_frame); self.n_max.insert(0, "100"); self.n_max.grid(row=7, column=1)

        ttk.Label(input_frame, text="Шаг ΔN:").grid(row=8, column=0, sticky='w')
        self.n_step = ttk.Entry(input_frame); self.n_step.insert(0, "5"); self.n_step.grid(row=8, column=1)

        ttk.Button(input_frame, text="Запустить моделирование", command=self.run_simulation).grid(row=9, column=0, columnspan=2, pady=20)
        ttk.Button(input_frame, text="Выйти", command=self.logout).grid(row=10, column=0, columnspan=2, pady=10)

        # --- Правая панель: Результаты ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Вкладка: Таблица
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="Таблица данных")
        self.tree = ttk.Treeview(self.table_frame, columns=("G", "N", "Psi"), show='headings')
        self.tree.heading("G", text="G (кг/ч)")
        self.tree.heading("N", text="N (об/мин)")
        self.tree.heading("Psi", text="Ψ (Степень заполнения)")
        self.tree.pack(fill='both', expand=True)

        # Вкладка: Графики
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_frame, text="Графики")

        # Вкладка: Производительность

        # Вкладка: Экспорт

        self.df_result = None

    def validate_inputs(self):
        try:
            g_min = float(self.g_min.get())
            g_max = float(self.g_max.get())
            g_step = float(self.g_step.get())
            n_min = float(self.n_min.get())
            n_max = float(self.n_max.get())
            n_step = float(self.n_step.get())

            if g_min < 0 or g_max < 0 or n_min < 0 or n_max < 0:
                raise ValueError("Значения не могут быть отрицательными")
            if g_min == 0 or g_step <= 0 or n_step <= 0:
                raise ValueError("Шаг должен быть больше нуля, G_min не может быть 0")
            if g_min > g_max or n_min > n_max:
                raise ValueError("Минимальное значение не может быть больше максимального")

            return g_min, g_max, g_step, n_min, n_max, n_step
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", f"Некорректные данные: {e}\nПроверьте, что введены числовые значения.")
            return None

    def calculate_psi(self, G, N, coefs):
        a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10 = coefs
        return (a0 + a1*G + a2*G**2 + a3*G**3 + a4*G**4 + a5*G**5 +
                a6*N + a7*N**2 + a8*N**3 + a9*N**4 + a10*N**5)

    def run_simulation(self):
        params = self.validate_inputs()
        if not params: return

        g_min, g_max, g_step, n_min, n_max, n_step = params

        idx = self.poly_combo.current()
        poly_id = self.polymers[idx][0]
        coefs = self.db.get_coefficients(poly_id)

        g_values = np.arange(g_min, g_max + g_step/2, g_step)
        n_values = np.arange(n_min, n_max + n_step/2, n_step)

        data = []
        for G in g_values:
            for N in n_values:
                psi = self.calculate_psi(G, N, coefs)
                data.append((round(G, 2), round(N, 2), round(psi, 4)))

        self.df_result = pd.DataFrame(data, columns=["G", "N", "Psi"])

        self.update_table()
        self.update_graphs(g_values, n_values, coefs)

    def update_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self.df_result.itertuples(index=False):
            self.tree.insert("", "end", values=row)

    def update_graphs(self, g_values, n_values, coefs):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

        n_vals_to_plot = [n_values[0], n_values[len(n_values)//2], n_values[-1]]
        for n in n_vals_to_plot:
            psi_vals = [self.calculate_psi(g, n, coefs) for g in g_values]
            ax1.plot(g_values, psi_vals, label=f'N={n}')
        ax1.set_xlabel('Расход G (кг/ч)')
        ax1.set_ylabel('Степень заполнения Ψ')
        ax1.set_title('Зависимость Ψ от G')
        ax1.legend()
        ax1.grid(True)

        g_vals_to_plot = [g_values[0], g_values[len(g_values)//2], g_values[-1]]
        for g in g_vals_to_plot:
            psi_vals = [self.calculate_psi(g, n, coefs) for n in n_values]
            ax2.plot(n_values, psi_vals, label=f'G={g}')
        ax2.set_xlabel('Частота N (об/мин)')
        ax2.set_ylabel('Степень заполнения Ψ')
        ax2.set_title('Зависимость Ψ от N')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def logout(self):
        self.root.destroy()
        self.login_root.deiconify()


def export_to_excel(df, filepath=f"{BASE_DIR}\\report_extruder.xlsx"):
    """Сохраняет DataFrame с результатами в Excel."""
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Результаты', index=False)
    print(f"Отчёт сохранён: {filepath}")


if __name__ == "__main__":
    db = Database()
    root = tk.Tk()
    app = LoginWindow(root, db)
    root.mainloop()