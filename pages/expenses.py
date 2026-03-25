import streamlit as st
import pandas as pd
from database import get_projects, get_expenses, add_expense, delete_expense, get_expense_categories

TYPE_LABELS = {
    "fixed":    "Fixed",
    "variable": "Variable",
    "employee": "Payroll / Staff",
}


def render():
    st.title("💸 Expenses")

    projects = get_projects()
    project_options = [("", "— General (no project) —")] + [(p["id"], p["name"]) for p in projects]

    tab_list, tab_add = st.tabs(["All Expenses", "Add Expense"])

    # ── List ──────────────────────────────────────────────────────────────────
    with tab_list:
        filter_col, _ = st.columns([2, 4])
        filter_project = filter_col.selectbox(
            "Filter by project",
            options=["All"] + [p["name"] for p in projects],
            key="expense_filter"
        )

        if filter_project == "All":
            expenses = get_expenses()
        else:
            pid = next((p["id"] for p in projects if p["name"] == filter_project), None)
            expenses = get_expenses(project_id=pid)

        if not expenses:
            st.info("No expenses recorded yet.")
        else:
            df = pd.DataFrame(expenses)
            df["Type"]           = df["expense_type"].map(TYPE_LABELS)
            df["Project"]        = df["project_name"].fillna("General")
            df["Planned Date"]   = df["planned_date"].fillna("—")
            df["Actual Date"]    = df["actual_date"].fillna("—")
            df["Amount"]         = df["amount"].apply(lambda x: f"${x:,.0f}")
            df["Recurring"]      = df["is_recurring"].map({0: "No", 1: "Yes"})

            total = df["amount"].sum()
            st.metric("Total Expenses Shown", f"${total:,.0f}")

            with st.expander("Breakdown by category"):
                cat_df = df.groupby("category")["amount"].sum().reset_index()
                cat_df.columns = ["Category", "Amount"]
                cat_df["Amount"] = cat_df["Amount"].apply(lambda x: f"${x:,.0f}")
                st.dataframe(cat_df, use_container_width=True, hide_index=True)

            display = df[["id", "category", "Type", "Project", "Amount",
                          "Planned Date", "Actual Date", "description", "Recurring"]]
            display = display.rename(columns={
                "id": "ID",
                "category": "Category",
                "description": "Description",
            })
            st.dataframe(display, use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("Delete an expense")
            del_id = st.number_input("Expense ID to delete", min_value=1, step=1, key="del_exp")
            if st.button("Delete", key="del_exp_btn", type="secondary"):
                delete_expense(int(del_id))
                st.success("Expense deleted.")
                st.rerun()

    # ── Add ───────────────────────────────────────────────────────────────────
    with tab_add:
        categories = get_expense_categories()
        with st.form("add_expense_form"):
            st.subheader("New Expense")
            c1, c2, c3 = st.columns(3)
            category     = c1.selectbox("Category *", categories)
            expense_type = c2.selectbox("Type", list(TYPE_LABELS.keys()),
                                        format_func=lambda x: TYPE_LABELS[x])
            amount       = c3.number_input("Amount ($) *", min_value=0.0, step=100.0, format="%.2f")

            proj_idx   = st.selectbox(
                "Project",
                options=list(range(len(project_options))),
                format_func=lambda i: project_options[i][1],
            )
            project_id = project_options[proj_idx][0] or None

            d1, d2       = st.columns(2)
            planned_date = d1.text_input("Planned date (YYYY-MM-DD)")
            actual_date  = d2.text_input("Actual date (YYYY-MM-DD)")
            description  = st.text_input("Description")

            r1, r2        = st.columns(2)
            is_recurring  = r1.checkbox("Recurring expense?")
            recurrence    = r2.selectbox("Frequency",
                                         ["Monthly", "Weekly", "Quarterly", "Yearly"],
                                         disabled=not is_recurring)

            if st.form_submit_button("Add Expense", type="primary"):
                if amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    add_expense(project_id, category, expense_type, amount,
                                planned_date or None, actual_date or None,
                                description, is_recurring,
                                recurrence if is_recurring else None)
                    st.success("Expense added!")
                    st.rerun()
