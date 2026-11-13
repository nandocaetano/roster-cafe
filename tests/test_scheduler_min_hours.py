"""
Tests for T-20261113-05: scheduler ignoring minimum hours.

Root cause: `hour_deviation_cost` weighs `under_vars` at 1/min.
`fairness_cost` weighs spread at 10/min.  When multiple Part-timers
compete for the same slots, the solver equalises to minimise spread
rather than honouring binding minimum-hours constraints, because the
equal-distribution solution has lower total cost.

Fix: add MIN_HOURS_COST (500/min below horas_min) so that violating
a minimum-hours constraint is far more expensive than a fairness spread.
"""
import re
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic import gerar_escala_automatica, calcular_horas_turno


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _emp(nome, horas_min, horas_max, disponibilidade,
         contrato="Part-time", cargo="Barista", nivel="experiente"):
    return {
        nome: {
            "vai_trabalhar": True,
            "horas_min": float(horas_min),
            "horas_max": float(horas_max),
            "horas_alvo": int(horas_max),
            "cargo": cargo,
            "tipo_contrato": contrato,
            "nivel": nivel,
            "preferencia_turno": "Sem preferência",
            "disponibilidade": disponibilidade,
            "dias_folga": [],
            "dias_ferias": [],
            "dias_treinamento": [],
            "horas_treinamento": 0.0,
        }
    }


def _hours(df, nome):
    rows = df[df["Funcionário"] == nome]
    return sum(calcular_horas_turno(r["Horário"]) for _, r in rows.iterrows())


_LIVRE = {d: "Livre" for d in ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")}


def _in_window(horario: str, avail: str) -> bool:
    """Return True if the shift string fits within the availability value."""
    if avail in ("Indisponível", "Folga", "Férias"):
        return False
    if avail == "Livre":
        return True
    times = re.findall(r"(\d{1,2}):(\d{2})", horario)
    if len(times) < 2:
        return True
    s_start = int(times[0][0]) * 60 + int(times[0][1])
    s_end   = int(times[1][0]) * 60 + int(times[1][1])
    av = re.findall(r"(\d{1,2}):(\d{2})", avail)
    if len(av) < 2:
        return True
    av_start = int(av[0][0]) * 60 + int(av[0][1])
    av_end   = int(av[1][0]) * 60 + int(av[1][1])
    return s_start >= av_start and s_end <= av_end


# ---------------------------------------------------------------------------
# Test 1 — abstract: fairness vs minimum hours (deterministic failure)
# ---------------------------------------------------------------------------
# 3 Part-timers (Alice min 20h, Bob/Ciara min 0h), all same contract group.
# 7 days × 1 slot "07:00-12:00" (5 h), headcount 1.
# Alice can only work Mon–Thu (4 slots = 20 h max).
# Bob/Ciara can work every day.
#
# Without MIN_HOURS_COST: total under_vars is identical regardless of who
# gets each slot (all targets are equal), so only fairness drives the choice.
# The minimum-fairness-spread solution distributes roughly 2 slots each
# (Alice ≤ 3 slots = 15 h < 20 h minimum).
#
# With MIN_HOURS_COST: 500 × 300 min = 150 000 cost units for Alice at 10 h,
# dominating fairness (3 000) → solver gives Alice her 4 slots (20 h).
# ---------------------------------------------------------------------------

_ALICE_DISP = {
    "Seg": "Específico: 07:00 - 12:00",
    "Ter": "Específico: 07:00 - 12:00",
    "Qua": "Específico: 07:00 - 12:00",
    "Qui": "Específico: 07:00 - 12:00",
    "Sex": "Indisponível",
    "Sáb": "Indisponível",
    "Dom": "Indisponível",
}

_TURNOS_SHORT = {d: ["07:00 - 12:00"] for d in ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")}


def test_minimum_hours_not_sacrificed_for_fairness():
    """
    Alice (Part-time, min 20 h) must receive her 4 available Mon–Thu slots.
    Current code lets fairness suppress her below the minimum.
    """
    config = {}
    config.update(_emp("Alice", horas_min=20, horas_max=26, disponibilidade=_ALICE_DISP))
    config.update(_emp("Bob",   horas_min=0,  horas_max=26, disponibilidade=_LIVRE))
    config.update(_emp("Ciara", horas_min=0,  horas_max=26, disponibilidade=_LIVRE))

    df, _ = gerar_escala_automatica(
        config, _TURNOS_SHORT, margem_horas=2.0, min_dias_folga=1
    )

    alice_hours = _hours(df, "Alice")
    assert alice_hours >= 20.0, (
        f"Alice should reach her 20 h minimum (got {alice_hours:.1f} h). "
        "Fairness is overriding minimum hours."
    )


# ---------------------------------------------------------------------------
# Test 2 — real Ignacio scenario with Default Cafe shifts
# ---------------------------------------------------------------------------

_IGNACIO_DISP = {
    "Seg": "Específico: 07:00 - 12:00",
    "Ter": "Específico: 07:00 - 12:00",
    "Qua": "Específico: 07:00 - 12:00",
    "Qui": "Específico: 07:00 - 12:00",
    "Sex": "Específico: 07:00 - 16:00",
    "Sáb": "Livre",
    "Dom": "Livre",
}

_TURNOS_REAL = {
    d: [
        "07:00 - 12:00",
        "07:00 - 14:00",
        "07:30 - 15:00",
        "08:00 - 16:00",
        "09:00 - 18:15 (Fechamento)",
        "12:00 - 18:15 (Fechamento)",
        "14:00 - 18:15 (Fechamento)",
    ]
    for d in ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
}


def test_ignacio_scenario():
    """
    Ignacio (Part-time, Barista, Trainee, min 20 h, Custom availability)
    must receive >= 20 h and <= 26 h.  No shift may fall outside his
    availability window for the day.  Also verifies that Fri 07:30–15:00
    fits his Fri window (07:00–16:00).
    """
    config = {}
    # Ignacio: Part-time, Barista, Trainee ("novato")
    config.update(_emp(
        "Ignacio", horas_min=20, horas_max=26,
        disponibilidade=_IGNACIO_DISP,
        contrato="Part-time", cargo="Barista", nivel="novato",
    ))
    # Ana: Full-time Manager (keyholder, covers closing shifts)
    config.update(_emp(
        "Ana", horas_min=0, horas_max=40,
        disponibilidade=_LIVRE,
        contrato="Full-time", cargo="Manager", nivel="experiente",
    ))
    # Ciara: Part-time, Barista (competes with Ignacio for Part-time slots)
    config.update(_emp(
        "Ciara", horas_min=15, horas_max=26,
        disponibilidade=_LIVRE,
        contrato="Part-time", cargo="Barista", nivel="experiente",
    ))
    # Emerson: Part-time, Head Barista (also keyholder, also competes)
    config.update(_emp(
        "Emerson", horas_min=15, horas_max=26,
        disponibilidade=_LIVRE,
        contrato="Part-time", cargo="Head Barista", nivel="experiente",
    ))

    df, _ = gerar_escala_automatica(
        config, _TURNOS_REAL, margem_horas=2.0, min_dias_folga=1
    )

    # 1. Fri 07:30-15:00 must be within Ignacio's Fri window (logic sanity)
    assert _in_window("07:30 - 15:00", _IGNACIO_DISP["Sex"]), (
        "Fri 07:30-15:00 should fit Ignacio's Fri window (07:00-16:00)"
    )

    # 2. No shift assigned to Ignacio may exceed his window for that day
    ignacio_rows = df[df["Funcionário"] == "Ignacio"]
    for _, row in ignacio_rows.iterrows():
        avail = _IGNACIO_DISP.get(row["Dia"], "Indisponível")
        assert _in_window(row["Horário"], avail), (
            f"Ignacio assigned to {row['Dia']} {row['Horário']} "
            f"which is outside his availability '{avail}'"
        )

    # 3. Total hours within contract bounds
    ignacio_hours = _hours(df, "Ignacio")
    assert ignacio_hours >= 20.0, (
        f"Ignacio should reach 20 h minimum (got {ignacio_hours:.1f} h)"
    )
    assert ignacio_hours <= 26.0, (
        f"Ignacio must not exceed 26 h maximum (got {ignacio_hours:.1f} h)"
    )
