import re
from typing import Optional


# =========================
# ТИПЫ СОБЫТИЙ
# =========================

CLEAR_PATTERNS = (
    r"\bвідбій\b",
    r"\bвідбій\s+загроз\w*\b",
    r"\bзагроз\w*\s+минула\b",
    r"\bне\s+фіксу\w*\b",
    r"\bбільше\s+не\s+фіксу\w*\b",
)

DRONE_PATTERNS = (
    r"\bбпла\b",
    r"\bбезпілот\w*\b",
    r"\bшахед\w*\b",
    r"\bгербер\w*\b",
    r"\bдрон\w*\b",
    r"\bреактивн\w*\s+бпла\b",
)

KAB_PATTERNS = (
    r"\bкаб\w*\b",
    r"\bуаб\w*\b",
    r"\bфаб\w*\b",
    r"\bкерован\w*\s+авіаційн\w*\s+бомб\w*\b",
    r"\bкерован\w*\s+авіабомб\w*\b",
    r"\bавіабомб\w*\b",
)

MISSILE_PATTERNS = (
    r"\bракет\w*\b",
    r"\bбаліст\w*\b",
    r"\bкрилат\w*\b",
    r"\bкалібр\w*\b",
    r"\bкинджал\w*\b",
    r"\bаеробаліст\w*\b",
    r"\bшвидкісн\w*\s+ціл\w*\b",
)

AVIATION_PATTERNS = (
    r"\bтактичн\w*\s+авіаці\w*\b",
    r"\bавіаційн\w*\s+засоб\w*\s+уражен\w*\b",
    r"\bактивність\s+ворож\w*\s+авіаці\w*\b",
)

GENERAL_THREAT_PATTERNS = (
    r"\bзагроз\w*\b",
    r"\bнебезпек\w*\b",
    r"\bпуск\w*\b",
)


# =========================
# СУМЫ, РАЙОН И ОБЛАСТЬ
# =========================

SUMY_TARGET_PATTERNS = (
    # Город Сумы во всех основных падежах
    r"\bсуми\b",
    r"\bсум\b",
    r"\bсумах\b",
    r"\bсумами\b",
    r"\bсумам\b",
    r"\bм\.?\s*суми\b",
    r"\bміст\w*\s+суми\b",

    # Сумщина во всех падежах
    r"\bсумщин\w*\b",

    # Сумская область — украинские формы
    r"\bсумськ\w*\s+област\w*\b",

    # Сумская область — русские формы
    r"\bсумск\w*\s+област\w*\b",

    # Сумский район
    r"\bсумськ\w*\s+район\w*\b",
    r"\bсумск\w*\s+район\w*\b",

    # Сумское направление
    r"\bсумськ\w*\s+напрям\w*\b",
    r"\bсумск\w*\s+направлен\w*\b",

    # Направление или курс на Сумы
    r"\bнапрям\w*\s+(?:на|до)\s+сум(?:и|ах|ами|ам)?\b",
    r"\bкурс\w*\s+(?:на|до)\s+сум(?:и|ах|ами|ам)?\b",
)


# Населённые пункты Сумского района,
# которые могут встречаться в сообщениях Воздушных сил
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
        _matches(line, SUMY_TARGET_PATTERNS)
        or _matches(line, LOCAL_TARGET_PATTERNS)
    )


def extract_sumy_event(message: str) -> Optional[dict]:
    """
    Извлекает из официального сообщения только строки,
    которые относятся к Сумам, Сумскому району
    или Сумской области.

    Пример:

        БпЛА на Харківщині.
        БпЛА курсом на Суми.
        КАБи на Сумщину.

    В канал попадут только две последние строки.
    """

    raw_lines = (message or "").splitlines()

    lines = []

    for raw_line in raw_lines:
        clean_line = _clean_line(raw_line)

        if clean_line:
            lines.append(clean_line)

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

    # Убираем одинаковые строки,
    # сохраняя первоначальный порядок
    unique_lines = []

    for line in relevant_lines:
        if line not in unique_lines:
            unique_lines.append(line)

    return {
        "type": event_type,
        "lines": unique_lines,
    }