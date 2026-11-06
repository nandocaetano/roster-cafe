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


def gerar_escala_automatica(config_semana: dict, turnos_padrao: dict, margem_horas: float = 2.0) -> tuple:
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
            unassigned[d, s] = model.NewBoolVar(f"unassigned|{d}|{s}")

    # ── HARD CONSTRAINTS ─────────────────────────────────────────────────────

    # C1: Coverage — exactly 1 employee OR explicitly unassigned
    for d in days:
        for s in turnos_padrao[d]:
            model.Add(
                sum(x[e, d, s] for e in employees) + unassigned[d, s] == 1
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

    BIG_PENALTY = 100_000  # strongly prefer filling every shift

    unassigned_cost = sum(BIG_PENALTY * unassigned[d, s]
                          for d in days for s in turnos_padrao[d])

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

    model.Minimize(unassigned_cost + hour_deviation_cost + preference_cost + fairness_cost)

    # ── SOLVE ────────────────────────────────────────────────────────────────

    status = solver.Solve(model)

    # ── EXTRACT SOLUTION ─────────────────────────────────────────────────────

    records = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for d in days:
            for s in turnos_padrao[d]:
                assigned = "A Preencher"
                for e in employees:
                    if solver.Value(x[e, d, s]) == 1:
                        assigned = e
                        break
                records.append({"Dia": d, "Horário": s, "Funcionário": assigned})
    else:
        warnings.append(
            "CP-SAT: modelo infeasível com as constraints actuais — "
            "verifique disponibilidades, keyholder coverage e limites de horas."
        )
        for d in days:
            for s in turnos_padrao[d]:
                records.append({"Dia": d, "Horário": s, "Funcionário": "A Preencher"})

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
