import os
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN")

watchlist = {}

def get_player_id(player_name):
    url = f"https://www.futbin.com/search?year=26&term={player_name}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200 and "player_id" in r.text:
        try:
            pid = r.text.split('player_id":')[1].split(",")[0]
            return pid.strip()
        except:
            return None
    return None

def get_player_info(player_id):
    url = f"https://www.futbin.com/26/playerPrices?player={player_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        if str(player_id) in data:
            prices = data[str(player_id)]["prices"]["ps"]["LCPrice"]
            image = f"https://cdn.futbin.com/content/fifa26/img/players/{player_id}.png"
            return int(prices.replace(",", "")), image
    return None, None

async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("اكتب الاسم + السعر\nمثال:\n/watch Kimmich 20000")
        return

    player_name = " ".join(context.args[:-1])
    target_price = int(context.args[-1])

    pid = get_player_id(player_name)
    if not pid:
        await update.message.reply_text("⚠️ اللاعب غير موجود في Futbin.")
        return

    watchlist[player_name] = {"target": target_price, "id": pid}
    await update.message.reply_text(f"✅ أضفت {player_name} للمتابعة (سعر: {target_price})")

async def list_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not watchlist:
        await update.message.reply_text("ما فيه لاعبين تحت المراقبة.")
        return

    msg = "📋 قائمة اللاعبين:\n"
    for i, (name, data) in enumerate(watchlist.items(), 1):
        msg += f"{i}. {name} - {data['target']}\n"
    await update.message.reply_text(msg)

async def unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("اكتب رقم اللاعب من /list")
        return

    try:
        idx = int(context.args[0]) - 1
        key = list(watchlist.keys())[idx]
        del watchlist[key]
        await update.message.reply_text(f"❌ تم حذف {key} من المتابعة.")
    except:
        await update.message.reply_text("رقم غير صحيح.")

async def price_checker(app):
    while True:
        for name, data in list(watchlist.items()):
            price, image = get_player_info(data["id"])
            if price and price >= data["target"]:
                await app.bot.send_photo(
                    chat_id=app.chat_id,
                    photo=image,
                    caption=f"{name} السعر: {price} ✅"
                )
        time.sleep(600)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.application.chat_id = update.message.chat_id
    await update.message.reply_text("👋 أهلا! أرسل /watch لإضافة لاعب.\n/list لعرض القائمة.\n/unwatch لحذف لاعب.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("watch", watch))
    app.add_handler(CommandHandler("list", list_watch))
    app.add_handler(CommandHandler("unwatch", unwatch))

    Thread(target=lambda: app.run_polling()).start()
    Thread(target=lambda: app.run_async(price_checker(app))).start()

if __name__ == "__main__":
    main()
