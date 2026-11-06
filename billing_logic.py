"""Subscription and billing helpers."""

import os
from datetime import date, datetime

from database import _P, _PG, _get_conn


def get_subscription(tenant_id):
    """Return the tenant subscription, or the default free plan."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT plano, validade, stripe_subscription_id
            FROM Subscriptions
            WHERE tenant_id = {_P}
            ORDER BY criado_em DESC
            LIMIT 1
            """,
            (tenant_id,),
        )
        row = cur.fetchone()
        if not row:
            return {"plano": "free"}
        return {
            "plano": row["plano"] if _PG else row[0],
            "validade": row["validade"] if _PG else row[1],
            "stripe_subscription_id": (
                row["stripe_subscription_id"] if _PG else row[2]
            ),
        }
    except Exception:
        return {"plano": "free"}
    finally:
        conn.close()


def _validity_is_current(validade):
    if validade is None:
        return True
    if isinstance(validade, datetime):
        now = datetime.now(validade.tzinfo) if validade.tzinfo else datetime.now()
        return validade >= now
    if isinstance(validade, date):
        return validade >= date.today()
    raw_validade = str(validade)
    if "T" not in raw_validade and " " not in raw_validade:
        try:
            return date.fromisoformat(raw_validade) >= date.today()
        except (TypeError, ValueError):
            return False
    try:
        parsed = datetime.fromisoformat(raw_validade.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        try:
            return date.fromisoformat(str(validade)) >= date.today()
        except (TypeError, ValueError):
            return False
    now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
    return parsed >= now


def is_pro(tenant_id):
    subscription = get_subscription(tenant_id)
    return subscription.get("plano") == "pro" and _validity_is_current(
        subscription.get("validade")
    )


def get_employee_limit(tenant_id):
    return 20 if is_pro(tenant_id) else 10


def check_feature_gate(tenant_id, feature: str):
    if is_pro(tenant_id):
        return True
    return feature not in {"pdf_export", "analytics", "roster_history"}


def create_stripe_checkout_session(tenant_id, success_url, cancel_url):
    import stripe

    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[
            {
                # One-time setup fee — billed on the first invoice only
                "price_data": {
                    "currency": "eur",
                    "unit_amount": 3990,  # €39.90
                    "product_data": {"name": "Roster Café — Setup"},
                },
                "quantity": 1,
            },
            {
                "price_data": {
                    "currency": "eur",
                    "unit_amount": 2000,  # €20.00/mês
                    "recurring": {"interval": "month"},
                    "product_data": {"name": "Roster Café Pro — Mensal"},
                },
                "quantity": 1,
            },
        ],
        metadata={"tenant_id": str(tenant_id)},
        subscription_data={"metadata": {"tenant_id": str(tenant_id)}},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url
