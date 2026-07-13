import re
from typing import Optional

from threat_parser import extract_sumy_events


DRONE_PATTERN = re.compile(
    r"\b(?:"
    r"бпла|"
    r"безпілот\w*|"
    r"шахед\w*|"
    r"дрон\w*"
    r")\b",
    flags=re.IGNORECASE,
)


SUMY_CLEAR_GEOGRAPHY_PATTERNS = (
    r"\bсуми\b",
    r"\bсумах\b",
    r"\bсумами\b",
    r"\bнад\s+сумами\b",
    r"\bпо\s+сумах\b",
    r"\bсумськ\w*\s+район\w*\b",
    r"\bрайон\w*\s+сум\b",
)


CLEAR_PATTERNS = (
    r"\b(?:бпла|шахед\w*|дрон\w*)"
    r".{0,50}"
    r"(?:не\s+фіксуються|"
    r"не\s+спостерігаються|"
    r"відсутні|"
    r"локаційно\s+чисто|"
    r"локально\s+чисто)\b",

    r"\b(?:по\s+)?"
    r"(?:бпла|шахед\w*|дрон\w*)"
    r".{0,30}"
    r"\bчисто\b",

    r"\b(?:локаційно|локально)\s+чисто"
    r".{0,30}"
    r"(?:по\s+)?"
    r"(?:бпла|шахед\w*|дрон\w*)\b",
)


MULTIPLE_WORD_PATTERNS = (
    r"\b(?:кілька|декілька|багато)"
    r".{0,30}"
    r"(?:бпла|шахед\w*|дрон\w*)\b",

    r"\b(?:група|групи|групами)"
    r".{0,30}"
    r"(?:бпла|шахед\w*|дрон\w*)\b",

    r"\b(?:бпла|шахед\w*|дрон\w*)"
    r".{0,30}"
    r"(?:кілька|декілька|багато)\b",
)


COUNT_PATTERN = re.compile(
    r"\b(\d{1,2})\s+"
    r"(?:\w+\s+){0,2}"
    r"(?:бпла|шахед\w*|дрон\w*)\b",
    flags=re.IGNORECASE,
)


def _matches(
    text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def _has_multiple_drones(text: str) -> bool:
    for match in COUNT_PATTERN.finditer(text):
        try:
            count = int(match.group(1))

        except ValueError:
            continue

        if count >= 2:
            return True

    return _matches(
        text,
        MULTIPLE_WORD_PATTERNS,
    )


def parse_sumygo_message(
    message: str,
) -> Optional[dict]:
    text = " ".join(
        (message or "").split()
    )

    if not text:
        return None

    has_drone_word = bool(
        DRONE_PATTERN.search(text)
    )

    has_clear_geography = _matches(
        text,
        SUMY_CLEAR_GEOGRAPHY_PATTERNS,
    )

    # Завершение локальной угрозы принимаем
    # только при прямом упоминании Сум
    # или Сумского района.
    if (
        has_drone_word
        and has_clear_geography
        and _matches(text, CLEAR_PATTERNS)
    ):
        return {
            "action": "clear",
        }

    # Для сообщения о нескольких БпЛА
    # используем основной фильтр географии.
    sumy_events = extract_sumy_events(text)

    has_sumy_drone_event = any(
        event_data.get("type") == "drone"
        for event_data in sumy_events
    )

    if (
        has_sumy_drone_event
        and _has_multiple_drones(text)
    ):
        return {
            "action": "multiple",
        }

    return None