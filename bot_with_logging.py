import os
import requests
import logging
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update

# إعداد نظام اللوقز
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

watchlist = {}

def start(update: Update, context: CallbackContext):
    update.message.reply_text("⚽️ FIFA Bot جاهز! استخدم /watch <اسم اللاعب> <السعر> لمتابعة الأسعار.")

def watch(update: Update, context: CallbackContext):
    try:
        if len(context.args) < 2:
            update.message.reply_text("❌ الصيغة: /watch <اسم اللاعب> <السعر>")
            return
        player = context.args[0]
        price = int(context.args[1])
        watchlist[player] = price
        update.message.reply_text(f"✅ تمت إضافة {player} بالسعر {price} للمراقبة.")
    except Exception as e:
        logger.error(f"خطأ في /watch: {e}")
        update.message.reply_text("❌ صار خطأ، تأكد من الأوامر.")

def unwatch(update: Update, context: CallbackContext):
    try:
        if not context.args:
            update.message.reply_text("❌ الصيغة: /unwatch <اسم اللاعب>")
            return
        player = context.args[0]
        if player in watchlist:
            del watchlist[player]
            update.message.reply_text(f"🗑️ تم حذف {player} من المراقبة.")
        else:
            update.message.reply_text("❌ اللاعب غير موجود في القائمة.")
    except Exception as e:
        logger.error(f"خطأ في /unwatch: {e}")

def check_prices(context: CallbackContext):
    for player, target_price in list(watchlist.items()):
        try:
            url = f"https://www.futbin.com/search?query={player}"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                # هذا مثال فقط (السكربت الحقيقي يحتاج scraping أدق)
                current_price = 20000  
                if current_price >= target_price:
                    context.bot.send_message(
                        chat_id=context.job.context,
                        text=f"📸 {player} السعر الحالي: {current_price} ✅"
                    )
            else:
                logger.warning(f"فشل جلب بيانات {player}, كود: {r.status_code}")
        except Exception as e:
            logger.error(f"خطأ أثناء جلب الأسعار لـ {player}: {e}")

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("watch", watch))
    dp.add_handler(CommandHandler("unwatch", unwatch))

    updater.job_queue.run_repeating(check_prices, interval=600, first=10, context=updater.bot.id)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
