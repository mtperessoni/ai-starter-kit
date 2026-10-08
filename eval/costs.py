"""Cost of a run split by the role of the agent that spent it (main, surveyor, docs, executor, reviewer)."""

# USD per million tokens: input, output, cache write, cache read
PRICES = {"opus": (5.0, 25.0, 6.25, 0.5), "sonnet": (3.0, 15.0, 3.75, 0.3), "haiku": (1.0, 5.0, 1.25, 0.1)}
DEFAULT_FAMILY = "sonnet"


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0


def family(model):
    name = str(model or "").lower()
    return next((f for f in PRICES if f in name), DEFAULT_FAMILY)


def price(model, usage):
    p_in, p_out, p_write, p_read = PRICES[family(model)]
    return (_num(usage.get("input_tokens")) * p_in + _num(usage.get("output_tokens")) * p_out
            + _num(usage.get("cache_creation_input_tokens")) * p_write
            + _num(usage.get("cache_read_input_tokens")) * p_read) / 1_000_000


def role_costs(messages, model_usage=None):
    """{role: usd} from `messages`, a list of (role, model, usage). Each message is priced by its model's table,
    then every model's total is scaled to the `costUSD` the result reports for it (cache tiers and rate changes
    stay exact); a reported model with no message adds to main."""
    raw, per_model = {}, {}
    for role, model, usage in messages:
        c = price(model, usage)
        raw[(role, model)] = raw.get((role, model), 0.0) + c
        per_model[model] = per_model.get(model, 0.0) + c
    reported = {k: _num(v.get("costUSD")) for k, v in (model_usage or {}).items()
                if isinstance(v, dict) and _num(v.get("costUSD"))}
    out = {}
    for (role, model), c in raw.items():
        scale = reported[model] / per_model[model] if model in reported and per_model[model] > 0 else 1.0
        out[role] = out.get(role, 0.0) + c * scale
    for model, usd in reported.items():
        if model not in per_model:
            out["main"] = out.get("main", 0.0) + usd
    return out
