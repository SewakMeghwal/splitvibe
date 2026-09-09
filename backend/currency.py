"""
Multi-Currency Foreign Exchange Engine
Provides exchange rates and currency conversion across USD, EUR, GBP, JPY, CAD.
"""

# Base currency: USD
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 148.50,
    "CAD": 1.35,
    "AUD": 1.52
}

def convert_currency(amount: float, from_curr: str, to_curr: str = "USD") -> float:
    """
    Converts amount from_curr to to_curr using base USD rates.
    """
    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    rate_from = EXCHANGE_RATES.get(from_curr, 1.0)
    rate_to = EXCHANGE_RATES.get(to_curr, 1.0)

    # Convert to USD first, then to target currency
    amount_in_usd = amount / rate_from
    converted = amount_in_usd * rate_to

    return round(converted, 2)
