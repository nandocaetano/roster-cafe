"""Business logic: shift-hour calculations, availability checks, and auto-scheduling."""
import re
from datetime import datetime

import pandas as pd


def calcular_horas_turno(turno_str):
    """Return the duration in hours for a shift string like '07:00 - 14:00 (Fecho)'."""
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
    if disp == "Só Manhã" and "Fecho" in turno_str:
        return False
    if disp == "Só Manhã":
        return True
    if disp == "Só Tarde" and int(turno_str[0:2]) < 12:
        return False
    if disp == "Só Tarde":
        return True
    # "Específico" availability: treat as available (manual override expected)
    return True


def gerar_escala_automatica(config_semana: dict, turnos_padrao: dict) -> tuple:
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
        availability = data.get("disponibilidade", {})
        if not isinstance(availability, dict):
            return False
        value = availability.get(day, "Indisponível")
        value_text = str(value or "").strip()
        if value_text == "Indisponível":
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
    assigned_days: dict = {name: set() for name in employees}
    closing_by_day: dict = {}
    records: list = []

    days = list(turnos_padrao)
    previous_closing: set = set()

    for day in days:
        shifts = list(turnos_padrao[day])
        parsed_shifts = [(shift, parse_times(shift)) for shift in shifts]
        closing_shifts = [
            shift for shift, times in parsed_shifts
            if times is not None and times[1] > 17 * 60
        ]
        normal_shifts = [shift for shift in shifts if shift not in closing_shifts]
        ordered_shifts = closing_shifts + normal_shifts

        assigned_today: set = set()
        closing_today: set = set()

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
            ]

            if candidates:
                candidates.sort(
                    key=lambda e: (
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

    for employee in employees:
        if assigned_hours[employee] + 1e-9 > maximum_hours[employee]:
            warnings.append(
                f"{employee}: limite semanal excedido "
                f"({assigned_hours[employee]:.2f}h > {maximum_hours[employee]:.2f}h)."
            )
        if assigned_hours[employee] + 1e-9 < minimum_hours[employee]:
            warnings.append(
                f"{employee}: mínimo semanal não atingido "
                f"({assigned_hours[employee]:.2f}h < {minimum_hours[employee]:.2f}h)."
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
