import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Polytanks MFG — 2024 Dashboard",
    page_icon="🏭",
    layout="wide"
)

@st.cache_data
def load_data():
    path = "Polytanks_Cleaned.xlsx"
    sales = pd.read_excel(path, sheet_name="Distributor_Sales", parse_dates=["Date"])
    prod  = pd.read_excel(path, sheet_name="Factory_Production", parse_dates=["Date"])
    rm    = pd.read_excel(path, sheet_name="RM_Inventory",       parse_dates=["Date"])
    sales["Month"]      = sales["Date"].dt.month
    sales["Month_Name"] = sales["Date"].dt.strftime("%b")
    prod["Month"]       = prod["Date"].dt.month
    rm["Month"]         = rm["Date"].dt.month
    rm["Below_Reorder"] = rm["Closing_Stock_MT"] < rm["Reorder_Level_MT"]
    return sales, prod, rm

sales, prod, rm = load_data()

st.markdown("""
<style>
    .main { background-color: #F4F6F9; }
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 18px 22px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #2E75B6;
        margin-bottom: 10px;
    }
    .metric-card.red   { border-left-color: #C0392B; }
    .metric-card.green { border-left-color: #27AE60; }
    .metric-card.orange{ border-left-color: #E67E22; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #1F3864; }
    .metric-label { font-size: 0.85rem; color: #7F8C8D; margin-top: 2px; }
    h1 { color: #1F3864; }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🏭 Polytanks Manufacturing — 2024 Performance Dashboard")
st.markdown("**Data coverage:** January – December 2024 &nbsp;|&nbsp; **Factories:** Accra, Kumasi, Tamale &nbsp;|&nbsp; **Distributors:** 15")
st.divider()

st.sidebar.markdown("### Filters")
factory_filter = st.sidebar.multiselect(
    "Factory", options=["Accra","Kumasi","Tamale"],
    default=["Accra","Kumasi","Tamale"]
)
month_filter = st.sidebar.multiselect(
    "Month", options=list(range(1,13)),
    format_func=lambda x: pd.Timestamp(2024, x, 1).strftime("%B"),
    default=list(range(1,13))
)

sales_f = sales[sales["Month"].isin(month_filter)]
prod_f  = prod[(prod["Factory"].isin(factory_filter)) & (prod["Month"].isin(month_filter))]
rm_f    = rm[(rm["Factory"].isin(factory_filter)) & (rm["Month"].isin(month_filter))]

total_rev      = sales_f["Total_Value_GHS"].sum()
total_units    = sales_f["Qty_Units"].sum()
overdue_val    = sales_f[sales_f["Payment_Status"]=="Overdue"]["Total_Value_GHS"].sum()
pending_val    = sales_f[sales_f["Payment_Status"]=="Pending"]["Total_Value_GHS"].sum()
rejection_rate = prod_f["Rejected_Units"].sum() / prod_f["Actual_Units"].sum() * 100
total_downtime = prod_f["Downtime_Hours"].sum()

k1,k2,k3,k4,k5,k6 = st.columns(6)

def kpi(col, label, value, color=""):
    col.markdown(f"""
    <div class="metric-card {color}">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>""", unsafe_allow_html=True)

kpi(k1, "Total Revenue",         f"GHS {total_rev/1e6:.1f}M")
kpi(k2, "Units Sold",            f"{total_units:,}")
kpi(k3, "Overdue + Pending",     f"GHS {(overdue_val+pending_val)/1e6:.1f}M", "red")
kpi(k4, "Overall Rejection Rate",f"{rejection_rate:.2f}%",                    "orange")
kpi(k5, "Total Downtime Hrs",    f"{total_downtime:,.0f}",                    "orange")
kpi(k6, "Stockout Events",       f"{rm_f['Below_Reorder'].sum()}",            "red")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Sales Performance",
    "Factory Performance",
    "Raw Materials",
    "Linked Insights",
    "Data Quality Log"
])

BG = "#F4F6F9"
factory_colors_map = {"Accra":"#2E75B6","Kumasi":"#70AD47","Tamale":"#C55A11"}

with tab1:
    st.markdown("### Part A — Sales Performance")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**A1 — Top 5 Distributors by Revenue**")
        a1 = (sales_f.groupby(["Distributor_Name","Region"])["Total_Value_GHS"]
              .sum().reset_index().sort_values("Total_Value_GHS", ascending=False).head(5))
        fig, ax = plt.subplots(figsize=(6,4))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        colors = ["#1F3864","#2E75B6","#4A90D9","#6BAED6","#9ECAE1"]
        bars = ax.barh(a1["Distributor_Name"][::-1], a1["Total_Value_GHS"][::-1],
                       color=colors, edgecolor="white")
        for bar, val in zip(bars, a1["Total_Value_GHS"][::-1]):
            ax.text(bar.get_width()+50000, bar.get_y()+bar.get_height()/2,
                    f"GHS {val/1e6:.1f}M", va="center", fontsize=8.5, fontweight="bold")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1e6:.0f}M"))
        ax.set_xlabel("Revenue (GHS)", fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.markdown("**A4 — Payment Status Breakdown**")
        status = sales_f["Payment_Status"].value_counts()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6,4))
        fig.patch.set_facecolor(BG)
        ax1.set_facecolor(BG)
        wedge_colors = ["#27AE60","#E67E22","#C0392B"]
        ax1.pie(status.values, labels=status.index, colors=wedge_colors,
                autopct="%1.1f%%", startangle=90, textprops={"fontsize":9})
        ax1.set_title("Transaction Count", fontsize=10, fontweight="bold")
        ax2.set_facecolor(BG)
        status_val = sales_f.groupby("Payment_Status")["Total_Value_GHS"].sum().reindex(["Paid","Pending","Overdue"])
        ax2.bar(status_val.index, status_val.values/1e6, color=wedge_colors, edgecolor="white")
        ax2.set_ylabel("GHS (Millions)", fontsize=9)
        ax2.set_title("Value at Risk", fontsize=10, fontweight="bold")
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        for i, val in enumerate(status_val.values):
            ax2.text(i, val/1e6+0.3, f"{val/1e6:.1f}M", ha="center", fontsize=8.5, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.markdown("**A3 — Seasonal Sales Pattern**")
    monthly = (sales_f.groupby(["Month","Month_Name"])
               .agg(Revenue=("Total_Value_GHS","sum"), Units=("Qty_Units","sum"))
               .reset_index().sort_values("Month"))
    fig, axes = plt.subplots(1, 2, figsize=(14,4))
    fig.patch.set_facecolor(BG)
    avg_r = monthly["Revenue"].mean()
    bar_colors = ["#C0392B" if r == monthly["Revenue"].max()
                  else "#2E75B6" if r >= avg_r else "#AEB6BF"
                  for r in monthly["Revenue"]]
    axes[0].set_facecolor(BG)
    axes[0].bar(monthly["Month_Name"], monthly["Revenue"], color=bar_colors, edgecolor="white")
    axes[0].axhline(avg_r, color="#E67E22", linewidth=1.5, linestyle="--",
                    label=f"Avg: GHS {avg_r/1e6:.1f}M")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1e6:.1f}M"))
    axes[0].set_title("Monthly Revenue (GHS)", fontsize=12, fontweight="bold")
    axes[0].legend(fontsize=9)
    axes[0].spines["top"].set_visible(False)
    axes[0].spines["right"].set_visible(False)
    axes[1].set_facecolor(BG)
    axes[1].plot(monthly["Month_Name"], monthly["Units"], color="#1F3864",
                 linewidth=2.5, marker="o", markersize=7, markerfacecolor="#E74C3C")
    axes[1].fill_between(monthly["Month_Name"], monthly["Units"], alpha=0.15, color="#2E75B6")
    axes[1].axhline(monthly["Units"].mean(), color="#E67E22", linewidth=1.5, linestyle="--",
                    label=f"Avg: {monthly['Units'].mean():,.0f} units")
    axes[1].set_title("Monthly Units Sold", fontsize=12, fontweight="bold")
    axes[1].legend(fontsize=9)
    axes[1].spines["top"].set_visible(False)
    axes[1].spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown("**A2 — Underperforming Distributors vs Regional Average**")
    reg_rev = (sales_f.groupby(["Distributor_ID","Distributor_Name","Region"])["Total_Value_GHS"]
               .sum().reset_index())
    avg_region = reg_rev.groupby("Region")["Total_Value_GHS"].mean().reset_index()
    avg_region.columns = ["Region","Regional_Avg"]
    a2 = reg_rev.merge(avg_region, on="Region")
    a2["Variance_Pct"] = ((a2["Total_Value_GHS"] - a2["Regional_Avg"]) / a2["Regional_Avg"] * 100).round(1)
    under = a2[a2["Variance_Pct"] < -20].sort_values("Variance_Pct")
    if len(under) == 0:
        st.success("No distributors are more than 20% below their regional average.")
    else:
        fig, ax = plt.subplots(figsize=(10,3))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        ax.barh(under["Distributor_Name"], under["Variance_Pct"], color="#C0392B", edgecolor="white")
        ax.axvline(-20, color="#E67E22", linestyle="--", linewidth=1.5, label="-20% threshold")
        ax.set_xlabel("Variance vs Regional Average (%)")
        ax.set_title("Distributors Below Regional Average", fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

with tab2:
    st.markdown("### Part B — Factory Performance")
    col1, col2 = st.columns(2)

    b1 = (prod_f.groupby("Factory")
          .agg(Target=("Target_Units","sum"),
               Actual=("Actual_Units","sum"),
               Rejected=("Rejected_Units","sum"),
               Downtime=("Downtime_Hours","sum"))
          .reset_index())
    b1["Rejection_Rate"] = (b1["Rejected"] / b1["Actual"] * 100).round(2)
    b1["Efficiency"]     = (b1["Actual"]   / b1["Target"]  * 100).round(2)

    with col1:
        st.markdown("**B1 — Rejection Rate per Factory**")
        fig, ax = plt.subplots(figsize=(6,4))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        bar_c = ["#C0392B" if r == b1["Rejection_Rate"].max() else "#2E75B6" for r in b1["Rejection_Rate"]]
        bars = ax.bar(b1["Factory"], b1["Rejection_Rate"], color=bar_c, edgecolor="white", width=0.5)
        for bar, val in zip(bars, b1["Rejection_Rate"]):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                    f"{val}%", ha="center", fontsize=10, fontweight="bold")
        ax.set_ylabel("Rejection Rate %")
        ax.set_title("Rejection Rate by Factory", fontsize=12, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.markdown("**B4 — Factory Efficiency Comparison**")
        fig, ax = plt.subplots(figsize=(6,4))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        eff_c = ["#C0392B" if e == b1["Efficiency"].min() else "#27AE60" for e in b1["Efficiency"]]
        bars = ax.bar(b1["Factory"], b1["Efficiency"], color=eff_c, edgecolor="white", width=0.5)
        ax.axhline(87, color="#E67E22", linestyle="--", linewidth=1.5, label="Target: 87%")
        for bar, val in zip(bars, b1["Efficiency"]):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                    f"{val}%", ha="center", fontsize=10, fontweight="bold")
        ax.set_ylabel("Production Efficiency %")
        ax.set_title("Efficiency by Factory", fontsize=12, fontweight="bold")
        ax.set_ylim(0,100)
        ax.legend(fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.markdown("**B2 — Machine Downtime Hours**")
    b2 = (prod_f.groupby(["Machine_ID","Factory"])["Downtime_Hours"]
          .sum().reset_index().sort_values("Downtime_Hours", ascending=False))
    b2_colors = [factory_colors_map[f] for f in b2["Factory"]]
    fig, ax = plt.subplots(figsize=(12,4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    bars = ax.bar(b2["Machine_ID"], b2["Downtime_Hours"], color=b2_colors, edgecolor="white")
    for bar, val in zip(bars, b2["Downtime_Hours"]):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2,
                f"{val:.0f}h", ha="center", fontsize=8.5, fontweight="bold")
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=v, label=k) for k,v in factory_colors_map.items()]
    ax.legend(handles=legend_elements, fontsize=9)
    ax.set_ylabel("Total Downtime Hours")
    ax.set_title("Downtime Hours per Machine — 2024", fontsize=12, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown("**B3 — Downtime vs Rejection Rate (Correlation)**")
    b3 = (prod_f.groupby(["Machine_ID","Factory"])
          .agg(Downtime=("Downtime_Hours","sum"),
               Rejected=("Rejected_Units","sum"),
               Actual=("Actual_Units","sum"))
          .reset_index())
    b3["Rejection_Rate"] = (b3["Rejected"] / b3["Actual"] * 100).round(2)
    fig, ax = plt.subplots(figsize=(8,4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for factory, grp in b3.groupby("Factory"):
        ax.scatter(grp["Downtime"], grp["Rejection_Rate"],
                   color=factory_colors_map[factory], s=120, label=factory, zorder=5)
        for _, row in grp.iterrows():
            ax.annotate(row["Machine_ID"], (row["Downtime"], row["Rejection_Rate"]),
                        textcoords="offset points", xytext=(6,4), fontsize=8)
    m, b_coef = np.polyfit(b3["Downtime"], b3["Rejection_Rate"], 1)
    x_line = np.linspace(b3["Downtime"].min(), b3["Downtime"].max(), 100)
    ax.plot(x_line, m*x_line+b_coef, color="#E74C3C", linewidth=1.5,
            linestyle="--", label="Trend (r = -0.498)")
    ax.set_xlabel("Total Downtime Hours", fontsize=10)
    ax.set_ylabel("Rejection Rate %", fontsize=10)
    ax.set_title("Downtime vs Rejection Rate — Weak Negative Correlation", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with tab3:
    st.markdown("### Part C — Raw Materials & Supply Chain")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**C1 — Stockout Events per Factory**")
        c1 = (rm_f[rm_f["Below_Reorder"]]
              .groupby("Factory")["Below_Reorder"].sum().reset_index())
        c1.columns = ["Factory","Stockout_Events"]
        fig, ax = plt.subplots(figsize=(5,4))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        bar_c = ["#C0392B" if v == c1["Stockout_Events"].max() else "#E67E22" for v in c1["Stockout_Events"]]
        bars = ax.bar(c1["Factory"], c1["Stockout_Events"], color=bar_c, edgecolor="white", width=0.5)
        for bar, val in zip(bars, c1["Stockout_Events"]):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                    str(int(val)), ha="center", fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of Stockout Events")
        ax.set_title("Times Below Reorder Level", fontsize=12, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.markdown("**C2 — RM Stockout Risk (Months of Cover)**")
        c2 = (rm_f.groupby("RM_Name")
              .agg(Avg_Consumed=("Consumed_MT","mean"),
                   Avg_Closing=("Closing_Stock_MT","mean"),
                   Times_Below=("Below_Reorder","sum"))
              .reset_index())
        c2["Months_Cover"] = (c2["Avg_Closing"] / c2["Avg_Consumed"]).round(2)
        c2 = c2.sort_values("Months_Cover")
        fig, ax = plt.subplots(figsize=(5,4))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        risk_colors = ["#C0392B" if v < 1.5 else "#E67E22" if v < 2.5 else "#27AE60" for v in c2["Months_Cover"]]
        ax.barh(c2["RM_Name"], c2["Months_Cover"], color=risk_colors, edgecolor="white")
        ax.axvline(1.5, color="#C0392B", linestyle="--", linewidth=1.5, label="Critical (<1.5 months)")
        ax.set_xlabel("Months of Stock Cover")
        ax.set_title("Stock Cover by RM Item", fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    st.markdown("**C3 — Monthly Consumption Spikes**")
    monthly_rm = (rm_f.groupby(["Month","RM_Name"])["Consumed_MT"].sum().reset_index())
    monthly_total_rm = monthly_rm.groupby("Month")["Consumed_MT"].sum().reset_index()
    monthly_total_rm["Month_Name"] = monthly_total_rm["Month"].apply(
        lambda x: pd.Timestamp(2024, x, 1).strftime("%b"))
    overall_avg = monthly_total_rm["Consumed_MT"].mean()
    monthly_total_rm["Spike_Pct"] = ((monthly_total_rm["Consumed_MT"] - overall_avg) / overall_avg * 100).round(1)
    fig, ax = plt.subplots(figsize=(12,4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    spike_colors = ["#C0392B" if v > 50 else "#2E75B6" if v >= 0 else "#AEB6BF"
                    for v in monthly_total_rm["Spike_Pct"]]
    bars = ax.bar(monthly_total_rm["Month_Name"], monthly_total_rm["Consumed_MT"],
                  color=spike_colors, edgecolor="white")
    ax.axhline(overall_avg, color="#E67E22", linewidth=1.5, linestyle="--",
               label=f"Monthly Average: {overall_avg:,.0f} MT")
    for bar, val in zip(bars, monthly_total_rm["Spike_Pct"]):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5,
                f"{val:+.0f}%", ha="center", fontsize=8.5, fontweight="bold",
                color="#C0392B" if val > 50 else "black")
    ax.set_ylabel("Total Consumed (MT)")
    ax.set_title("Monthly Raw Material Consumption — March Spike Highlighted", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

with tab4:
    st.markdown("### Part D — Linking It Together")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**D1 — RM Stockouts vs Production Efficiency**")
        monthly_prod = (prod_f.groupby(["Factory","Month"])
                        .agg(Actual=("Actual_Units","sum"),
                             Target=("Target_Units","sum"),
                             Downtime=("Downtime_Hours","sum"))
                        .reset_index())
        monthly_prod["Efficiency"] = (monthly_prod["Actual"] / monthly_prod["Target"] * 100).round(1)
        stockout_months = (rm_f[rm_f["Below_Reorder"]]
                           .groupby(["Factory","Month"]).size()
                           .reset_index().rename(columns={0:"Stockout_Items"}))
        d1 = monthly_prod.merge(stockout_months, on=["Factory","Month"], how="left")
        d1["Had_Stockout"] = d1["Stockout_Items"].notna()
        d1_sum = d1.groupby("Had_Stockout").agg(
            Avg_Efficiency=("Efficiency","mean"),
            Avg_Downtime=("Downtime","mean")
        ).reset_index().round(2)
        fig, ax = plt.subplots(figsize=(5,4))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        labels = ["No Stockout","Had Stockout"]
        effs   = d1_sum["Avg_Efficiency"].tolist()
        ax.bar(labels, effs, color=["#27AE60","#E67E22"], edgecolor="white", width=0.4)
        for i, v in enumerate(effs):
            ax.text(i, v+0.2, f"{v}%", ha="center", fontsize=12, fontweight="bold")
        ax.set_ylabel("Average Efficiency %")
        ax.set_ylim(70,90)
        ax.set_title("Does Stockout Affect Efficiency?", fontsize=12, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        st.info("Minimal difference (81.6% vs 81.7%) — no direct causal link confirmed.")

    with col2:
        st.markdown("**D2 — Distributor Sales vs Factory Output**")
        factory_sales = (sales_f.groupby("Supplying_Factory")
                         .agg(Units_Sold=("Qty_Units","sum")).reset_index())
        factory_prod2 = (prod_f.groupby("Factory")
                         .agg(Actual=("Actual_Units","sum"),
                              Rejected=("Rejected_Units","sum"))
                         .reset_index())
        factory_prod2["Net_Output"] = factory_prod2["Actual"] - factory_prod2["Rejected"]
        d2 = factory_sales.merge(factory_prod2, left_on="Supplying_Factory", right_on="Factory")
        d2["Coverage_Pct"] = (d2["Units_Sold"] / d2["Net_Output"] * 100).round(1)
        fig, ax = plt.subplots(figsize=(5,4))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)
        x = np.arange(len(d2))
        w = 0.35
        ax.bar(x-w/2, d2["Units_Sold"],  w, label="Sold via Distributors", color="#2E75B6", edgecolor="white")
        ax.bar(x+w/2, d2["Net_Output"],  w, label="Net Production",        color="#AEB6BF", edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels(d2["Supplying_Factory"])
        ax.set_ylabel("Units")
        ax.set_title("Sales vs Production by Factory", fontsize=12, fontweight="bold")
        ax.legend(fontsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for i, row in d2.iterrows():
            ax.text(i, row["Net_Output"]+200, f"{row['Coverage_Pct']}%",
                    ha="center", fontsize=9, fontweight="bold", color="#C0392B")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
        st.info("All factories sell 8-15% through distributors. Kumasi most reliant on other channels.")

with tab5:
    st.markdown("### Data Cleaning Log — All Issues Found & Fixed")
    log = pd.read_excel("Polytanks_Cleaned.xlsx", sheet_name="Cleaning_Log")
    st.dataframe(log, use_container_width=True, hide_index=True)
    st.markdown(f"**Total issues documented: {len(log)}**")

st.divider()
st.caption("Polytanks Manufacturing — 2024 Data Analysis | Built with Python & Streamlit")