import logging
import asyncio
from config import settings
from services.email_service import send_email_alert
from services.telegram_service import send_telegram_message
from services.whatsapp_service import send_whatsapp_alert
from services.push_service import send_push_notification
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def inject_affiliate_link(url: str, retailer: str) -> str:
    """Inject affiliate tags into URLs to generate passive income."""
    if "amazon.in" in url and settings.AMAZON_AFFILIATE_TAG:
        # Check if query parameter already exists
        connector = "&" if "?" in url else "?"
        return f"{url}{connector}tag={settings.AMAZON_AFFILIATE_TAG}"
    elif "flipkart.com" in url and settings.FLIPKART_AFFILIATE_ID:
        connector = "&" if "?" in url else "?"
        return f"{url}{connector}affid={settings.FLIPKART_AFFILIATE_ID}"
    return url


async def notify_subscribers(
    product_slug: str,
    product_name: str,
    retailer: str,
    price: int,
    product_url: str,
):
    """
    Find active subscribers for this product and retailer, and notify them
    via their selected channels (Email, Telegram, WhatsApp).
    """
    if not supabase:
        logger.warning(
            "Supabase not initialized. Cannot fetch subscribers to notify."
        )
        return

    try:
        # Format links
        monetized_url = inject_affiliate_link(product_url, retailer)

        # Query all active subscribers who:
        # 1. Have this product slug in their watched products list (or products contains the slug)
        # 2. Have this retailer in their watched list (or retailers is null/empty or contains the retailer)
        # 3. Have max_price is null or price <= max_price
        query = (
            supabase.table("subscribers")
            .select("*")
            .eq("is_active", True)
            .contains("products", [product_slug])
        )

        response = query.execute()
        subscribers = response.data

        if not subscribers:
            logger.info(f"No active subscribers found for {product_slug}")
            return

        # Prepare messages
        telegram_msg = (
            f"🚨 <b>{product_name} in Stock!</b>\n\n"
            f"🛒 <b>Retailer</b>: {retailer.upper()}\n"
            f"💰 <b>Price</b>: ₹{price:,}\n"
            f"⚡ <a href='{monetized_url}'>Buy Now (Link)</a>\n\n"
            f"Act fast, stock sells out in minutes!"
        )

        email_subject = f"🚨 RESTOCK ALERT: {product_name} in stock at {retailer.upper()}!"
        email_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #003087;">DropAlert Stock Drop!</h2>
                <p>Great news! The product you are tracking is back in stock.</p>
                <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <strong>Product:</strong> {product_name}<br>
                    <strong>Retailer:</strong> {retailer.upper()}<br>
                    <strong>Price:</strong> ₹{price:,}<br>
                </div>
                <p>
                    <a href="{monetized_url}" style="background-color: #003087; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Buy on {retailer.upper()} ↗
                    </a>
                </p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 11px; color: #777;">You are receiving this because you subscribed to alert drops on DropAlert.</p>
            </body>
        </html>
        """

        whatsapp_msg = (
            f"🚨 *{product_name} in Stock!* 🚨\n\n"
            f"🛒 *Retailer*: {retailer.upper()}\n"
            f"💰 *Price*: ₹{price:,}\n"
            f"⚡ *Buy*: {monetized_url}\n\n"
            f"Act fast, stock sells out in minutes! - DropAlert"
        )

        tasks = []

        for sub in subscribers:
            # Check price threshold
            max_price = sub.get("max_price")
            if max_price and price > max_price:
                continue  # Skip if price is above user threshold

            # Email notification (Free tier)
            email = sub.get("email")
            if email:
                tasks.append(send_email_alert(email, email_subject, email_html))

            # Telegram notification (Free tier)
            tg_id = sub.get("telegram_id")
            if tg_id:
                tasks.append(send_telegram_message(tg_id, telegram_msg))

            # WhatsApp notification (Premium tier only)
            phone = sub.get("phone")
            tier = sub.get("tier", "free")
            if phone and tier == "premium":
                tasks.append(send_whatsapp_alert(phone, whatsapp_msg))

            # Browser Push notification
            push_token = sub.get("push_token")
            if push_token:
                push_payload = {
                    "title": f"🚨 Restock: {product_name}!",
                    "body": f"In stock at {retailer.upper()} for ₹{price:,}.",
                    "url": monetized_url,
                    "icon": "/icon-192x192.png"
                }
                tasks.append(send_push_notification(push_token, push_payload))

        # Run all notifications concurrently
        if tasks:
            logger.info(
                f"Dispatching {len(tasks)} notifications for {product_slug} restock..."
            )
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Count successes
            successes = sum(1 for r in results if r is True)
            logger.info(
                f"Notification dispatch complete. {successes}/{len(tasks)} succeeded."
            )

    except Exception as e:
        logger.error(
            f"Error in subscriber notification orchestrator: {e}", exc_info=True
        )
