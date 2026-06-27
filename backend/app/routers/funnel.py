from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Assignment, Event

router = APIRouter(prefix="/admin/funnel", tags=["funnel"])

FUNNEL_STEPS = ["signup", "game_started", "game_won", "paywall_viewed", "upgraded"]


@router.get("")
def get_funnel(db: Session = Depends(get_db)) -> dict:
    step_counts = {}
    for step in FUNNEL_STEPS:
        count = (
            db.query(func.count(func.distinct(Event.user_id)))
            .filter(Event.name == step)
            .scalar()
        )
        step_counts[step] = count or 0

    signup_count = step_counts.get("signup") or 1  # avoid div-by-zero
    conversion_rates = {
        step: round(count / signup_count * 100, 1) for step, count in step_counts.items()
    }

    variant_rows = (
        db.query(Assignment.variant, func.count(func.distinct(Assignment.user_id)))
        .filter(Assignment.experiment_key == "onboarding_flow")
        .group_by(Assignment.variant)
        .all()
    )
    variant_users = {variant: count for variant, count in variant_rows}

    won_users_by_variant = {}
    for variant in variant_users:
        won_count = (
            db.query(func.count(func.distinct(Event.user_id)))
            .join(Assignment, Assignment.user_id == Event.user_id)
            .filter(
                Event.name == "game_won",
                Assignment.experiment_key == "onboarding_flow",
                Assignment.variant == variant,
            )
            .scalar()
        )
        won_users_by_variant[variant] = won_count or 0

    onboarding_variant_breakdown = {
        variant: {
            "assigned_users": variant_users[variant],
            "won_game": won_users_by_variant.get(variant, 0),
            "activation_rate_pct": round(
                won_users_by_variant.get(variant, 0) / variant_users[variant] * 100, 1
            )
            if variant_users[variant]
            else 0,
        }
        for variant in variant_users
    }

    return {
        "step_counts": step_counts,
        "conversion_rates_pct": conversion_rates,
        "onboarding_variant_breakdown": onboarding_variant_breakdown,
    }
