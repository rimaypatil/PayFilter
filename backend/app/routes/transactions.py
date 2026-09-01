"""Transaction scoring route (POST /transactions/check)."""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

# Root proxy imports from Phase 1
from features import extract_single_transaction_features
from backend.app.db.models import RulesConfig
from backend.app.db.repository.audit_repo import AuditRepository
from backend.app.db.repository.rules_repo import RulesRepository
from backend.app.db.repository.transactions_repo import TransactionsRepository
from backend.app.risk_engine.idempotency import IdempotencyChecker
from backend.app.risk_engine.model import MLModelManager, get_model_manager
from backend.app.risk_engine.rules import RuleEngine
from backend.app.risk_engine.scorer import RiskScorer
from backend.app.schemas import TransactionCheckRequest, TransactionCheckResponse

logger = logging.getLogger("payfilter.routes.transactions")
router = APIRouter(prefix="/transactions", tags=["Transactions"])


# Dependency providers
def get_txns_repo() -> TransactionsRepository:
    return TransactionsRepository()


def get_audit_repo() -> AuditRepository:
    return AuditRepository()


def get_rules_repo() -> RulesRepository:
    return RulesRepository()


def get_risk_scorer() -> RiskScorer:
    return RiskScorer()


@router.post(
    "/check",
    response_model=TransactionCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate transaction risk and return decision",
)
def check_transaction(
    request: TransactionCheckRequest,
    txns_repo: TransactionsRepository = Depends(get_txns_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    rules_repo: RulesRepository = Depends(get_rules_repo),
    scorer: RiskScorer = Depends(get_risk_scorer),
    model_manager: MLModelManager = Depends(get_model_manager),
) -> TransactionCheckResponse:
    """Evaluates an incoming AI-agent payment transaction.

    Workflow:
    1. Idempotency check: If transaction_id already exists, return stored decision.
    2. Customer history retrieval: Fetch past transactions strictly prior to t_curr.
    3. Feature extraction: Compute leakage-safe feature vector (features.py).
    4. Deterministic rules check: Evaluate merchant caps and velocity (rules.py).
    5. Scoring decision: Combine rules + ML anomaly model (scorer.py).
    6. Database persistence: Write record to transactions table.
    7. Audit log append: Write cryptographically hash-chained entry to audit_log.
    8. Return structured decision.

    # AUTH: added in Phase 3
    """
    # 1. Idempotency Check
    idempotency = IdempotencyChecker(transactions_repo=txns_repo)
    cached_result = idempotency.check_existing(request.transaction_id)
    if cached_result is not None:
        logger.info(f"Duplicate transaction_id '{request.transaction_id}' detected. Returning cached decision.")
        return cached_result

    # 2. Fetch Customer History strictly before current timestamp
    customer_history_df = txns_repo.get_customer_history(
        customer_id=request.customer_id,
        before_timestamp=request.timestamp,
        merchant_id=request.merchant_id,
    )

    # 3. Extract Leakage-Safe Features
    txn_dict = {
        "customer_id": request.customer_id,
        "amount": request.amount,
        "timestamp": request.timestamp,
        "merchant_category": request.merchant_category,
        "agent_type": request.agent_type,
    }
    feature_vector = extract_single_transaction_features(
        current_txn=txn_dict,
        customer_history_df=customer_history_df,
    )

    # 4. Deterministic Rules Evaluation
    rules_config: RulesConfig = rules_repo.get_rules_config(request.merchant_id)
    rule_engine = RuleEngine(transactions_repo=txns_repo)
    rule_result = rule_engine.evaluate_rules(request, rules_config)

    # 5. ML Scoring & Threshold Decision
    decision_status, risk_score, reason = scorer.score_transaction(
        rule_result=rule_result,
        features=feature_vector,
    )

    # 6. Persist Transaction Record
    txn_record_data = {
        "id": request.transaction_id,
        "merchant_id": request.merchant_id,
        "customer_id": request.customer_id,
        "amount": request.amount,
        "agent_type": request.agent_type,
        "status": decision_status,
        "risk_score": risk_score,
        "reason": reason,
        "model_version": model_manager.model_version,
        "created_at": request.timestamp.isoformat(),
    }
    persisted_txn = txns_repo.create_transaction(txn_record_data)

    # 7. Append to Cryptographic Audit Chain
    audit_entry = audit_repo.append_audit_entry(
        merchant_id=request.merchant_id,
        action=f"transaction_scored:{decision_status}",
        transaction_id=request.transaction_id,
        actor="system",
        created_at=request.timestamp.isoformat(),
    )

    # 8. Return Response
    return TransactionCheckResponse(
        transaction_id=persisted_txn.id,
        status=persisted_txn.status,  # type: ignore
        risk_score=persisted_txn.risk_score,
        reason=persisted_txn.reason,
        audit_log_id=audit_entry.id or "",
    )
