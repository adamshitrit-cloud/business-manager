import streamlit as st
import pandas as pd
from database import get_projects, get_revenues, add_revenue, update_revenue_status, delete_revenue

STATUS_LABELS = {
    "expected":  "Expected",
    "invoiced":  "Invoice Sent",
    "received":  "Received",
    "delayed":   "Delayed",
    "cancelled": "Cancelled",
}
STATUS_ICONS = {
    "expected":  "🕐",
    "invoiced":  "📄",
    "received":  "✅",
    "delayed":   "⚠️",
    "cancelled": "❌",
}


def render():
    st.title("💰 Revenues")

    projects = get_projects()
    project_options = [("", "— General —")] + [(p["id"], p["name"]) for p in projects]

    tab_list, tab_add, tab_update = st.tabs([
        "All Revenues", "Add Expected Revenue", "Update Status"
    ])

    # ── List ──────────────────────────────────────────────────────────────────
    with tab_list:
        fc, sc, _ = st.columns([2, 2, 2])
        filter_project = fc.selectbox(
            "Filter by project",
            options=["All"] + [p["name"] for p in projects],
            key="rev_filter_proj"
        )
        filter_status = sc.selectbox(
            "Filter by status",
            options=["All"] + list(STATUS_LABELS.keys()),
            format_func=lambda x: STATUS_LABELS.get(x, x),
            key="rev_filter_status"
        )

        revenues = get_revenues(
            project_id=next((p["id"] for p in projects if p["name"] == filter_project), None)
            if filter_project != "All" else None
        )
        if filter_status != "All":
            revenues = [r for r in revenues if r["status"] == filter_status]

        if not revenues:
            st.info("No revenues recorded yet.")
        else:
            total_planned  = sum(r["planned_amount"] for r in revenues)
            total_received = sum(r["actual_amount"] or 0 for r in revenues if r["status"] == "received")
            gap            = total_planned - total_received

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Planned",   f"${total_planned:,.0f}")
            m2.metric("Total Received",  f"${total_received:,.0f}")
            m3.metric("Gap / Pending",   f"${gap:,.0f}",
                      delta=f"${gap:,.0f} outstanding",
                      delta_color="inverse" if gap > 0 else "normal")

            for r in revenues:
                icon  = STATUS_ICONS.get(r["status"], "")
                label = STATUS_LABELS.get(r["status"], r["status"])
                proj  = r.get("project_name") or "General"
                with st.container():
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    c1.write(f"{icon} **{r['description'] or '(no description)'}**  \n{proj}")
                    c2.write(f"Planned: ${r['planned_amount']:,.0f}")
                    c3.write(f"Actual: ${r['actual_amount']:,.0f}" if r["actual_amount"] else "Actual: —")
                    c4.write(f"{label}  \n{r['planned_date'] or '—'}")
                st.divider()

    # ── Add ───────────────────────────────────────────────────────────────────
    with tab_add:
        with st.form("add_revenue_form"):
            st.subheader("New Expected Revenue")
            description    = st.text_input("Description / Revenue name *")
            c1, c2         = st.columns(2)
            planned_amount = c1.number_input("Planned amount ($) *", min_value=0.0,
                                             step=500.0, format="%.2f")
            planned_date   = c2.text_input("Expected date (YYYY-MM-DD)")

            proj_idx   = st.selectbox(
                "Project",
                options=list(range(len(project_options))),
                format_func=lambda i: project_options[i][1],
                key="rev_add_proj"
            )
            project_id = project_options[proj_idx][0] or None
            status     = st.selectbox("Initial status", list(STATUS_LABELS.keys()),
                                      format_func=lambda x: STATUS_LABELS[x])

            if st.form_submit_button("Add Revenue", type="primary"):
                if not description.strip() or planned_amount <= 0:
                    st.error("Description and planned amount are required.")
                else:
                    add_revenue(project_id, description.strip(), planned_amount,
                                None, planned_date or None, None, status)
                    st.success("Revenue added!")
                    st.rerun()

    # ── Update status ─────────────────────────────────────────────────────────
    with tab_update:
        st.subheader("Mark Revenue as Received")
        revenues_all = get_revenues()
        pending = [r for r in revenues_all if r["status"] != "received"]
        if not pending:
            st.success("All revenues have been updated.")
        else:
            rev_options = {
                f"#{r['id']} — {r['description'] or '(no description)'} — ${r['planned_amount']:,.0f}": r
                for r in pending
            }
            selected_key = st.selectbox("Select revenue to update", list(rev_options.keys()))
            selected     = rev_options[selected_key]

            with st.form("update_revenue_form"):
                c1, c2, c3    = st.columns(3)
                actual_amount = c1.number_input(
                    "Actual amount received ($)",
                    min_value=0.0, step=100.0, format="%.2f",
                    value=float(selected["planned_amount"])
                )
                actual_date = c2.text_input("Date received (YYYY-MM-DD)")
                new_status  = c3.selectbox(
                    "New status",
                    list(STATUS_LABELS.keys()),
                    format_func=lambda x: STATUS_LABELS[x],
                    index=list(STATUS_LABELS.keys()).index("received")
                )
                if st.form_submit_button("Update", type="primary"):
                    update_revenue_status(selected["id"], actual_amount,
                                          actual_date or None, new_status)
                    st.success("Revenue updated!")
                    st.rerun()
