"""Database layer: SQLite (local dev) or PostgreSQL via DATABASE_URL (Supabase/cloud)."""
import hashlib
import json
import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = 'roster_cafe.db'
_PG = bool(os.environ.get('DATABASE_URL'))   # True on Streamlit Cloud with secret set
_P  = '%s' if _PG else '?'                  # SQL parameter placeholder

SHIFT_DAYS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
DEFAULT_SHIFT_TEMPLATES = {
    "Seg": [("07:00", "12:00", False), ("07:00", "14:00", False), ("07:30", "15:00", False), ("08:00", "16:00", False), ("09:00", "18:15", True), ("12:00", "18:15", True), ("14:00", "18:15", True)],
    "Ter": [("07:00", "12:00", False), ("07:00", "14:00", False), ("07:30", "15:00", False), ("08:00", "16:00", False), ("09:00", "18:15", True), ("12:00", "18:15", True), ("14:00", "18:15", True)],
    "Qua": [("06:30", "12:00", False), ("07:00", "14:00", False), ("07:30", "15:00", False), ("08:00", "16:00", False), ("09:00", "18:15", True), ("12:00", "18:15", True), ("14:00", "18:15", True)],
    "Qui": [("07:00", "12:00", False), ("07:00", "14:00", False), ("07:30", "15:00", False), ("08:00", "16:00", False), ("09:00", "18:15", True), ("12:00", "18:15", True), ("14:00", "18:15", True)],
    "Sex": [("07:00", "12:00", False), ("07:00", "14:00", False), ("07:30", "15:00", False), ("08:00", "16:00", False), ("09:00", "18:15", True), ("12:00", "18:15", True), ("14:00", "18:15", True)],
    "Sáb": [("07:30", "14:00", False), ("07:30", "15:00", False), ("09:00", "18:15", True), ("12:00", "18:15", True), ("14:00", "18:15", True)],
    "Dom": [("07:30", "14:00", False), ("07:30", "15:00", False), ("09:00", "18:15", True), ("12:00", "18:15", True), ("14:00", "18:15", True)],
}


# ──────────────────────────────────────────────────────────────────
# Connection factory & low-level helpers
# ──────────────────────────────────────────────────────────────────

def _get_conn():
    """Return a configured DB connection (psycopg2 or sqlite3)."""
    if _PG:
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(
            os.environ['DATABASE_URL'],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def _cnt(cur, table, where='', params=()):
    """Return COUNT(*) for a table with optional WHERE clause."""
    sql = f"SELECT COUNT(*) AS n FROM {table}"
    if where:
        sql += f" WHERE {where}"
    cur.execute(sql, params)
    return cur.fetchone()['n']


def _fetchdf(cur):
    """Fetch all rows from cursor and return a DataFrame."""
    rows = cur.fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


# ──────────────────────────────────────────────────────────────────
# Password helpers (SHA-256 + random 16-byte salt)
# ──────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    return f"{salt.hex()}:{h}"


def _check_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(':', 1)
        salt = bytes.fromhex(salt_hex)
        return hashlib.sha256(salt + password.encode('utf-8')).hexdigest() == hash_hex
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────
# init_db — create tables + seed
# ──────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables, run migrations, and seed default data."""
    conn = _get_conn()
    cur = conn.cursor()

    if _PG:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Cafes (
                id          SERIAL PRIMARY KEY,
                name        TEXT    NOT NULL,
                admin_email TEXT,
                min_dias_folga INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT    NOT NULL DEFAULT (NOW()::TEXT)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id            SERIAL PRIMARY KEY,
                tenant_id     INTEGER NOT NULL REFERENCES Cafes(id),
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL DEFAULT 'admin',
                created_at    TEXT    NOT NULL DEFAULT (NOW()::TEXT)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Funcionarios (
                id_funcionario SERIAL PRIMARY KEY,
                tenant_id      INTEGER NOT NULL DEFAULT 1 REFERENCES Cafes(id),
                nome           TEXT NOT NULL,
                cargo          TEXT NOT NULL,
                tipo_contrato  TEXT NOT NULL,
                horas_min      INTEGER,
                horas_max      INTEGER,
                d_seg TEXT, d_ter TEXT, d_qua TEXT,
                d_qui TEXT, d_sex TEXT, d_sab TEXT, d_dom TEXT,
                status_ativo      BOOLEAN DEFAULT TRUE,
                nivel             TEXT    DEFAULT 'experiente',
                preferencia_turno TEXT    DEFAULT 'Sem preferência'
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Rosters (
                id         SERIAL PRIMARY KEY,
                tenant_id  INTEGER NOT NULL REFERENCES Cafes(id),
                semana     TEXT    NOT NULL,
                dados_json TEXT    NOT NULL,
                criado_em  TEXT    NOT NULL DEFAULT (NOW()::TEXT)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Subscriptions (
                id                     SERIAL PRIMARY KEY,
                tenant_id              INTEGER NOT NULL REFERENCES Cafes(id),
                plano                  TEXT    NOT NULL DEFAULT 'free',
                validade               TEXT,
                stripe_customer_id     TEXT,
                stripe_subscription_id TEXT,
                criado_em              TEXT    NOT NULL DEFAULT (NOW()::TEXT)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ShiftTemplates (
                id          SERIAL PRIMARY KEY,
                tenant_id   INTEGER NOT NULL REFERENCES Cafes(id),
                dia         TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_fim    TEXT NOT NULL,
                fechamento  BOOLEAN NOT NULL DEFAULT FALSE,
                headcount   INTEGER NOT NULL DEFAULT 1,
                prioridade  TEXT NOT NULL DEFAULT 'essential',
                ativo       BOOLEAN NOT NULL DEFAULT TRUE,
                criado_em   TEXT NOT NULL DEFAULT (NOW()::TEXT)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS WeeklySetup (
                id          SERIAL PRIMARY KEY,
                tenant_id   INTEGER NOT NULL REFERENCES Cafes(id),
                semana_key  TEXT NOT NULL,
                dados_json  TEXT NOT NULL,
                criado_em   TEXT NOT NULL DEFAULT (NOW()::TEXT)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS DateHeadcountOverrides (
                id            SERIAL PRIMARY KEY,
                tenant_id     INTEGER NOT NULL REFERENCES Cafes(id),
                override_date TEXT NOT NULL,
                shift_label   TEXT NOT NULL,
                headcount     INTEGER NOT NULL,
                criado_em     TEXT NOT NULL,
                UNIQUE (tenant_id, override_date, shift_label)
            )
        ''')
        # Safe migrations (PG 9.6+ supports IF NOT EXISTS)
        cur.execute('''
            ALTER TABLE Funcionarios
            ADD COLUMN IF NOT EXISTS tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES Cafes(id)
        ''')
        cur.execute('''
            ALTER TABLE Funcionarios
            ADD COLUMN IF NOT EXISTS nivel TEXT DEFAULT 'experiente'
        ''')
        cur.execute('''
            ALTER TABLE Funcionarios
            ADD COLUMN IF NOT EXISTS preferencia_turno TEXT DEFAULT 'Sem preferência'
        ''')
        cur.execute('''
            ALTER TABLE Cafes
            ADD COLUMN IF NOT EXISTS min_dias_folga INTEGER NOT NULL DEFAULT 1
        ''')
    else:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Cafes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                admin_email TEXT,
                min_dias_folga INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id     INTEGER NOT NULL REFERENCES Cafes(id),
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL DEFAULT 'admin',
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Funcionarios (
                id_funcionario INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id      INTEGER NOT NULL DEFAULT 1 REFERENCES Cafes(id),
                nome           TEXT NOT NULL,
                cargo          TEXT NOT NULL,
                tipo_contrato  TEXT NOT NULL,
                horas_min      INTEGER,
                horas_max      INTEGER,
                d_seg TEXT, d_ter TEXT, d_qua TEXT,
                d_qui TEXT, d_sex TEXT, d_sab TEXT, d_dom TEXT,
                status_ativo      BOOLEAN DEFAULT 1,
                nivel             TEXT    DEFAULT 'experiente',
                preferencia_turno TEXT    DEFAULT 'Sem preferência'
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Rosters (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id  INTEGER NOT NULL REFERENCES Cafes(id),
                semana     TEXT    NOT NULL,
                dados_json TEXT    NOT NULL,
                criado_em  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Subscriptions (
                id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id              INTEGER NOT NULL REFERENCES Cafes(id),
                plano                  TEXT    NOT NULL DEFAULT 'free',
                validade               TEXT,
                stripe_customer_id     TEXT,
                stripe_subscription_id TEXT,
                criado_em              TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ShiftTemplates (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id   INTEGER NOT NULL REFERENCES Cafes(id),
                dia         TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_fim    TEXT NOT NULL,
                fechamento  BOOLEAN NOT NULL DEFAULT 0,
                headcount   INTEGER NOT NULL DEFAULT 1,
                prioridade  TEXT NOT NULL DEFAULT 'essential',
                ativo       BOOLEAN NOT NULL DEFAULT 1,
                criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS WeeklySetup (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id   INTEGER NOT NULL REFERENCES Cafes(id),
                semana_key  TEXT NOT NULL,
                dados_json  TEXT NOT NULL,
                criado_em   TEXT NOT NULL DEFAULT (datetime('now'))
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS DateHeadcountOverrides (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id     INTEGER NOT NULL REFERENCES Cafes(id),
                override_date TEXT NOT NULL,
                shift_label   TEXT NOT NULL,
                headcount     INTEGER NOT NULL,
                criado_em     TEXT NOT NULL,
                UNIQUE (tenant_id, override_date, shift_label)
            )
        ''')
        try:
            cur.execute(
                "ALTER TABLE Funcionarios ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES Cafes(id)"
            )
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE Funcionarios ADD COLUMN nivel TEXT DEFAULT 'experiente'")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE Funcionarios ADD COLUMN preferencia_turno TEXT DEFAULT 'Sem preferência'")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE Cafes ADD COLUMN min_dias_folga INTEGER NOT NULL DEFAULT 1")
        except sqlite3.OperationalError:
            pass

    # Seed default tenant
    if _cnt(cur, 'Cafes') == 0:
        cur.execute(
            f"INSERT INTO Cafes (name, admin_email, created_at) VALUES ({_P},{_P},{_P})",
            ("Default Cafe", "admin@cafe.com", datetime.utcnow().isoformat()),
        )

    # Seed default superadmin
    if _cnt(cur, 'Users') == 0:
        cur.execute(
            f"INSERT INTO Users (tenant_id, email, password_hash, role, created_at) VALUES ({_P},{_P},{_P},{_P},{_P})",
            (1, "admin@cafe.com", _hash_password("admin123"), "superadmin", datetime.utcnow().isoformat()),
        )

    # Migration: upgrade existing admin seed to superadmin
    cur.execute(
        f"UPDATE Users SET role = 'superadmin' WHERE email = {_P} AND role = 'admin'",
        ("admin@cafe.com",),
    )

    # Seed free plan for default tenant
    if _cnt(cur, 'Subscriptions', f"tenant_id = {_P}", (1,)) == 0:
        cur.execute(
            f"INSERT INTO Subscriptions (tenant_id, plano, criado_em) VALUES ({_P},{_P},{_P})",
            (1, 'free', datetime.utcnow().isoformat()),
        )

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────
# Tenant helpers
# ──────────────────────────────────────────────────────────────────

def get_cafes():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Cafes")
    df = _fetchdf(cur)
    conn.close()
    return df


def criar_cafe(name, admin_email):
    conn = _get_conn()
    cur = conn.cursor()
    if _PG:
        cur.execute(
            "INSERT INTO Cafes (name, admin_email, created_at) VALUES (%s,%s,%s) RETURNING id",
            (name, admin_email, datetime.utcnow().isoformat()),
        )
        new_id = cur.fetchone()['id']
    else:
        cur.execute(
            "INSERT INTO Cafes (name, admin_email, created_at) VALUES (?,?,?)",
            (name, admin_email, datetime.utcnow().isoformat()),
        )
        new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_cafe_by_id(cafe_id):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM Cafes WHERE id = {_P}", (cafe_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_cafe_min_dias_folga(cafe_id):
    """Return the configured minimum weekly rest days for a cafe."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT min_dias_folga FROM Cafes WHERE id = {_P}", (cafe_id,))
        row = cur.fetchone()
    except Exception:
        row = None
    conn.close()
    try:
        value = int((dict(row) if row else {}).get("min_dias_folga") or 1)
    except (TypeError, ValueError):
        value = 1
    return max(1, min(7, value))


def set_cafe_min_dias_folga(cafe_id, min_dias_folga):
    """Persist the minimum weekly rest days for a cafe."""
    value = max(1, min(7, int(min_dias_folga)))
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE Cafes SET min_dias_folga = {_P} WHERE id = {_P}",
        (value, cafe_id),
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────
# User CRUD
# ──────────────────────────────────────────────────────────────────

def create_user(tenant_id, email, password, role="admin"):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO Users (tenant_id, email, password_hash, role, created_at) VALUES ({_P},{_P},{_P},{_P},{_P})",
        (tenant_id, email, _hash_password(password), role, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def verify_credentials(email, password):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM Users WHERE email = {_P}", (email,))
    row = cur.fetchone()
    conn.close()
    if row and _check_password(password, dict(row)['password_hash']):
        return dict(row)
    return None


def get_all_users() -> pd.DataFrame:
    """Return all users joined with cafe name. Superadmin use only."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT u.id, u.tenant_id, u.email, u.role, c.name AS cafe_nome "
        "FROM Users u JOIN Cafes c ON c.id = u.tenant_id "
        "ORDER BY c.name, u.email"
    )
    df = _fetchdf(cur)
    conn.close()
    return df


def reset_password(email: str, new_password: str) -> bool:
    """Update password_hash for the user with given email. Returns True if user found."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE Users SET password_hash = {_P} WHERE email = {_P}",
        (_hash_password(new_password), email),
    )
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ──────────────────────────────────────────────────────────────────
# Employee CRUD — all queries scoped to tenant_id
# ──────────────────────────────────────────────────────────────────

EMPLOYEE_LIMIT = 100  # safety-net cap; billing tiers enforce real limits via get_employee_limit()


def get_funcionarios_ativos(tenant_id):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT * FROM Funcionarios WHERE status_ativo = TRUE AND tenant_id = {_P}",
        (tenant_id,),
    )
    df = _fetchdf(cur)
    conn.close()
    return df


def adicionar_funcionario(tenant_id, nome, cargo, contrato, h_min, h_max, dias, nivel='experiente', preferencia='Sem preferência'):
    """Insert a new employee. Raises ValueError if the tenant has reached EMPLOYEE_LIMIT."""
    conn = _get_conn()
    cur = conn.cursor()
    if _cnt(cur, 'Funcionarios', f"tenant_id = {_P} AND status_ativo = TRUE", (tenant_id,)) >= EMPLOYEE_LIMIT:
        conn.close()
        raise ValueError(f"limite_funcionarios:{EMPLOYEE_LIMIT}")
    cur.execute(
        f'''INSERT INTO Funcionarios
            (tenant_id, nome, cargo, tipo_contrato, horas_min, horas_max,
             d_seg, d_ter, d_qua, d_qui, d_sex, d_sab, d_dom, nivel, preferencia_turno)
            VALUES ({_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P})''',
        (tenant_id, nome, cargo, contrato, h_min, h_max, *dias, nivel, preferencia),
    )
    conn.commit()
    conn.close()


def atualizar_funcionario(tenant_id, id_func, nome, cargo, contrato, h_min, h_max, dias, nivel='experiente', preferencia='Sem preferência'):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f'''UPDATE Funcionarios
            SET nome={_P}, cargo={_P}, tipo_contrato={_P}, horas_min={_P}, horas_max={_P},
                d_seg={_P}, d_ter={_P}, d_qua={_P}, d_qui={_P}, d_sex={_P}, d_sab={_P}, d_dom={_P},
                nivel={_P}, preferencia_turno={_P}
            WHERE id_funcionario={_P} AND tenant_id={_P}''',
        (nome, cargo, contrato, h_min, h_max, *dias, nivel, preferencia, id_func, tenant_id),
    )
    conn.commit()
    conn.close()


def desativar_funcionario(tenant_id, id_func):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE Funcionarios SET status_ativo = FALSE WHERE id_funcionario = {_P} AND tenant_id = {_P}",
        (id_func, tenant_id),
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────
# Shift templates & weekly setup
# ──────────────────────────────────────────────────────────────────

def _shift_text(hora_inicio, hora_fim, fechamento=False):
    suffix = " (Fechamento)" if fechamento else ""
    return f"{hora_inicio} - {hora_fim}{suffix}"


def get_shift_templates(tenant_id):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"""SELECT id, dia, hora_inicio, hora_fim, fechamento, headcount, prioridade, ativo
            FROM ShiftTemplates
            WHERE tenant_id = {_P} AND ativo = TRUE
            ORDER BY CASE dia WHEN 'Seg' THEN 1 WHEN 'Ter' THEN 2 WHEN 'Qua' THEN 3
                              WHEN 'Qui' THEN 4 WHEN 'Sex' THEN 5 WHEN 'Sáb' THEN 6 WHEN 'Dom' THEN 7 ELSE 8 END,
                     hora_inicio, hora_fim, id""",
        (tenant_id,),
    )
    df = _fetchdf(cur)
    conn.close()
    return df


def save_shift_templates(tenant_id, rows):
    if hasattr(rows, "to_dict"):
        rows = rows.to_dict("records")
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(f"DELETE FROM ShiftTemplates WHERE tenant_id = {_P}", (tenant_id,))
        for row in rows:
            dia = str(row.get("dia", row.get("Dia", ""))).strip()
            inicio = str(row.get("hora_inicio", row.get("Início", ""))).strip()
            fim = str(row.get("hora_fim", row.get("Fim", ""))).strip()
            if dia not in SHIFT_DAYS or not inicio or not fim:
                continue
            fechamento = bool(row.get("fechamento", row.get("Fechamento", False)))
            headcount = max(1, min(6, int(row.get("headcount", row.get("Pessoas", 1)) or 1)))
            prioridade = str(row.get("prioridade", "optional" if row.get("Opcional", False) else "essential"))
            prioridade = "optional" if prioridade == "optional" else "essential"
            ativo = bool(row.get("ativo", row.get("Ativo", True)))
            cur.execute(
                f"""INSERT INTO ShiftTemplates
                    (tenant_id, dia, hora_inicio, hora_fim, fechamento, headcount, prioridade, ativo, criado_em)
                    VALUES ({_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P},{_P})""",
                (tenant_id, dia, inicio, fim, fechamento, headcount, prioridade, ativo, datetime.utcnow().isoformat()),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_shift_templates(tenant_id):
    if not get_shift_templates(tenant_id).empty:
        return get_shift_templates(tenant_id)
    rows = []
    for dia in SHIFT_DAYS:
        for inicio, fim, fechamento in DEFAULT_SHIFT_TEMPLATES[dia]:
            rows.append({
                "dia": dia,
                "hora_inicio": inicio,
                "hora_fim": fim,
                "fechamento": fechamento,
                "headcount": 1,
                "prioridade": "optional" if inicio == "08:00" and fim == "16:00" else "essential",
                "ativo": True,
            })
    save_shift_templates(tenant_id, rows)
    return get_shift_templates(tenant_id)


def build_turnos_padrao(tenant_id):
    templates = get_shift_templates(tenant_id)
    if templates.empty:
        templates = seed_shift_templates(tenant_id)
    result = {day: [] for day in SHIFT_DAYS}
    for _, row in templates.iterrows():
        result.setdefault(row["dia"], []).append(
            _shift_text(row["hora_inicio"], row["hora_fim"], bool(row["fechamento"]))
        )
    return {day: shifts for day, shifts in result.items() if shifts}


def build_slot_config(tenant_id):
    templates = get_shift_templates(tenant_id)
    if templates.empty:
        templates = seed_shift_templates(tenant_id)
    config = {}
    for _, row in templates.iterrows():
        shift = _shift_text(row["hora_inicio"], row["hora_fim"], bool(row["fechamento"]))
        config[(row["dia"], shift)] = {
            "headcount": max(1, min(6, int(row["headcount"]))),
            "priority": "optional" if row["prioridade"] == "optional" else "essential",
        }
    return config


def get_weekly_setup(tenant_id, semana_key=None):
    conn = _get_conn()
    cur = conn.cursor()
    if semana_key:
        cur.execute(
            f"""SELECT dados_json FROM WeeklySetup
                WHERE tenant_id = {_P} AND semana_key = {_P}
                ORDER BY criado_em DESC LIMIT 1""",
            (tenant_id, semana_key),
        )
    else:
        cur.execute(
            f"""SELECT dados_json FROM WeeklySetup
                WHERE tenant_id = {_P}
                ORDER BY criado_em DESC LIMIT 1""",
            (tenant_id,),
        )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    raw = row["dados_json"] if _PG else row[0]
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None


def save_weekly_setup(tenant_id, semana_key, overrides):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"""INSERT INTO WeeklySetup (tenant_id, semana_key, dados_json, criado_em)
            VALUES ({_P},{_P},{_P},{_P})""",
        (tenant_id, str(semana_key).strip(), json.dumps(overrides, ensure_ascii=False), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def build_config_semana(tenant_id, overrides=None):
    employees = get_funcionarios_ativos(tenant_id)
    overrides = overrides or {}
    employee_overrides = overrides.get("employees", overrides)
    config = {}
    for _, row in employees.iterrows():
        nome = row["nome"]
        dias = {
            "Seg": row.get("d_seg", "Indisponível"),
            "Ter": row.get("d_ter", "Indisponível"),
            "Qua": row.get("d_qua", "Indisponível"),
            "Qui": row.get("d_qui", "Indisponível"),
            "Sex": row.get("d_sex", "Indisponível"),
            "Sáb": row.get("d_sab", "Indisponível"),
            "Dom": row.get("d_dom", "Indisponível"),
        }
        config[nome] = {
            "vai_trabalhar": True,
            "horas_alvo": int(row.get("horas_max", 0) or 0),
            "horas_min": float(row.get("horas_min", 0) or 0),
            "horas_max": float(row.get("horas_max", 0) or 0),
            "cargo": row.get("cargo", ""),
            "tipo_contrato": str(row.get("tipo_contrato", "Full-time") or "Full-time"),
            "nivel": str(row.get("nivel", "experiente") or "experiente"),
            "preferencia_turno": str(row.get("preferencia_turno", "Sem preferência") or "Sem preferência"),
            "disponibilidade": dias,
            "dias_folga": [],
            "dias_ferias": [],
            "dias_treinamento": [],
            "horas_treinamento": 0.0,
        }
        allowed = {"vai_trabalhar", "horas_alvo", "dias_folga", "dias_ferias", "dias_treinamento", "horas_treinamento"}
        for key, value in (employee_overrides.get(nome, {}) or {}).items():
            if key in allowed:
                config[nome][key] = value
    return config


# ──────────────────────────────────────────────────────────────────
# Roster History CRUD
# ──────────────────────────────────────────────────────────────────

def salvar_roster(tenant_id: int, semana: str, dados_json: str):
    conn = _get_conn()
    cur = conn.cursor()
    if _PG:
        cur.execute(
            "INSERT INTO Rosters (tenant_id, semana, dados_json, criado_em) VALUES (%s,%s,%s,%s) RETURNING id",
            (tenant_id, semana, dados_json, datetime.utcnow().isoformat()),
        )
        new_id = cur.fetchone()['id']
    else:
        cur.execute(
            "INSERT INTO Rosters (tenant_id, semana, dados_json, criado_em) VALUES (?,?,?,?)",
            (tenant_id, semana, dados_json, datetime.utcnow().isoformat()),
        )
        new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_rosters(tenant_id: int) -> pd.DataFrame:
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT id, semana, criado_em FROM Rosters WHERE tenant_id = {_P} ORDER BY id DESC",
        (tenant_id,),
    )
    df = _fetchdf(cur)
    conn.close()
    return df


def get_roster_by_id(tenant_id: int, roster_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT dados_json FROM Rosters WHERE id = {_P} AND tenant_id = {_P}",
        (roster_id, tenant_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row)['dados_json'] if row else None


def deletar_roster(tenant_id: int, roster_id: int):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"DELETE FROM Rosters WHERE id = {_P} AND tenant_id = {_P}",
        (roster_id, tenant_id),
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────
# Date-Specific Headcount Overrides CRUD
# ──────────────────────────────────────────────────────────────────

def get_date_headcount_overrides(tenant_id: int, week_dates: list) -> list:
    """Return all headcount overrides for the given tenant where override_date is in week_dates.
    Each item is a dict with keys: id, override_date, shift_label, headcount.
    """
    if not week_dates:
        return []
    conn = _get_conn()
    cur = conn.cursor()
    placeholders = ','.join([_P] * len(week_dates))
    cur.execute(
        f"SELECT id, override_date, shift_label, headcount FROM DateHeadcountOverrides "
        f"WHERE tenant_id = {_P} AND override_date IN ({placeholders}) "
        f"ORDER BY override_date, shift_label",
        (tenant_id, *week_dates),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_date_headcount_override(tenant_id: int, override_date: str, shift_label: str, headcount: int):
    """Upsert a date-specific headcount override.
    For PostgreSQL: uses INSERT ... ON CONFLICT DO UPDATE.
    For SQLite: DELETE existing + INSERT (simpler than upsert).
    """
    conn = _get_conn()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    if _PG:
        cur.execute(
            f"""INSERT INTO DateHeadcountOverrides (tenant_id, override_date, shift_label, headcount, criado_em)
                VALUES ({_P},{_P},{_P},{_P},{_P})
                ON CONFLICT (tenant_id, override_date, shift_label)
                DO UPDATE SET headcount = EXCLUDED.headcount, criado_em = EXCLUDED.criado_em""",
            (tenant_id, override_date, shift_label, headcount, now),
        )
    else:
        cur.execute(
            f"DELETE FROM DateHeadcountOverrides WHERE tenant_id = {_P} AND override_date = {_P} AND shift_label = {_P}",
            (tenant_id, override_date, shift_label),
        )
        cur.execute(
            f"""INSERT INTO DateHeadcountOverrides (tenant_id, override_date, shift_label, headcount, criado_em)
                VALUES ({_P},{_P},{_P},{_P},{_P})""",
            (tenant_id, override_date, shift_label, headcount, now),
        )
    conn.commit()
    conn.close()


def delete_date_headcount_override(tenant_id: int, override_date: str, shift_label: str):
    """Delete a date-specific headcount override identified by (tenant_id, override_date, shift_label)."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        f"DELETE FROM DateHeadcountOverrides WHERE tenant_id = {_P} AND override_date = {_P} AND shift_label = {_P}",
        (tenant_id, override_date, shift_label),
    )
    conn.commit()
    conn.close()
