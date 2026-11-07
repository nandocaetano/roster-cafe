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


def gerar_escala_automatica(config_semana: dict, turnos_padrao: dict, margem_horas: float = 2.0, slot_config: dict = None) -> tuple:
    """Generate a constraint-compliant weekly roster via OR-Tools CP-SAT solver."""
    from ortools.sat.python import cp_model

    keyholder_roles = {"Manager", "Assistant Manager", "Head Barista"}
    output_columns = ["Dia", "Horário", "Funcionário"]
    warnings: list = []

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

    # Build slot headcount and priority from slot_config
    # slot_config: {(day, shift): {"headcount": int, "priority": "essential"|"optional"}}
    _slot_hc: dict = {}
    _slot_opt: dict = {}
    for d in days:
        for s in turnos_padrao[d]:
            _cfg_s = (slot_config or {}).get((d, s), {})
            _slot_hc[d, s] = max(1, int(_cfg_s.get("headcount", 1)))
            _slot_opt[d, s] = _cfg_s.get("priority", "essential") == "optional"

    if not employees:
        records = [{"Dia": d, "Horário": s, "Funcionário": "A Preencher"}
                   for d in days for s in turnos_padrao[d]]
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
    unassigned = {}   # unassigned[d, s] = 1 iff no employee covers (d, s)

    for e in employees:
        for d in days:
            for s in turnos_padrao[d]:
                x[e, d, s] = model.NewBoolVar(f"x|{e}|{d}|{s}")

    for d in days:
        for s in turnos_padrao[d]:
            unassigned[d, s] = model.NewIntVar(0, _slot_hc[d, s], f"unassigned|{d}|{s}")

    # ── HARD CONSTRAINTS ─────────────────────────────────────────────────────

    # C1: Coverage — exactly headcount employees (shortfall tracked in unassigned)
    for d in days:
        for s in turnos_padrao[d]:
            model.Add(
                sum(x[e, d, s] for e in employees) + unassigned[d, s] == _slot_hc[d, s]
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

    # ── OBJECTIVE ────────────────────────────────────────────────────────────

    BIG_PENALTY      = 100_000  # essential slots — solver strongly avoids leaving unfilled
    OPTIONAL_PENALTY = 1_000    # optional slots — dropped first when understaffed

    unassigned_cost = sum(
        (OPTIONAL_PENALTY if _slot_opt[d, s] else BIG_PENALTY) * unassigned[d, s]
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

    # Soft: short shifts (<6h) prefer part-timers — penalise full-timers when a part-timer is available
    PARTTIME_AFFINITY = 500
    _parttimers = contract_groups.get("Part-time", [])
    _fulltimers  = contract_groups.get("Full-time", [])
    _affinity_terms = []
    for d in days:
        for s in turnos_padrao[d]:
            if duration_min(s) >= 6 * 60:
                continue
            if any(is_available(e, d, s) for e in _parttimers):
                for e in _fulltimers:
                    if is_available(e, d, s):
                        _affinity_terms.append(PARTTIME_AFFINITY * x[e, d, s])
    parttime_affinity_cost = sum(_affinity_terms) if _affinity_terms else 0

    model.Minimize(unassigned_cost + hour_deviation_cost + preference_cost + fairness_cost + parttime_affinity_cost)

    # ── SOLVE ────────────────────────────────────────────────────────────────

    status = solver.Solve(model)

    # ── EXTRACT SOLUTION ─────────────────────────────────────────────────────

    records = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for d in days:
            for s in turnos_padrao[d]:
                assigned_emps = [e for e in employees if solver.Value(x[e, d, s]) == 1]
                shortfall = solver.Value(unassigned[d, s])
                for e in assigned_emps:
                    records.append({"Dia": d, "Horário": s, "Funcionário": e})
                for _ in range(shortfall):
                    records.append({"Dia": d, "Horário": s, "Funcionário": "A Preencher"})
                if not assigned_emps and shortfall == 0:
                    records.append({"Dia": d, "Horário": s, "Funcionário": "A Preencher"})
    else:
        warnings.append(
            "CP-SAT: modelo infeasível com as constraints actuais — "
            "verifique disponibilidades, keyholder coverage e limites de horas."
        )
        for d in days:
            for s in turnos_padrao[d]:
                records.append({"Dia": d, "Horário": s, "Funcionário": "A Preencher"})

    # ── POST-SOLVE WARNINGS ──────────────────────────────────────────────────

    # Unassigned shifts (deduplicate by slot — headcount > 1 may produce multiple A Preencher rows)
    _warned_slots: set = set()
    for row in records:
        if row["Funcionário"] == "A Preencher":
            d, s = row["Dia"], row["Horário"]
            if (d, s) not in _warned_slots:
                reason = "nenhum keyholder elegível" if s in closing_shifts_by_day[d] else "nenhum funcionário elegível"
                warnings.append(f"{d} - {s}: turno não atribuído ({reason}).")
                _warned_slots.add((d, s))

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
    schedule_map: dict = {}
    for r in records:
        if r["Funcionário"] != "A Preencher":
            schedule_map.setdefault((r["Dia"], r["Horário"]), []).append(r["Funcionário"])
    for i, d in enumerate(days[:-1]):
        next_d = days[i + 1]
        for s_close in closing_shifts_by_day[d]:
            for worker in schedule_map.get((d, s_close), []):
                for s_open in opening_shifts_by_day[next_d]:
                    if worker in schedule_map.get((next_d, s_open), []):
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


def gerar_excel_escala(roster_df: pd.DataFrame, config_semana: dict = None,
                        cafe_nome: str = "Café", semana_label: str = "") -> bytes:
    """Excel export with two sheets: shift grid + per-employee hour summary (Nati's layout)."""
    import io as _io
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return b""

    wb = Workbook()
    ws = wb.active
    ws.title = "Escala"
    ws_res = wb.create_sheet("Resumo de Horas")

    days = list(dict.fromkeys(roster_df["Dia"].tolist()))

    day_data: dict = {d: [] for d in days}
    for _, row in roster_df.iterrows():
        day_data[row["Dia"]].append((row["Horário"], row["Funcionário"]))

    DAY_FILL   = PatternFill("solid", fgColor="2D2D2D")
    SHIFT_FILL = PatternFill("solid", fgColor="4A6FA5")
    ALT_FILL   = PatternFill("solid", fgColor="EAF2FB")
    WHT_FILL   = PatternFill("solid", fgColor="FFFFFF")
    HDR_FILL   = PatternFill("solid", fgColor="3A5F8C")
    white_bold = Font(bold=True, color="FFFFFF")
    center     = Alignment(horizontal="center", vertical="center")

    def _border():
        s = Side(style="thin", color="CCCCCC")
        return Border(left=s, right=s, top=s, bottom=s)

    # ── Sheet 1: Shift grid ──────────────────────────────────────────────────
    total_cols_ws = max(1, 1 + len(days) * 3)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols_ws)
    tc = ws.cell(row=1, column=1, value=f"{cafe_nome} — Escala da Semana")
    tc.font = Font(bold=True, size=14); tc.alignment = center
    if semana_label:
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=total_cols_ws)
        ws.cell(row=2, column=1, value=semana_label).alignment = center

    HDR_ROW, SUB_ROW, DATA_START = 3, 4, 5
    ws.column_dimensions["A"].width = 3

    for i, day in enumerate(days):
        col_sh = 2 + i * 3
        col_st = col_sh + 1
        ws.merge_cells(start_row=HDR_ROW, start_column=col_sh,
                       end_row=HDR_ROW, end_column=col_st)
        dc = ws.cell(row=HDR_ROW, column=col_sh, value=day.upper())
        dc.font = white_bold; dc.fill = DAY_FILL; dc.alignment = center
        for col, lbl in ((col_sh, "Turno"), (col_st, "Colaborador")):
            sc2 = ws.cell(row=SUB_ROW, column=col, value=lbl)
            sc2.font = white_bold; sc2.fill = SHIFT_FILL; sc2.alignment = center
        ws.column_dimensions[get_column_letter(col_sh)].width = 24
        ws.column_dimensions[get_column_letter(col_st)].width = 22
        ws.column_dimensions[get_column_letter(col_st + 1)].width = 2

        for r_idx, (shift, name) in enumerate(day_data[day]):
            rn = DATA_START + r_idx
            bg = ALT_FILL if r_idx % 2 == 0 else WHT_FILL
            for col, val in ((col_sh, shift), (col_st, name)):
                cell = ws.cell(row=rn, column=col, value=val)
                cell.fill = bg; cell.border = _border()

    # ── Sheet 2: Employee hour summary ───────────────────────────────────────
    hours_lookup: dict = {}
    for _, row in roster_df.iterrows():
        name = row["Funcionário"]
        if name == "A Preencher":
            continue
        h = calcular_horas_turno(str(row["Horário"]))
        key = (name, row["Dia"])
        hours_lookup[key] = hours_lookup.get(key, 0.0) + h

    if config_semana:
        emps = [n for n, d in config_semana.items() if d.get("vai_trabalhar", True)]
    else:
        seen: set = set()
        emps = []
        for n in roster_df["Funcionário"]:
            if n != "A Preencher" and n not in seen:
                seen.add(n); emps.append(n)

    ws_res.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(days) + 2)
    res_title = ws_res.cell(row=1, column=1, value=f"{cafe_nome} — Resumo de Horas")
    res_title.font = Font(bold=True, size=13); res_title.alignment = center

    ws_res.cell(row=2, column=1, value="Colaborador").font = white_bold
    ws_res.cell(row=2, column=1).fill = HDR_FILL
    ws_res.cell(row=2, column=1).alignment = center
    ws_res.column_dimensions["A"].width = 24
    for i, day in enumerate(days):
        c = ws_res.cell(row=2, column=2 + i, value=day)
        c.font = white_bold; c.fill = HDR_FILL; c.alignment = center
        ws_res.column_dimensions[get_column_letter(2 + i)].width = 10
    tot_col = 2 + len(days)
    ws_res.cell(row=2, column=tot_col, value="Total").font = white_bold
    ws_res.cell(row=2, column=tot_col).fill = HDR_FILL
    ws_res.cell(row=2, column=tot_col).alignment = center
    ws_res.column_dimensions[get_column_letter(tot_col)].width = 10

    for r_idx, emp in enumerate(emps):
        rn = 3 + r_idx
        bg = ALT_FILL if r_idx % 2 == 0 else WHT_FILL
        ws_res.cell(row=rn, column=1, value=emp).fill = bg
        total = 0.0
        for i, day in enumerate(days):
            h = hours_lookup.get((emp, day), 0.0)
            cell = ws_res.cell(row=rn, column=2 + i, value=round(h, 2) if h else "")
            cell.fill = bg; cell.border = _border(); cell.alignment = center
            total += h
        tc3 = ws_res.cell(row=rn, column=tot_col, value=round(total, 2))
        tc3.fill = bg; tc3.border = _border(); tc3.alignment = center
        tc3.font = Font(bold=True)

    buf = _io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
