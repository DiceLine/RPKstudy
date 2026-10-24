def calculate_psi(G, N, coefs):
    """
    Ψ = a0 + a1*G + a2*G^2 + a3*G^3 + a4*G^4 + a5*G^5
          + a6*N + a7*N^2 + a8*N^3 + a9*N^4 + a10*N^5
    """
    a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10 = coefs
    return (a0 + a1*G + a2*G**2 + a3*G**3 + a4*G**4 + a5*G**5 +
            a6*N + a7*N**2 + a8*N**3 + a9*N**4 + a10*N**5)


# Коэффициенты для Полистирола
COEFS_POLYSTYRENE = (
    0.765, 0.030, -0.003, 1.88e-5, 3.09e-5, -1.47e-6,
    8.14e-4, 7.04e-6, 7.27e-8, -7.45e-10, -4e-11
)


if __name__ == "__main__":
    print("Расчёт степени заполнения канала шнека экструдера")
    print("=" * 50)
    G = float(input("Введите расход сырья G (кг/ч): "))
    N = float(input("Введите частоту вращения N (об/мин): "))
    psi = calculate_psi(G, N, COEFS_POLYSTYRENE)
    print(f"\nСтепень заполнения Ψ = {psi:.4f}")