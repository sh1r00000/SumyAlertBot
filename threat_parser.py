SUMY_LOCATIONS = [
    "суми",
    "сумщина",
    "сумській області",
    "сумський район",
    "токарі",
    "хотінь",
    "степанівка",
    "піщане",
    "садки",
    "косівщина",
    "бездрик",
    "верхня сироватка",
    "нижня сироватка",
    "стецьківка",
    "юнаківка",
    "миропілля",
    "краснопілля",
    "білопілля",
    "роменська",
    "центр",
    "над містом",
    "курс місто",
    "місто"
]


def parse_message(source, message):
    text = message.lower()

    result = {
        "type": None,
        "status": None,
        "confidence": 0,
        "sumy_related": False
    }

    # ==========================
    # Проверка связи с Сумами
    # ==========================

    if any(location in text for location in SUMY_LOCATIONS):
        result["sumy_related"] = True

    # Общие сообщения по области тоже оставляем
    if any(word in text for word in [
        "по області",
        "в області",
        "сумщина",
        "сумській області"
    ]):
        result["sumy_related"] = True

    # ==========================
    # Определение типа угрозы
    # ==========================

    # БПЛА / шахеды
    if any(word in text for word in [
        "шахед",
        "шах",
        "бпла",
        "дрон",
        "мопед",
        "гербера",
        "гербер",
        "тополя"
    ]):
        result["type"] = "drone"

    # Ракеты
    elif any(word in text for word in [
        "ракета",
        "ракети",
        "баліст",
        "крилата",
        "крилаті"
    ]):
        result["type"] = "missile"

    # КАБы
    elif any(word in text for word in [
        "каб",
        "керован",
        "авіабомб",
        "авіаційних бомб",
        "уаб"
    ]):
        result["type"] = "kab"

    # ==========================
    # Определение статуса
    # ==========================

    # Отбой
    if any(word in text for word in [
        "не фіксується",
        "більше не фіксується",
        "зник",
        "покинув область",
        "покинув місто",
        "відбій"
    ]):
        result["status"] = "ended"

    # Работа ПВО, взрывы, прилеты
    elif any(word in text for word in [
        "ппо",
        "йде робота",
        "робота",
        "вибух",
        "вибухи",
        "уєбало",
        "приліт",
        "прильот"
    ]):
        result["status"] = "engaged"

    # Активная угроза
    else:
        result["status"] = "active"

    # ==========================
    # Доверие к источнику
    # ==========================

    if source == "kpszsu":
        result["confidence"] = 3
    elif source == "sumyregion":
        result["confidence"] = 2
    elif source == "ZhenyokSay":
        result["confidence"] = 1
    else:
        result["confidence"] = 0

    return result