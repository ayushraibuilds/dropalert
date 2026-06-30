import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from config import settings
from scrapers import SCRAPER_CLASSES, StockResult
from services.notification_service import notify_subscribers, inject_affiliate_link

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dropalert")

# Initialize Supabase
supabase = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")

# Initialize Redis (fallback to in-memory cache if Redis is down/unavailable)
redis_client = None
local_cache: Dict[str, Dict] = {}  # key -> dict state

if settings.REDIS_URL:
    try:
        import redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        # Test connection
        redis_client.ping()
        logger.info("Redis client connected successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}. Using in-memory fallback cache.")
        redis_client = None


# Cache helpers
def get_cached_status(retailer: str, product_slug: str) -> Optional[dict]:
    key = f"stock:{product_slug}:{retailer}"
    if redis_client:
        try:
            import json
            val = redis_client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
    
    # Fallback to local memory cache
    return local_cache.get(key)


def set_cached_status(retailer: str, product_slug: str, status: dict):
    key = f"stock:{product_slug}:{retailer}"
    if redis_client:
        try:
            import json
            redis_client.set(key, json.dumps(status))
            return
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    # Fallback to local memory cache
    local_cache[key] = status


# Scraper Stats for Health Checks
scraper_stats = {
    "last_run_time": None,
    "last_run_duration_seconds": 0,
    "runs_count": 0,
    "success_count": 0,
    "error_count": 0,
    "retailer_health": {}
}


async def run_scraper_cycle():
    """Fetch active URLs, run scrapers, detect stock changes, and notify."""
    if not supabase:
        logger.warning("Supabase not set up. Skipping scraper run.")
        return

    logger.info("Starting scraper cycle...")
    start_time = datetime.now(timezone.utc)
    
    try:
        # Fetch active products & their URLs
        # Join product_retailer_urls with products
        urls_response = supabase.table("product_retailer_urls").select(
            "*, products(slug, name)"
        ).eq("is_active", True).execute()
        
        mappings = urls_response.data
        if not mappings:
            logger.info("No active scraper URLs found in database.")
            return

        tasks = []
        for mapping in mappings:
            retailer = mapping["retailer"]
            url = mapping["url"]
            product = mapping["products"]
            
            if not product:
                continue
                
            product_slug = product["slug"]
            product_name = product["name"]
            
            scraper_cls = SCRAPER_CLASSES.get(retailer)
            if not scraper_cls:
                logger.error(f"No scraper class found for retailer: {retailer}")
                continue
                
            scraper = scraper_cls(product_slug=product_slug, url=url)
            
            # Wrap check_stock in a helper to capture metadata
            async def run_and_log(s=scraper, p_name=product_name):
                t_start = datetime.now(timezone.utc)
                res: StockResult = await s.check_stock()
                t_end = datetime.now(timezone.utc)
                duration = (t_end - t_start).total_seconds()
                return res, p_name, duration
                
            tasks.append(run_and_log())

        if not tasks:
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res_tuple in results:
            if isinstance(res_tuple, Exception):
                logger.error(f"Scraper execution crashed with exception: {res_tuple}")
                scraper_stats["error_count"] += 1
                continue

            result: StockResult = res_tuple[0]
            product_name = res_tuple[1]
            duration = res_tuple[2]

            retailer = result.retailer
            product_slug = result.product_slug
            in_stock = result.in_stock
            price = result.price
            url = result.url
            error = result.error

            # Track health stats
            scraper_stats["retailer_health"][retailer] = {
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": duration,
                "success": error is None,
                "error": error
            }

            if error:
                logger.error(f"Scraper error [{retailer} / {product_slug}]: {error}")
                scraper_stats["error_count"] += 1
                continue

            scraper_stats["success_count"] += 1
            logger.info(f"Scrape result [{retailer} / {product_slug}]: in_stock={in_stock}, price={price}")

            # Get last known state
            old_state = get_cached_status(retailer, product_slug)
            
            # Check if stock changed or price changed
            state_changed = False
            is_restocked = False
            
            new_state = {
                "in_stock": in_stock,
                "price": price,
                "url": url,
                "last_checked": datetime.now(timezone.utc).isoformat()
            }

            if not old_state:
                # First time seeing this product/retailer
                state_changed = True
                if in_stock:
                    is_restocked = True
            else:
                old_in_stock = old_state.get("in_stock", False)
                old_price = old_state.get("price")

                if in_stock != old_in_stock:
                    state_changed = True
                    if in_stock and not old_in_stock:
                        is_restocked = True
                elif price != old_price and in_stock:
                    # Price change for in-stock items is a state change
                    state_changed = True

            # Save state if changed
            if state_changed:
                set_cached_status(retailer, product_slug, new_state)

                # Log event in database
                event_type = "in_stock" if is_restocked else ("price_change" if (in_stock and old_state and price != old_state.get("price")) else "out_of_stock")
                try:
                    # Get product ID
                    prod_resp = supabase.table("products").select("id").eq("slug", product_slug).execute()
                    if prod_resp.data:
                        product_id = prod_resp.data[0]["id"]
                        supabase.table("stock_events").insert({
                            "product_id": product_id,
                            "retailer": retailer,
                            "event": event_type,
                            "price": price,
                            "url": url
                        }).execute()

                        # If price changed or in stock, save to price history
                        if price and in_stock:
                            supabase.table("price_history").insert({
                                "product_id": product_id,
                                "retailer": retailer,
                                "price": price
                            }).execute()
                except Exception as db_err:
                    logger.error(f"Failed to write event to DB: {db_err}")

                # Trigger notifications if RESTOCKED
                if is_restocked and price:
                    # Run in background to not block loop
                    asyncio.create_task(
                        notify_subscribers(
                            product_slug=product_slug,
                            product_name=product_name,
                            retailer=retailer,
                            price=price,
                            product_url=url
                        )
                    )

    except Exception as e:
        logger.error(f"Global error in scraper cycle: {e}", exc_info=True)
    finally:
        end_time = datetime.now(timezone.utc)
        scraper_stats["last_run_time"] = end_time.isoformat()
        scraper_stats["last_run_duration_seconds"] = (end_time - start_time).total_seconds()
        scraper_stats["runs_count"] += 1


async def scheduler_loop():
    """Infinite loop for task scheduling."""
    # Give the server a few seconds to boot up before first run
    await asyncio.sleep(5.0)
    
    interval = settings.SCRAPER_INTERVAL_MINUTES * 60
    while True:
        try:
            await run_scraper_cycle()
        except Exception as e:
            logger.error(f"Error in scheduler loop execution: {e}")
        
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch background scheduler task
    scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("Background stock tracker scheduler task started.")
    
    yield
    
    # Shutdown: Clean up background tasks
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        logger.info("Scheduler task shut down successfully.")


app = FastAPI(
    title="DropAlert API",
    description="Real-time product stock tracking and subscription alert system.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production Vercel frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SubscriptionRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    products: List[str]
    retailers: Optional[List[str]] = None
    max_price: Optional[int] = None


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "DropAlert Stock Tracker API",
        "current_time": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check for service monitoring and UptimeRobot."""
    db_status = "connected" if supabase else "disconnected"
    redis_status = "connected" if redis_client else "in_memory_fallback"
    
    return {
        "status": "ok" if (supabase and (redis_client or local_cache is not None)) else "degraded",
        "database": db_status,
        "cache": redis_status,
        "scheduler": scraper_stats
    }


@app.post("/api/subscribe")
async def subscribe_user(req: SubscriptionRequest):
    """Subscribe a user to stock drop notifications."""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    if not req.email and not req.phone and not req.telegram_id:
        raise HTTPException(
            status_code=400,
            detail="At least one alert destination (email, phone, telegram_id) is required",
        )

    try:
        # Check if user already exists by email
        existing = None
        if req.email:
            resp = supabase.table("subscribers").select("*").eq("email", req.email).execute()
            if resp.data:
                existing = resp.data[0]

        payload = {
            "email": req.email,
            "phone": req.phone,
            "telegram_id": req.telegram_id,
            "products": req.products,
            "retailers": req.retailers or [],
            "max_price": req.max_price,
            "is_active": True
        }

        if existing:
            # Update subscription details
            # Merge products if already exists
            merged_products = list(set(existing.get("products", []) + req.products))
            payload["products"] = merged_products
            
            supabase.table("subscribers").update(payload).eq("id", existing["id"]).execute()
            return {"status": "success", "message": "Subscription updated", "id": existing["id"]}
        else:
            # Create new subscription
            resp = supabase.table("subscribers").insert(payload).execute()
            if resp.data:
                return {"status": "success", "message": "Subscribed successfully", "id": resp.data[0]["id"]}
            else:
                raise HTTPException(status_code=500, detail="Failed to create subscriber record")

    except Exception as e:
        logger.error(f"Error subscribing user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
