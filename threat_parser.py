import re
from typing import Optional


# =========================
# ТИПЫ СОБЫТИЙ
# =========================

CLEAR_PATTERNS = (
    r"\bвідбій\b",
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
    # Город Сумы
    r"\bсуми\b",
    r"\bсумах\b",
    r"\bсумами\b",
    r"\bсумам\b",
    r"\bм\.?\s*суми\b",
    r"\bміст\w*\s+суми\b",

    # Формы вроде «до Сум», «на Сум»
    r"\b(?:на|до|у|в|для|біля|поблизу)\s+сум\b",

    # Сумщина
    r"\bсумщин\w*\b",

    # Сумская область
    r"\bсумськ\w*\s+област\w*\b",
    r"\bсумск\w*\s+област\w*\b",

    # Сумский район
    r"\bсумськ\w*\s+район\w*\b",
    r"\bсумск\w*\s+район\w*\b",

    # Сумское направление
    r"\bсумськ\w*\s+напрям\w*\b",
    r"\bсумск\w*\s+направлен\w*\b",

    # Курс и направление на Сумы
    r"\bнапрям\w*\s+(?:на|до)\s+сум(?:и|ах|ами|ам)?\b",
    r"\bкурс\w*\s+(?:на|до)\s+сум(?:и|ах|ами|ам)?\b",
)


# Населённые пункты Сумского района
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
    line = re.sub(
        r"https?://\S+|t\.me/\S+",
        "",
        line,
        flags=re.IGNORECASE,
    )

    return " ".join(line.split()).strip()


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


def extract_sumy_events(message: str) -> list[dict]:
    """
    Извлекает из одного сообщения все отдельные события,
    относящиеся к Сумам, Сумскому району или Сумщине.

    Тип угрозы определяется для каждой строки отдельно.

    Если строка с географией не содержит тип угрозы,
    используется ближайшая предыдущая строка-контекст.
    """

    lines = [
        cleaned
        for raw_line in (message or "").splitlines()
        if (cleaned := _clean_line(raw_line))
    ]

    if not lines:
        return []

    # Если во всём сообщении найден только один конкретный
    # тип угрозы, его можно использовать как запасной.
    explicit_types = [
        event_type
        for line in lines
        if (
            event_type := _detect_event_type(line)
        ) not in (None, "general")
    ]

    unique_explicit_types = list(
        dict.fromkeys(explicit_types)
    )

    fallback_type = (
        unique_explicit_types[0]
        if len(unique_explicit_types) == 1
        else None
    )

    grouped: dict[str, list[str]] = {}

    current_type: Optional[str] = None
    current_context: Optional[str] = None

    for line in lines:
        explicit_type = _detect_event_type(line)

        # Запоминаем ближайший заголовок или строку
        # с конкретным типом угрозы.
        if explicit_type and explicit_type != "general":
            current_type = explicit_type
            current_context = line

        elif (
            explicit_type == "general"
            and current_type is None
        ):
            current_type = "general"
            current_context = line

        # Строки не про Сумы пропускаем.
        if not _is_target_line(line):
            continue

        if explicit_type and explicit_type != "general":
            event_type = explicit_type
        else:
            event_type = (
                current_type
                or fallback_type
                or explicit_type
            )

        if event_type is None:
            continue

        event_lines = grouped.setdefault(
            event_type,
            [],
        )

        # Если перед строкой был заголовок вроде
        # «Рух ударних БпЛА:», добавляем его для понятности.
        if (
            current_context
            and current_context != line
            and current_context not in event_lines
        ):
            event_lines.append(current_context)

        if line not in event_lines:
            event_lines.append(line)

    return [
        {
            "type": event_type,
            "lines": event_lines,
        }
        for event_type, event_lines in grouped.items()
        if event_lines
    ]