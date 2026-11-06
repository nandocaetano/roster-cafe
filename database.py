"""Database layer: SQLite (local dev) or PostgreSQL via DATABASE_URL (Supabase/cloud)."""
import hashlib
import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = 'roster_cafe.db'
_PG = bool(os.environ.get('DATABASE_URL'))   # True on Streamlit Cloud with secret set
_P  = '%s' if _PG else '?'                  # SQL parameter placeholder


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
    else:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS Cafes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                admin_email TEXT,
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

EMPLOYEE_LIMIT = 20


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
