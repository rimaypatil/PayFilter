# PayFilter Unified Frontend Architecture & Migration Plan

## Problem Statement
PayFilter currently has two separate frontend applications:
- `frontend/landing` running on `http://localhost:3000`
- `frontend/dashboard` running on `http://localhost:3001`

The user requires ONE unified web application running strictly on `http://localhost:3000`, eliminating port 3001 entirely, with unified routing, shared Stitch design system, real Supabase Auth RBAC, and seamless client-side navigation.

## Target URL & Route Structure
- `/` -> Redirects to `/landing` (or renders Landing)
- `/landing` -> Stitch-based PayFilter Landing page
- `/how-it-works` -> How It Works page
- `/docs` -> Security & Developers page
- `/signup` -> Merchant Signup & Onboarding flow
- `/login` -> Real Supabase Auth login
- `/dashboard` -> Live Risk Overview (Dashboard layout)
- `/dashboard/transactions` -> Live Transactions Overview
- `/dashboard/queue` (or `/dashboard/review-queue`) -> Flagged Transaction Queue & Analyst Confirmation
- `/dashboard/risk-engine` -> Risk Engine Overview / Rules
- `/dashboard/rules` -> Rules & Velocity Caps Settings
- `/dashboard/audit` (or `/dashboard/audit-log`) -> Cryptographic Audit Trail
- `/dashboard/kill-switch` (or `/dashboard/security`) -> Emergency Kill Switch & Step-Up Auth

## Unified Frontend Architecture
- **Location**: `frontend/` (root)
  - `package.json`: Merged dependencies (React 18, React Router DOM 6, @supabase/supabase-js, Lucide React, Vite).
  - `vite.config.js`: Single dev server configured on port 3000.
  - `.env`: Single frontend environment (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_BACKEND_URL=http://localhost:8000`).
  - `public/`: Merged assets (`favicon.png`, `payfilter-logo.png`, `payfilter-icon.png`, `risk_layer_badge.png`, `stitch_landing.png`).
  - `src/`:
    - `components/`:
      - Common: `Navbar.jsx`, `Footer.jsx`
      - Dashboard: `Sidebar.jsx`, `ProtectedRoute.jsx`, `RoleGate.jsx`, `RiskBadge.jsx`, `TransactionCard.jsx`, `MetricsPanel.jsx`
    - `pages/`:
      - Landing: `Home.jsx`, `HowItWorks.jsx`, `Docs.jsx`
      - Auth: `Login.jsx`, `SignUp.jsx`
      - Dashboard: `Dashboard.jsx`, `FlaggedQueue.jsx`, `AuditLog.jsx`, `RulesSettings.jsx`, `KillSwitch.jsx`
    - `lib/`:
      - `supabaseClient.js`
      - `useAuth.jsx`
      - `api.js`
    - `index.css`: Unified Stitch Design System styling (variables, cards, glassmorphic containers, typography, buttons, scrollbars, brand logo responsive rules).
    - `App.jsx`: Global router with `AuthProvider`.
    - `main.jsx`: Single entrypoint.

## Backend CORS Update
In `backend/app/main.py`:
Replace `allow_origins=["*"]` with explicit allowed origins:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
And allow configurable CORS origins via `CORS_ORIGINS` setting with credentials support.

## Verification Plan
1. Install dependencies in `frontend/` and build/start on port 3000.
2. Verify port 3001 is completely free and unreferenced.
3. Test all routes (`/landing`, `/login`, `/signup`, `/dashboard`, etc.) in browser.
4. Verify backend test suite (`pytest backend/tests ml/tests -v`).
