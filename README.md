# DropAlert 🎮

DropAlert is a real-time product availability and price tracking dashboard built for high-demand electronics and consoles (like PS5, PS5 Pro, Xbox Series X, GPUs, and new iPhones) in India.

## Features
- **Real-Time Monitoring**: Checks Amazon, Flipkart, Croma, Reliance Digital, PlayStation Direct, Games The Shop, and Vijay Sales every 5 minutes.
- **Instant Alerts**: Free email notifications (Resend), browser push notifications, and Telegram bot alerts. Premium WhatsApp alerts (Twilio).
- **Price History**: Track price changes over time to spot trends and restock patterns.

## Tech Stack
- **Backend**: Python, FastAPI, Playwright (async chromium + stealth), Celery, Redis, Supabase.
- **Frontend**: Next.js (React), TailwindCSS, Supabase Realtime client.
- **Hosting**: Render (Backend & Workers), Vercel (Frontend), Supabase (Database), Upstash (Redis).

## License
MIT
