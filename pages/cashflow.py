import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from database import get_cashflow_timeline


def render():
    st.title("📅 Cash Flow")

    raw = get_cashflow_timeline()
    if not raw:
        st.info("No data to display. Add revenues and expenses with dates first.")
        return

    df = pd.DataFrame(raw)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    df = df.sort_values("month")

    rev_m = df[df["flow_type"] == "revenue"].set_index("month")["amount"].rename("Revenue")
    exp_m = df[df["flow_type"] == "expense"].set_index("month")["amount"].rename("Expenses")

    combined = pd.concat([rev_m, exp_m], axis=1).fillna(0)
    combined["Profit"]            = combined["Revenue"] - combined["Expenses"]
    combined["Cumulative Cash Flow"] = combined["Profit"].cumsum()
    combined.index = combined.index.strftime("%Y-%m")
    combined = combined.reset_index().rename(columns={"month": "Month"})

    # ── KPIs ──────────────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue",    f"${combined['Revenue'].sum():,.0f}")
    m2.metric("Total Expenses",   f"${combined['Expenses'].sum():,.0f}")
    net = combined["Profit"].sum()
    m3.metric("Net Profit",       f"${net:,.0f}",
              delta_color="normal" if net >= 0 else "inverse")
    last_cumul = combined["Cumulative Cash Flow"].iloc[-1] if not combined.empty else 0
    m4.metric("Cumulative Cash Flow", f"${last_cumul:,.0f}")

    st.divider()

    # ── Chart ─────────────────────────────────────────────────────────────────
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Revenue",  x=combined["Month"], y=combined["Revenue"],
                         marker_color="#4CAF50", opacity=0.85))
    fig.add_trace(go.Bar(name="Expenses", x=combined["Month"], y=combined["Expenses"],
                         marker_color="#F44336", opacity=0.85))
    fig.add_trace(go.Scatter(
        name="Cumulative Cash Flow",
        x=combined["Month"], y=combined["Cumulative Cash Flow"],
        mode="lines+markers",
        line=dict(color="#2196F3", width=3),
        yaxis="y2",
    ))
    fig.update_layout(
        barmode="group",
        title="Monthly Cash Flow",
        xaxis_title="Month",
        yaxis_title="$",
        yaxis2=dict(title="Cumulative ($)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Negative month alerts ─────────────────────────────────────────────────
    neg = combined[combined["Profit"] < 0]
    if not neg.empty:
        st.warning(f"⚠️ **{len(neg)} month(s) with negative cash flow:** " +
                   ", ".join(neg["Month"].tolist()))

    # ── Table ─────────────────────────────────────────────────────────────────
    with st.expander("Detailed data table"):
        display = combined.copy()
        for col in ["Revenue", "Expenses", "Profit", "Cumulative Cash Flow"]:
            display[col] = display[col].apply(lambda x: f"${x:,.0f}")
        st.dataframe(display, use_container_width=True, hide_index=True)
