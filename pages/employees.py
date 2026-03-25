import streamlit as st
import pandas as pd
from database import get_employees, add_employee, get_projects, get_work_logs, add_work_log

RATE_LABELS = {"monthly": "Monthly", "hourly": "Hourly"}


def render():
    st.title("👥 Employees")

    tab_emp, tab_logs, tab_add_emp = st.tabs([
        "Employee List", "Work Log", "Add Employee"
    ])

    # ── Employee list ─────────────────────────────────────────────────────────
    with tab_emp:
        employees = get_employees(active_only=False)
        if not employees:
            st.info("No employees added yet.")
        else:
            df = pd.DataFrame(employees)
            df["Rate Type"] = df["rate_type"].map(RATE_LABELS)
            df["Rate"]      = df.apply(
                lambda r: f"${r['rate']:,.0f}/mo" if r["rate_type"] == "monthly"
                else f"${r['rate']:,.2f}/hr", axis=1
            )
            df["Active"] = df["active"].map({1: "Yes", 0: "No"})
            st.dataframe(
                df[["name", "Rate Type", "Rate", "Active"]].rename(columns={"name": "Name"}),
                use_container_width=True, hide_index=True
            )

    # ── Work log ──────────────────────────────────────────────────────────────
    with tab_logs:
        logs = get_work_logs()
        if not logs:
            st.info("No work logs recorded.")
        else:
            df_logs = pd.DataFrame(logs)
            df_logs["Cost"] = df_logs.apply(
                lambda r: r["rate"] * r["hours"] if r["rate_type"] == "hourly" else 0.0, axis=1
            )
            df_logs["Hours"]   = df_logs["hours"].apply(lambda x: f"{x:.1f}")
            df_logs["Project"] = df_logs["project_name"].fillna("General")
            df_logs["Cost $"]  = df_logs["Cost"].apply(lambda x: f"${x:,.0f}" if x > 0 else "—")

            display = df_logs[["employee_name", "Project", "Hours", "log_date",
                                "description", "Cost $"]]
            display = display.rename(columns={
                "employee_name": "Employee",
                "log_date":      "Date",
                "description":   "Description",
            })
            st.dataframe(display, use_container_width=True, hide_index=True)
            st.metric("Total Calculated Hourly Cost",
                      f"${df_logs['Cost'].sum():,.0f}")

        st.divider()
        st.subheader("Log Work Hours")
        employees = get_employees()
        projects  = get_projects()
        project_options = [("", "— General —")] + [(p["id"], p["name"]) for p in projects]

        if not employees:
            st.warning("Add an employee first.")
        else:
            with st.form("add_work_log_form"):
                c1, c2, c3 = st.columns(3)
                emp_idx    = c1.selectbox("Employee", range(len(employees)),
                                          format_func=lambda i: employees[i]["name"])
                employee_id = employees[emp_idx]["id"]

                proj_idx   = c2.selectbox(
                    "Project", range(len(project_options)),
                    format_func=lambda i: project_options[i][1],
                    key="wl_proj"
                )
                project_id = project_options[proj_idx][0] or None
                hours      = c3.number_input("Hours", min_value=0.0, step=0.5, format="%.1f")

                log_date    = st.text_input("Date (YYYY-MM-DD)")
                description = st.text_input("Description")

                if st.form_submit_button("Add Log", type="primary"):
                    if hours <= 0 or not log_date:
                        st.error("Hours and date are required.")
                    else:
                        add_work_log(employee_id, project_id, hours, log_date, description)
                        st.success("Work log added!")
                        st.rerun()

    # ── Add employee ──────────────────────────────────────────────────────────
    with tab_add_emp:
        with st.form("add_employee_form"):
            st.subheader("New Employee")
            name      = st.text_input("Name *")
            c1, c2    = st.columns(2)
            rate_type = c1.selectbox("Rate type", list(RATE_LABELS.keys()),
                                     format_func=lambda x: RATE_LABELS[x])
            rate      = c2.number_input(
                "Rate ($)" + (" per hour" if rate_type == "hourly" else " per month"),
                min_value=0.0, step=50.0, format="%.2f"
            )
            if st.form_submit_button("Add Employee", type="primary"):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    add_employee(name.strip(), rate_type, rate)
                    st.success(f"Employee '{name}' added!")
                    st.rerun()
