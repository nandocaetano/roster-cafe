"""Business logic: shift-hour calculations, availability checks, CP-SAT scheduler, PDF export."""
import re
from datetime import datetime

import pandas as pd


def calcular_horas_turno(turno_str):
    """Return the duration in hours for a shift string like '07:00 - 14:00 (Fechamento)'."""
    matches = re.findall(r'(\d{1,2}:\d{2})', turno_str)
    if len(matches) == 2:
        fmt = '%H:%M'
        t1 = datetime.strptime(matches[0], fmt)
        t2 = datetime.strptime(matches[1], fmt)
        return (t2 - t1).total_seconds() / 3600
    return 0


def pode_trabalhar(nome, turno_str, dia, config_semana):
    """
    Return True if the employee can be assigned to turno_str on dia,
    based on their availability entry in config_semana.
    """
    disp = config_semana[nome]["disponibilidade"].get(dia, "Indisponível")
    if disp == "Indisponível":
        return False
    if disp == "Livre":
        return True
    if disp == "Só Manhã" and "Fechamento" in turno_str:
        return False
    if disp == "Só Manhã":
        return True
    if disp == "Só Tarde" and int(turno_str[0:2]) < 12:
        return False
    if disp == "Só Tarde":
        return True
    return True


def gerar_escala_automatica(
    config_semana: dict,
    turnos_padrao: dict,
    margem_horas: float = 2.0,
    headcount_por_turno: dict | None = None,
) -> tuple:
    """Generate a constraint-compliant weekly roster via OR-Tools CP-SAT solver."""
    from ortools.sat.python import cp_model

    keyholder_roles = {"Manager", "Assistant Manager", "Head Barista"}
    output_columns = ["Dia", "Horário", "Funcionário"]
    warnings: list = []
    headcount_por_turno = headcount_por_turno or {}

    # ── helpers ──────────────────────────────────────────────────────────────

    def parse_times(shift):
        m = re.findall(r"(\d{1,2}):(\d{2})", str(shift))
        if len(m) != 2:
            return None
        return (int(m[0][0]) * 60 + int(m[0][1]), int(m[1][0]) * 60 + int(m[1][1]))

    def duration_min(shift):
        t = parse_times(shift)
        if t is None:
            return 0
        d = t[1] - t[0]
        return d + 24 * 60 if d < 0 else d

    def required_headcount(day, shift):
        value = headcount_por_turno.get((day, shift), headcount_por_turno.get(f"{day}|{shift}", 1))
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 1

    def is_optional_shift(shift):
        times = parse_times(shift)
        return bool(times and times == (8 * 60, 16 * 60))

    def is_short_priority_shift(shift):
        times = parse_times(shift)
        return bool(times and times in {
            (7 * 60, 12 * 60),
            (14 * 60, 18 * 60 + 15),
        })

    def numeric_value(data, keys, default):
        for key in keys:
            value = data.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            try:
                if value is not None:
                    return float(str(value).replace(",", "."))
            except (TypeError, ValueError):
                continue
        return default

    def is_available(employee, day, shift):
        """Return True if employee can work shift on day (respects all override flags)."""
        data = config_semana[employee]
        if day in data.get("dias_folga", []):
            return False
        if day in data.get("dias_ferias", []):
            return False
        if day in data.get("dias_treinamento", []):
            return False
        availability = data.get("disponibilidade", {})
        if not isinstance(availability, dict):
            return False
        value_text = str(availability.get(day, "Indisponível") or "").strip()
        if value_text in ("Indisponível", "Folga", "Férias"):
            return False
        if value_text == "Livre":
            return True
        t = parse_times(shift)
        if t is None:
            return False
        start, end = t
        if value_text == "Só Manhã":
            return start < 12 * 60 and end <= 14 * 60
        if value_text == "Só Tarde":
            return start >= 12 * 60
        specific = re.search(r"(\d{1,2}):(\d{2}).*?(\d{1,2}):(\d{2})", value_text)
        if specific:
            av_start = int(specific.group(1)) * 60 + int(specific.group(2))
            av_end   = int(specific.group(3)) * 60 + int(specific.group(4))
            if av_end < av_start:
                av_end += 24 * 60
            return start >= av_start and end <= av_end
        return "Específico" in value_text

    # ── employee pools ────────────────────────────────────────────────────────

    employees = [n for n, d in config_semana.items() if bool(d.get("vai_trabalhar", True))]
    days = list(turnos_padrao)

    if not employees:
        records = [
            {"Dia": d, "Horário": s, "Funcionário": "A Preencher"}
            for d in days
            for s in turnos_padrao[d]
            for _ in range(required_headcount(d, s))
        ]
        warnings.append("Nenhum funcionário escalado para esta semana.")
        return pd.DataFrame(records, columns=output_columns), warnings

    def _fval(e, keys, default):
        return numeric_value(config_semana[e], keys, default)

    minimum_hours  = {e: max(0.0, _fval(e, ("horas_min",), 0.0)) for e in employees}
    maximum_hours  = {e: min(60.0, max(0.0, _fval(e, ("horas_max",), 39.0))) for e in employees}
    target_hours   = {
        e: min(maximum_hours[e], max(minimum_hours[e], _fval(e, ("horas_alvo",), 0.0)))
        for e in employees
    }
    training_min   = {
        e: int(_fval(e, ("horas_treinamento",), 0.0) * 60)
        if config_semana[e].get("dias_treinamento") else 0
        for e in employees
    }
    novato_emps    = [e for e in employees
                      if str(config_semana[e].get("nivel", "experiente")).lower() == "novato"]

    # Preference and contract grouping — consumed by soft objectives below
    preferencia = {
        e: str(config_semana[e].get("preferencia_turno", "Sem preferência") or "Sem preferência")
        for e in employees
    }
    contract_groups: dict = {}
    for e in employees:
        ct = str(config_semana[e].get("tipo_contrato", "Full-time") or "Full-time")
        contract_groups.setdefault(ct, []).append(e)

    # Classify shifts once
    closing_shifts_by_day = {}
    opening_shifts_by_day = {}
    for d in days:
        closing_shifts_by_day[d] = [s for s in turnos_padrao[d]
                                     if (lambda t: t and t[1] > 17 * 60)(parse_times(s))]
        opening_shifts_by_day[d] = [s for s in turnos_padrao[d]
                                     if (lambda t: t and t[0] < 9 * 60)(parse_times(s))]

    # ── CP-SAT model ──────────────────────────────────────────────────────────

    model  = cp_model.CpModel()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0

    # Decision variables
    x          = {}   # x[e, d, s] = 1 iff employee e works shift s on day d
    shortfall = {}    # shortfall[d, s] = uncovered headcount for the shift

    for e in employees:
        for d in days:
            for s in turnos_padrao[d]:
                x[e, d, s] = model.NewBoolVar(f"x|{e}|{d}|{s}")

    for d in days:
        for s in turnos_padrao[d]:
            shortfall[d, s] = model.NewIntVar(
                0, required_headcount(d, s), f"shortfall|{d}|{s}"
            )

    # ── HARD CONSTRAINTS ─────────────────────────────────────────────────────

    # C1: Coverage — meet the configured headcount or expose a shortfall.
    for d in days:
        for s in turnos_padrao[d]:
            model.Add(
                sum(x[e, d, s] for e in employees) + shortfall[d, s] == required_headcount(d, s)
            )

    # C2: Availability — forbid unavailable assignments
    for e in employees:
        for d in days:
            for s in turnos_padrao[d]:
                if not is_available(e, d, s):
                    model.Add(x[e, d, s] == 0)

    # C3: One shift per employee per day
    for e in employees:
        for d in days:
            model.Add(sum(x[e, d, s] for s in turnos_padrao[d]) <= 1)

    # C4: Contract max hours (minutes arithmetic to stay integer)
    for e in employees:
        assigned_min_expr = sum(
            duration_min(s) * x[e, d, s]
            for d in days
            for s in turnos_padrao[d]
        )
        model.Add(assigned_min_expr + training_min[e] <= int(maximum_hours[e] * 60))

    # C5: Keyholder on closing shifts
    for d in days:
        for s in closing_shifts_by_day[d]:
            for e in employees:
                if str(config_semana[e].get("cargo", "")) not in keyholder_roles:
                    model.Add(x[e, d, s] == 0)

    # C6: WTI clopening — 11h rest between close and next-day open
    for i, d in enumerate(days[:-1]):
        next_d = days[i + 1]
        for e in employees:
            for s_close in closing_shifts_by_day[d]:
                t_close = parse_times(s_close)
                for s_open in opening_shifts_by_day[next_d]:
                    t_open = parse_times(s_open)
                    if t_close and t_open:
                        gap = (24 * 60 - t_close[1]) + t_open[0]
                        if gap < 11 * 60:
                            model.Add(x[e, d, s_close] + x[e, next_d, s_open] <= 1)

    # C7: Novato constraint — max 1 novato per opening block and per closing block per day
    if novato_emps:
        for d in days:
            if opening_shifts_by_day[d]:
                model.Add(
                    sum(x[e, d, s]
                        for e in novato_emps
                        for s in opening_shifts_by_day[d]) <= 1
                )
            if closing_shifts_by_day[d]:
                model.Add(
                    sum(x[e, d, s]
                        for e in novato_emps
                        for s in closing_shifts_by_day[d]) <= 1
                )

    # Prefer the default five working days and two rest days without making it hard.
    workday = {}
    for e in employees:
        for d in days:
            workday[e, d] = model.NewBoolVar(f"workday|{e}|{d}")
            assigned_that_day = sum(x[e, d, s] for s in turnos_padrao[d])
            model.Add(assigned_that_day <= workday[e, d] * len(turnos_padrao[d]))
            model.Add(assigned_that_day >= workday[e, d])

    # ── OBJECTIVE ────────────────────────────────────────────────────────────

    BIG_PENALTY = 100_000  # strongly prefer filling every required slot

    shortfall_cost = sum(
        (1 if is_optional_shift(s) else BIG_PENALTY) * shortfall[d, s]
        for d in days for s in turnos_padrao[d]
    )

    # Deviation from target hours (absolute value via over/under split)
    over_vars  = {}
    under_vars = {}
    for e in employees:
        target_m = int(target_hours[e] * 60)
        max_dev  = int(maximum_hours[e] * 60) + 10  # generous upper bound
        over_vars[e]  = model.NewIntVar(0, max_dev, f"over|{e}")
        under_vars[e] = model.NewIntVar(0, max_dev, f"under|{e}")
        assigned_expr = sum(
            duration_min(s) * x[e, d, s]
            for d in days
            for s in turnos_padrao[d]
        )
        # assigned + training - target = over - under
        model.Add(assigned_expr + training_min[e] - target_m == over_vars[e] - under_vars[e])

    hour_deviation_cost = sum(over_vars[e] + under_vars[e] for e in employees)

    # Soft: shift preference penalty (Timefold-inspired REA, Add-on B)
    # PREF_PENALTY << BIG_PENALTY so hard constraints (C1-C7) always dominate.
    PREF_PENALTY = 60
    preference_cost_terms = []
    for e in employees:
        pref = preferencia[e]
        if pref == "Sem preferência":
            continue
        for d in days:
            for s in turnos_padrao[d]:
                t = parse_times(s)
                if t is None:
                    continue
                is_morning = t[0] < 12 * 60
                if (pref == "Manhã" and not is_morning) or (pref == "Tarde" and is_morning):
                    preference_cost_terms.append(PREF_PENALTY * x[e, d, s])
    preference_cost = sum(preference_cost_terms) if preference_cost_terms else 0

    # Small shifts are preferred for part-time employees, as requested in the reference.
    PART_TIME_PENALTY = 180
    short_shift_cost_terms = []
    for e in employees:
        contract = str(config_semana[e].get("tipo_contrato", "Full-time") or "Full-time").lower()
        if "part" in contract:
            continue
        for d in days:
            for s in turnos_padrao[d]:
                if is_short_priority_shift(s):
                    short_shift_cost_terms.append(PART_TIME_PENALTY * x[e, d, s])
    short_shift_cost = sum(short_shift_cost_terms) if short_shift_cost_terms else 0

    days_target_cost_terms = []
    for e in employees:
        worked_days = sum(workday[e, d] for d in days)
        days_over = model.NewIntVar(0, len(days), f"days_over|{e}")
        days_under = model.NewIntVar(0, len(days), f"days_under|{e}")
        model.Add(worked_days - 5 == days_over - days_under)
        days_target_cost_terms.append(15 * (days_over + days_under))
    days_target_cost = sum(days_target_cost_terms) if days_target_cost_terms else 0

    # Soft: fairness score — minimize hour spread within same contract type (Timefold-inspired REA, Add-on A)
    # max_g/min_g auxiliary vars bound the spread; solver minimises it at FAIRNESS_WEIGHT per minute.
    FAIRNESS_WEIGHT = 10
    fairness_cost_terms = []
    _max_min = max(int(maximum_hours[e] * 60) for e in employees) + 10
    for ct, group in contract_groups.items():
        if len(group) < 2:
            continue
        max_g  = model.NewIntVar(0, _max_min, f"max_g|{ct}")
        min_g  = model.NewIntVar(0, _max_min, f"min_g|{ct}")
        spread = model.NewIntVar(0, _max_min, f"spread|{ct}")
        for e in group:
            _assigned_m = sum(duration_min(s) * x[e, d, s] for d in days for s in turnos_padrao[d])
            model.Add(max_g >= _assigned_m + training_min[e])
            model.Add(min_g <= _assigned_m + training_min[e])
        model.Add(spread == max_g - min_g)
        fairness_cost_terms.append(FAIRNESS_WEIGHT * spread)
    fairness_cost = sum(fairness_cost_terms) if fairness_cost_terms else 0

    model.Minimize(
        shortfall_cost
        + hour_deviation_cost
        + preference_cost
        + short_shift_cost
        + days_target_cost
        + fairness_cost
    )

    # ── SOLVE ────────────────────────────────────────────────────────────────

    status = solver.Solve(model)

    # ── EXTRACT SOLUTION ─────────────────────────────────────────────────────

    records = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for d in days:
            for s in turnos_padrao[d]:
                records.extend(
                    {"Dia": d, "Horário": s, "Funcionário": e}
                    for e in employees
                    if solver.Value(x[e, d, s]) == 1
                )
                records.extend(
                    {"Dia": d, "Horário": s, "Funcionário": "A Preencher"}
                    for _ in range(solver.Value(shortfall[d, s]))
                )
    else:
        warnings.append(
            "CP-SAT: modelo infeasível com as constraints actuais — "
            "verifique disponibilidades, keyholder coverage e limites de horas."
        )
        for d in days:
            for s in turnos_padrao[d]:
                records.extend(
                    {"Dia": d, "Horário": s, "Funcionário": "A Preencher"}
                    for _ in range(required_headcount(d, s))
                )

    # ── POST-SOLVE WARNINGS ──────────────────────────────────────────────────

    # Unassigned shifts
    for row in records:
        if row["Funcionário"] == "A Preencher":
            d, s = row["Dia"], row["Horário"]
            reason = "nenhum keyholder elegível" if s in closing_shifts_by_day[d] else "nenhum funcionário elegível"
            warnings.append(f"{d} - {s}: turno não atribuído ({reason}).")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return pd.DataFrame(records, columns=output_columns), warnings

    # Compute final assigned hours per employee for downstream warnings
    assigned_hours = {e: 0.0 for e in employees}
    for row in records:
        e = row["Funcionário"]
        if e in assigned_hours:
            assigned_hours[e] += duration_min(row["Horário"]) / 60.0

    for e in employees:
        total = assigned_hours[e] + training_min[e] / 60.0
        # Use 0.05h (3 min) tolerance to avoid false positives when solver hits exactly max
        if total > maximum_hours[e] + 0.05:
            warnings.append(
                f"{e}: limite semanal excedido ({total:.2f}h > {maximum_hours[e]:.2f}h)."
            )
        elif total > target_hours[e] + margem_horas + 1e-9:
            warnings.append(
                f"{e}: horas acima da margem — {total:.1f}h "
                f"(Alvo: {target_hours[e]:.0f}h + margem: {margem_horas:.0f}h)."
            )
        if total + 1e-9 < minimum_hours[e]:
            warnings.append(
                f"{e}: mínimo semanal não atingido ({total:.2f}h < {minimum_hours[e]:.2f}h)."
            )
        elif total < target_hours[e] - margem_horas - 1e-9:
            warnings.append(
                f"{e}: horas abaixo da margem — {total:.1f}h "
                f"(Alvo: {target_hours[e]:.0f}h - margem: {margem_horas:.0f}h)."
            )

    # WTI: 7 consecutive days
    assigned_days = {e: set() for e in employees}
    for row in records:
        if row["Funcionário"] in assigned_days:
            assigned_days[row["Funcionário"]].add(row["Dia"])
    for e in employees:
        if len(assigned_days[e]) == len(days):
            warnings.append(
                f"{e}: WTI — {len(days)} dias consecutivos sem folga (mín. 1 dia de descanso/semana)."
            )

    # WTI break warnings — one summary line each instead of one per shift
    wti_30 = sum(
        1 for row in records
        if row["Funcionário"] != "A Preencher" and duration_min(row["Horário"]) > 6 * 60
    )
    wti_15 = sum(
        1 for row in records
        if row["Funcionário"] != "A Preencher"
        and 4 * 60 + 30 < duration_min(row["Horário"]) <= 6 * 60
    )
    if wti_30:
        warnings.append(
            f"WTI pausas: {wti_30} turno(s) >6h — pausa de 30 min obrigatória por lei."
        )
    if wti_15:
        warnings.append(
            f"WTI pausas: {wti_15} turno(s) entre 4.5h–6h — pausa de 15 min recomendada."
        )

    # Keyholder on closing check (post-solve verification)
    for row in records:
        d, s = row["Dia"], row["Horário"]
        if s not in closing_shifts_by_day[d]:
            continue
        assigned = row["Funcionário"]
        if assigned == "A Preencher":
            continue
        if str(config_semana.get(assigned, {}).get("cargo", "")) not in keyholder_roles:
            warnings.append(f"{d} - {s}: regra de fechamento sem keyholder.")

    # Clopening cross-day post-solve verification
    schedule_map = {(r["Dia"], r["Horário"]): r["Funcionário"] for r in records}
    for i, d in enumerate(days[:-1]):
        next_d = days[i + 1]
        for s_close in closing_shifts_by_day[d]:
            worker = schedule_map.get((d, s_close), "A Preencher")
            if worker == "A Preencher":
                continue
            for s_open in opening_shifts_by_day[next_d]:
                if schedule_map.get((next_d, s_open)) == worker:
                    t_close = parse_times(s_close)
                    t_open  = parse_times(s_open)
                    if t_close and t_open:
                        gap = (24 * 60 - t_close[1]) + t_open[0]
                        if gap < 11 * 60:
                            warnings.append(
                                f"{worker}: clopening inválido entre {d} e {next_d}."
                            )

    # Solver status note
    if status == cp_model.OPTIMAL:
        warnings.append(f"CP-SAT: solução ÓPTIMA encontrada em {solver.WallTime():.2f}s.")
    elif status == cp_model.FEASIBLE:
        warnings.append(f"CP-SAT: solução VIÁVEL (não óptima) encontrada em {solver.WallTime():.2f}s.")

    # Sort to match turnos_padrao order
    records.sort(key=lambda r: (days.index(r["Dia"]), turnos_padrao[r["Dia"]].index(r["Horário"])))

    return pd.DataFrame(records, columns=output_columns), warnings


def gerar_pdf_escala(roster_df, cafe_nome: str = "Café", semana_label: str = "") -> bytes:
    """Return a printable PDF of the roster as raw bytes (landscape A4)."""
    from fpdf import FPDF

    def _l(s: str) -> str:
        return str(s).encode('latin-1', 'replace').decode('latin-1')

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    pdf.set_font("Arial", "B", 15)
    pdf.cell(0, 9, _l(f"{cafe_nome} — Escala da Semana"), ln=True, align='C')
    if semana_label:
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 7, _l(semana_label), ln=True, align='C')
    pdf.ln(4)

    w_dia, w_hora, w_func = 28, 72, 90
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    for w, h in ((w_dia, "Dia"), (w_hora, "Horario"), (w_func, "Funcionario")):
        pdf.cell(w, 8, h, border=1, fill=True, align='C')
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)

    last_day, shade = None, False
    for _, row in roster_df.iterrows():
        if row['Dia'] != last_day:
            shade = not shade
            last_day = row['Dia']
        pdf.set_fill_color(235, 245, 255) if shade else pdf.set_fill_color(255, 255, 255)
        pdf.cell(w_dia, 7, _l(row['Dia']), border=1, fill=True)
        pdf.cell(w_hora, 7, _l(row['Horário']), border=1, fill=True)
        pdf.cell(w_func, 7, _l(row['Funcionário']), border=1, fill=True)
        pdf.ln()

    result = pdf.output(dest='S')
    return result.encode('latin-1') if isinstance(result, str) else bytes(result)


def gerar_excel_escala(
    roster_df,
    cafe_nome: str = "Café",
    semana_label: str = "",
    headcount_por_turno: dict | None = None,
) -> bytes:
    """Return a styled workbook with the weekly roster and per-person hour totals."""
    from io import BytesIO
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.page import PageMargins

    headcount_por_turno = headcount_por_turno or {}
    day_order = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    day_labels = {
        "Seg": "SEGUNDA-FEIRA", "Ter": "TERÇA-FEIRA", "Qua": "QUARTA-FEIRA",
        "Qui": "QUINTA-FEIRA", "Sex": "SEXTA-FEIRA", "Sáb": "SÁBADO", "Dom": "DOMINGO",
    }
    rows = roster_df.to_dict("records") if hasattr(roster_df, "to_dict") else list(roster_df)
    by_day = {day: [] for day in day_order}
    for row in rows:
        day = str(row.get("Dia", ""))
        if day in by_day:
            by_day[day].append(row)

    def shift_hours(shift):
        return calcular_horas_turno(str(shift))

    def styled_shift(shift):
        return f"{shift}\n{shift_hours(shift):.1f}h"

    wb = Workbook()
    ws = wb.active
    ws.title = "Escala semanal"
    purple = "4B2A82"
    violet = "7C3AED"
    light = "F3EEFF"
    rule = Side(style="thin", color="D9D0EA")
    border = Border(left=rule, right=rule, top=rule, bottom=rule)

    ws.merge_cells("A1:N1")
    ws["A1"] = f"{cafe_nome} — Escala semanal"
    ws["A1"].font = Font(name="Arial", size=18, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=purple)
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.merge_cells("A2:N2")
    ws["A2"] = semana_label or "Turnos e horas planeadas"
    ws["A2"].font = Font(name="Arial", size=11, italic=True, color="5E5375")
    ws["A2"].alignment = Alignment(horizontal="center")

    header_row, subheader_row = 4, 5
    for day_index, day in enumerate(day_order):
        start_col = 1 + day_index * 2
        end_col = start_col + 1
        ws.merge_cells(start_row=header_row, start_column=start_col, end_row=header_row, end_column=end_col)
        cell = ws.cell(header_row, start_col, day_labels[day])
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=violet)
        cell.alignment = Alignment(horizontal="center")
        for col, label in ((start_col, "Shift"), (end_col, "Staff")):
            sub = ws.cell(subheader_row, col, label)
            sub.font = Font(bold=True, color="FFFFFF")
            sub.fill = PatternFill("solid", fgColor=purple)
            sub.alignment = Alignment(horizontal="center")

    max_rows = max((len(by_day[day]) for day in day_order), default=0)
    for row_offset in range(max_rows):
        excel_row = subheader_row + 1 + row_offset
        for day_index, day in enumerate(day_order):
            start_col = 1 + day_index * 2
            day_rows = by_day[day]
            if row_offset < len(day_rows):
                shift = str(day_rows[row_offset].get("Horário", ""))
                staff = str(day_rows[row_offset].get("Funcionário", ""))
                ws.cell(excel_row, start_col, styled_shift(shift))
                ws.cell(excel_row, start_col + 1, staff)
            for col in (start_col, start_col + 1):
                cell = ws.cell(excel_row, col)
                cell.border = border
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if row_offset % 2 == 0:
                    cell.fill = PatternFill("solid", fgColor=light)

    summary_start = subheader_row + max_rows + 3
    ws.cell(summary_start, 1, "Horas por funcionário")
    ws.cell(summary_start, 1).font = Font(size=13, bold=True, color=purple)
    summary_header = summary_start + 1
    headers = ["Funcionário"]
    for day in day_order:
        headers.extend([day_labels[day].title(), "Horas"])
    headers.append("Total semana")
    for col, header in enumerate(headers, 1):
        cell = ws.cell(summary_header, col, header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=purple)
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = border

    staff_names = sorted({
        str(row.get("Funcionário")) for row in rows
        if row.get("Funcionário") and row.get("Funcionário") != "A Preencher"
    })
    for staff_index, staff in enumerate(staff_names, summary_header + 1):
        ws.cell(staff_index, 1, staff)
        weekly_total = 0.0
        for day_index, day in enumerate(day_order):
            assigned = [
                str(row.get("Horário", "")) for row in by_day[day]
                if str(row.get("Funcionário", "")) == staff
            ]
            hours = sum(shift_hours(shift) for shift in assigned)
            weekly_total += hours
            col = 2 + day_index * 2
            ws.cell(staff_index, col, "\n".join(assigned) or "—")
            ws.cell(staff_index, col + 1, round(hours, 2))
        ws.cell(staff_index, 16, round(weekly_total, 2))
        for col in range(1, 17):
            cell = ws.cell(staff_index, col)
            cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    coverage_start = summary_header + len(staff_names) + 3
    ws.cell(coverage_start, 1, "Cobertura por turno")
    ws.cell(coverage_start, 1).font = Font(size=13, bold=True, color=purple)
    coverage_header = coverage_start + 1
    for col, header in enumerate(["Dia", "Shift", "Necessário", "Atribuído", "Em falta"], 1):
        cell = ws.cell(coverage_header, col, header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=purple)
        cell.border = border
    coverage_keys = []
    for row in rows:
        key = (str(row.get("Dia", "")), str(row.get("Horário", "")))
        if key not in coverage_keys:
            coverage_keys.append(key)
    for row_index, (day, shift) in enumerate(coverage_keys, coverage_header + 1):
        key = (day, shift)
        required = headcount_por_turno.get(key, headcount_por_turno.get(f"{day}|{shift}", 1))
        assigned = sum(1 for candidate in rows if candidate.get("Dia") == day and candidate.get("Horário") == shift and candidate.get("Funcionário") != "A Preencher")
        missing = max(0, int(required) - assigned)
        values = [day, shift, int(required), assigned, missing]
        for col, value in enumerate(values, 1):
            cell = ws.cell(row_index, col, value)
            cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    widths = {1: 24, 2: 22, 3: 20, 4: 22, 5: 20, 6: 22, 7: 20, 8: 22, 9: 20, 10: 22, 11: 20, 12: 22, 13: 20, 14: 22, 15: 20, 16: 16}
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = "A6"
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_margins = PageMargins(left=0.25, right=0.25, top=0.5, bottom=0.5)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()
