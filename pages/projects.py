import streamlit as st
from database import get_project_summary, add_project, update_project, delete_project

STATUS_LABELS = {
    "active":    "Active",
    "completed": "Completed",
    "paused":    "Paused",
    "cancelled": "Cancelled",
}
STATUS_ICONS = {
    "active":    "🟢",
    "completed": "✅",
    "paused":    "🟡",
    "cancelled": "🔴",
}


def render():
    st.title("📁 Projects")

    tab_list, tab_add = st.tabs(["All Projects", "Add Project"])

    # ── List tab ──────────────────────────────────────────────────────────────
    with tab_list:
        summaries = get_project_summary()
        if not summaries:
            # BUG FIX: was "return" here which killed render() entirely,
            # preventing the Add Project tab from ever loading.
            st.info("No projects yet. Switch to the 'Add Project' tab to create one.")
        else:
            for p in summaries:
                icon    = STATUS_ICONS.get(p["status"], "⚪")
                label   = STATUS_LABELS.get(p["status"], p["status"])
                revenue = p["actual_revenue"] or p["planned_revenue"]
                profit  = revenue - p["total_expenses"]
                margin  = (profit / revenue * 100) if revenue else 0

                with st.expander(f"{icon} {p['name']}  —  {label}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Planned Revenue", f"${p['planned_revenue']:,.0f}")
                    c2.metric("Actual Revenue",  f"${p['actual_revenue']:,.0f}")
                    c3.metric("Total Expenses",  f"${p['total_expenses']:,.0f}")
                    c4.metric("Gross Profit",    f"${profit:,.0f}",
                              delta=f"{margin:.1f}% margin",
                              delta_color="normal" if profit >= 0 else "inverse")
                    st.caption(
                        f"Start: {p['start_date'] or '—'}   |   End: {p['end_date'] or '—'}"
                    )

                    with st.form(f"edit_project_{p['id']}"):
                        st.subheader("Edit")
                        col1, col2 = st.columns(2)
                        new_name   = col1.text_input("Project name", value=p["name"])
                        new_status = col2.selectbox(
                            "Status",
                            list(STATUS_LABELS.keys()),
                            format_func=lambda x: STATUS_LABELS[x],
                            index=list(STATUS_LABELS.keys()).index(p["status"])
                        )
                        new_desc  = st.text_area("Description",
                                                 value=p.get("description") or "")
                        d1, d2    = st.columns(2)
                        new_start = d1.text_input("Start date (YYYY-MM-DD)",
                                                  value=p.get("start_date") or "")
                        new_end   = d2.text_input("End date (YYYY-MM-DD)",
                                                  value=p.get("end_date") or "")

                        save_col, del_col = st.columns([3, 1])
                        if save_col.form_submit_button("Save changes", type="primary"):
                            update_project(p["id"], new_name, new_desc, new_status,
                                           new_start or None, new_end or None)
                            st.success("Project updated.")
                            st.rerun()
                        if del_col.form_submit_button("Delete", type="secondary"):
                            delete_project(p["id"])
                            st.warning("Project deleted.")
                            st.rerun()

    # ── Add tab ───────────────────────────────────────────────────────────────
    with tab_add:
        with st.form("add_project_form"):
            st.subheader("New Project")
            name        = st.text_input("Project name *")
            description = st.text_area("Description")
            c1, c2, c3  = st.columns(3)
            status      = c1.selectbox("Status", list(STATUS_LABELS.keys()),
                                       format_func=lambda x: STATUS_LABELS[x])
            start_date  = c2.text_input("Start date (YYYY-MM-DD)")
            end_date    = c3.text_input("End date (YYYY-MM-DD)")

            if st.form_submit_button("Create Project", type="primary"):
                if not name.strip():
                    st.error("Project name is required.")
                else:
                    add_project(name.strip(), description, status,
                                start_date or None, end_date or None)
                    st.success(f"Project '{name}' created!")
                    st.rerun()
