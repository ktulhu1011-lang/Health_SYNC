from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_log_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚬 Вредные привычки", callback_data="cat:bad_habits")],
        [InlineKeyboardButton("💊 Добавки", callback_data="cat:supplements")],
        [InlineKeyboardButton("🥗 Питание", callback_data="cat:nutrition")],
        [InlineKeyboardButton("💧 Вода", callback_data="cat:water")],
        [InlineKeyboardButton("🧘 Активности / самочувствие", callback_data="cat:wellbeing")],
        [InlineKeyboardButton("✅ Готово", callback_data="log:done")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="log:menu")],
    ])


# --- Bad Habits ---

def smoking_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Не курил ✅", callback_data="habit:smoking:0")],
        [InlineKeyboardButton("Курил", callback_data="habit:smoking:ask_count")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:bad_habits")],
    ])


def alcohol_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Не пил ✅", callback_data="habit:alcohol:0")],
        [InlineKeyboardButton("1 бокал", callback_data="habit:alcohol:1")],
        [InlineKeyboardButton("2–3 бокала", callback_data="habit:alcohol:2-3")],
        [InlineKeyboardButton("4+ бокала", callback_data="habit:alcohol:4+")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:bad_habits")],
    ])


def sweets_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Не ел ✅", callback_data="habit:sweets:0")],
        [InlineKeyboardButton("Немного (1 раз)", callback_data="habit:sweets:1")],
        [InlineKeyboardButton("Много (2+ раза)", callback_data="habit:sweets:2+")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:bad_habits")],
    ])


def fastfood_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Нет ✅", callback_data="habit:fastfood:0")],
        [InlineKeyboardButton("Да", callback_data="habit:fastfood:1")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:bad_habits")],
    ])


def screen_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Выключил до 22:00 ✅", callback_data="habit:screen_bedtime:before_22")],
        [InlineKeyboardButton("До 23:00", callback_data="habit:screen_bedtime:before_23")],
        [InlineKeyboardButton("После 23:00", callback_data="habit:screen_bedtime:after_23")],
        [InlineKeyboardButton("Смотрел в кровати", callback_data="habit:screen_bedtime:in_bed")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:bad_habits")],
    ])


def coffee_count_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Не пил ✅", callback_data="habit:coffee:0")],
        [InlineKeyboardButton("1 чашка", callback_data="habit:coffee_count:1")],
        [InlineKeyboardButton("2 чашки", callback_data="habit:coffee_count:2")],
        [InlineKeyboardButton("3+ чашки", callback_data="habit:coffee_count:3+")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:bad_habits")],
    ])


def coffee_time_keyboard(count: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("До 14:00 ✅", callback_data=f"habit:coffee:{count}:before14")],
        [InlineKeyboardButton("После 14:00", callback_data=f"habit:coffee:{count}:after14")],
    ])


def bad_habits_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚬 Курение", callback_data="bh:smoking")],
        [InlineKeyboardButton("🍷 Алкоголь", callback_data="bh:alcohol")],
        [InlineKeyboardButton("🍭 Сладкое", callback_data="bh:sweets")],
        [InlineKeyboardButton("🍔 Фастфуд / джанк", callback_data="bh:fastfood")],
        [InlineKeyboardButton("📱 Экран перед сном", callback_data="bh:screen")],
        [InlineKeyboardButton("☕ Кофе", callback_data="bh:coffee")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="log:menu")],
    ])


# --- Supplements ---

def supplements_group_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧘 Антистресс", callback_data="supp:group:antistress")],
        [InlineKeyboardButton("🛡 Антиоксиданты", callback_data="supp:group:antioxidants")],
        [InlineKeyboardButton("⚡ Базовые", callback_data="supp:group:basic")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="log:menu")],
    ])


SUPPLEMENT_GROUPS = {
    "antistress": [
        ("ashwagandha", "Ashwagandha (KSM-66)"),
        ("magnesium", "Magnesium Glycinate"),
        ("theanine", "L-Theanine"),
        ("rhodiola", "Rhodiola Rosea"),
        ("gaba", "GABA"),
        ("b_complex", "Vitamin B-Complex"),
        ("melatonin", "Мелатонин"),
        ("5htp", "5-HTP"),
    ],
    "antioxidants": [
        ("vitamin_c", "Vitamin C"),
        ("vitamin_e", "Vitamin E"),
        ("ala", "Alpha Lipoic Acid"),
        ("coq10", "CoQ10"),
        ("resveratrol", "Resveratrol"),
        ("nac", "NAC"),
    ],
    "basic": [
        ("vitamin_d3k2", "Vitamin D3 + K2"),
        ("omega3", "Omega-3"),
        ("zinc", "Zinc"),
    ],
}


def supplement_list_keyboard(group: str, taken: set, active: set) -> InlineKeyboardMarkup:
    supps = SUPPLEMENT_GROUPS.get(group, [])
    rows = []
    for key, label in supps:
        if active and key not in active:
            continue
        emoji = "✅" if key in taken else "⬜"
        rows.append([InlineKeyboardButton(
            f"{emoji} {label}",
            callback_data=f"supp:toggle:{group}:{key}"
        )])
    rows.append([InlineKeyboardButton("◀️ Назад к группам", callback_data="cat:supplements")])
    return InlineKeyboardMarkup(rows)


# --- Nutrition ---

def nutrition_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍭 Сладкое", callback_data="nutr:sweets")],
        [InlineKeyboardButton("🍔 Фастфуд", callback_data="nutr:fastfood")],
        [InlineKeyboardButton("🌙 Переел на ночь", callback_data="nutr:late_eating")],
        [InlineKeyboardButton("🕐 Еда за 2ч до сна", callback_data="nutr:pre_sleep_eating")],
        [InlineKeyboardButton("⭐ Качество питания", callback_data="nutr:quality")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="log:menu")],
    ])


def nutr_sweets_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Не ел ✅", callback_data="habit:nutrition_sweets:0")],
        [InlineKeyboardButton("Немного", callback_data="habit:nutrition_sweets:1")],
        [InlineKeyboardButton("Много", callback_data="habit:nutrition_sweets:2+")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:nutrition")],
    ])


def nutr_fastfood_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Нет ✅", callback_data="habit:nutrition_fastfood:0")],
        [InlineKeyboardButton("Да", callback_data="habit:nutrition_fastfood:1")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:nutrition")],
    ])


def nutr_late_eating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Нет ✅", callback_data="habit:late_eating:0")],
        [InlineKeyboardButton("Поел после 20:00", callback_data="habit:late_eating:after20")],
        [InlineKeyboardButton("Поел после 22:00", callback_data="habit:late_eating:after22")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:nutrition")],
    ])


def nutr_pre_sleep_eating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Нет, не ел ✅", callback_data="habit:pre_sleep_eating:0")],
        [InlineKeyboardButton("Лёгкий перекус", callback_data="habit:pre_sleep_eating:1")],
        [InlineKeyboardButton("Полноценная еда", callback_data="habit:pre_sleep_eating:2")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:nutrition")],
    ])


def nutr_quality_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥦 Отлично", callback_data="habit:nutrition_quality:3")],
        [InlineKeyboardButton("😐 Норм", callback_data="habit:nutrition_quality:2")],
        [InlineKeyboardButton("🍕 Плохо", callback_data="habit:nutrition_quality:1")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:nutrition")],
    ])


# --- Water ---

def water_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("< 1 л", callback_data="habit:water:0")],
        [InlineKeyboardButton("1–1.5 л", callback_data="habit:water:1")],
        [InlineKeyboardButton("1.5–2 л", callback_data="habit:water:2")],
        [InlineKeyboardButton("2+ л ✅", callback_data="habit:water:3")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="log:menu")],
    ])


# --- Wellbeing ---

def wellbeing_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧘 Медитация", callback_data="wb:meditation")],
        [InlineKeyboardButton("🚶 Прогулка", callback_data="wb:walk")],
        [InlineKeyboardButton("😊 Самочувствие", callback_data="wb:feeling")],
        [InlineKeyboardButton("😤 Уровень стресса", callback_data="wb:stress")],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="log:menu")],
    ])


def meditation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Нет", callback_data="habit:meditation:0")],
        [InlineKeyboardButton("5–10 мин", callback_data="habit:meditation:10")],
        [InlineKeyboardButton("10–20 мин", callback_data="habit:meditation:20")],
        [InlineKeyboardButton("20+ мин ✅", callback_data="habit:meditation:30")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:wellbeing")],
    ])


def walk_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Нет", callback_data="habit:walk:0")],
        [InlineKeyboardButton("До 30 мин", callback_data="habit:walk:20")],
        [InlineKeyboardButton("30+ мин ✅", callback_data="habit:walk:40")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:wellbeing")],
    ])


def feeling_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("😴 1", callback_data="habit:feeling:1"),
            InlineKeyboardButton("😐 2", callback_data="habit:feeling:2"),
            InlineKeyboardButton("🙂 3", callback_data="habit:feeling:3"),
            InlineKeyboardButton("😊 4", callback_data="habit:feeling:4"),
            InlineKeyboardButton("🌟 5", callback_data="habit:feeling:5"),
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:wellbeing")],
    ])


def stress_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😌 Низкий", callback_data="habit:subjective_stress:1")],
        [InlineKeyboardButton("😐 Средний", callback_data="habit:subjective_stress:2")],
        [InlineKeyboardButton("😟 Высокий", callback_data="habit:subjective_stress:3")],
        [InlineKeyboardButton("😰 Очень высокий", callback_data="habit:subjective_stress:4")],
        [InlineKeyboardButton("◀️ Назад", callback_data="cat:wellbeing")],
    ])
