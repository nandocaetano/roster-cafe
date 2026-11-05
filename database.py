"""Database layer: SQLite connection, table creation, and CRUD for roster_cafe.db."""
import hashlib
import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = 'roster_cafe.db'


# ------------------------------------------------------------------
# Password helpers (SHA-256 + random 16-byte salt)
# ------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """Return 'salt_hex:hash_hex' for the given plaintext password."""
    salt = os.urandom(16)
    h = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    return f"{salt.hex()}:{h}"


def _check_password(password: str, stored: str) -> bool:
    """Return True if password matches the stored 'salt_hex:hash_hex' value."""
    try:
        salt_hex, hash_hex = stored.split(':', 1)
        salt = bytes.fromhex(salt_hex)
        return hashlib.sha256(salt + password.encode('utf-8')).hexdigest() == hash_hex
    except Exception:
        return False


def init_db():
    """
    Create Cafes, Users, and Funcionarios tables if they do not exist.
    Migrates existing Funcionarios rows to include tenant_id.
    Seeds a default tenant and admin user on first run.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Cafes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            admin_email TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id     INTEGER NOT NULL REFERENCES Cafes(id),
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'admin',
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
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
            status_ativo   BOOLEAN DEFAULT 1
        )
    ''')

    # Migration: add tenant_id to pre-existing Funcionarios tables that lack it.
    try:
        cursor.execute("ALTER TABLE Funcionarios ADD COLUMN tenant_id INTEGER NOT NULL DEFAULT 1 REFERENCES Cafes(id)")
    except sqlite3.OperationalError:
        pass  # column already exists

    # Seed default tenant if the Cafes table is empty.
    cursor.execute("SELECT COUNT(*) FROM Cafes")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Cafes (name, admin_email, created_at) VALUES (?, ?, ?)",
            ("Default Cafe", "admin@cafe.com", datetime.utcnow().isoformat()),
        )

    # Seed default admin user if the Users table is empty.
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Users (tenant_id, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (1, "admin@cafe.com", _hash_password("admin123"), "admin", datetime.utcnow().isoformat()),
        )

    conn.commit()
    conn.close()


# ------------------------------------------------------------------
# Tenant helpers
# ------------------------------------------------------------------

def get_cafes():
    """Return a DataFrame of all tenants."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM Cafes", conn)
    conn.close()
    return df


def criar_cafe(name, admin_email):
    """Insert a new tenant and return its new id."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Cafes (name, admin_email, created_at) VALUES (?, ?, ?)",
        (name, admin_email, datetime.utcnow().isoformat()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_cafe_by_id(cafe_id):
    """Return a dict for the given tenant id, or None if not found."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Cafes WHERE id = ?", (cafe_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ------------------------------------------------------------------
# User CRUD
# ------------------------------------------------------------------

def create_user(tenant_id, email, password, role="admin"):
    """
    Hash password and insert a new user. Raises sqlite3.IntegrityError
    if the email already exists (UNIQUE constraint).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Users (tenant_id, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (tenant_id, email, _hash_password(password), role, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def verify_credentials(email, password):
    """
    Return a plain dict for the user if email/password match, else None.
    The dict includes: id, tenant_id, email, role, created_at.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row and _check_password(password, row['password_hash']):
        return dict(row)
    return None


# ------------------------------------------------------------------
# Employee CRUD — all queries are scoped to tenant_id
# ------------------------------------------------------------------

def get_funcionarios_ativos(tenant_id):
    """Return a DataFrame of active employees for the given tenant."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT * FROM Funcionarios WHERE status_ativo = 1 AND tenant_id = ?",
        conn,
        params=(tenant_id,),
    )
    conn.close()
    return df


def adicionar_funcionario(tenant_id, nome, cargo, contrato, h_min, h_max, dias):
    """Insert a new employee record for the given tenant. dias is a 7-element list (Seg..Dom)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Funcionarios
        (tenant_id, nome, cargo, tipo_contrato, horas_min, horas_max,
         d_seg, d_ter, d_qua, d_qui, d_sex, d_sab, d_dom)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tenant_id, nome, cargo, contrato, h_min, h_max, *dias))
    conn.commit()
    conn.close()


def atualizar_funcionario(tenant_id, id_func, nome, cargo, contrato, h_min, h_max, dias):
    """Update an employee record. tenant_id guard prevents cross-tenant writes."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Funcionarios
        SET nome=?, cargo=?, tipo_contrato=?, horas_min=?, horas_max=?,
            d_seg=?, d_ter=?, d_qua=?, d_qui=?, d_sex=?, d_sab=?, d_dom=?
        WHERE id_funcionario=? AND tenant_id=?
    ''', (nome, cargo, contrato, h_min, h_max, *dias, id_func, tenant_id))
    conn.commit()
    conn.close()


def desativar_funcionario(tenant_id, id_func):
    """Soft-delete an employee. tenant_id guard prevents cross-tenant writes."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Funcionarios SET status_ativo = 0 WHERE id_funcionario = ? AND tenant_id = ?",
        (id_func, tenant_id),
    )
    conn.commit()
    conn.close()
