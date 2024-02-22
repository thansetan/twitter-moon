def float_or_none(value: str | None):
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
