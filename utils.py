def discipline_labels(discipline: str, variants: list[str]) -> list[str]:
    labels = []
    seen = set()
    for value in [discipline, *variants]:
        cleaned = " ".join(value.strip().split())
        if cleaned and cleaned.casefold() not in seen:
            seen.add(cleaned.casefold())
            labels.append(cleaned)
    return labels
