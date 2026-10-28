import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Если код запускается не как файл (например, в Jupyter), используем текущую директорию
    BASE_DIR = os.getcwd()

def calculate_psi(G, N, coefs):
    a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10 = coefs
    return (a0 + a1*G + a2*G**2 + a3*G**3 + a4*G**4 + a5*G**5 +
            a6*N + a7*N**2 + a8*N**3 + a9*N**4 + a10*N**5)


USERS = {
    "admin": {"password": "admin", "role": "admin"},
    "researcher": {"password": "researcher", "role": "researcher"},
}


COEFS_POLYSTYRENE = (
    0.765, 0.030, -0.003, 1.88e-5, 3.09e-5, -1.47e-6,
    8.14e-4, 7.04e-6, 7.27e-8, -7.45e-10, -4e-11
)


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Авторизация")
        self.root.geometry("300x200")

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
        user = USERS.get(username)
        if user and user["password"] == password:
            self.root.withdraw()
            if user["role"] == "admin":
                AdminWindow(tk.Toplevel(), self.root)
            else:
                ResearcherWindow(tk.Toplevel(), self.root)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")


class AdminWindow:
    def __init__(self, root, login_root):
        self.root = root
        self.login_root = login_root
        self.root.title("Панель администратора")
        self.root.geometry("400x300")
        ttk.Label(root, text="Раздел в разработке...").pack(pady=50)
        ttk.Button(root, text="Выйти", command=self.logout).pack()

    def logout(self):
        self.root.destroy()
        self.login_root.deiconify()


class ResearcherWindow:
    def __init__(self, root, login_root):
        self.root = root
        self.login_root = login_root
        self.root.title("Исследовательский комплекс")
        self.root.geometry("500x400")
        ttk.Label(root, text="Параметры моделирования").pack(pady=10)
        ttk.Button(root, text="Запустить (заглушка)").pack(pady=10)
        ttk.Button(root, text="Выйти", command=self.logout).pack(pady=10)

    def logout(self):
        self.root.destroy()
        self.login_root.deiconify()


def run_experiment(g_min, g_max, g_step, n_min, n_max, n_step, coefs):
    """Перебор по сетке значений G и N, возвращает DataFrame."""
    g_values = np.arange(g_min, g_max + g_step/2, g_step)
    n_values = np.arange(n_min, n_max + n_step/2, n_step)

    data = []
    for G in g_values:
        for N in n_values:
            psi = calculate_psi(G, N, coefs)
            data.append((round(G, 2), round(N, 2), round(psi, 4)))
    return pd.DataFrame(data, columns=["G", "N", "Psi"])


def plot_results(g_values, n_values, coefs):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

    # Зависимость Ψ от G при разных N
    n_vals_to_plot = [n_values[0], n_values[len(n_values)//2], n_values[-1]]
    for n in n_vals_to_plot:
        psi_vals = [calculate_psi(g, n, coefs) for g in g_values]
        ax1.plot(g_values, psi_vals, label=f'N={n}')
    ax1.set_xlabel('Расход G (кг/ч)')
    ax1.set_ylabel('Степень заполнения Ψ')
    ax1.set_title('Зависимость Ψ от G')
    ax1.legend()
    ax1.grid(True)

    # Зависимость Ψ от N при разных G
    g_vals_to_plot = [g_values[0], g_values[len(g_values)//2], g_values[-1]]
    for g in g_vals_to_plot:
        psi_vals = [calculate_psi(g, n, coefs) for n in n_values]
        ax2.plot(n_values, psi_vals, label=f'G={g}')
    ax2.set_xlabel('Частота N (об/мин)')
    ax2.set_ylabel('Степень заполнения Ψ')
    ax2.set_title('Зависимость Ψ от N')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


def export_to_excel(df, filepath=f"{BASE_DIR}\\report_extruder.xlsx"):
    """Сохраняет DataFrame с результатами в Excel."""
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Результаты', index=False)
    print(f"Отчёт сохранён: {filepath}")


if __name__ == "__main__":
    print("Вычислительный эксперимент для Полистирола")
    df = run_experiment(2, 10, 0.5, 40, 100, 5, COEFS_POLYSTYRENE)

    g_values = np.arange(2, 10 + 0.25, 0.5)
    n_values = np.arange(40, 100 + 2.5, 5)
    plot_results(g_values, n_values, COEFS_POLYSTYRENE)

    print("Сгенерировать excel отчет? Y/N")

    if input()[0].upper() == 'Y':
        export_to_excel(df)

    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()