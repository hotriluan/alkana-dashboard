# 05. Technology Stack

## 1. Backend (The Core)
*   **Language:** Python 3.10+
*   **Framework:** FastAPI (High performance, async support).
*   **Data Processing:** Pandas 2.0 (for vectorised heavy lifting) + NumPy.
*   **Database ORM:** SQLAlchemy 2.0 (Async support).
*   **Validation:** Pydantic V2.

## 2. Database
*   **Engine:** PostgreSQL 15+
*   **Drivers:** `psycopg2-binary` and `asyncpg`.
*   **Design:** Star Schema with Relational Integrity.

## 3. Frontend (The Face)
*   **Framework:** React 18
*   **Build Tool:** Vite (Ultra-fast HMR).
*   **Language:** TypeScript (Strict mode enabled).
*   **Styling:** Tailwind CSS v4 (Utility-first).
*   **State Management:** React Query (Server state), Context API (Client state).
*   **Visualization:** Recharts (SVG-based charting).
*   **Icons:** Lucide React.
*   **Routing:** React Router v6.

## 4. Infrastructure & DevOps
*   **Containerization:** Docker & Docker Compose.
*   **Version Control:** Git.
*   **Dependency Management:** `pip` (Backend), `npm` (Frontend).
*   **Environment:** Verified on Windows (Development) and Linux (Production).
