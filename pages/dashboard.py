import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from database import get_project_summary, get_expenses, get_revenues, get_cashflow_timeline

ALERT_THRESHOLD_MARGIN = 0.10


def _build_alerts(summaries, revenues):
    alerts = []

    for p in summaries:
        if p["status"] not in ("active", "paused"):
            continue
        revenue = p["actual_revenue"] or p["planned_revenue"]
        if revenue > 0:
            margin = (revenue - p["total_expenses"]) / revenue
            if margin < ALERT_THRESHOLD_MARGIN:
                alerts.append({
                    "level": "danger" if margin < 0 else "warning",
                    "msg": f"Project **{p['name']}**: low margin ({margin*100:.1f}%) — "
                           f"Expenses: ${p['total_expenses']:,.0f} / Revenue: ${revenue:,.0f}"
                })

    today = date.today().isoformat()
    for r in revenues:
        if r["status"] in ("expected", "invoiced") and r["planned_date"] and r["planned_date"] < today:
            days_late = (date.today() - date.fromisoformat(r["planned_date"])).days
            alerts.append({
                "level": "warning",
                "msg": f"Revenue **{r['description'] or '#' + str(r['id'])}** not yet received — "
                       f"{days_late} days overdue (expected: {r['planned_date']})"
            })

    return alerts


def render():
    st.title("📊 Dashboard")

    summaries = get_project_summary()
    revenues  = get_revenues()
    expenses  = get_expenses()
    cashflow_raw = get_cashflow_timeline()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_planned_rev = sum(p["planned_revenue"] for p in summaries)
    total_actual_rev  = sum(p["actual_revenue"]  for p in summaries)
    total_expenses    = sum(p["total_expenses"]  for p in summaries)
    net_profit        = total_actual_rev - total_expenses

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Active Projects",   len([p for p in summaries if p["status"] == "active"]))
    k2.metric("Planned Revenue",   f"${total_planned_rev:,.0f}")
    k3.metric("Revenue Received",  f"${total_actual_rev:,.0f}")
    k4.metric("Total Expenses",    f"${total_expenses:,.0f}")
    k5.metric("Net Profit",        f"${net_profit:,.0f}",
              delta_color="normal" if net_profit >= 0 else "inverse")

    st.divider()

    # ── Alerts ────────────────────────────────────────────────────────────────
    alerts = _build_alerts(summaries, revenues)
    if alerts:
        st.subheader("🔔 Alerts")
        for a in alerts:
            st.markdown(
                f'<div class="alert-box {a["level"]}">{a["msg"]}</div>',
                unsafe_allow_html=True
            )

    # ── Charts ────────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Profitability by Project")
        if summaries:
            chart_data = []
            for p in summaries:
                rev = p["actual_revenue"] or p["planned_revenue"]
                chart_data.append({
                    "Project": p["name"],
                    "Revenue": rev,
                    "Expenses": p["total_expenses"],
                    "Profit": rev - p["total_expenses"],
                })
            df = pd.DataFrame(chart_data)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Revenue",  x=df["Project"], y=df["Revenue"],
                                 marker_color="#4CAF50"))
            fig.add_trace(go.Bar(name="Expenses", x=df["Project"], y=df["Expenses"],
                                 marker_color="#F44336"))
            fig.add_trace(go.Scatter(name="Profit", x=df["Project"], y=df["Profit"],
                                     mode="lines+markers",
                                     line=dict(color="#2196F3", width=2)))
            fig.update_layout(barmode="group", height=350,
                              legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No projects yet.")

    with col_right:
        st.subheader("Expenses by Category")
        if expenses:
            cat_totals = {}
            for e in expenses:
                cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
            df_pie = pd.DataFrame(list(cat_totals.items()), columns=["Category", "Amount"])
            fig_pie = px.pie(df_pie, names="Category", values="Amount",
                             height=350, hole=0.35)
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenses yet.")

    # ── Cash flow trend ───────────────────────────────────────────────────────
    if cashflow_raw:
        st.subheader("Cash Flow Trend")
        df = pd.DataFrame(cashflow_raw)
        df["month"] = pd.to_datetime(df["month"] + "-01")
        rev_m = df[df["flow_type"] == "revenue"].set_index("month")["amount"].rename("Revenue")
        exp_m = df[df["flow_type"] == "expense"].set_index("month")["amount"].rename("Expenses")
        combined = pd.concat([rev_m, exp_m], axis=1).fillna(0)
        combined["Profit"] = combined["Revenue"] - combined["Expenses"]
        combined.index = combined.index.strftime("%Y-%m")

        fig_cf = go.Figure()
        fig_cf.add_trace(go.Scatter(
            x=combined.index, y=combined["Profit"],
            fill="tozeroy",
            line=dict(color="#2196F3", width=2),
            fillcolor="rgba(33,150,243,0.15)",
            name="Monthly Profit"
        ))
        fig_cf.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
        fig_cf.update_layout(height=250, showlegend=False,
                             yaxis_title="$", xaxis_title="")
        st.plotly_chart(fig_cf, use_container_width=True)

    # ── Projects table ────────────────────────────────────────────────────────
    st.subheader("Projects Summary")
    if summaries:
        rows = []
        for p in summaries:
            rev = p["actual_revenue"] or p["planned_revenue"]
            profit = rev - p["total_expenses"]
            margin = (profit / rev * 100) if rev else 0
            rows.append({
                "Project":    p["name"],
                "Status":     p["status"].capitalize(),
                "Revenue":    f"${rev:,.0f}",
                "Expenses":   f"${p['total_expenses']:,.0f}",
                "Profit":     f"${profit:,.0f}",
                "Margin %":   f"{margin:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No data yet. Start by adding a project.")
