
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ===== НАСТРОЙКИ =====

BOT_TOKEN = "8863985861:AAHo_2ZP4bllTF55eSt6Yv3bZqQfRcn69YE"
CHANNEL_ID = "@USERNAME_ТВОЕГО_КАНАЛА"
CHANNEL_URL = "https://t.me/USERNAME_ТВОЕГО_КАНАЛА"

QUESTIONS = [
    "Вопрос 1. Как давно ты играешь в Standoff 2?",
    "Вопрос 2. Какой у тебя игровой ранг?",
    "Вопрос 3. Какой нож тебе интересен?",
    "Вопрос 4. Как часто ты играешь?",
    "Вопрос 5. Почему ты хочешь получить нож?",
]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Form(StatesGroup):
    questions = State()
    game_id = State()
    screenshot = State()


def subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📢 Подписаться",
                url=CHANNEL_URL
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Я уже подписан",
                callback_data="check_subscription"
            )
        ]
    ])


def next_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data="next"
            )
        ]
    ])


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "🎁 Розыгрыш ножа в Standoff 2!\n\n"
        "Для участия подпишись на наш Telegram-канал, "
        "а затем нажми кнопку проверки подписки.",
        reply_markup=subscription_keyboard()
    )


@dp.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery):
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_ID,
            user_id=callback.from_user.id
        )

        subscribed = member.status in (
            "member", "administrator", "creator"
        )

    except Exception:
        await callback.answer(
            "Не удалось проверить подписку. "
            "Попробуй ещё раз позже.",
            show_alert=True
        )
        return

    if not subscribed:
        await callback.answer(
            "Вы ещё не подписаны на канал!",
            show_alert=True
        )
        return

    await callback.message.answer(
        "✅ Подписка подтверждена!\n\n"
        "Теперь можно перейти к вопросам.",
        reply_markup=next_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "next")
async def begin_questions(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.update_data(question_index=0, answers=[])

    await state.set_state(Form.questions)

    await callback.message.answer(
        "📝 Вопрос 1 из 5\n\n" + QUESTIONS[0]
    )
    await callback.answer()


@dp.message(Form.questions)
async def process_question(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer("Пожалуйста, отправь ответ текстом.")
        return

    data = await state.get_data()
    answers = data.get("answers", [])
    answers.append(message.text)

    index = data.get("question_index", 0) + 1

    await state.update_data(
        answers=answers,
        question_index=index
    )

    if index < len(QUESTIONS):
        await message.answer(
            f"📝 Вопрос {index + 1} из 5\n\n"
            + QUESTIONS[index]
        )
        return

    await state.set_state(Form.game_id)

    await message.answer(
        "🎮 Все 5 вопросов пройдены!\n\n"
        "Теперь отправь свой игровой ID Standoff 2."
    )


@dp.message(Form.game_id)
async def process_game_id(
    message: Message,
    state: FSMContext
):
    if not message.text:
        await message.answer("Отправь игровой ID текстовым сообщением.")
        return

    await state.update_data(game_id=message.text)
    await state.set_state(Form.screenshot)

    await message.answer(
        "✅ Игровой ID получен.\n\n"
        "Если для участия предусмотрено официальное подтверждение, "
        "отправь его скриншот сюда.\n\n"
        "Не отправляй данные банковской карты, пароли "
        "или коды подтверждения."
    )


@dp.message(Form.screenshot, F.photo)
async def process_screenshot(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    await message.answer(
        "📨 Фото успешно отправлено на проверку модерации.\n\n"
        "Ожидай ответа модератора. Проверка может занять "
        "10–15 минут."
    )

    # Здесь можно добавить пересылку заявки модератору.
    # Например, отправлять game_id и фото в закрытый чат команды.

    await state.clear()


@dp.message(Form.screenshot)
async def screenshot_reminder(message: Message):
    await message.answer(
        "Пожалуйста, отправь изображение скриншота фотографией."
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
