"""Rolling multi-turn risk context without unbounded accumulation."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import Interaction, SessionRiskState, utcnow


def previous_session_context(db: Session, session_id: str) -> dict[str, object]:
    rows = list(
        db.scalars(
            select(Interaction)
            .where(Interaction.session_id == session_id)
            .order_by(desc(Interaction.created_at))
            .limit(5)
        )
    )
    unsupported = sum(float(row.risks.get("hallucination", 0)) >= 0.55 for row in rows)
    weights = [0.40, 0.25, 0.16, 0.11, 0.08]
    rolling = sum(row.overall_risk * weights[index] for index, row in enumerate(rows))
    reason = (
        f"Session risk is elevated because {unsupported} of the previous {len(rows)} turns contained unsupported or contradicted claims."
        if unsupported >= 2
        else "No compounding-risk escalation is active for this session."
    )
    return {"rolling_risk": round(rolling, 3), "previous_turns": len(rows), "risky_claim_turns": unsupported, "elevated": unsupported >= 2, "explanation": reason}


def update_session_state(db: Session, session_id: str, context: dict[str, object], decision: str) -> None:
    state = db.get(SessionRiskState, session_id)
    if state is None:
        state = SessionRiskState(session_id=session_id)
        db.add(state)
    state.rolling_risk = float(context["rolling_risk"])
    state.recent_event_count = int(context["previous_turns"]) + 1
    state.elevated_reason = str(context["explanation"])
    state.previous_decisions = ([decision] + list(state.previous_decisions or []))[:5]
    state.updated_at = utcnow()
