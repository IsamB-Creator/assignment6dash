import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(page_title="Poverty & Millionaire Analytics Dashboard", layout="wide")

st.title("Poverty & Millionaire Analytics Dashboard")

st.write(
    """
This dashboard lets you explore a Poverty & Millionaire dataset.  
Upload the dataset below, map the correct columns in the sidebar, and then use the tabs to view:
1. A comparison of **Poverty vs Millionaire population** by state.  
2. A **Millionaire density choropleth map** of the U.S.  
3. A **Poverty rate comparison** across states.  
"""
)

# -------------------------------------------------
# File uploader (used for all questions)
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload the Poverty/Millionaire dataset (CSV or Excel)", 
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is None:
    st.info("Upload your Poverty/Millionaire dataset to begin.")
    st.stop()

filename = uploaded_file.name.lower()
if filename.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

st.subheader("Dataset Preview")
st.dataframe(df.head())

# -------------------------------------------------
# Column mapping in sidebar (so it works with any column names)
# -------------------------------------------------
st.sidebar.header("Column Mapping")

all_cols = list(df.columns)

def default_index(name, cols):
    return cols.index(name) if name in cols else 0

state_col = st.sidebar.selectbox(
    "State name column",
    options=all_cols,
    index=default_index("State", all_cols)
)

population_col = st.sidebar.selectbox(
    "State population column",
    options=all_cols,
    index=default_index("State Population", all_cols)
)

poverty_col = st.sidebar.selectbox(
    "Number in Poverty column",
    options=all_cols,
    index=default_index("Number in Poverty", all_cols)
)

millionaire_col = st.sidebar.selectbox(
    "Number of Millionaires column",
    options=all_cols,
    index=default_index("Number of Millionaires", all_cols)
)

st.sidebar.markdown("---")
st.sidebar.write("Make sure each mapping matches the correct fields in your dataset.")

# -------------------------------------------------
# Basic cleaning / conversions
# -------------------------------------------------
# Numeric conversions
for col in [population_col, poverty_col, millionaire_col]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows missing key info
df_clean = df.dropna(subset=[state_col, population_col, poverty_col, millionaire_col]).copy()

# Precompute rates for later
df_clean["Millionaire_Density"] = df_clean[millionaire_col] / df_clean[population_col]
df_clean["Poverty_Rate"] = df_clean[poverty_col] / df_clean[population_col]

# -------------------------------------------------
# State name -> abbreviation mapping for the map
# -------------------------------------------------
STATE_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "District of Columbia": "DC", "D.C.": "DC"
}

df_clean["state_code"] = df_clean[state_col].map(STATE_ABBREV)
df_map = df_clean.dropna(subset=["state_code"]).copy()

# -------------------------------------------------
# Tabs for Q4
# -------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    ["Poverty vs Millionaires", "Millionaire Density Map", "Poverty Rate"]
)

# =================================================
# Tab 1 – Q1: Poverty vs Millionaire population (side-by-side bar chart)
# =================================================
with tab1:
    st.header("Poverty vs Millionaire Population by State")

    # Multiselect at least 5 states
    all_states = sorted(df_clean[state_col].unique().tolist())
    selected_states = st.multiselect(
        "Select at least 5 states to compare:",
        options=all_states,
        default=all_states[:5] if len(all_states) >= 5 else all_states
    )

    if len(selected_states) == 0:
        st.warning("Select at least one state to see the comparison.")
    else:
        if len(selected_states) < 5:
            st.info("Assignment requirement: use at least **5** states, but the chart will still render.")

        subset = df_clean[df_clean[state_col].isin(selected_states)].copy()

        # Group (in case there are multiple rows per state)
        grouped = subset.groupby(state_col)[[poverty_col, millionaire_col]].sum()

        st.write("Total population in poverty vs millionaires for selected states:")
        display_df = grouped.rename(
            columns={poverty_col: "Number in Poverty", millionaire_col: "Number of Millionaires"}
        ).reset_index()
        st.dataframe(display_df)

        # Side-by-side bar chart with Matplotlib
        states_idx = range(len(grouped))
        width = 0.4

        fig1, ax1 = plt.subplots()
        ax1.bar([i - width/2 for i in states_idx], grouped[poverty_col], width=width, label="In Poverty")
        ax1.bar([i + width/2 for i in states_idx], grouped[millionaire_col], width=width, label="Millionaires")

        ax1.set_xticks(list(states_idx))
        ax1.set_xticklabels(grouped.index, rotation=45, ha="right")
        ax1.set_xlabel("State")
        ax1.set_ylabel("Number of People")
        ax1.set_title("Poverty vs Millionaire Population (Selected States)")
        ax1.legend()

        st.pyplot(fig1)

        # Interpretation
        st.markdown(
            """
**Interpretation (Q1):**  
This chart compares how many people are in poverty versus how many are millionaires in each selected state.  
You can talk about which states show a large poverty population with relatively few millionaires,  
and which states have a higher millionaire count relative to poverty.  
This helps illustrate how uneven wealth distribution can be across different states.
"""
        )

# =================================================
# Tab 2 – Q2: Millionaire Density Map (choropleth)
# =================================================
with tab2:
    st.header("Millionaire Density by U.S. State")

    if df_map.empty:
        st.warning(
            "No valid state codes found for the map. Make sure your state column uses full state names "
            "(e.g., 'California', 'Texas') that can be mapped to two-letter abbreviations."
        )
    else:
        # Choropleth map
        fig2 = px.choropleth(
            df_map,
            locations="state_code",
            locationmode="USA-states",
            color="Millionaire_Density",
            scope="usa",
            hover_name=state_col,
            hover_data={
                state_col: True,
                population_col: True,
                millionaire_col: True,
                "Millionaire_Density": ":.6f"
            },
            color_continuous_scale="Viridis",
            labels={"Millionaire_Density": "Millionaire Density"}
        )

        fig2.update_layout(
            title_text="Millionaire Density by U.S. State",
            geo=dict(showlakes=True, lakecolor="lightblue")
        )

        st.plotly_chart(fig2, use_container_width=True)

        # Interpretation: highlight top and bottom states by density
        dens_sorted = df_map.sort_values("Millionaire_Density", ascending=False)
        top_states = dens_sorted.head(3)[[state_col, "Millionaire_Density"]]
        bottom_states = dens_sorted.tail(3)[[state_col, "Millionaire_Density"]]

        # Build simple text
        top_text = ", ".join(
            f"{row[state_col]} ({row['Millionaire_Density']:.6f})"
            for _, row in top_states.iterrows()
        )
        bottom_text = ", ".join(
            f"{row[state_col]} ({row['Millionaire_Density']:.6f})"
            for _, row in bottom_states.iterrows()
        )

        st.markdown(
            f"""
**Interpretation (Q2):**  
This map shows the share of each state's population that are millionaires (millionaire density).  
States with darker colors have a higher concentration of millionaires relative to their total population.  
In this dataset, some of the highest millionaire densities appear in: {top_text}.  
On the other hand, states such as {bottom_text} sit at the lower end of the distribution.  
You can use this to discuss regional wealth clusters (e.g., coastal vs. inland, North vs. South)  
and how millionaire concentration does **not** always line up with overall population size.
"""
        )

# =================================================
# Tab 3 – Q3: Poverty Rate comparison (horizontal bar chart)
# =================================================
with tab3:
    st.header("Poverty Rate Across States")

    if df_clean.empty:
        st.warning("No valid data available to compute poverty rates.")
    else:
        rate_df = df_clean[[state_col, "Poverty_Rate"]].dropna().drop_duplicates()
        rate_df = rate_df.sort_values("Poverty_Rate", ascending=False)

        st.write("Poverty rate by state:")
        rate_display = rate_df.copy()
        rate_display["Poverty_Rate (%)"] = rate_display["Poverty_Rate"] * 100
        st.dataframe(rate_display[[state_col, "Poverty_Rate (%)"]])

        # Horizontal bar chart
        fig3, ax3 = plt.subplots(figsize=(8, max(4, len(rate_df) * 0.2)))
        ax3.barh(rate_df[state_col], rate_df["Poverty_Rate"] * 100)
        ax3.set_xlabel("Poverty Rate (%)")
        ax3.set_ylabel("State")
        ax3.set_title("Poverty Rate by State (Highest to Lowest)")
        plt.gca().invert_yaxis()  # highest at top

        st.pyplot(fig3)

        # Interpretation
        top_high = rate_df.head(3)
        top_low = rate_df.tail(3)

        high_text = ", ".join(
            f"{row[state_col]} ({row['Poverty_Rate']*100:.1f}%)"
            for _, row in top_high.iterrows()
        )
        low_text = ", ".join(
            f"{row[state_col]} ({row['Poverty_Rate']*100:.1f}%)"
            for _, row in top_low.iterrows()
        )

        st.markdown(
            f"""
**Interpretation (Q3):**  
This chart ranks states by the share of residents living in poverty.  
States at the top of the chart (e.g., {high_text}) carry the heaviest poverty burden.  
At the bottom, states such as {low_text} have much lower poverty rates.  
You can discuss how these differences might connect to regional economies, cost of living,  
and policy choices that affect income support, jobs, and education.
"""
        )
