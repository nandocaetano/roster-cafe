"""Smoke test: verifies core modules load without syntax or import errors."""
import sys
import os
import py_compile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = "✅"
FAIL = "❌"


def test_app_syntax():
    try:
        py_compile.compile(os.path.join(ROOT, "app.py"), doraise=True)
        print(f"{PASS} app.py — syntax OK")
    except py_compile.PyCompileError as e:
        print(f"{FAIL} app.py — {e}")
        sys.exit(1)


def test_database_import():
    try:
        import database  # noqa: F401
        print(f"{PASS} database — imported OK")
    except Exception as e:
        print(f"{FAIL} database — {e}")
        sys.exit(1)


def test_logic_import():
    try:
        import logic  # noqa: F401
        print(f"{PASS} logic — imported OK")
    except Exception as e:
        print(f"{FAIL} logic — {e}")
        sys.exit(1)


def test_billing_logic_import():
    try:
        import billing_logic  # noqa: F401
        print(f"{PASS} billing_logic — imported OK")
    except Exception as e:
        print(f"{FAIL} billing_logic — {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("Smoke Test — Escala")
    print("=" * 50)
    test_app_syntax()
    test_database_import()
    test_logic_import()
    test_billing_logic_import()
    print("=" * 50)
    print("All smoke tests passed.")
