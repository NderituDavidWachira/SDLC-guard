"""Business rules for risk: kept out of views so they are easy to unit test."""
from collections import Counter

SEVERITY_WEIGHTS = {'Critical': 10, 'High': 7, 'Medium': 4, 'Low': 1}
OPEN_STATUSES = ('open', 'investigating')


def classify_severity(score):
    """Map a 0-10 score to Critical / High / Medium / Low."""
    if isinstance(score, bool) or not 0 <= score <= 10:
        raise ValueError('score must be between 0 and 10')
    if score >= 9:
        return 'Critical'
    if score >= 7:
        return 'High'
    if score >= 4:
        return 'Medium'
    return 'Low'


def risk_score(severities):
    """Pillar risk score 0-100: weighted sum of open finding severities, capped."""
    counts = Counter(severities)
    unknown = set(counts) - set(SEVERITY_WEIGHTS)
    if unknown:
        raise ValueError(f'unknown severity: {sorted(unknown)}')
    return min(100, sum(SEVERITY_WEIGHTS[s] * n for s, n in counts.items()))


def risk_level(score):
    """Translate a 0-100 risk score into a label (Low <20, Medium <30, High <45)."""
    if not 0 <= score <= 100:
        raise ValueError('risk score must be between 0 and 100')
    if score >= 45:
        return 'Critical'
    if score >= 30:
        return 'High'
    if score >= 20:
        return 'Medium'
    return 'Low'
