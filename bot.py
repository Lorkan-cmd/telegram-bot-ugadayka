import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class GameStates(StatesGroup):
    choosing_level = State()
    guessing = State()


def get_guess_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Больше", callback_data="more"),
            InlineKeyboardButton(text="🎯 Угадал!", callback_data="correct"),
            InlineKeyboardButton(text="📉 Меньше", callback_data="less")
        ]
    ])
    return keyboard


def get_level_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1️⃣ От 1 до 100", callback_data="level_100"),
            InlineKeyboardButton(text="2️⃣ От 1 до 1000", callback_data="level_1000"),
            InlineKeyboardButton(text="3️⃣ От 1 до 10000", callback_data="level_10000")
        ]
    ])
    return keyboard


@dp.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        " <b>Игра-угадайка!</b>\n\n"
        "Загадай число, а я попробую его угадать за минимальное количество попыток.\n\n"
        "Выбери уровень сложности:",
        reply_markup=get_level_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(GameStates.choosing_level)


@dp.callback_query(F.data.startswith("level_"), GameStates.choosing_level)
async def process_level_choice(callback: types.CallbackQuery, state: FSMContext):
    max_num = int(callback.data.split("_")[1])
    await state.update_data(min_num=1, max_num=max_num, attempts=0)

    await callback.message.edit_text(
        f"Отлично! Загадай число от 1 до {max_num}.\n\n"
        "Я начинаю угадывать! Нажимай кнопки, чтобы подсказать мне."
    )

    await state.set_state(GameStates.guessing)
    await make_guess(callback.message, state)


async def make_guess(message: types.Message, state: FSMContext):
    data = await state.get_data()
    min_num = data['min_num']
    max_num = data['max_num']
    attempts = data['attempts']

    guess = (min_num + max_num) // 2
    attempts += 1

    await state.update_data(attempts=attempts, current_guess=guess)

    await message.answer(
        f" Попытка #{attempts}\n\n"
        f"Ты загадал число <b>{guess}</b>?\n\n"
        f"(Диапазон: {min_num} - {max_num})",
        reply_markup=get_guess_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.in_(["more", "less", "correct"]), GameStates.guessing)
async def process_guess(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    min_num = data['min_num']
    max_num = data['max_num']
    current_guess = data['current_guess']

    if callback.data == "correct":
        await callback.message.edit_text(
            f"🎉 <b>Ура! Я угадал!</b>\n\n"
            f"Ты загадал число <b>{current_guess}</b>.\n"
            f"Мне понадобилось попыток: <b>{data['attempts']}</b>\n\n"
            f"Хочешь сыграть еще раз? Нажми /start",
            parse_mode="HTML"
        )
        await state.clear()

    elif callback.data == "more":
        new_min = current_guess + 1
        if new_min > max_num:
            await callback.message.edit_text("🤨 Кажется, ты жульничаешь... Давай начнем заново! Напиши /start")
            await state.clear()
            return
        await state.update_data(min_num=new_min)
        await callback.message.edit_text(f"Понял, число больше {current_guess}. Думаю дальше...")
        await make_guess(callback.message, state)

    elif callback.data == "less":
        new_max = current_guess - 1
        if new_max < min_num:
            await callback.message.edit_text("🤨 Кажется, ты жульничаешь... Давай начнем заново! Напиши /start")
            await state.clear()
            return
        await state.update_data(max_num=new_max)
        await callback.message.edit_text(f"Понял, число меньше {current_guess}. Думаю дальше...")
        await make_guess(callback.message, state)


async def main():
    print(" Бот-угадайка успешно запущен!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")