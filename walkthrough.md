# PayFilter — Frontend Merge Walkthrough & Verification

## Executive Summary
The PayFilter landing page and merchant dashboard have been successfully merged into **one single frontend web application** running exclusively on `http://localhost:3000`. Port `3001` has been completely eliminated. 

All features, including Stitch design language, Supabase Auth RBAC, real JWT bearer authentication, merchant onboarding, transactions overview, review queue, hash-chained audit logging, risk engine settings, and the emergency kill switch are unified under React Router on `http://localhost:3000`.

---

## 1. Unified Architecture & Routing

### Application Origin & Port
- **Frontend App**: `http://localhost:3000` (Single Vite server)
- **Backend API**: `http://localhost:8000` (FastAPI daemon)

### Unified Route Table
| Route | Access | Component | Purpose |
| :--- | :--- | :--- | :--- |
| `/` | Public | Redirects to `/landing` | Default root redirect |
| `/landing` | Public | `<Home />` | Stitch-designed AI Risk Firewall landing page |
| `/how-it-works` | Public | `<HowItWorks />` | Autonomous AI transaction risk architecture |
| `/docs` | Public | `<Docs />` | Developer docs and security model |
| `/login` | Public | `<Login />` | Real Supabase Auth login |
| `/signup` | Public | `<SignUp />` | User registration + Merchant organization onboarding |
| `/dashboard` | Protected (JWT) | `<Dashboard />` | Live Risk Overview & real-time transaction evaluations |
| `/dashboard/transactions` | Protected (JWT) | `<Dashboard />` | Alias to live transactions table |
| `/dashboard/review-queue` | Protected (JWT) | `<FlaggedQueue />` | Held transactions queue for 1-click human analyst confirmation |
| `/dashboard/queue` | Protected (JWT) | `<FlaggedQueue />` | Review queue alias |
| `/dashboard/audit-log` | Protected (JWT) | `<AuditLog />` | SHA-256 hash-chained cryptographic audit trail |
| `/dashboard/audit` | Protected (JWT) | `<AuditLog />` | Audit log alias |
| `/dashboard/risk-engine` | Protected (Admin) | `<RulesSettings />` | Hard rules, order caps, and category limits |
| `/dashboard/rules` | Protected (Admin) | `<RulesSettings />` | Rules alias |
| `/dashboard/security` | Protected (Admin) | `<KillSwitch />` | Emergency 2FA Step-Up Kill Switch controls |
| `/dashboard/kill-switch` | Protected (Admin) | `<KillSwitch />` | Kill switch alias |

---

## 2. Technical Implementation Details

### A. Unified Structure
```
frontend/
├── .env                  # Single VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_BACKEND_URL
├── index.html            # Unified HTML entrypoint with Plus Jakarta Sans & JetBrains Mono
├── package.json          # Merged dependencies (React 18, React Router DOM 6, @supabase/supabase-js, Lucide React)
├── vite.config.js        # Single dev server configured for port 3000
├── public/               # Shared assets: favicon.png, payfilter-logo.png, payfilter-icon.png, risk_layer_badge.png
└── src/
    ├── App.jsx           # Unified React Router application with AuthProvider & ProtectedRoute
    ├── main.jsx          # Root ReactDOM render mounting BrowserRouter
    ├── index.css         # Complete Stitch design system tokens, glassmorphism, buttons, and scrollbars
    ├── components/
    │   ├── Navbar.jsx    # Public navigation with links to Product, How It Works, Security, Console, Sign In, Sign Up
    │   ├── Footer.jsx    # Stitch footer
    │   ├── Sidebar.jsx   # Dashboard sidebar with deep links to /dashboard/... routes & role switcher
    │   ├── ProtectedRoute.jsx # Enforces real Supabase session, redirecting unauthenticated users to /login
    │   ├── RoleGate.jsx  # Admin-only gate for sensitive controls
    │   ├── RiskBadge.jsx # Color-coded risk verdict badges
    │   ├── TransactionCard.jsx # Transaction review card
    │   └── MetricsPanel.jsx    # High-level aggregate metrics
    ├── pages/
    │   ├── Home.jsx, HowItWorks.jsx, Docs.jsx
    │   ├── Login.jsx, SignUp.jsx
    │   └── Dashboard.jsx, FlaggedQueue.jsx, AuditLog.jsx, RulesSettings.jsx, KillSwitch.jsx
    └── lib/
        ├── api.js            # Centralized API client passing Supabase JWT Bearer token
        ├── supabaseClient.js # Supabase client using public anon key
        └── useAuth.jsx       # AuthContext handling login, signUp, session restoration, and logout
```

### B. Backend CORS Hardening
In [backend/app/main.py](file:///c:/Users/rimay/Desktop/PayFilter/backend/app/main.py):
Replaced wildcard `allow_origins=["*"]` with explicit frontend origins allowing credentials:
```python
CORSMiddleware,
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
```

---

## 3. Verification & Test Results

### 1. Automated Test Suite
Ran full test suite covering backend API, ML isolation forest model, cryptographic audit chains, and tenant isolation:
```bash
pytest backend/tests ml/tests -v
```
**Result:** `91 passed, 12 warnings in 14.97s (100% pass rate)`.

### 2. Browser Verification
An automated browser subagent executed all user journeys on `http://localhost:3000`:
- **Landing Page**: Loaded `http://localhost:3000/landing` with full Stitch styling, official PayFilter logo, and functional navigation.
- **Unauthenticated Redirection**: Clicking "Console" smoothly redirected to `http://localhost:3000/login` within the same tab without referencing port 3001.
- **Authentication**: Signed in with `admin@payfilter.test` / `password123`. The session was verified and user was redirected to `http://localhost:3000/dashboard`.
- **Dashboard Navigation**: Verified all sections:
  - `/dashboard/review-queue`
  - `/dashboard/audit-log`
  - `/dashboard/risk-engine`
  - `/dashboard/security`
- **Session Preservation**: Refreshed `http://localhost:3000/dashboard` in the browser; session and ADMIN role were preserved without redirecting.
- **Logout**: Clicking logout cleanly signed out and redirected back to `http://localhost:3000/login`.
- **Port 3001**: Verified via `netstat` that port 3001 is completely inactive.
