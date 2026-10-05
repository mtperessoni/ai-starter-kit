"""Tax feature: regional rates and the tax calculation (TAX-01 to TAX-05)."""
from market.features.tax.tax_calculator import TaxResult, compute_tax
from market.features.tax.tax_rates import rate_for

__all__ = ["TaxResult", "compute_tax", "rate_for"]
