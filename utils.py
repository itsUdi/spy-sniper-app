import pandas as pd

def calculate_rsi(prices, period=14):
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def get_market_momentum(rsi):
    if rsi > 60:
        return "Bullish"
    elif rsi < 40:
        return "Bearish"
    else:
        return "Neutral"

def calculate_support_resistance(prices):
    # Basic support/resistance logic using rolling min/max
    recent = pd.Series(prices[-20:])
    support = recent.min()
    resistance = recent.max()
    return support, resistance

def get_best_option_contract(option_chain, spy_price, momentum, support, resistance):
    best_contract = None
    best_score = -float('inf')

    for contract in option_chain:
        option = contract.get('call') if momentum == "Bullish" else contract.get('put')
        if not option: continue

        strike = float(option.get("strikePrice", 0))
        price_diff = abs(strike - spy_price)

        # Only keep contracts 3-4 dollars OTM
        if 3 <= price_diff <= 4:
            volume = float(option.get("volume", 0))
            delta = abs(float(option.get("delta", 0)))
            oi = float(option.get("openInterest", 0))

            # Add bonus if strike is near support/resistance
            sr_bonus = 1.2 if (
                momentum == "Bullish" and support <= strike <= spy_price or
                momentum == "Bearish" and spy_price <= strike <= resistance
            ) else 1.0

            # Scoring model: weight volume, delta, and open interest
            score = (volume * delta * 0.6 + oi * 0.4) * sr_bonus

            if score > best_score:
                best_score = score
                best_contract = option

    return best_contract
