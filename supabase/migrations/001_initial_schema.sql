-- Products table (multi-product from day 1)
CREATE TABLE IF NOT EXISTS products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,       -- "ps5-disc", "ps5-digital", "xbox-series-x"
  name TEXT NOT NULL,
  category TEXT NOT NULL,          -- "console", "gpu", "phone"
  image_url TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Seed initial products
INSERT INTO products (slug, name, category) VALUES
  ('ps5-disc', 'PlayStation 5 (Disc Edition)', 'console'),
  ('ps5-digital', 'PlayStation 5 (Digital Edition)', 'console'),
  ('ps5-pro', 'PlayStation 5 Pro', 'console'),
  ('xbox-series-x', 'Xbox Series X', 'console'),
  ('xbox-series-s', 'Xbox Series S', 'console')
ON CONFLICT (slug) DO NOTHING;

-- Product Retailer URLs Mapping
CREATE TABLE IF NOT EXISTS product_retailer_urls (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  retailer TEXT NOT NULL,          -- "amazon", "flipkart", "croma", "reliance", "playstation_direct", "games_the_shop", "vijaysales"
  url TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(product_id, retailer)
);
CREATE INDEX IF NOT EXISTS idx_product_retailer_urls ON product_retailer_urls(product_id, is_active);

-- Stock events log
CREATE TABLE IF NOT EXISTS stock_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  retailer TEXT NOT NULL,
  event TEXT NOT NULL,             -- "in_stock", "out_of_stock", "price_change"
  price INTEGER,
  url TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_stock_events_lookup ON stock_events(product_id, retailer, created_at DESC);

-- Subscribers
CREATE TABLE IF NOT EXISTS subscribers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  phone TEXT,
  telegram_id TEXT,
  tier TEXT DEFAULT 'free',        -- "free" / "premium"
  products TEXT[],                 -- product slugs to watch
  retailers TEXT[],                -- retailer names to watch
  max_price INTEGER,
  push_token TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Price history
CREATE TABLE IF NOT EXISTS price_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  retailer TEXT NOT NULL,
  price INTEGER NOT NULL,
  recorded_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_price_history_lookup ON price_history(product_id, retailer, recorded_at DESC);

-- Second-hand listings (Phase 2, table created now for forward-compatibility)
CREATE TABLE IF NOT EXISTS secondhand_listings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL,
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  condition TEXT,
  price INTEGER NOT NULL,
  original_price INTEGER,
  warranty_months INTEGER DEFAULT 0,
  url TEXT NOT NULL,
  is_available BOOLEAN DEFAULT true,
  scraped_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_secondhand_product ON secondhand_listings(product_id, is_available);
