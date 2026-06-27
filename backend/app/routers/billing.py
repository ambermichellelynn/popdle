"""Stripe test-mode Checkout for the Premium subscription.

If STRIPE_SECRET_KEY isn't configured, checkout-session creation falls back to
a simulated session id so the upgrade flow can still be demoed end-to-end
without a Stripe account.
"""

import uuid

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import Subscription, User

router = APIRouter(prefix="/billing", tags=["billing"])

PREMIUM_PRICE_USD_CENTS = 299
SIMULATED_SESSION_PREFIX = "simulated_"


class CheckoutSessionRequest(BaseModel):
    user_id: str


class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str
    simulated: bool


class ConfirmCheckoutRequest(BaseModel):
    user_id: str
    session_id: str


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(payload: CheckoutSessionRequest, db: Session = Depends(get_db)) -> CheckoutSessionResponse:
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success_url = f"{settings.frontend_base_url}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.frontend_base_url}/?checkout=cancel"

    if not settings.stripe_secret_key:
        session_id = f"{SIMULATED_SESSION_PREFIX}{uuid.uuid4()}"
        return CheckoutSessionResponse(
            url=success_url.replace("{CHECKOUT_SESSION_ID}", session_id),
            session_id=session_id,
            simulated=True,
        )

    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user.email if "@anon.popdle.local" not in user.email else None,
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Popdle Premium"},
                    "unit_amount": PREMIUM_PRICE_USD_CENTS,
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=user.id,
    )
    return CheckoutSessionResponse(url=session.url, session_id=session.id, simulated=False)


def _grant_premium(db: Session, user: User, stripe_customer_id: str | None, stripe_subscription_id: str | None) -> None:
    user.is_premium = True
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id)
        db.add(subscription)
    subscription.status = "active"
    subscription.stripe_customer_id = stripe_customer_id
    subscription.stripe_subscription_id = stripe_subscription_id
    db.commit()


@router.post("/confirm")
def confirm_checkout(payload: ConfirmCheckoutRequest, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.session_id.startswith(SIMULATED_SESSION_PREFIX):
        _grant_premium(db, user, stripe_customer_id=None, stripe_subscription_id=None)
        return {"is_premium": True, "simulated": True}

    if not settings.stripe_secret_key:
        raise HTTPException(status_code=400, detail="Stripe is not configured")

    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.retrieve(payload.session_id)

    if session.client_reference_id != user.id or session.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Checkout session not confirmed for this user")

    _grant_premium(
        db,
        user,
        stripe_customer_id=session.customer,
        stripe_subscription_id=session.subscription,
    )
    return {"is_premium": True, "simulated": False}
