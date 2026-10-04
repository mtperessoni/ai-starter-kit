"""PAY-03, PAY-04: the fake payment gateway, driven by the token prefix."""
from decimal import Decimal

from market.features.payments.payment_models import GatewayResult

APPROVED = "approved"
TIMEOUT = "gateway_timeout"


def _approve(token: str) -> GatewayResult:
    return GatewayResult(True, APPROVED, f"GW-{token}")


def _decline(code: str) -> GatewayResult:
    return GatewayResult(False, code, None)


def _flaky_limit(token: str) -> int | None:
    """The N of a flaky_N token, or None when the token is not of that shape."""
    suffix = token[len("flaky_"):]
    return int(suffix) if suffix.isdigit() else None


def authorize(method: str, token: str, amount: Decimal, attempt: int) -> GatewayResult:
    """Decide one authorization attempt (attempts count from 1).

    Tokens:
      ok_*            approves with reference GW-<token>;
      decline_*       declines card_declined;
      fraud_*         declines suspected_fraud;
      flaky_N         times out on attempts 1 to N, then approves;
      timeout_always  times out on every attempt;
      anything else   declines invalid_token.

    A timeout is an unapproved result with code gateway_timeout; the caller decides to retry (PAY-04).
    """
    if amount <= 0 or attempt < 1:
        return _decline("invalid_request")
    if token.startswith("ok_"):
        return _approve(token)
    if token.startswith("decline_"):
        return _decline("card_declined")
    if token.startswith("fraud_"):
        return _decline("suspected_fraud")
    if token == "timeout_always":
        return _decline(TIMEOUT)
    if token.startswith("flaky_"):
        limit = _flaky_limit(token)
        if limit is None:
            return _decline("invalid_token")
        return _decline(TIMEOUT) if attempt <= limit else _approve(token)
    return _decline("invalid_token")


def describe_token(token: str) -> str:
    """What the fake gateway will do with a token, for test authors and logs.

        describe_token("flaky_2") -> "times out twice, then approves"
    """
    if token.startswith("ok_"):
        return "approves"
    if token.startswith("decline_"):
        return "declines as card_declined"
    if token.startswith("fraud_"):
        return "declines as suspected_fraud"
    if token == "timeout_always":
        return "always times out"
    if token.startswith("flaky_") and _flaky_limit(token) is not None:
        count = _flaky_limit(token)
        return f"times out {'once' if count == 1 else 'twice' if count == 2 else f'{count} times'}, then approves"
    return "declines as invalid_token"
