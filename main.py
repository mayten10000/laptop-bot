import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from database import init_db, save_search
from aiogram.fsm.storage.memory import MemoryStorage
from database import get_search_history

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Ошибка: BOT_TOKEN не найден в .env файле!")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

class LaptopSearch(StatesGroup):
    waiting_for_specs = State()


@dp.callback_query(F.data == "show_search_history")
async def show_search_history(call: types.CallbackQuery):
    try:
        user_id = call.from_user.id
        history = get_search_history(user_id)
        if history:
            history_text = "\n".join([f"{i+1}. {entry['query']}" for i, entry in enumerate(history)])
            await call.message.answer(f"Ваша история поиска:\n{history_text}")
        else:
            await call.message.answer("Ваша история поиска пуста.")
    except Exception as e:
        logging.error(f"Ошибка в show_search_history: {e}")
        await call.message.answer("Ошибка при получении истории поиска. Попробуйте позже.")


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Найти ноутбук", callback_data="find_laptop")],
            [InlineKeyboardButton(text="⚖️ Сравнить ноутбуки", callback_data="compare_laptops")],
            [InlineKeyboardButton(text="🔍 Показать историю", callback_data="show_search_history")]
        ])
        await message.answer("Привет! Я помогу найти и сравнить ноутбуки. Выбери действие:", reply_markup=keyboard)
    except Exception as e:
        logging.error(f"Ошибка в send_welcome: {e}")
        await message.answer("Ошибка при обработке команды. Попробуйте позже.")

@dp.message(Command("help"))
async def send_help(message: types.Message):
    try:
        help_text = (
            "💡 Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/history - Показать историю поиска\n"
            "/help - Показать справку\n\n"
            "📌 Вы также можете воспользоваться кнопками для поиска и сравнения ноутбуков."
        )
        await message.answer(help_text)
    except Exception as e:
        logging.error(f"Ошибка в send_help: {e}")
        await message.answer("Ошибка при обработке команды. Попробуйте позже.")

@dp.callback_query(F.data == "find_laptop")
async def find_laptop(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.answer("Введите характеристики ноутбука (например: 'игры, до 100 000 руб, RTX 4060'):")
        await state.set_state(LaptopSearch.waiting_for_specs)
    except Exception as e:
        logging.error(f"Ошибка в find_laptop: {e}")
        await call.message.answer("Ошибка при обработке запроса. Попробуйте позже.")
        await state.clear()

@dp.message(LaptopSearch.waiting_for_specs)
async def process_laptop_specs(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        user_specs = message.text
        logging.info(f"Сохранение запроса от пользователя {user_id}: {user_specs}")
        save_search(user_id, user_specs)
        await message.answer(f"🔍 Ищу ноутбуки по запросу: {user_specs}\n(Пример: MSI Katana 17, ASUS TUF 15)")
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка в process_laptop_specs: {e}")
        await message.answer("Ошибка при обработке запроса. Попробуйте позже.")

@dp.callback_query(F.data == "compare_laptops")
async def compare_laptops(call: types.CallbackQuery):
    try:
        await call.message.answer("Введите модели ноутбуков для сравнения через запятую (например: 'MSI Katana 17, ASUS TUF 15'):")
    except Exception as e:
        logging.error(f"Ошибка в compare_laptops: {e}")
        await call.message.answer("Ошибка при обработке запроса. Попробуйте позже.")

@dp.callback_query(F.text)
async def process_comparison_request(message: types.Message):
    try:
        laptop_models = message.text.split(", ")
        if len(laptop_models) < 2:
            await message.answer("❌ Пожалуйста, введите хотя бы две модели ноутбуков для сравнения.")
            return

        #Заглушка

        await message.answer(f"🔎 Сравниваю ноутбуки: {', '.join(laptop_models)}\n(Пример сравнения: характеристики, цена и т.д.)")
    except Exception as e:
        logging.error(f"Ошибка в process_comparison_request: {e}")
        await message.answer("Ошибка при обработке запроса. Попробуйте позже.")


async def main():
    try:
        await asyncio.to_thread(init_db)
        logging.info("База данных инициализирована успешно.")

        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(1)

        await dp.start_polling(bot)
    except Exception as e:
        logging.critical(f"Критическая ошибка в работе бота: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Ошибка при запуске бота: {e}")