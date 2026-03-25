import psycopg2
import psycopg2.extras
import streamlit as st


def get_connection():
    url = st.secrets["DATABASE_URL"]
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT,
            status      TEXT NOT NULL DEFAULT 'active',
            start_date  TEXT,
            end_date    TEXT,
            created_at  TEXT DEFAULT (CURRENT_DATE::TEXT)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id   SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    """)

    c.execute("""
        INSERT INTO expense_categories (name) VALUES
            ('Rent'), ('Salaries'), ('Suppliers'), ('Materials'),
            ('Marketing'), ('Development'), ('Operations'), ('Other')
        ON CONFLICT DO NOTHING
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id           SERIAL PRIMARY KEY,
            project_id   INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            category     TEXT NOT NULL,
            expense_type TEXT NOT NULL DEFAULT 'variable',
            amount       REAL NOT NULL,
            planned_date TEXT,
            actual_date  TEXT,
            description  TEXT,
            is_recurring INTEGER DEFAULT 0,
            recurrence   TEXT,
            created_at   TEXT DEFAULT (CURRENT_DATE::TEXT)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS revenues (
            id             SERIAL PRIMARY KEY,
            project_id     INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            description    TEXT,
            planned_amount REAL NOT NULL,
            actual_amount  REAL,
            planned_date   TEXT,
            actual_date    TEXT,
            status         TEXT NOT NULL DEFAULT 'expected',
            created_at     TEXT DEFAULT (CURRENT_DATE::TEXT)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id        SERIAL PRIMARY KEY,
            name      TEXT NOT NULL,
            rate_type TEXT NOT NULL DEFAULT 'monthly',
            rate      REAL NOT NULL,
            active    INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS work_logs (
            id          SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL REFERENCES employees(id),
            project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
            hours       REAL,
            log_date    TEXT NOT NULL,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()


# ── Projects ──────────────────────────────────────────────────────────────────

def get_projects(status=None):
    conn = get_connection()
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM projects WHERE status = %s ORDER BY created_at DESC", (status,))
    else:
        c.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_project(name, description, status, start_date, end_date):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO projects (name, description, status, start_date, end_date) VALUES (%s,%s,%s,%s,%s)",
        (name, description, status, start_date, end_date)
    )
    conn.commit()
    conn.close()


def update_project(project_id, name, description, status, start_date, end_date):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE projects SET name=%s, description=%s, status=%s, start_date=%s, end_date=%s WHERE id=%s",
        (name, description, status, start_date, end_date, project_id)
    )
    conn.commit()
    conn.close()


def delete_project(project_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    conn.commit()
    conn.close()


# ── Expenses ──────────────────────────────────────────────────────────────────

def get_expense_categories():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM expense_categories ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [r["name"] for r in rows]


def get_expenses(project_id=None):
    conn = get_connection()
    c = conn.cursor()
    if project_id:
        c.execute(
            """SELECT e.*, p.name as project_name
               FROM expenses e
               LEFT JOIN projects p ON e.project_id = p.id
               WHERE e.project_id = %s
               ORDER BY COALESCE(e.planned_date, e.actual_date) DESC""",
            (project_id,)
        )
    else:
        c.execute(
            """SELECT e.*, p.name as project_name
               FROM expenses e
               LEFT JOIN projects p ON e.project_id = p.id
               ORDER BY COALESCE(e.planned_date, e.actual_date) DESC"""
        )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_expense(project_id, category, expense_type, amount, planned_date, actual_date, description, is_recurring, recurrence):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO expenses
           (project_id, category, expense_type, amount, planned_date, actual_date, description, is_recurring, recurrence)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (project_id or None, category, expense_type, amount, planned_date or None, actual_date or None,
         description, int(is_recurring), recurrence or None)
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
    conn.commit()
    conn.close()


# ── Revenues ──────────────────────────────────────────────────────────────────

def get_revenues(project_id=None):
    conn = get_connection()
    c = conn.cursor()
    if project_id:
        c.execute(
            """SELECT r.*, p.name as project_name
               FROM revenues r
               LEFT JOIN projects p ON r.project_id = p.id
               WHERE r.project_id = %s
               ORDER BY COALESCE(r.planned_date, r.actual_date) DESC""",
            (project_id,)
        )
    else:
        c.execute(
            """SELECT r.*, p.name as project_name
               FROM revenues r
               LEFT JOIN projects p ON r.project_id = p.id
               ORDER BY COALESCE(r.planned_date, r.actual_date) DESC"""
        )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_revenue(project_id, description, planned_amount, actual_amount, planned_date, actual_date, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO revenues
           (project_id, description, planned_amount, actual_amount, planned_date, actual_date, status)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (project_id or None, description, planned_amount,
         actual_amount or None, planned_date or None, actual_date or None, status)
    )
    conn.commit()
    conn.close()


def update_revenue_status(revenue_id, actual_amount, actual_date, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE revenues SET actual_amount=%s, actual_date=%s, status=%s WHERE id=%s",
        (actual_amount, actual_date, status, revenue_id)
    )
    conn.commit()
    conn.close()


def delete_revenue(revenue_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM revenues WHERE id = %s", (revenue_id,))
    conn.commit()
    conn.close()


# ── Employees ─────────────────────────────────────────────────────────────────

def get_employees(active_only=True):
    conn = get_connection()
    c = conn.cursor()
    if active_only:
        c.execute("SELECT * FROM employees WHERE active=1 ORDER BY name")
    else:
        c.execute("SELECT * FROM employees ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_employee(name, rate_type, rate):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO employees (name, rate_type, rate) VALUES (%s,%s,%s)",
        (name, rate_type, rate)
    )
    conn.commit()
    conn.close()


def get_work_logs():
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """SELECT wl.*, e.name as employee_name, e.rate, e.rate_type,
                  p.name as project_name
           FROM work_logs wl
           JOIN employees e ON wl.employee_id = e.id
           LEFT JOIN projects p ON wl.project_id = p.id
           ORDER BY wl.log_date DESC"""
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_work_log(employee_id, project_id, hours, log_date, description):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO work_logs (employee_id, project_id, hours, log_date, description) VALUES (%s,%s,%s,%s,%s)",
        (employee_id, project_id or None, hours, log_date, description)
    )
    conn.commit()
    conn.close()


# ── Aggregations for dashboard / reports ─────────────────────────────────────

def get_project_summary():
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """SELECT
               p.id,
               p.name,
               p.status,
               p.start_date,
               p.end_date,
               COALESCE(SUM(DISTINCT CASE WHEN r.status='received' THEN r.actual_amount END), 0) as actual_revenue,
               COALESCE(SUM(DISTINCT r.planned_amount), 0) as planned_revenue,
               COALESCE(SUM(DISTINCT e.amount), 0) as total_expenses
           FROM projects p
           LEFT JOIN revenues r ON r.project_id = p.id
           LEFT JOIN expenses e ON e.project_id = p.id
           GROUP BY p.id
           ORDER BY p.created_at DESC"""
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_cashflow_timeline():
    """Returns monthly in/out for the next 12 months plus history."""
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """SELECT
               SUBSTRING(COALESCE(planned_date, actual_date), 1, 7) as month,
               SUM(CASE WHEN status='received' THEN COALESCE(actual_amount,0)
                        ELSE planned_amount END) as amount,
               'revenue' as flow_type
           FROM revenues
           WHERE COALESCE(planned_date, actual_date) IS NOT NULL
           GROUP BY month"""
    )
    revenues = c.fetchall()

    c.execute(
        """SELECT
               SUBSTRING(COALESCE(planned_date, actual_date), 1, 7) as month,
               SUM(amount) as amount,
               'expense' as flow_type
           FROM expenses
           WHERE COALESCE(planned_date, actual_date) IS NOT NULL
           GROUP BY month"""
    )
    expenses = c.fetchall()

    conn.close()
    return [dict(r) for r in revenues] + [dict(r) for r in expenses]
