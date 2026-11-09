"""Subscription and billing helpers."""

import os
from datetime import date, datetime

from database import _P, _PG, _get_conn

TIER_LIMITS = {
    "free": 10,
    "starter": 10,
    "standard": 20,
    "plus": 40,
    "network": None,
    "pro": 20,
}
TIER_PRICES_CENTS = {
    "starter": 1990,
    "standard": 3900,
    "plus": 6500,
    "network": 3500,
}
TIER_PRICES_ANNUAL_CENTS = {
    "starter": 15900,
    "standard": 32900,
    "plus": 54900,
    "network": 29500,
}
TIER_PRICE_ENV = {
    "starter": "STRIPE_PRICE_STARTER",
    "standard": "STRIPE_PRICE_STANDARD",
    "plus": "STRIPE_PRICE_PLUS",
    "network": "STRIPE_PRICE_NETWORK",
    "starter_annual": "STRIPE_PRICE_STARTER_ANNUAL",
    "standard_annual": "STRIPE_PRICE_STANDARD_ANNUAL",
    "plus_annual": "STRIPE_PRICE_PLUS_ANNUAL",
    "network_annual": "STRIPE_PRICE_NETWORK_ANNUAL",
}


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


def get_plan_tier(tenant_id):
    """Return the current pricing tier for a tenant."""
    tier = str(get_subscription(tenant_id).get("plano", "free") or "free").lower()
    if tier == "pro":
        tier = "standard"
    return tier


def is_pro(tenant_id):
    tier = get_plan_tier(tenant_id)
    subscription = get_subscription(tenant_id)
    return tier in ("starter", "standard", "plus", "network") and _validity_is_current(
        subscription.get("validade")
    )


def get_employee_limit(tenant_id):
    tier = get_plan_tier(tenant_id)
    return TIER_LIMITS.get(tier, 10)


def check_feature_gate(tenant_id, feature: str):
    if is_pro(tenant_id):
        return True
    return feature not in {"pdf_export", "analytics", "roster_history"}


def create_stripe_checkout_session(tenant_id, tier, success_url, cancel_url, interval="month", cafe_name=""):
    import stripe

    if tier not in TIER_PRICES_CENTS or interval not in ("month", "year"):
        raise ValueError("Invalid pricing tier")
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    prices = TIER_PRICES_ANNUAL_CENTS if interval == "year" else TIER_PRICES_CENTS
    price_env_key = f"{tier}_annual" if interval == "year" else tier
    price_id = os.environ.get(TIER_PRICE_ENV[price_env_key])
    product_period = "Anual" if interval == "year" else "Mensal"
    if price_id:
        line_item = {"price": price_id, "quantity": 1}
    else:
        line_item = {
            "price_data": {
                "currency": "eur",
                "unit_amount": prices[tier],
                "recurring": {"interval": interval},
                "product_data": {"name": f"escala {tier.capitalize()} — Subscricao {product_period}"},
            },
            "quantity": 1,
        }
    subscription_data = {
        "metadata": {"tenant_id": str(tenant_id), "tier": tier},
    }
    if interval == "month":
        subscription_data["trial_period_days"] = 7
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[line_item],
        metadata={"tenant_id": str(tenant_id), "tier": tier, "cafe_name": cafe_name},
        subscription_data=subscription_data,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def upsert_subscription(tenant_id, plano, validade, stripe_customer_id=None, stripe_subscription_id=None):
    """Append a subscription state change to the tenant audit trail."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        if _PG:
            cur.execute(
                """
                INSERT INTO Subscriptions (tenant_id, plano, validade, stripe_customer_id, stripe_subscription_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (tenant_id, plano, validade, stripe_customer_id, stripe_subscription_id),
            )
        else:
            cur.execute(
                """
                INSERT INTO Subscriptions (tenant_id, plano, validade, stripe_customer_id, stripe_subscription_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tenant_id, plano, validade, stripe_customer_id, stripe_subscription_id),
            )
        conn.commit()
    finally:
        conn.close()
