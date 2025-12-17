import ssl
import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.express as px

# --- PARCHE DE SEGURIDAD PARA MAC ---
ssl._create_default_https_context = ssl._create_unverified_context
# ------------------------------------
# -----------------------------------------------------------------------------
# STEP 1: CONFIGURATION
# -----------------------------------------------------------------------------


FRED_API_KEY = 'd2165896795f34ec9586913d5212de02' 

st.set_page_config(page_title="Macro Trash Index", layout="wide", page_icon="🗑️")

# Custom CSS for styling (Optional - Clean VC Look)
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# STEP 2: DATA LOADING FUNCTIONS
# -----------------------------------------------------------------------------

@st.cache_data
def get_cardboard_data():
    """Fetches the Producer Price Index (PPI) for Cardboard Manufacturing from FRED."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        # Series ID: PCU322211322211P = PPI for Corrugated and Solid Fiber Box Manufacturing
        data = fred.get_series('PCU322211322211P')
        df = pd.DataFrame(data, columns=['Index_Value'])
        df.index.name = 'Date'
        df = df.reset_index()
        # Filter: Last 5 Years
        df = df[df['Date'] > '2019-01-01']
        return df
    except Exception as e:
        st.error(f"Error fetching Cardboard Data. Did you paste your API Key? Details: {e}")
        return pd.DataFrame()

@st.cache_data
def get_nyc_waste_data():
    """Fetches real municipal waste tonnage from NYC Open Data."""
    try:
        url = "https://data.cityofnewyork.us/resource/ebb7-mvp5.json?$limit=5000"
        df = pd.read_json(url)
        
        # Clean Date Format
        df['month'] = pd.to_datetime(df['month'])
        
        # Calculate Total Waste (Residential + Commercial Paper signals)
        # Note: Summing relevant columns to get a proxy for consumption volume
        df['total_waste'] = df['refusetonscollected'] + df['papertonscollected']
        
        # Group by Month to get total tonnage
        monthly_df = df.groupby('month')['total_waste'].sum().reset_index()
        
        # Filter: Last 5 Years
        monthly_df = monthly_df[monthly_df['month'] > '2019-01-01']
        return monthly_df
    except Exception as e:
        st.error(f"Error fetching NYC Data: {e}")
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# STEP 3: THE DASHBOARD LAYOUT
# -----------------------------------------------------------------------------

st.title("🗑️ The Trash Index: Alternative Economic Data")
st.markdown("### Tracking 'Real' Economic Activity via Waste & Packaging Volume")
st.markdown("---")

# Load Data with a loading spinner
with st.spinner('Fetching real time government data...'):
    df_cardboard = get_cardboard_data()
    df_nyc = get_nyc_waste_data()

# Only render the dashboard if data loaded successfully
if not df_cardboard.empty and not df_nyc.empty:
    
    # --- KEY METRICS ROW ---
    col1, col2, col3 = st.columns(3)
    
    # Calculate % Change for Cardboard
    latest_c = df_cardboard.iloc[-1]['Index_Value']
    prev_c = df_cardboard.iloc[-2]['Index_Value']
    delta_c = ((latest_c - prev_c) / prev_c) * 100
    
    # Calculate % Change for Waste
    latest_w = df_nyc.iloc[-1]['total_waste']
    prev_w = df_nyc.iloc[-2]['total_waste']
    delta_w = ((latest_w - prev_w) / prev_w) * 100

    # Display Metrics
    col1.metric("📦 Cardboard Demand (PPI)", f"{latest_c:.1f}", f"{delta_c:.2f}%")
    col2.metric("🚛 NYC Waste (Tons)", f"{latest_w:,.0f}", f"{delta_w:.2f}%")
    
    # Analyst Insight Box
    col3.info("""
    **Analyst Note:**
    * **Cardboard (Manufacturing):** Measures industrial output & shipping demand.
    * **Waste (Consumption):** Measures consumer spending behavior.
    * **Divergence:** If Cardboard drops while Waste stays high, expect a supply chain lag.
    """)

    st.markdown("---")

    # --- CHARTS ROW ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🏭 Manufacturing Signal")
        fig1 = px.line(df_cardboard, x='Date', y='Index_Value', 
                       title='Cardboard Box Producer Price Index (PPI)',
                       color_discrete_sequence=['#FF4B4B']) # Red for Industry
        fig1.update_layout(height=350)
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Source: Federal Reserve Economic Data (FRED)")

    with c2:
        st.subheader("🛍️ Consumer Signal")
        fig2 = px.bar(df_nyc, x='month', y='total_waste', 
                      title='NYC Monthly Waste Tonnage',
                      color_discrete_sequence=['#0068C9']) # Blue for Services
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Source: NYC Open Data Portal")

else:
    st.warning("Data is loading... If this takes too long, please check your API Key configuration.")

# -----------------------------------------------------------------------------
# FOOTER (Portfolio Branding)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("###### *Project by Juan Pablo Cajiga | Built with Python & Streamlit*")