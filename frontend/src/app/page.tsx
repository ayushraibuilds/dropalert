"use client";

import { useEffect, useState } from "react";
import { 
  Bell, 
  Check, 
  AlertTriangle, 
  RefreshCw, 
  Zap, 
  Mail, 
  Send, 
  MessageSquare,
  History,
  TrendingDown
} from "lucide-react";

// Mock data to fall back on if Python backend is offline
const MOCK_PRODUCTS = [
  {
    slug: "ps5-disc",
    name: "Sony PlayStation 5 (Disc Edition)",
    category: "console",
    retailers: [
      { name: "Croma", in_stock: true, price: 54990, url: "https://www.croma.com/sony-playstation-5-console-slim/p/304193" },
      { name: "Amazon", in_stock: false, price: 54990, url: "https://www.amazon.in/dp/B09FH23FQ3" },
      { name: "Flipkart", in_stock: false, price: 54990, url: "https://www.flipkart.com" },
      { name: "Reliance", in_stock: false, price: 54990, url: "https://www.reliancedigital.in" },
      { name: "Sony SC", in_stock: true, price: 54990, url: "https://shopatsc.com" },
      { name: "Vijay Sales", in_stock: false, price: 54490, url: "https://www.vijaysales.com" },
      { name: "Games The Shop", in_stock: false, price: 54990, url: "https://www.gamesthe.shop" }
    ]
  },
  {
    slug: "ps5-pro",
    name: "Sony PlayStation 5 Pro",
    category: "console",
    retailers: [
      { name: "Croma", in_stock: false, price: 68900, url: "https://www.croma.com" },
      { name: "Amazon", in_stock: false, price: 68900, url: "https://www.amazon.in" },
      { name: "Sony SC", in_stock: false, price: 68900, url: "https://shopatsc.com" }
    ]
  },
  {
    slug: "xbox-series-x",
    name: "Microsoft Xbox Series X",
    category: "console",
    retailers: [
      { name: "Amazon", in_stock: true, price: 55990, url: "https://www.amazon.in" },
      { name: "Flipkart", in_stock: true, price: 55990, url: "https://www.flipkart.com" }
    ]
  }
];

const MOCK_DROPS = [
  { id: 1, product: "PS5 Disc Edition", retailer: "Croma", event: "Restocked", price: 54990, time: "12 minutes ago" },
  { id: 2, product: "Xbox Series X", retailer: "Amazon", event: "Restocked", price: 55990, time: "1 hour ago" },
  { id: 3, product: "PS5 Disc Edition", retailer: "Sony SC", event: "Restocked", price: 54990, time: "3 hours ago" },
  { id: 4, product: "PS5 Pro", retailer: "Amazon", event: "Price drop to ₹67,990", price: 67990, time: "1 day ago" }
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("all");
  const [products, setProducts] = useState(MOCK_PRODUCTS);
  const [drops, setDrops] = useState(MOCK_DROPS);
  const [isDemoMode, setIsDemoMode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  // Subscription Form State
  const [email, setEmail] = useState("");
  const [telegramId, setTelegramId] = useState("");
  const [phone, setPhone] = useState("");
  const [selectedProducts, setSelectedProducts] = useState<string[]>(["ps5-disc"]);
  const [maxPrice, setMaxPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [subSuccess, setSubSuccess] = useState(false);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  const fetchStatus = async () => {
    setRefreshing(true);
    try {
      const res = await fetch(`${apiBaseUrl}/health`);
      if (res.ok) {
        const data = await res.json();
        setIsDemoMode(false);
        // Load data if Python backend has fetched it
        // For baseline design, we'll keep fallback UI but disable demo warning
      } else {
        setIsDemoMode(true);
      }
    } catch (err) {
      setIsDemoMode(true);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSubSuccess(false);

    const payload = {
      email: email || undefined,
      phone: phone || undefined,
      telegram_id: telegramId || undefined,
      products: selectedProducts,
      max_price: maxPrice ? parseInt(maxPrice) : undefined
    };

    try {
      const res = await fetch(`${apiBaseUrl}/api/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setSubSuccess(true);
        setEmail("");
        setTelegramId("");
        setPhone("");
        setMaxPrice("");
      } else {
        const err = await res.json();
        alert(`Subscription failed: ${err.detail || "Unknown error"}`);
      }
    } catch (err) {
      if (isDemoMode) {
        // Mock successful submit in demo mode
        setTimeout(() => {
          setSubSuccess(true);
          setSubmitting(false);
        }, 1000);
        return;
      }
      alert("Could not connect to the backend server. Please verify uvicorn is running.");
    } finally {
      if (!isDemoMode) {
        setSubmitting(false);
      }
    }
  };

  const toggleProductSelect = (slug: string) => {
    setSelectedProducts(prev => 
      prev.includes(slug) 
        ? prev.filter(s => s !== slug)
        : [...prev, slug]
    );
  };

  const filteredProducts = activeTab === "all" 
    ? products 
    : products.filter(p => p.category === activeTab);

  return (
    <div>
      {/* Header Navigation */}
      <header className="glass-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.5rem", fontWeight: "700", letterSpacing: "-0.5px" }}>DropAlert</span>
            <span className="badge success">
              <span className="pulse-dot success"></span> Live
            </span>
          </div>
          
          <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
            <a 
              href="https://github.com/ayushraibuilds/dropalert" 
              target="_blank" 
              rel="noreferrer"
              style={{ color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "5px", textDecoration: "none", fontSize: "0.9rem" }}
            >
              <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg> GitHub
            </a>
          </div>
        </div>
      </header>

      <main className="glass-container" style={{ display: "grid", gridTemplateColumns: "1fr", gap: "2rem" }}>
        
        {/* Demo Mode Notice */}
        {isDemoMode && (
          <div className="glass-card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderColor: "rgba(245, 158, 11, 0.35)", background: "rgba(245, 158, 11, 0.05)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <AlertTriangle color="var(--warning)" size={24} />
              <div>
                <h4 style={{ fontWeight: "600", fontSize: "1rem" }}>Running in Demo Mode</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "2px" }}>
                  FastAPI backend is offline. Showing simulated mock data. Run `uvicorn main:app` to connect.
                </p>
              </div>
            </div>
            <button 
              onClick={fetchStatus} 
              disabled={refreshing}
              className="primary-btn" 
              style={{ background: "rgba(255, 255, 255, 0.08)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "white", padding: "8px 14px", boxShadow: "none" }}
            >
              <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
              {refreshing ? "Checking..." : "Reconnect"}
            </button>
          </div>
        )}

        {/* Dashboard Grid Layout */}
        <div style={{ gap: "2rem" }} className="main-layout-grid">
          
          {/* Main Stock Tracking Section */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            
            {/* Tabs Filter */}
            <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--card-border)", paddingBottom: "10px" }}>
              {["all", "console", "gpu", "phone"].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  style={{
                    background: activeTab === tab ? "rgba(0, 102, 255, 0.15)" : "transparent",
                    color: activeTab === tab ? "white" : "var(--text-secondary)",
                    border: "none",
                    padding: "6px 16px",
                    borderRadius: "20px",
                    cursor: "pointer",
                    fontSize: "0.9rem",
                    fontWeight: activeTab === tab ? "500" : "400",
                    transition: "all 0.2s"
                  }}
                >
                  {tab.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Product List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              {filteredProducts.map(product => (
                <div key={product.slug} className="glass-card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <h3 style={{ fontSize: "1.2rem", fontWeight: "600" }}>{product.name}</h3>
                  
                  {/* Retailers Status Rows */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {product.retailers.map(ret => (
                      <div 
                        key={ret.name} 
                        style={{ 
                          display: "flex", 
                          justifyContent: "space-between", 
                          alignItems: "center",
                          padding: "10px 14px",
                          borderRadius: "10px",
                          background: "rgba(255,255,255,0.02)",
                          border: "1px solid rgba(255, 255, 255, 0.03)"
                        }}
                      >
                        <span style={{ fontWeight: "500", fontSize: "0.95rem" }}>{ret.name}</span>
                        
                        <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                          <span className={`badge ${ret.in_stock ? "success" : "danger"}`}>
                            {ret.in_stock ? "In Stock" : "Out of Stock"}
                          </span>
                          
                          {ret.price && (
                            <span style={{ fontWeight: "600", fontSize: "0.95rem" }}>₹{ret.price.toLocaleString("en-IN")}</span>
                          )}

                          <a 
                            href={ret.url} 
                            target="_blank" 
                            rel="noreferrer"
                            className="primary-btn" 
                            style={{ 
                              padding: "6px 12px", 
                              fontSize: "0.8rem", 
                              boxShadow: "none",
                              background: ret.in_stock ? "var(--primary)" : "rgba(255,255,255,0.05)",
                              color: ret.in_stock ? "white" : "var(--text-secondary)",
                              pointerEvents: ret.in_stock ? "auto" : "none",
                              opacity: ret.in_stock ? 1 : 0.4
                            }}
                          >
                            Buy Now
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Drops History Feed */}
            <div className="glass-card">
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "1.25rem" }}>
                <History size={18} color="var(--primary)" />
                <h3 style={{ fontSize: "1.1rem", fontWeight: "600" }}>Latest Restock Drops</h3>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {drops.map(drop => (
                  <div 
                    key={drop.id} 
                    style={{ 
                      display: "flex", 
                      justifyContent: "space-between", 
                      alignItems: "center",
                      paddingBottom: "8px",
                      borderBottom: "1px solid rgba(255, 255, 255, 0.04)"
                    }}
                  >
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <span style={{ fontSize: "0.9rem", fontWeight: "500" }}>{drop.product}</span>
                      <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                        {drop.event} on <span style={{ color: "white" }}>{drop.retailer}</span> for ₹{drop.price.toLocaleString("en-IN")}
                      </span>
                    </div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{drop.time}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Right Sidebar Form Section */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            
            {/* Setup Alerts Form */}
            <div className="glass-card" style={{ borderColor: "rgba(0, 102, 255, 0.15)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "1.25rem" }}>
                <Bell size={18} color="var(--primary)" />
                <h3 style={{ fontSize: "1.1rem", fontWeight: "600" }}>Setup Stock Alerts</h3>
              </div>

              {subSuccess ? (
                <div style={{ textAlign: "center", padding: "1.5rem 0" }}>
                  <div style={{ display: "inline-flex", background: "rgba(16,185,129,0.15)", borderRadius: "50%", padding: "12px", marginBottom: "10px" }}>
                    <Check size={28} color="var(--success)" />
                  </div>
                  <h4 style={{ fontWeight: "600" }}>Alert Configured!</h4>
                  <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "4px" }}>
                    We will notify you the instant stock appears. Keep your notifications open.
                  </p>
                  <button 
                    onClick={() => setSubSuccess(false)}
                    className="primary-btn" 
                    style={{ marginTop: "1rem", width: "100%", justifyContent: "center" }}
                  >
                    Create Another Alert
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubscribe} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  
                  {/* Select Products */}
                  <div>
                    <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "block", marginBottom: "6px", fontWeight: "500" }}>
                      PRODUCTS TO WATCH
                    </label>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      {products.map(p => (
                        <label 
                          key={p.slug} 
                          style={{ 
                            display: "flex", 
                            alignItems: "center", 
                            gap: "8px", 
                            fontSize: "0.85rem", 
                            cursor: "pointer",
                            background: selectedProducts.includes(p.slug) ? "rgba(0, 102, 255, 0.08)" : "transparent",
                            padding: "6px 10px",
                            borderRadius: "6px",
                            border: "1px solid",
                            borderColor: selectedProducts.includes(p.slug) ? "rgba(0, 102, 255, 0.2)" : "transparent"
                          }}
                        >
                          <input 
                            type="checkbox" 
                            checked={selectedProducts.includes(p.slug)} 
                            onChange={() => toggleProductSelect(p.slug)}
                          />
                          {p.name}
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Destination - Email */}
                  <div style={{ marginTop: "8px" }}>
                    <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "block", marginBottom: "6px", fontWeight: "500" }}>
                      EMAIL ALERTS (FREE)
                    </label>
                    <div style={{ position: "relative" }}>
                      <Mail size={16} style={{ position: "absolute", left: "10px", top: "12px", color: "var(--text-muted)" }} />
                      <input 
                        type="email" 
                        placeholder="yourname@gmail.com" 
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        className="input-field"
                        style={{ paddingLeft: "34px" }}
                      />
                    </div>
                  </div>

                  {/* Destination - Telegram */}
                  <div>
                    <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "block", marginBottom: "6px", fontWeight: "500" }}>
                      TELEGRAM BOT ALERTS (FREE)
                    </label>
                    <div style={{ position: "relative" }}>
                      <Send size={16} style={{ position: "absolute", left: "10px", top: "12px", color: "var(--text-muted)" }} />
                      <input 
                        type="text" 
                        placeholder="Telegram Chat ID (e.g. 9827361)" 
                        value={telegramId}
                        onChange={e => setTelegramId(e.target.value)}
                        className="input-field"
                        style={{ paddingLeft: "34px" }}
                      />
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                      Chat ID from <a href="https://t.me/dropalert_bot" target="_blank" rel="noreferrer" style={{ color: "var(--primary)" }}>@dropalert_bot</a>
                    </span>
                  </div>

                  {/* Max Price Threshold */}
                  <div>
                    <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "block", marginBottom: "6px", fontWeight: "500" }}>
                      MAX PRICE LIMIT (OPTIONAL)
                    </label>
                    <div style={{ position: "relative" }}>
                      <TrendingDown size={16} style={{ position: "absolute", left: "10px", top: "12px", color: "var(--text-muted)" }} />
                      <input 
                        type="number" 
                        placeholder="Only alert if below ₹ (e.g. 55000)" 
                        value={maxPrice}
                        onChange={e => setMaxPrice(e.target.value)}
                        className="input-field"
                        style={{ paddingLeft: "34px" }}
                      />
                    </div>
                  </div>

                  <button 
                    type="submit" 
                    disabled={submitting}
                    className="primary-btn" 
                    style={{ width: "100%", justifyContent: "center", marginTop: "10px" }}
                  >
                    {submitting ? "Configuring..." : "Subscribe to Stock Drops"}
                  </button>
                </form>
              )}
            </div>

            {/* Twilio WhatsApp Premium Pitch */}
            <div className="glass-card" style={{ background: "linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(13, 20, 35, 0.45) 100%)", borderColor: "rgba(16, 185, 129, 0.2)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <Zap size={18} color="var(--success)" />
                <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#34d399" }}>Instant WhatsApp Alerts</h3>
              </div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: "1.45" }}>
                Email/Telegram can be delayed by spam filters. Upgrade to **Premium Alerts** to receive instant automated WhatsApp messages from our dedicated Twilio numbers.
              </p>
              
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "14px 0", borderTop: "1px dashed rgba(16,185,129,0.15)", paddingTop: "10px" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>PRICE</span>
                <span style={{ fontWeight: "700", fontSize: "1.1rem" }}>₹99<span style={{ fontSize: "0.8rem", fontWeight: "400", color: "var(--text-muted)" }}>/month</span></span>
              </div>

              <button 
                className="primary-btn" 
                style={{ 
                  width: "100%", 
                  justifyContent: "center", 
                  background: "var(--success)", 
                  boxShadow: "0 4px 14px var(--success-glow)" 
                }}
                onClick={() => alert("Upgrade linking to Razorpay Sandbox webhook checkout.")}
              >
                <MessageSquare size={16} /> Upgrade to WhatsApp Premium
              </button>
            </div>

          </div>

        </div>
        
        {/* Style block for manual responsiveness grid setup (excluding tailwind imports) */}
        <style jsx>{`
          .main-layout-grid {
            display: grid;
            grid-template-columns: 1fr;
          }
          @media (min-width: 1024px) {
            .main-layout-grid {
              grid-template-columns: 2fr 1fr;
            }
          }
        `}</style>

      </main>
    </div>
  );
}
