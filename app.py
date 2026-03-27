
import io
import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="BOQ PRO PH", page_icon="🏗️", layout="wide")

@st.cache_data
def load_library():
    return pd.read_csv("boq_library_ph.csv")

def normalize_cost(df, location_factor, market_factor):
    dfx = df.copy()
    dfx["unit_cost_min_adj"] = dfx["unit_cost_min"] * location_factor * market_factor
    dfx["unit_cost_max_adj"] = dfx["unit_cost_max"] * location_factor * market_factor
    dfx["unit_cost_mid_adj"] = (dfx["unit_cost_min_adj"] + dfx["unit_cost_max_adj"]) / 2
    return dfx

def money(x):
    return f"₱{x:,.2f}"

st.title("🏗️ BOQ PRO PH")
st.caption("Philippine BOQ library starter for Streamlit-based estimating and scope generation")

library = load_library()

with st.sidebar:
    st.header("Project Settings")
    project_name = st.text_input("Project name", value="Sample Project")
    region = st.selectbox(
        "Location factor",
        ["NCR / Metro Manila (1.00)", "Luzon Province (1.05)", "Visayas (1.08)", "Mindanao (1.10)", "Remote / Island (1.15)"],
        index=0
    )
    location_factor = {
        "NCR / Metro Manila (1.00)": 1.00,
        "Luzon Province (1.05)": 1.05,
        "Visayas (1.08)": 1.08,
        "Mindanao (1.10)": 1.10,
        "Remote / Island (1.15)": 1.15,
    }[region]
    market_factor = st.slider("Market escalation factor", 0.90, 1.30, 1.00, 0.01)
    contingency_pct = st.slider("Contingency %", 0.0, 25.0, 7.5, 0.5)
    ohp_pct = st.slider("Overhead + Profit %", 0.0, 25.0, 10.0, 0.5)
    vat_pct = st.slider("VAT %", 0.0, 15.0, 12.0, 0.5)

df = normalize_cost(library, location_factor, market_factor)

tab1, tab2, tab3, tab4 = st.tabs(["📚 Library", "🧮 BOQ Builder", "📊 Summary", "⬆️ Upload Override"])

with tab1:
    c1, c2, c3 = st.columns([1,1,2])
    category = c1.multiselect("Category", sorted(df["category"].unique()))
    subcat = c2.multiselect("Subcategory", sorted(df["subcategory"].unique()))
    keyword = c3.text_input("Search item")
    view = df.copy()
    if category:
        view = view[view["category"].isin(category)]
    if subcat:
        view = view[view["subcategory"].isin(subcat)]
    if keyword.strip():
        view = view[view["item"].str.contains(keyword, case=False, na=False)]
    st.dataframe(
        view[[
            "category","subcategory","item","unit","unit_cost_min_adj","unit_cost_max_adj","spec_level","notes"
        ]].rename(columns={
            "unit_cost_min_adj":"min_cost_adj",
            "unit_cost_max_adj":"max_cost_adj"
        }),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.subheader("Create Project BOQ")
    if "boq_rows" not in st.session_state:
        st.session_state.boq_rows = []

    c1, c2, c3, c4 = st.columns([2,2,1,1])
    cat = c1.selectbox("Category", sorted(df["category"].unique()))
    sub = c2.selectbox("Subcategory", sorted(df[df["category"] == cat]["subcategory"].unique()))
    items = df[(df["category"] == cat) & (df["subcategory"] == sub)]["item"].tolist()
    item = c3.selectbox("Item", items)
    spec_pick = c4.selectbox("Spec override", ["Use library", "Basic", "Standard", "Premium"])

    sel = df[df["item"] == item].iloc[0]
    c5, c6, c7, c8 = st.columns([1,1,1,1])
    qty = c5.number_input("Quantity", min_value=0.0, value=1.0, step=1.0)
    unit = c6.text_input("Unit", value=str(sel["unit"]))
    rate_mode = c7.selectbox("Rate basis", ["Mid", "Min", "Max", "Custom"])
    custom_rate = c8.number_input("Custom unit rate", min_value=0.0, value=float(sel["unit_cost_mid_adj"]), disabled=(rate_mode != "Custom"))

    min_cost = float(sel["unit_cost_min_adj"])
    max_cost = float(sel["unit_cost_max_adj"])
    mid_cost = float(sel["unit_cost_mid_adj"])

    if spec_pick == "Basic":
        min_cost *= 0.95
        max_cost *= 0.95
        mid_cost *= 0.95
    elif spec_pick == "Premium":
        min_cost *= 1.10
        max_cost *= 1.15
        mid_cost *= 1.125

    unit_rate = {
        "Min": min_cost,
        "Mid": mid_cost,
        "Max": max_cost,
        "Custom": float(custom_rate)
    }[rate_mode]

    amount = qty * unit_rate
    st.info(f"Selected rate: {money(unit_rate)} per {unit} | Amount: {money(amount)}")

    note = st.text_input("Project-specific note")
    if st.button("Add to BOQ", type="primary"):
        st.session_state.boq_rows.append({
            "category": cat,
            "subcategory": sub,
            "item": item,
            "qty": qty,
            "unit": unit,
            "unit_rate": round(unit_rate, 2),
            "amount": round(amount, 2),
            "note": note,
        })

    boq_df = pd.DataFrame(st.session_state.boq_rows)
    if not boq_df.empty:
        st.dataframe(boq_df, use_container_width=True, hide_index=True)
        c9, c10 = st.columns([1,1])
        if c9.button("Remove last row"):
            st.session_state.boq_rows.pop()
            st.rerun()
        if c10.button("Clear BOQ"):
            st.session_state.boq_rows = []
            st.rerun()

with tab3:
    boq_df = pd.DataFrame(st.session_state.get("boq_rows", []))
    st.subheader("Cost Summary")
    if boq_df.empty:
        st.warning("No BOQ items yet.")
    else:
        direct_cost = float(boq_df["amount"].sum())
        contingency = direct_cost * contingency_pct / 100.0
        ohp = direct_cost * ohp_pct / 100.0
        subtotal = direct_cost + contingency + ohp
        vat = subtotal * vat_pct / 100.0
        grand_total = subtotal + vat

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Direct Cost", money(direct_cost))
        m2.metric("Contingency", money(contingency))
        m3.metric("O/H + Profit", money(ohp))
        m4.metric("VAT", money(vat))
        m5.metric("Grand Total", money(grand_total))

        by_cat = boq_df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        st.bar_chart(by_cat.set_index("category"))

        summary = boq_df.groupby(["category","subcategory"], as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        st.dataframe(summary, use_container_width=True, hide_index=True)

        export_df = boq_df.copy()
        export_df.loc[len(export_df)] = ["","","DIRECT COST","","",round(direct_cost,2),""]
        export_df.loc[len(export_df)] = ["","","CONTINGENCY","","",round(contingency,2),f"{contingency_pct}%"]
        export_df.loc[len(export_df)] = ["","","O/H + PROFIT","","",round(ohp,2),f"{ohp_pct}%"]
        export_df.loc[len(export_df)] = ["","","VAT","","",round(vat,2),f"{vat_pct}%"]
        export_df.loc[len(export_df)] = ["","","GRAND TOTAL","","",round(grand_total,2),""]

        csv_bytes = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download BOQ CSV",
            csv_bytes,
            file_name=f"{project_name.lower().replace(' ','_')}_boq.csv",
            mime="text/csv"
        )

with tab4:
    st.subheader("Upload your own cost library")
    st.write("Upload a CSV with the same columns as the starter library if you want to override or extend this package.")
    up = st.file_uploader("Upload CSV", type=["csv"])
    if up:
        try:
            uploaded = pd.read_csv(up)
            st.success("CSV loaded successfully.")
            st.dataframe(uploaded.head(20), use_container_width=True)
        except Exception as e:
            st.error(f"Could not read file: {e}")

st.markdown("---")
st.caption("Tip: start with the starter library, then replace item rates with your own supplier quotes, recent abstracts, or agency-approved unit costs.")
