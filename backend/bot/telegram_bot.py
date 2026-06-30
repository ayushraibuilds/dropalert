import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import settings

logger = logging.getLogger(__name__)

# Lazy initialized supabase
supabase = None
def get_supabase():
    global supabase
    if not supabase:
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return supabase


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    chat_id = update.effective_chat.id
    welcome_text = (
        "🎮 <b>Welcome to DropAlert!</b> 🚨\n\n"
        "I will notify you instantly when gaming consoles (PS5, PS5 Pro, Xbox) or graphics cards go in stock in India!\n\n"
        "<b>Available Commands:</b>\n"
        "🔹 /status - Check current stock across all retailers\n"
        "🔹 /subscribe - Subscribe this chat to restock alerts\n"
        "🔹 /unsubscribe - Unsubscribe from alerts\n"
        "🔹 /help - Show this guide\n\n"
        f"Your Telegram Chat ID: <code>{chat_id}</code>\n"
        "Use this ID on the website to configure custom alert filters!"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display current stock status."""
    db = get_supabase()
    if not db:
        await update.message.reply_text("Database connection is currently unavailable.")
        return

    try:
        # Fetch active products & URLs
        urls_resp = db.table("product_retailer_urls").select(
            "retailer, url, products(slug, name)"
        ).eq("is_active", True).execute()
        
        mappings = urls_resp.data
        if not mappings:
            await update.message.reply_text("No products are currently being tracked.")
            return

        # Fetch status from cached states
        # For simplicity, we query the latest stock event or cached statuses
        # Let's import status cache helpers from main to see status
        from main import get_cached_status

        status_report = "🎮 <b>Live Stock Status (DropAlert)</b>\n\n"
        
        # Group by product
        products_dict = {}
        for m in mappings:
            prod = m.get("products")
            if not prod:
                continue
            slug = prod["slug"]
            name = prod["name"]
            retailer = m["retailer"]
            url = m["url"]
            
            if slug not in products_dict:
                products_dict[slug] = {"name": name, "retailers": []}
            
            cached = get_cached_status(retailer, slug)
            in_stock = cached.get("in_stock", False) if cached else False
            price = cached.get("price") if cached else None
            
            products_dict[slug]["retailers"].append({
                "name": retailer.upper(),
                "in_stock": in_stock,
                "price": price,
                "url": url
            })

        for slug, prod_info in products_dict.items():
            status_report += f"📦 <b>{prod_info['name']}</b>\n"
            for ret in prod_info["retailers"]:
                emoji = "🟢" if ret["in_stock"] else "🔴"
                status_str = f"In Stock (₹{ret['price']:,})" if ret["in_stock"] and ret["price"] else ("In Stock" if ret["in_stock"] else "Out of Stock")
                monetized_url = inject_affiliate_link(ret["url"], ret["name"].lower())
                status_report += f"  {emoji} {ret['name']}: <a href='{monetized_url}'>{status_str}</a>\n"
            status_report += "\n"

        await update.message.reply_text(status_report, parse_mode="HTML", disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error handling /status command: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while fetching status report.")


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe current chat to notifications."""
    chat_id = str(update.effective_chat.id)
    db = get_supabase()
    if not db:
        await update.message.reply_text("Database is currently unavailable.")
        return

    try:
        # Check if already subscribed
        resp = db.table("subscribers").select("*").eq("telegram_id", chat_id).execute()
        
        # Get all active product slugs
        prod_resp = db.table("products").select("slug").eq("is_active", True).execute()
        active_slugs = [p["slug"] for p in prod_resp.data] if prod_resp.data else ["ps5-disc", "ps5-digital", "ps5-pro"]

        if resp.data:
            await update.message.reply_text(
                "You are already subscribed to alerts! Use /status to check current stock."
            )
        else:
            # Create a subscriber entry using telegram chat ID
            db.table("subscribers").insert({
                "telegram_id": chat_id,
                "products": active_slugs,
                "retailers": [],  # All
                "tier": "free",
                "is_active": True
            }).execute()
            
            await update.message.reply_text(
                "✅ <b>Subscribed successfully!</b>\n\n"
                "You will receive instant alerts in this chat whenever a tracked item comes in stock.\n"
                "Use /status to see current availability.",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error subscribing user via TG: {e}", exc_info=True)
        await update.message.reply_text("Failed to create subscription. Please try again later.")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe chat from alerts."""
    chat_id = str(update.effective_chat.id)
    db = get_supabase()
    if not db:
        await update.message.reply_text("Database is currently unavailable.")
        return

    try:
        db.table("subscribers").delete().eq("telegram_id", chat_id).execute()
        await update.message.reply_text("❌ You have been unsubscribed from all stock drop alerts.")
    except Exception as e:
        logger.error(f"Error unsubscribing user: {e}", exc_info=True)
        await update.message.reply_text("Failed to remove subscription.")


# Helper import to prevent circular dependency
def inject_affiliate_link(url: str, retailer: str) -> str:
    from services.notification_service import inject_affiliate_link as ial
    return ial(url, retailer)


async def init_telegram_app() -> Optional[Application]:
    """Initialize and return python-telegram-bot application."""
    if not settings.TELEGRAM_TOKEN:
        logger.warning("TELEGRAM_TOKEN not configured. Telegram bot listener disabled.")
        return None

    try:
        app = Application.builder().token(settings.TELEGRAM_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", start))
        app.add_handler(CommandHandler("status", status))
        app.add_handler(CommandHandler("subscribe", subscribe))
        app.add_handler(CommandHandler("unsubscribe", unsubscribe))
        
        # Initialize application (must be called when running inside existing event loop)
        await app.initialize()
        return app
    except Exception as e:
        logger.error(f"Failed to initialize Telegram Bot application: {e}", exc_info=True)
        return None
