from telethon import TelegramClient, events, functions
import asyncio
import time

# === ДАНІ ===
api_id = 23957413
api_hash = "bc7d03b7a971257f13cb8cc676dabe06"
phone = "+421952160825"
group_id = -1002452764624
main_user_id = 888387442

call_interval = 60
last_call_time = 0
active_call = None

client = TelegramClient("twin_account", api_id, api_hash)

# Перевірка наявності CreateGroupCall (означає, що підтримуються групові дзвінки)
HAS_GROUP_CALL = hasattr(functions.phone, "CreateGroupCall")

async def get_or_create_group_call():
    """Повертає існуючий або створює новий груповий дзвінок (якщо підтримується)"""
    global active_call
    if active_call:
        return active_call

    try:
        chats = await client(functions.phone.GetGroupCallRequest(
            peer=await client.get_entity(group_id),
            limit=1
        ))
        if chats.call:
            active_call = chats.call
            return active_call
    except:
        pass

    if HAS_GROUP_CALL:
        print("🎙 Створюю новий голосовий чат...")
        result = await client(functions.phone.CreateGroupCall(
            peer=await client.get_entity(group_id),
            random_id=client.rnd_id(),
        ))
        active_call = result.call
        return active_call
    else:
        return None

@client.on(events.NewMessage(chats=group_id))
async def handler(event):
    global last_call_time
    now = time.time()

    if now - last_call_time < call_interval:
        print("⏳ Пропускаю — ще не минув інтервал.")
        return

    print(f"📩 Нове повідомлення: {event.message.text}")

    if HAS_GROUP_CALL:
        try:
            call = await get_or_create_group_call()
            if call:
                await client(functions.phone.InviteToGroupCall(
                    call=call,
                    users=[await client.get_entity(main_user_id)]
                ))
                print("📞 Запрошення на груповий дзвінок відправлено!")
            else:
                # Якщо з якоїсь причини не вийшло створити дзвінок — fallback
                await client.send_message(main_user_id, "📞 Дзвінок! Зайди в групу.")
                print("📢 Надіслано пінг у особисті повідомлення (fallback).")
        except Exception as e:
            print("❌ Помилка дзвінка:", e)
            await client.send_message(main_user_id, "📞 Дзвінок! Зайди в групу.")
    else:
        # Fallback для старих версій Telethon — пишемо в ЛС
        await client.send_message(main_user_id, "📞 Дзвінок! Зайди в групу.")
        print("📢 Надіслано пінг у особисті повідомлення.")

    last_call_time = now

async def main():
    await client.start(phone)
    print("✅ Бот запущений. Слухаю групу...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

