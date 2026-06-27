"""Minimal feature-flag / A-B assignment service (stands in for LaunchDarkly/Eppo).

Assignment is deterministic per user+experiment via hashing, then persisted so
a user always sees the same variant on repeat visits.
"""

import hashlib

from sqlalchemy.orm import Session

from app.models.models import Assignment, Experiment

DEFAULT_EXPERIMENTS: dict[str, list[str]] = {
    "onboarding_flow": ["control", "guided_tutorial"],
}


def _hash_bucket(user_id: str, experiment_key: str, num_buckets: int) -> int:
    digest = hashlib.sha256(f"{user_id}:{experiment_key}".encode()).hexdigest()
    return int(digest, 16) % num_buckets


def get_or_create_experiment(db: Session, key: str) -> Experiment:
    experiment = db.query(Experiment).filter(Experiment.key == key).first()
    if experiment:
        return experiment
    variants = DEFAULT_EXPERIMENTS.get(key, ["control", "variant"])
    experiment = Experiment(key=key, variants=",".join(variants))
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def assign_variant(db: Session, user_id: str, experiment_key: str) -> str:
    existing = (
        db.query(Assignment)
        .filter(Assignment.user_id == user_id, Assignment.experiment_key == experiment_key)
        .first()
    )
    if existing:
        return existing.variant

    experiment = get_or_create_experiment(db, experiment_key)
    variants = experiment.variants.split(",")
    variant = variants[_hash_bucket(user_id, experiment_key, len(variants))]

    assignment = Assignment(user_id=user_id, experiment_key=experiment_key, variant=variant)
    db.add(assignment)
    db.commit()
    return variant
