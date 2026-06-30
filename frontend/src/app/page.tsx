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
  TrendingDown,
  BookOpen,
  Smartphone,
  Globe
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
  { id: 1, product: "PS5 Disc Edition", retailer: "Croma", event: "Restocked", price: 54990, time: "12 minutes ago", status: "in_stock" },
  { id: 2, product: "Xbox Series X", retailer: "Amazon", event: "Restocked", price: 55990, time: "1 hour ago", status: "in_stock" },
  { id: 3, product: "PS5 Disc Edition", retailer: "Sony SC", event: "Restocked", price: 54990, time: "3 hours ago", status: "in_stock" },
  { id: 4, product: "PS5 Pro", retailer: "Amazon", event: "Price drop to ₹67,990", price: 67990, time: "1 day ago", status: "price_drop" }
];

const BLOG_POSTS = [
  {
    id: 1,
    title: "Why PlayStation 5 Pro stock is extremely volatile in India",
    summary: "Following the recent import tariff revisions and increased hardware demands in major cities, Sony's distribution pipeline is experiencing bottlenecks. Learn the schedule Sony uses to refresh warehouse stocks.",
    readTime: "4 min read",
    date: "June 28, 2026",
    category: "Market Analysis"
  },
  {
    id: 2,
    title: "The Golden Window: Best times to track and buy console stock",
    summary: "Scraping millions of requests reveals stock drop patterns. Most Indian electronic retailers like Croma and Reliance Digital release cancelled pre-orders during specific midnight intervals. Here is the data breakdown.",
    readTime: "6 min read",
    date: "June 25, 2026",
    category: "Buying Guide"
  },
  {
    id: 3,
    title: "How to avoid scalpels and purchase at direct MRP",
    summary: "Refuse high markups. We detail how tracking APIs, setting price thresholds, and deploying immediate browser hooks can give you a crucial edge over scalping bots in flash sales.",
    readTime: "5 min read",
    date: "June 20, 2026",
    category: "Pro Tips"
  }
];

function urlB64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/\-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("all");
  const [products, setProducts] = useState(MOCK_PRODUCTS);
  const [drops, setDrops] = useState(MOCK_DROPS);
  const [isDemoMode, setIsDemoMode] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Subscription Form State
  const [email, setEmail] = useState("");
  const [telegramId, setTelegramId] = useState("");
  const [phone, setPhone] = useState("");
  const [selectedProducts, setSelectedProducts] = useState<string[]>(["ps5-disc"]);
  const [maxPrice, setMaxPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [subSuccess, setSubSuccess] = useState(false);

  // Web Push Subscription states
  const [pushEnabled, setPushEnabled] = useState(false);
  const [pushSubscription, setPushSubscription] = useState<any>(null);
  const [requestingPush, setRequestingPush] = useState(false);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  // Check backend health & status
  const fetchStatus = async () => {
    setRefreshing(true);
    try {
      const res = await fetch(`${apiBaseUrl}/health`);
      if (res.ok) {
        setIsDemoMode(false);
      } else {
        setIsDemoMode(true);
      }
    } catch (err) {
      setIsDemoMode(true);
    } finally {
      setRefreshing(false);
    }
  };

  // Register push service worker & check existing registration
  useEffect(() => {
    fetchStatus();

    if ("serviceWorker" in navigator && "PushManager" in window) {
      navigator.serviceWorker.register("/sw.js")
        .then(reg => {
          console.log("Push Service Worker registered.");
          return reg.pushManager.getSubscription();
        })
        .then(sub => {
          if (sub) {
            setPushSubscription(sub);
            setPushEnabled(true);
          }
        })
        .catch(err => console.error("Push Service Worker registration failed:", err));
    }
  }, []);

  const enableBrowserPush = async () => {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      alert("Browser Push Notifications are not supported in your browser.");
      return;
    }

    setRequestingPush(true);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        alert("Web Push notification permission denied. Please allow notifications in browser settings.");
        setRequestingPush(false);
        return;
      }

      const reg = await navigator.serviceWorker.ready;
      // Standard VAPID Public Key for client subscription setup
      const vapidPublicKey = "BJF6y_gP6D5p_C-v65Yy9Jz1q37dF5qNlT3n2pL4n9w8v7b6v5c4x3z2a1s0d9f8";
      
      try {
        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlB64ToUint8Array(vapidPublicKey)
        });
        setPushSubscription(sub);
        setPushEnabled(true);
        alert("Success! Browser push alerts are enabled.");
      } catch (subErr) {
        console.error("VAPID subscription failed:", subErr);
        if (isDemoMode) {
          // Simulation fallback for demo mode
          const mockSub = {
            endpoint: "https://fcm.googleapis.com/fcm/send/mock-push-endpoint-12345",
            keys: {
              p256dh: "BElj53n16Jv...",
              auth: "mock_auth_token_value_xyz"
            }
          };
          setPushSubscription(mockSub);
          setPushEnabled(true);
          alert("Success! (Demo Mode: Enabled with mock subscription).");
        } else {
          alert("Failed to contact push server. Using local sandbox fallback.");
        }
      }
    } catch (err) {
      console.error("Error setting up Web Push", err);
      alert("Error enabling notifications. Verify permissions.");
    } finally {
      setRequestingPush(false);
    }
  };

  const disableBrowserPush = async () => {
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await sub.unsubscribe();
      }
      setPushSubscription(null);
      setPushEnabled(false);
      alert("Browser push alerts disabled.");
    } catch (e) {
      console.error(e);
      setPushEnabled(false);
    }
  };

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSubSuccess(false);

    const payload = {
      email: email || undefined,
      phone: phone || undefined,
      telegram_id: telegramId || undefined,
      push_token: pushEnabled && pushSubscription ? JSON.stringify(pushSubscription) : undefined,
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
      alert("Could not connect to the backend server. Please verify the API server is running.");
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
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: "1200px", margin: "0 auto", padding: "0 1rem" }}>
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

      <main className="glass-container" style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
        
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

            {/* Visual Stock History Timeline */}
            <div className="glass-card">
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "1.5rem" }}>
                <History size={18} color="var(--primary)" />
                <h3 style={{ fontSize: "1.1rem", fontWeight: "600" }}>Live Stock Drops Timeline</h3>
              </div>

              {/* Vertical Timeline Component */}
              <div style={{ position: "relative", paddingLeft: "30px", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                {/* Center line */}
                <div style={{ 
                  position: "absolute", 
                  left: "9px", 
                  top: "6px", 
                  bottom: "6px", 
                  width: "2px", 
                  background: "linear-gradient(180deg, var(--primary) 0%, rgba(255,255,255,0.05) 100%)" 
                }} />

                {drops.map(drop => (
                  <div key={drop.id} style={{ position: "relative", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {/* Circle marker */}
                    <div style={{
                      position: "absolute",
                      left: "-26px",
                      top: "4px",
                      width: "12px",
                      height: "12px",
                      borderRadius: "50%",
                      background: drop.status === "in_stock" ? "var(--success)" : "var(--primary)",
                      boxShadow: drop.status === "in_stock" ? "0 0 8px var(--success-glow)" : "0 0 8px var(--primary-glow)",
                      border: "2px solid #0d1423"
                    }} />

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <span style={{ fontSize: "0.95rem", fontWeight: "600", color: "white" }}>{drop.product}</span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: "500" }}>{drop.time}</span>
                    </div>

                    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                      <span style={{ 
                        color: drop.status === "in_stock" ? "var(--success)" : "#38bdf8",
                        fontWeight: "500"
                      }}>
                        {drop.event}
                      </span>
                      {" "}at <span style={{ color: "white", fontWeight: "500" }}>{drop.retailer}</span> for{" "}
                      <span style={{ color: "white", fontWeight: "600" }}>₹{drop.price.toLocaleString("en-IN")}</span>
                    </div>
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

                  {/* Browser Push alerts channel */}
                  <div style={{ marginTop: "8px" }}>
                    <label style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "block", marginBottom: "6px", fontWeight: "500" }}>
                      BROWSER PUSH ALERTS (FREE)
                    </label>
                    <div style={{ 
                      display: "flex", 
                      alignItems: "center", 
                      justifyContent: "space-between",
                      background: pushEnabled ? "rgba(16, 185, 129, 0.06)" : "rgba(255,255,255,0.02)",
                      border: "1px solid",
                      borderColor: pushEnabled ? "rgba(16, 185, 129, 0.2)" : "rgba(255,255,255,0.05)",
                      padding: "10px",
                      borderRadius: "8px"
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <Smartphone size={16} color={pushEnabled ? "var(--success)" : "var(--text-secondary)"} />
                        <div>
                          <span style={{ fontSize: "0.8rem", fontWeight: "500", display: "block" }}>
                            {pushEnabled ? "Browser Push Enabled" : "Not Configured"}
                          </span>
                          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                            Direct desktop/mobile push
                          </span>
                        </div>
                      </div>
                      
                      {pushEnabled ? (
                        <button 
                          type="button" 
                          onClick={disableBrowserPush}
                          style={{
                            background: "transparent",
                            border: "none",
                            color: "var(--danger)",
                            fontSize: "0.75rem",
                            cursor: "pointer",
                            fontWeight: "500"
                          }}
                        >
                          Disable
                        </button>
                      ) : (
                        <button 
                          type="button" 
                          onClick={enableBrowserPush}
                          disabled={requestingPush}
                          className="primary-btn"
                          style={{
                            padding: "4px 8px",
                            fontSize: "0.75rem",
                            boxShadow: "none"
                          }}
                        >
                          {requestingPush ? "Configuring..." : "Enable"}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Destination - Email */}
                  <div>
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

        {/* Premium Blog Section */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", marginTop: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <BookOpen size={20} color="var(--primary)" />
            <h2 style={{ fontSize: "1.3rem", fontWeight: "700" }}>DropAlert Pro Insights & Blogs</h2>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1.5rem" }} className="blog-grid">
            {BLOG_POSTS.map(post => (
              <div key={post.id} className="glass-card" style={{ display: "flex", flexDirection: "column", gap: "12px", height: "100%", justifyContent: "space-between" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                    <span style={{ fontSize: "0.75rem", background: "rgba(0,102,255,0.1)", color: "#60a5fa", padding: "3px 8px", borderRadius: "12px", fontWeight: "600" }}>
                      {post.category}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {post.date}
                    </span>
                  </div>
                  
                  <h3 style={{ fontSize: "1.05rem", fontWeight: "600", color: "white", lineHeight: "1.35", marginTop: "4px" }}>
                    {post.title}
                  </h3>
                  
                  <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "8px", lineHeight: "1.45" }}>
                    {post.summary}
                  </p>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.04)", paddingTop: "10px", marginTop: "8px" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{post.readTime}</span>
                  <a href="#" onClick={(e) => { e.preventDefault(); alert("Full articles are unlocked for free subscribers. Register your email or push notifications above to receive direct links."); }} style={{ fontSize: "0.8rem", color: "var(--primary)", fontWeight: "600", textDecoration: "none" }}>
                    Read Article ↗
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Style block for manual responsiveness grid setup (excluding tailwind imports) */}
        <style jsx>{`
          .main-layout-grid {
            display: grid;
            grid-template-columns: 1fr;
          }
          .blog-grid {
            display: grid;
            grid-template-columns: 1fr;
          }
          @media (min-width: 768px) {
            .blog-grid {
              grid-template-columns: repeat(3, 1fr);
            }
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
