from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import feedparser
from time import mktime
from datetime import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler  # Import the scheduler

# BOT TOKKENS
TOKEN = "7961912258:AAG7wiDpZzGSdZZFun_hk6GVZ4bGSz96wxA"  # BOT TOKEN

# --- Get weather information using Open-Meteo API ---
def get_weather_by_location(lat, lon):
    # إرسال طلب للحصول على بيانات الطقس
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&temperature_unit=celsius&windspeed_unit=kmh&hourly=temperature_2m,relative_humidity_2m"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        
        current_weather = data["current_weather"]
        temperature = current_weather.get("temperature", "N/A")
        weather_description = current_weather.get("weathercode", "N/A")
        wind_speed = current_weather.get("windspeed", "N/A")
        humidity = current_weather.get("relative_humidity_2m", "N/A") 

        # التنسيق
        weather_text = (
            f"الطقس الحالي:\n"
            f"الحرارة: {temperature}°C\n"
            f"الطقس: {weather_description}\n"
            f"الرطوبة: {humidity}%\n"
            f"الرياح: {wind_speed} كم/س"
        )
        return weather_text
    else:
        return "حدث خطأ أثناء جلب البيانات من Open-Meteo."

# --- Get the latest news ---
async def fetch_news():
    entries = []

    # Apple Developer News
    try:
        apple_feed = feedparser.parse("https://developer.apple.com/news/rss/news.rss")
        for entry in apple_feed.entries:
            entries.append({
                'source': 'Apple',
                'title': entry.title,
                'link': entry.link,
                'date': entry.published_parsed
            })
    except Exception as e:
        print(f"خطأ في جلب أخبار Apple: {e}")

    # Hacking with Swift
    try:
        swift_feed = feedparser.parse("https://www.hackingwithswift.com/articles.rss")
        for entry in swift_feed.entries:
            entries.append({
                'source': 'Hacking with Swift',
                'title': entry.title,
                'link': entry.link,
                'date': entry.published_parsed
            })
    except Exception as e:
        print(f"خطأ في جلب أخبار Hacking with Swift: {e}")

    # iOS Dev Weekly
    try:
        ios_weekly_feed = feedparser.parse("https://iosdevweekly.com/issues.rss")
        for entry in ios_weekly_feed.entries:
            entries.append({
                'source': 'iOS Dev Weekly',
                'title': entry.title,
                'link': entry.link,
                'date': entry.published_parsed
            })
    except Exception as e:
        print(f"خطأ في جلب أخبار iOS Dev Weekly: {e}")

    # News Arrange
    entries.sort(key=lambda x: x['date'], reverse=True)

    # OutPut Layout
    news_list = []
    for item in entries[:5]:  # Last 5 News
        date_str = datetime.fromtimestamp(mktime(item['date'])).strftime("%Y-%m-%d %H:%M")
        news_list.append(
            f"📅 التاريخ: {date_str}\n"
            f"📢 المصدر: {item['source']}\n"
            f"📰 العنوان: {item['title']}\n"
            f"🔗 الرابط: {item['link']}\n"
            "----"
        )

    return "\n".join(news_list) if news_list else "لا توجد أخبار جديدة حاليًا."

# --- Send News every hour ---
def send_news_to_users(application: Application):
    """Send the latest news to the users"""
    news_text = fetch_news()
    if news_text != "لا توجد أخبار جديدة حاليًا.":
        # Here, you can send the news to specific users (you need to store their user_ids)
        # For now, I'll assume you have a list of user IDs (e.g., from database or file)
        user_ids = [123456789]  # Example user IDs (replace with actual user IDs)
        
        for user_id in user_ids:
            application.bot.send_message(chat_id=user_id, text=f"📰 *أحدث الأخبار*\n\n{news_text}", parse_mode="Markdown")

# --- Set up the scheduler ---
def start_news_scheduler(application: Application):
    scheduler = BackgroundScheduler()
    # Use the `application` directly to call the bot's methods
    scheduler.add_job(send_news_to_users, 'interval', hours=1, args=[application])
    scheduler.start()


# --- BOT START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("مشاركة الموقع", request_location=True)],  # زر لمشاركة الموقع
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "مرحبًا! 🚀\n"
        "- شارك موقعك للحصول على حالة الطقس.\n"
        "- أرسل /news لمعرفة أحدث أخبار Swift وiOS.\n"
        "- أرسل /weather لعرض حالة الطقس باستخدام الموقع.\n"
        "- أرسل /help لمعرفة أوامر البوت.",
        reply_markup=reply_markup
    )

# --- BOT WEATHER_COMMAND ---
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # مشاركة الموقع
    await update.message.reply_text("شارك موقعك الحالي للحصول على حالة الطقس.")

# --- Handle Location Command ---
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # استقبال الموقع
    location = update.message.location
    if not location:
        await update.message.reply_text("لم يتم استلام الموقع. حاول مرة أخرى.")
        return

    # الحصول على الطقس باستخدام الموقع
    weather_info = get_weather_by_location(location.latitude, location.longitude)
    await update.message.reply_text(weather_info)

# --- BOT NEWS COMMAND ---
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض آخر 5 أخبار من مصادر iOS."""
    news_text = await fetch_news()
    message = "📰 *آخر 5 أخبار في عالم iOS وSwift:*\n\n" + news_text
    await update.message.reply_text(message, parse_mode="Markdown")

# --- BOT HELP COMMAND ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 *مساعدة*\n\n"
        "الأوامر المتاحة:\n"
        "• /start - بدء التفاعل مع البوت\n"
        "• /news - عرض أحدث أخبار Swift وiOS\n"
        "• /weather - عرض حالة الطقس باستخدام الموقع\n"
        "• /help - عرض هذه الرسالة\n\n"
        "📍 يمكنك أيضًا الضغط على زر 'مشاركة الموقع'."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

# --- All Commands ---
if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))

    # Start the scheduler to send news every hour
    start_news_scheduler(application)

    application.run_polling()