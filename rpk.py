import numpy as np
import pandas as pd


def calculate_psi(G, N, coefs):
    a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10 = coefs
    return (a0 + a1*G + a2*G**2 + a3*G**3 + a4*G**4 + a5*G**5 +
            a6*N + a7*N**2 + a8*N**3 + a9*N**4 + a10*N**5)


COEFS_POLYSTYRENE = (
    0.765, 0.030, -0.003, 1.88e-5, 3.09e-5, -1.47e-6,
    8.14e-4, 7.04e-6, 7.27e-8, -7.45e-10, -4e-11
)


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


if __name__ == "__main__":
    print("Вычислительный эксперимент для Полистирола")
    print("=" * 50)
    df = run_experiment(2, 10, 0.5, 40, 100, 5, COEFS_POLYSTYRENE)
    print(df.to_string(index=False))
    print(f"\nВсего точек: {len(df)}")