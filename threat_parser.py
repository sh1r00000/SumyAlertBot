import re
from typing import Optional


# Завершение конкретной угрозы
CLEAR_PATTERNS = (
    r"\bвідбій\b",
    r"\bзагроз\w*\s+минула\b",
    r"\bне\s+фіксу\w*\b",
    r"\bбільше\s+не\s+фіксу\w*\b",
)

# БпЛА
DRONE_PATTERNS = (
    r"\bбпла\b",
    r"\bбезпілот\w*\b",
    r"\bшахед\w*\b",
    r"\bгербер\w*\b",
    r"\bдрон\w*\b",
    r"\bреактивн\w*\s+бпла\b",
)

# КАБи / керовані авіабомби
KAB_PATTERNS = (
    r"\bкаб\w*\b",
    r"\bуаб\w*\b",
    r"\bфаб\w*\b",
    r"\bкерован\w*\s+авіаційн\w*\s+бомб\w*\b",
    r"\bавіабомб\w*\b",
)

# Ракети та балістика
MISSILE_PATTERNS = (
    r"\bракет\w*\b",
    r"\bбаліст\w*\b",
    r"\bкрилат\w*\b",
    r"\bкалібр\w*\b",
    r"\bкинджал\w*\b",
    r"\bшвидкісн\w*\s+ціл\w*\b",
)

# Тактична авіація та авіаційні засоби ураження
AVIATION_PATTERNS = (
    r"\bтактичн\w*\s+авіаці\w*\b",
    r"\bавіаційн\w*\s+засоб\w*\s+уражен\w*\b",
    r"\bактивність\s+ворож\w*\s+авіаці\w*\b",
)

# Загальна загроза без уточненого типу
GENERAL_THREAT_PATTERNS = (
    r"\bзагроз\w*\b",
    r"\bнебезпек\w*\b",
    r"\bпуск\w*\b",
)


# Прямі згадки міста та району
MAIN_TARGET_PATTERNS = (
    r"\bсуми\b",
    r"\bм\.?\s*суми\b",
    r"\bсумськ\w*\s+район\w*\b",
)

# Населені пункти та центри громад Сумського району,
# які найчастіше зустрічаються в повідомленнях.
LOCAL_TARGET_PATTERNS = (
    r"\bбездрик\w*\b",
    r"\bбілопілл\w*\b",
    r"\bверхн\w*\s+сироват\w*\b",
    r"\bворожб\w*\b",
    r"\bкраснопілл\w*\b",
    r"\bлебедин\w*\b",
    r"\bмиколаївк\w*\b",
    r"\bмиропілл\w*\b",
    r"\bнижн\w*\s+сироват\w*\b",
    r"\bстепанівк\w*\b",
    r"\bхотін\w*\b",
    r"\bюнаківк\w*\b",
    r"\bтокар\w*\b",
    r"\bстецьківк\w*\b",
    r"\bкосівщин\w*\b",
    r"\bпіщан\w*\b",
    r"\bпушкарівк\w*\b",
    r"\bмогриц\w*\b",
    r"\bкияниц\w*\b",
    r"\bбасівк\w*\b",
    r"\bвелик\w*\s+чернеччин\w*\b",
    r"\bверхн\w*\s+піщан\w*\b",
    r"\bнизи\b",
)


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in patterns
    )


def _clean_line(line: str) -> str:
    line = " ".join(line.split()).strip()

    # Удаляем ссылки
    line = re.sub(
        r"https?://\S+|t\.me/\S+",
        "",
        line,
        flags=re.IGNORECASE,
    )

    return line.strip()


def _detect_event_type(text: str) -> Optional[str]:
    if _matches(text, CLEAR_PATTERNS):
        return "clear"

    if _matches(text, KAB_PATTERNS):
        return "kab"

    if _matches(text, MISSILE_PATTERNS):
        return "missile"

    if _matches(text, DRONE_PATTERNS):
        return "drone"

    if _matches(text, AVIATION_PATTERNS):
        return "aviation"

    if _matches(text, GENERAL_THREAT_PATTERNS):
        return "general"

    return None


def _is_target_line(line: str) -> bool:
    return (
        _matches(line, MAIN_TARGET_PATTERNS)
        or _matches(line, LOCAL_TARGET_PATTERNS)
    )


def extract_sumy_event(message: str) -> Optional[dict]:
    """
    Извлекает только строки официального сообщения,
    относящиеся к Сумам или Сумскому району.

    Например, из сообщения:

        БпЛА на Харківщині.
        БпЛА курсом на Суми.
        БпЛА на Полтавщині.

    вернётся только:

        БпЛА курсом на Суми.
    """
    raw_lines = (message or "").splitlines()

    lines = [
        _clean_line(line)
        for line in raw_lines
        if _clean_line(line)
    ]

    if not lines:
        return None

    full_text = " ".join(lines)
    event_type = _detect_event_type(full_text)

    if event_type is None:
        return None

    relevant_lines = [
        line
        for line in lines
        if _is_target_line(line)
    ]

    if not relevant_lines:
        return None

    # Убираем одинаковые строки с сохранением порядка
    unique_lines = []

    for line in relevant_lines:
        if line not in unique_lines:
            unique_lines.append(line)

    return {
        "type": event_type,
        "lines": unique_lines,
    }