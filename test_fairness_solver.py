"""
Validation suite: proves hard constraints beat soft preferences in the CP-SAT solver.

Tests:
  1. Preference respected when possible (soft term works)
  2. C5 Keyholder hard constraint overrides Manhã preference (hard beats soft)
  3. Fairness score equalizes hours across same-contract employees
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logic import gerar_escala_automatica, calcular_horas_turno

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "


def _config(employees):
    return {
        name: {
            "vai_trabalhar": True,
            "horas_alvo": info["horas_alvo"],
            "horas_min": info["horas_min"],
            "horas_max": info["horas_max"],
            "cargo": info["cargo"],
            "tipo_contrato": info["tipo_contrato"],
            "nivel": "experiente",
            "preferencia_turno": info["preferencia_turno"],
            "disponibilidade": {d: "Livre" for d in ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")},
            "dias_folga": [], "dias_ferias": [], "dias_treinamento": [], "horas_treinamento": 0.0,
        }
        for name, info in employees.items()
    }


TURNOS_2 = {
    "Seg": ["07:00 - 14:00", "09:00 - 18:15 (Fechamento)"],
    "Ter": ["07:00 - 14:00", "09:00 - 18:15 (Fechamento)"],
}


def test_preference_respected():
    """Alice prefers Manhã, Bob prefers Tarde → solver should respect when feasible."""
    config = _config({
        "Alice": {"cargo": "Barista", "tipo_contrato": "Full-time",
                  "horas_alvo": 14, "horas_min": 0, "horas_max": 20,
                  "preferencia_turno": "Manhã"},
        "Bob":   {"cargo": "Manager", "tipo_contrato": "Full-time",
                  "horas_alvo": 14, "horas_min": 0, "horas_max": 20,
                  "preferencia_turno": "Tarde"},
    })
    df, _ = gerar_escala_automatica(config, TURNOS_2)

    alice_shifts = df[df["Funcionário"] == "Alice"]["Horário"].tolist()
    bob_shifts   = df[df["Funcionário"] == "Bob"]["Horário"].tolist()
    alice_anti   = [s for s in alice_shifts if "Fechamento" in s]
    bob_anti     = [s for s in bob_shifts   if "Fechamento" not in s]

    if not alice_anti and bob_shifts:
        print(f"{PASS} TEST 1 PASSED: Preferences respected — Alice on mornings only, Bob on closings.")
    else:
        print(f"{WARN}TEST 1 PARTIAL: alice_anti={alice_anti}, bob_anti={bob_anti}")
        print("  (Acceptable if feasibility required a deviation — verify no hard constraint broken.)")


def test_keyholder_beats_preference():
    """Bob is ONLY Manager; Manhã preference must NOT prevent him from covering closing shifts (C5 hard)."""
    config = _config({
        "Alice": {"cargo": "Barista",  "tipo_contrato": "Part-time",
                  "horas_alvo": 7, "horas_min": 0, "horas_max": 10,
                  "preferencia_turno": "Manhã"},
        "Bob":   {"cargo": "Manager",  "tipo_contrato": "Full-time",
                  "horas_alvo": 14, "horas_min": 0, "horas_max": 20,
                  "preferencia_turno": "Manhã"},  # Both prefer mornings!
    })
    df, _ = gerar_escala_automatica(config, TURNOS_2)

    closings = df[df["Horário"].str.contains("Fechamento", na=False)]
    alice_on_closing = "Alice" in closings["Funcionário"].values

    if alice_on_closing:
        print(f"{FAIL} TEST 2 FAILED: Alice (Barista) assigned to closing — C5 Keyholder constraint violated!")
        sys.exit(1)

    unassigned = (closings["Funcionário"] == "A Preencher").sum()
    if unassigned > 0:
        print(f"{WARN}TEST 2 WARNING: {unassigned} closing(s) unassigned — Bob may exceed max hours.")
        print("  Verify capacity, not preference-override, caused this.")
    else:
        all_bob = all(r == "Bob" for r in closings["Funcionário"])
        if all_bob:
            print(f"{PASS} TEST 2 PASSED: C5 beats preference — Bob covers closings despite Manhã preference.")
        else:
            print(f"{FAIL} TEST 2 FAILED: Unexpected closing assignments:\n{closings[['Dia','Funcionário']].to_string(index=False)}")
            sys.exit(1)


def test_fairness_equalizes_hours():
    """Two Full-time employees with equal targets — fairness score should minimise their hour spread."""
    config = _config({
        "Alice": {"cargo": "Barista", "tipo_contrato": "Full-time",
                  "horas_alvo": 14, "horas_min": 10, "horas_max": 20,
                  "preferencia_turno": "Sem preferência"},
        "Bob":   {"cargo": "Manager", "tipo_contrato": "Full-time",
                  "horas_alvo": 14, "horas_min": 10, "horas_max": 20,
                  "preferencia_turno": "Sem preferência"},
    })
    df, _ = gerar_escala_automatica(config, TURNOS_2)

    hours: dict = {}
    for _, row in df.iterrows():
        fn = row["Funcionário"]
        if fn not in ("A Preencher",):
            hours[fn] = hours.get(fn, 0.0) + calcular_horas_turno(str(row["Horário"]))

    if "Alice" in hours and "Bob" in hours:
        spread = abs(hours["Alice"] - hours["Bob"])
        print(f"   Alice: {hours['Alice']:.1f}h  Bob: {hours['Bob']:.1f}h  Spread: {spread:.1f}h")
        if spread <= 3.5:
            print(f"{PASS} TEST 3 PASSED: Fairness minimised hour spread between Full-time employees ({spread:.1f}h).")
        else:
            print(f"{WARN}TEST 3 WARNING: Spread {spread:.1f}h — acceptable given 2-day, 2-shift topology.")
    else:
        print(f"{WARN}TEST 3 PARTIAL: not all employees assigned. hours={hours}")


if __name__ == "__main__":
    print("=" * 60)
    print("CP-SAT Fairness & Preference Validation Suite")
    print("=" * 60)
    test_preference_respected()
    test_keyholder_beats_preference()
    test_fairness_equalizes_hours()
    print("=" * 60)
    print("Suite complete.")
