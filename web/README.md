# Alkana Dashboard - Frontend

React TypeScript application for the Alkana Dashboard supply chain analytics platform.

## Overview

Interactive web interface providing real-time visibility into:
- Executive KPIs and business metrics
- Inventory management and movements
- Lead time analytics and bottlenecks
- Sales performance by channel/customer
- Production yield tracking
- Make-to-order fulfillment
- Accounts receivable aging
- Proactive alert monitoring

## Technology Stack

- **React 19** - UI library
- **TypeScript 5.9** - Type safety
- **Vite** - Build tool and dev server
- **TanStack Query** - Data fetching and caching
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Recharts** - Data visualization

## Quick Start

### Prerequisites
- Node.js 18+
- npm 9+

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### Build for Production

```bash
# Create optimized production build
npm run build

# Preview production build locally
npm run preview
```

Build output: `dist/` directory

## Project Structure

```
web/
├── public/              # Static assets
│   └── logo.svg
├── src/
│   ├── pages/           # Dashboard modules
│   │   ├── ExecutiveDashboard.tsx
│   │   ├── Inventory.tsx
│   │   ├── LeadTimeDashboard.tsx
│   │   ├── SalesPerformance.tsx
│   │   ├── ProductionYield.tsx
│   │   ├── MTOOrders.tsx
│   │   ├── ArAging.tsx
│   │   ├── AlertMonitor.tsx
│   │   └── Login.tsx
│   ├── components/      # Reusable UI components
│   │   ├── DashboardLayout.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── common/
│   ├── services/        # API client and utilities
│   │   └── api.ts
│   ├── types/           # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx          # Root component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── __tests__/           # Test files (coming soon)
├── index.html           # HTML template
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript config
├── package.json         # Dependencies
└── README.md            # This file
```

## Dashboard Modules

### 1. Executive Dashboard (`/`)
High-level KPIs and business overview

### 2. Inventory Management (`/inventory`)
Stock levels and material movements

### 3. Lead Time Analytics (`/lead-time`)
Order fulfillment speed analysis

### 4. Sales Performance (`/sales`)
Revenue analysis and trends

### 5. Production Yield (`/yield`)
Manufacturing efficiency tracking

### 6. MTO Orders (`/mto-orders`)
Make-to-order tracking

### 7. AR Aging (`/ar-aging`)
Receivables management

### 8. Alert Monitor (`/alerts`)
Proactive notifications

## Environment Configuration

Create `.env` file in `web/` directory:

```bash
# API endpoint
VITE_API_URL=http://localhost:8000

# App configuration
VITE_APP_TITLE=Alkana Dashboard
VITE_ENVIRONMENT=development
```

**Production:**
```bash
VITE_API_URL=https://api.dashboard.yourcompany.com
VITE_ENVIRONMENT=production
```

## Development

### Running Development Server

```bash
npm run dev
```

Features:
- Hot Module Replacement (HMR)
- Fast refresh
- Error overlay
- Auto-opens browser

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## API Integration

### Example Usage

```typescript
import { getExecutiveSummary, login } from './services/api';

// Login
const { access_token } = await login('username', 'password');
localStorage.setItem('token', access_token);

// Fetch data
const summary = await getExecutiveSummary();
```

## Related Documentation

- [Main README](../README.md) - Project overview
- [API Reference](../docs/API_REFERENCE.md) - Backend API documentation
- [User Guide](../docs/USER_GUIDE.md) - End-user instructions
- [Contributing](../docs/CONTRIBUTING.md) - Development guidelines

---

**Built with React 19 + TypeScript + Vite**
