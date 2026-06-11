"""Onboarding handler — /start greeting and profile creation flow.

``/start`` greets the user by name and shows the main menu.
The onboarding profile creation flow is triggered separately
via the "Creati una scheda" → "Crea nuovo profilo" menu path.

Onboarding steps:
1. Name input (free text)
2. Height input (cm)
3. Weight input (kg)
4. Body type selection (ectomorph / mesomorph / endomorph)
5. BMI display + continue
6. Experience level selection
7. Training frequency selection
8. Preferred split selection
9. Equipment selection (toggle-based)

Uses ``ConversationHandler`` with inline-keyboard callbacks and
``MessageHandler`` for free-text inputs.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from telegram import CallbackQuery, Update
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from wod.bot.keyboards import (
    bmi_continue_keyboard,
    body_type_keyboard,
    equipment_keyboard,
    expanded_menu_keyboard,
    experience_keyboard,
    frequency_keyboard,
    main_menu_keyboard,
    split_keyboard,
)
from wod.bot.utils import handle_equipment_toggle
from wod.core.bmi import calculate_bmi
from wod.core.types import BodyType, ExperienceLevel, SplitType
from wod.db.models import Base
from wod.db.repositories import (
    get_all_equipment,
    get_or_create_user,
    set_user_equipment,
    update_user_profile,
)
from wod.db.session import get_engine, get_session_factory

logger = logging.getLogger(__name__)

# Conversation states
(
    NAME,
    HEIGHT,
    WEIGHT,
    BODY_TYPE,
    BMI_DISPLAY,
    EXPERIENCE,
    FREQUENCY,
    SPLIT,
    EQUIPMENT,
) = range(9)


# ---------------------------------------------------------------------------
# /start command — greeting + menu (NOT part of ConversationHandler)
# ---------------------------------------------------------------------------


async def start_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — greet user by Telegram name and show the main menu."""
    assert update.effective_user is not None
    assert update.message is not None

    # Ensure tables exist
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_session_factory()() as session:
        await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
        )
        await session.commit()

    first_name = update.effective_user.first_name or "atleta"

    await update.message.reply_text(
        f"Ciao {first_name}! 👋\n\n"
        "Sono *FitBot* 🏋️, il tuo assistente personale di allenamento!\n\n"
        "Ecco cosa posso fare per te:\n"
        "• 🏋️ *Nuova scheda* — crea la tua scheda personalizzata\n"
        "• 👤 *Profilo* — visualizza e modifica il tuo profilo\n"
        "• 🔥 *WOD del giorno* — consulta il tuo allenamento quotidiano\n"
        "• 📜 *Storico* — rivedi le schede passate\n"
        "• ⭐ *Preferiti* — accedi alle schede salvate\n\n"
        "Usa i pulsanti qui sotto per iniziare! 👇",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


# ---------------------------------------------------------------------------
# Onboarding entry point (triggered via menu, not /start)
# ---------------------------------------------------------------------------


async def begin_onboarding(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Begin the onboarding flow — ask for the user's name.

    Triggered by the 'crea:new' callback from the menu choice keyboard.
    """
    query = update.callback_query
    assert query is not None
    await query.answer()

    await query.edit_message_text(
        "🏋️ *Configuriamo il tuo profilo di allenamento!*\n\nCome ti chiami?",
        parse_mode="Markdown",
    )
    return NAME


# ---------------------------------------------------------------------------
# Step 1 — Name (free text)
# ---------------------------------------------------------------------------


async def name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's name input."""
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    name = update.message.text.strip()
    if not name or len(name) > 128:
        await update.message.reply_text(
            "⚠️ Inserisci un nome valido (max 128 caratteri):"
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        f"✅ Nome: *{name}*\n\n" "📏 Qual è la tua altezza in *cm*?\n" "_(es: 175)_",
        parse_mode="Markdown",
    )
    return HEIGHT


# ---------------------------------------------------------------------------
# Step 2 — Height (free text, numeric)
# ---------------------------------------------------------------------------


async def height_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's height input."""
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    try:
        height = float(update.message.text.strip().replace(",", "."))
        if height < 50 or height > 300:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Inserisci un'altezza valida in cm (es: 175):"
        )
        return HEIGHT

    context.user_data["height_cm"] = height

    await update.message.reply_text(
        f"✅ Altezza: *{height:.0f} cm*\n\n"
        "⚖️ Qual è il tuo peso in *kg*?\n"
        "_(es: 72.5)_",
        parse_mode="Markdown",
    )
    return WEIGHT


# ---------------------------------------------------------------------------
# Step 3 — Weight (free text, numeric)
# ---------------------------------------------------------------------------


async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's weight input."""
    assert update.message is not None
    assert update.message.text is not None
    assert context.user_data is not None

    try:
        weight = float(update.message.text.strip().replace(",", "."))
        if weight < 20 or weight > 500:
            raise ValueError("out of range")
    except ValueError:
        await update.message.reply_text("⚠️ Inserisci un peso valido in kg (es: 72.5):")
        return WEIGHT

    context.user_data["weight_kg"] = weight

    await update.message.reply_text(
        f"✅ Peso: *{weight:.1f} kg*\n\n" "Qual è il tuo tipo di corporatura?",
        parse_mode="Markdown",
        reply_markup=body_type_keyboard(),
    )
    return BODY_TYPE


# ---------------------------------------------------------------------------
# Step 4 — Body Type (inline keyboard)
# ---------------------------------------------------------------------------

_BODY_TYPE_LABELS = {
    BodyType.ECTOMORPH: "Ectomorfo",
    BodyType.MESOMORPH: "Mesomorfo",
    BodyType.ENDOMORPH: "Endomorfo",
}


async def body_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle body type selection and show BMI."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    assert context.user_data is not None

    body_str = query.data.split(":")[1]
    body = BodyType(body_str)
    context.user_data["body_type"] = body

    # Calculate BMI
    height_cm = context.user_data["height_cm"]
    weight_kg = context.user_data["weight_kg"]
    bmi_value, bmi_category = calculate_bmi(weight_kg, height_cm)
    context.user_data["bmi_value"] = bmi_value
    context.user_data["bmi_category"] = bmi_category

    body_label = _BODY_TYPE_LABELS[body]
    await query.edit_message_text(
        f"✅ Corporatura: *{body_label}*\n\n"
        f"📊 *Il tuo BMI: {bmi_value}* — _{bmi_category}_\n\n"
        "Ora configuriamo il tuo allenamento!",
        parse_mode="Markdown",
        reply_markup=bmi_continue_keyboard(),
    )
    return BMI_DISPLAY


# ---------------------------------------------------------------------------
# Step 5 — BMI Display → Continue to Experience
# ---------------------------------------------------------------------------


async def bmi_continue_callback(
    update: Update, _context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle BMI continue button — move to experience selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    await query.edit_message_text(
        "Qual è il tuo livello di esperienza?",
        reply_markup=experience_keyboard(),
    )
    return EXPERIENCE


# ---------------------------------------------------------------------------
# Step 6 — Experience Level (inline keyboard)
# ---------------------------------------------------------------------------


async def experience_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle experience level selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    level_str = query.data.split(":")[1]
    level = ExperienceLevel(level_str)

    # Store in user_data for the session
    assert context.user_data is not None
    context.user_data["experience_level"] = level

    await query.edit_message_text(
        f"✅ Livello: *{level.value.title()}*\n\n"
        "Quanti giorni a settimana vuoi allenarti?",
        parse_mode="Markdown",
        reply_markup=frequency_keyboard(),
    )
    return FREQUENCY


# ---------------------------------------------------------------------------
# Step 7 — Training Frequency (inline keyboard)
# ---------------------------------------------------------------------------


async def frequency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle training frequency selection."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    freq = int(query.data.split(":")[1])
    assert context.user_data is not None
    context.user_data["training_frequency"] = freq

    await query.edit_message_text(
        f"✅ Frequenza: *{freq} giorni/settimana*\n\n"
        "Scegli il tipo di split settimanale:",
        parse_mode="Markdown",
        reply_markup=split_keyboard(frequency=freq),
    )
    return SPLIT


# ---------------------------------------------------------------------------
# Step 8 — Split Type (inline keyboard)
# ---------------------------------------------------------------------------


async def split_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle split type selection, then show equipment selector."""
    query = update.callback_query
    assert query is not None
    await query.answer()

    assert query.data is not None
    split_str = query.data.split(":")[1]
    split_type = SplitType(split_str)
    assert context.user_data is not None
    context.user_data["preferred_split"] = split_type

    # Load equipment from DB
    async with get_session_factory()() as session:
        all_eq = await get_all_equipment(session)
        eq_list = [(eq.id, eq.name) for eq in all_eq]

    context.user_data["equipment_list"] = eq_list
    context.user_data["selected_equipment"] = set()

    split_label = split_type.value.replace("_", " ").title()
    await query.edit_message_text(
        f"✅ Split: *{split_label}*\n\n"
        "Seleziona l'attrezzatura disponibile nella tua Home Gym.\n"
        "Tocca per selezionare/deselezionare, poi conferma:",
        parse_mode="Markdown",
        reply_markup=equipment_keyboard(eq_list, set()),
    )
    return EQUIPMENT


# ---------------------------------------------------------------------------
# Step 9 — Equipment Selection (toggle-based inline keyboard)
# ---------------------------------------------------------------------------


async def equipment_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """Handle equipment toggle or confirmation."""
    query = update.callback_query
    assert query is not None
    assert query.data is not None
    assert context.user_data is not None

    data = query.data.split(":")[1]

    if data == "done":
        selected = context.user_data.get("selected_equipment", set())
        if not selected:
            await query.answer(
                text="⚠️ Seleziona almeno un attrezzo per procedere!",
                show_alert=True,
            )
            return EQUIPMENT
        await query.answer()
        # Save everything to DB
        return await _finalize_onboarding(query, context)

    await query.answer()
    handle_equipment_toggle(context.user_data, data)

    selected = context.user_data["selected_equipment"]
    eq_list = context.user_data["equipment_list"]
    try:
        await query.edit_message_text(
            "Seleziona l'attrezzatura disponibile nella tua Home Gym.\n"
            "Tocca per selezionare/deselezionare, poi conferma:",
            reply_markup=equipment_keyboard(eq_list, selected),
        )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise

    return EQUIPMENT


# ---------------------------------------------------------------------------
# Finalization
# ---------------------------------------------------------------------------


async def _finalize_onboarding(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Persist all onboarding data and end the conversation."""
    assert query.from_user is not None
    assert context.user_data is not None

    async with get_session_factory()() as session:
        user = await get_or_create_user(session, telegram_id=query.from_user.id)
        await update_user_profile(
            session,
            user,
            name=context.user_data.get("name"),
            height_cm=context.user_data.get("height_cm"),
            weight_kg=context.user_data.get("weight_kg"),
            body_type=context.user_data.get("body_type"),
            experience_level=context.user_data["experience_level"],
            training_frequency=context.user_data["training_frequency"],
            preferred_split=context.user_data["preferred_split"],
        )
        selected_ids = list(context.user_data.get("selected_equipment", set()))
        if selected_ids:
            await set_user_equipment(session, user, selected_ids)
        await session.commit()

    name = context.user_data.get("name", "—")
    height = context.user_data.get("height_cm", 0)
    weight = context.user_data.get("weight_kg", 0)
    bmi_value = context.user_data.get("bmi_value", "—")
    bmi_cat = context.user_data.get("bmi_category", "")
    # pyrefly: ignore [no-matching-overload]
    body_label = _BODY_TYPE_LABELS.get(
        cast(BodyType, context.user_data.get("body_type")), "—"
    )
    level = context.user_data["experience_level"].value.title()
    freq = context.user_data["training_frequency"]
    split_label = context.user_data["preferred_split"].value.replace("_", " ").title()
    eq_count = len(context.user_data.get("selected_equipment", set()))

    await query.edit_message_text(
        "🎉 *Profilo configurato!*\n\n"
        f"📛 Nome: {name}\n"
        f"📏 Altezza: {height:.0f} cm\n"
        f"⚖️ Peso: {weight:.1f} kg\n"
        f"📊 BMI: {bmi_value} ({bmi_cat})\n"
        f"🦴 Corporatura: {body_label}\n"
        f"• Livello: {level}\n"
        f"• Frequenza: {freq} giorni/settimana\n"
        f"• Split: {split_label}\n"
        f"• Attrezzatura: {eq_count} elementi\n\n"
        "⏳ *Generazione della scheda in corso...*",
        parse_mode="Markdown",
    )

    # Re-show the main menu keyboard
    assert query.message is not None
    from telegram import Message  # pylint: disable=import-outside-toplevel

    if isinstance(query.message, Message):
        try:
            update_id = int(query.id)
        except (ValueError, TypeError):
            update_id = 0

        # Delegate to wod_command to generate a workout for the new profile
        fake_update = Update(
            update_id=update_id,
            message=query.message,
        )
        # Set effective_user manually
        # pylint: disable=protected-access
        fake_update._effective_user = query.from_user
        # pylint: enable=protected-access

        # pylint: disable=import-outside-toplevel
        from wod.bot.handlers.wod import wod_command

        await wod_command(fake_update, context)

        # Show the expanded menu keyboard so they have options ready
        await query.message.reply_text(
            "📋 *Menu completo:*",
            parse_mode="Markdown",
            reply_markup=expanded_menu_keyboard(),
        )
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


async def cancel_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the onboarding conversation."""
    assert update.message is not None
    await update.message.reply_text(
        "❌ Configurazione annullata. Usa /start per ricominciare."
    )
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# ConversationHandler builder
# ---------------------------------------------------------------------------


def build_start_handler() -> CommandHandler[Any, Any]:
    """Build the /start command handler (greeting + menu)."""
    return CommandHandler("start", start_command)


def build_onboarding_handler() -> ConversationHandler[ContextTypes.DEFAULT_TYPE]:
    """Build and return the ConversationHandler for onboarding.

    Entry point is the ``crea:new`` callback from the menu choice keyboard.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(begin_onboarding, pattern=r"^crea:new$"),
        ],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    name_input,
                )
            ],
            HEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    height_input,
                )
            ],
            WEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    weight_input,
                )
            ],
            BODY_TYPE: [CallbackQueryHandler(body_type_callback, pattern=r"^body:")],
            BMI_DISPLAY: [
                CallbackQueryHandler(bmi_continue_callback, pattern=r"^bmi:")
            ],
            EXPERIENCE: [CallbackQueryHandler(experience_callback, pattern=r"^exp:")],
            FREQUENCY: [CallbackQueryHandler(frequency_callback, pattern=r"^freq:")],
            SPLIT: [CallbackQueryHandler(split_callback, pattern=r"^split:")],
            EQUIPMENT: [CallbackQueryHandler(equipment_callback, pattern=r"^equip:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        per_message=False,
    )
