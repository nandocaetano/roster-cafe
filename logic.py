"""Business logic: shift-hour calculations, availability checks, and auto-scheduling."""
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
    # "Específico" availability: treat as available (manual override expected)
    return True


def gerar_escala_automatica(config_semana: dict, turnos_padrao: dict, margem_horas: float = 2.0) -> tuple:
    """Generate a constraint-compliant weekly roster and a list of warnings."""
    keyholder_roles = {"Manager", "Assistant Manager", "Head Barista"}
    output_columns = ["Dia", "Horário", "Funcionário"]
    warnings: list = []

    def parse_times(shift):
        matches = re.findall(r"(\d{1,2}):(\d{2})", str(shift))
        if len(matches) != 2:
            return None
        return (
            int(matches[0][0]) * 60 + int(matches[0][1]),
            int(matches[1][0]) * 60 + int(matches[1][1]),
        )

    def shift_hours(shift):
        times = parse_times(shift)
        if times is None:
            return 0.0
        start, end = times
        if end < start:
            end += 24 * 60
        return (end - start) / 60.0

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

    def available(employee, day, shift):
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
        value = availability.get(day, "Indisponível")
        value_text = str(value or "").strip()
        if value_text in ("Indisponível", "Folga", "Férias"):
            return False
        if value_text == "Livre":
            return True
        times = parse_times(shift)
        if times is None:
            return False
        start, end = times
        if end < start:
            end += 24 * 60
        if value_text == "Só Manhã":
            return start < 12 * 60 and end <= 14 * 60
        if value_text == "Só Tarde":
            return start >= 12 * 60
        specific = re.search(r"(\d{1,2}):(\d{2}).*?(\d{1,2}):(\d{2})", value_text)
        if specific:
            available_start = int(specific.group(1)) * 60 + int(specific.group(2))
            available_end = int(specific.group(3)) * 60 + int(specific.group(4))
            if available_end < available_start:
                available_end += 24 * 60
            return start >= available_start and end <= available_end
        return "Específico" in value_text

    employees = [
        name for name, data in config_semana.items()
        if bool(data.get("vai_trabalhar", True))
    ]

    minimum_hours = {
        name: max(0.0, numeric_value(config_semana[name],
            ("horas_min", "min_horas", "min_hours", "contract_min_hours"), 0.0))
        for name in employees
    }
    maximum_hours = {
        name: min(39.0, max(0.0, numeric_value(config_semana[name],
            ("horas_max", "max_horas", "max_hours", "contract_max_hours"), 39.0)))
        for name in employees
    }
    target_hours = {
        name: min(maximum_hours[name], max(minimum_hours[name],
            numeric_value(config_semana[name], ("horas_alvo", "target_hours"), 0.0)))
        for name in employees
    }

    assigned_hours = {name: 0.0 for name in employees}
    for name in employees:
        if config_semana[name].get("dias_treinamento"):
            assigned_hours[name] += numeric_value(config_semana[name], ("horas_treinamento",), 0.0)

    assigned_days: dict = {name: set() for name in employees}
    closing_by_day: dict = {}
    records: list = []

    days = list(turnos_padrao)
    previous_closing: set = set()
    prev_day_last_end: dict = {name: None for name in employees}

    for day in days:
        shifts = list(turnos_padrao[day])
        parsed_shifts = [(shift, parse_times(shift)) for shift in shifts]
        closing_shifts = [
            shift for shift, times in parsed_shifts
            if times is not None and times[1] > 17 * 60
        ]
        normal_shifts = [shift for shift in shifts if shift not in closing_shifts]
        ordered_shifts = closing_shifts + normal_shifts

        # Drop 08:00-16:00 when available staff count < number of shifts (staff shortage)
        _avail_today = sum(
            1 for emp in employees
            if day not in config_semana[emp].get('dias_folga', [])
            and day not in config_semana[emp].get('dias_ferias', [])
            and day not in config_semana[emp].get('dias_treinamento', [])
            and str(config_semana[emp].get('disponibilidade', {}).get(day, 'Indisponível'))
               not in ('Indisponível', 'Folga', 'Férias')
        )
        _MID_SHIFT = "08:00 - 16:00"
        if _avail_today < len(ordered_shifts) and _MID_SHIFT in shifts:
            warnings.append(
                f"{day}: turno 08:00-16:00 eliminado — {_avail_today} funcionários disponíveis "
                f"para {len(ordered_shifts)} turnos."
            )
            ordered_shifts = [s for s in ordered_shifts if s != _MID_SHIFT]

        assigned_today: set = set()
        closing_today: set = set()
        today_last_end: dict = {name: None for name in employees}
        novato_opening_today: bool = False
        novato_closing_today: bool = False

        for shift in ordered_shifts:
            times = parse_times(shift)
            duration = shift_hours(shift)
            is_closing = shift in closing_shifts
            is_opening = times is not None and times[0] < 9 * 60

            candidates = [
                employee for employee in employees
                if employee not in assigned_today
                and available(employee, day, shift)
                and assigned_hours[employee] + duration <= maximum_hours[employee] + 1e-9
                and not (is_opening and employee in previous_closing)
                and (not is_closing or str(config_semana[employee].get("cargo", "")) in keyholder_roles)
                and not (
                    times is not None
                    and prev_day_last_end[employee] is not None
                    and (24 * 60 - prev_day_last_end[employee]) + times[0] < 11 * 60
                )
                # Novato constraint: max 1 novato per opening block and per closing block
                and not (
                    str(config_semana[employee].get('nivel', 'experiente')).lower() == 'novato'
                    and is_opening and novato_opening_today
                )
                and not (
                    str(config_semana[employee].get('nivel', 'experiente')).lower() == 'novato'
                    and is_closing and novato_closing_today
                )
            ]

            if candidates:
                candidates.sort(
                    key=lambda e: (
                        # Priority 1: restricted availability employees first (they have fewer slots)
                        1 if str(config_semana[e].get('disponibilidade', {}).get(day, 'Livre') or '').strip()
                             not in ('Livre', '') else 0,
                        target_hours[e] - assigned_hours[e],
                        minimum_hours[e] - assigned_hours[e],
                        maximum_hours[e] - assigned_hours[e],
                    ),
                    reverse=True,
                )
                employee = candidates[0]
                assigned_hours[employee] += duration
                assigned_days[employee].add(day)
                assigned_today.add(employee)
                if is_closing:
                    closing_today.add(employee)
                # Track novato presence at opening/closing
                if str(config_semana[employee].get('nivel', 'experiente')).lower() == 'novato':
                    if is_opening:
                        novato_opening_today = True
                    if is_closing:
                        novato_closing_today = True
                if times is not None:
                    if today_last_end[employee] is None or times[1] > today_last_end[employee]:
                        today_last_end[employee] = times[1]
            else:
                employee = "A Preencher"
                reason = "nenhum funcionário elegível"
                if is_closing:
                    reason = "nenhum keyholder elegível"
                elif is_opening and previous_closing:
                    reason = "restrição de descanso/clopening"
                warnings.append(f"{day} - {shift}: turno não atribuído ({reason}).")

            records.append({"Dia": day, "Horário": shift, "Funcionário": employee})

        closing_by_day[day] = closing_today
        previous_closing = closing_today
        prev_day_last_end = today_last_end

    for employee in employees:
        total = assigned_hours[employee]
        if total + 1e-9 > maximum_hours[employee]:
            warnings.append(
                f"{employee}: limite semanal excedido "
                f"({total:.2f}h > {maximum_hours[employee]:.2f}h)."
            )
        elif total > target_hours[employee] + margem_horas + 1e-9:
            warnings.append(
                f"{employee}: horas acima da margem — {total:.1f}h "
                f"(Alvo: {target_hours[employee]:.0f}h + margem: {margem_horas:.0f}h)."
            )
        if total + 1e-9 < minimum_hours[employee]:
            warnings.append(
                f"{employee}: mínimo semanal não atingido "
                f"({total:.2f}h < {minimum_hours[employee]:.2f}h)."
            )
        elif total < target_hours[employee] - margem_horas - 1e-9:
            warnings.append(
                f"{employee}: horas abaixo da margem — {total:.1f}h "
                f"(Alvo: {target_hours[employee]:.0f}h - margem: {margem_horas:.0f}h)."
            )
        if len(assigned_days[employee]) == len(days):
            warnings.append(
                f"{employee}: WTI — {len(days)} dias consecutivos sem folga (mín. 1 dia de descanso/semana)."
            )

    for row in records:
        if row["Funcionário"] == "A Preencher":
            continue
        times = parse_times(row["Horário"])
        if times is None:
            continue
        duration_min = times[1] - times[0]
        if duration_min < 0:
            duration_min += 24 * 60
        if duration_min > 6 * 60:
            warnings.append(
                f"{row['Funcionário']} ({row['Dia']} {row['Horário']}): turno >6h — pausa de 30 min obrigatória (WTI)."
            )
        elif duration_min > 4 * 60 + 30:
            warnings.append(
                f"{row['Funcionário']} ({row['Dia']} {row['Horário']}): turno >4.5h — pausa de 15 min recomendada."
            )

    for day, shifts in turnos_padrao.items():
        for shift in shifts:
            times = parse_times(shift)
            if times is None or times[1] <= 17 * 60:
                continue
            assigned = next(
                (row["Funcionário"] for row in records
                 if row["Dia"] == day and row["Horário"] == shift),
                "A Preencher",
            )
            if (assigned == "A Preencher"
                    or str(config_semana.get(assigned, {}).get("cargo", "")) not in keyholder_roles):
                warnings.append(f"{day} - {shift}: regra de fechamento sem keyholder.")

    for index, day in enumerate(days[:-1]):
        next_day = days[index + 1]
        closing_employees = closing_by_day.get(day, set())
        if not closing_employees:
            continue
        for row in records:
            if row["Dia"] != next_day:
                continue
            times = parse_times(row["Horário"])
            if (times is not None and times[0] < 9 * 60
                    and row["Funcionário"] in closing_employees):
                warnings.append(
                    f"{row['Funcionário']}: clopening inválido entre {day} e {next_day}."
                )

    records.sort(
        key=lambda row: (
            days.index(row["Dia"]),
            turnos_padrao[row["Dia"]].index(row["Horário"]),
        )
    )

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
