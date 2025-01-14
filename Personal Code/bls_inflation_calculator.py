import streamlit as st
import pandas as pd
import forex_python.converter as fx
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from bls import BLS
import yfinance as yf
import numpy as np

# Set page config
st.set_page_config(page_title="Global Currency Analysis Tool", layout="wide")

# Add title
st.title("Global Currency Strength Analysis")

# Initialize Forex converter and BLS
c = fx.CurrencyRates()
bls_client = BLS()

# Define currency dictionary with full names and Yahoo Finance symbols
CURRENCIES = {
    'USD': {'name': 'United States Dollar', 'symbol': None},
    'EUR': {'name': 'Euro', 'symbol': 'EURUSD=X'},
    'GBP': {'name': 'British Pound Sterling', 'symbol': 'GBPUSD=X'},
    'JPY': {'name': 'Japanese Yen', 'symbol': 'JPYUSD=X'},
    'AUD': {'name': 'Australian Dollar', 'symbol': 'AUDUSD=X'},
    'CAD': {'name': 'Canadian Dollar', 'symbol': 'CADUSD=X'},
    'CHF': {'name': 'Swiss Franc', 'symbol': 'CHFUSD=X'},
    'CNY': {'name': 'Chinese Yuan', 'symbol': 'CNYUSD=X'},
}

def get_historical_rates(currency_pair, period='1y'):
    """Get historical exchange rate data using yfinance"""
    try:
        data = yf.download(currency_pair, period=period, interval='1d')
        return data['Close']
    except Exception as e:
        st.error(f"Error fetching historical data for {currency_pair}: {str(e)}")
        return None

def calculate_currency_strength(historical_rates):
    """Calculate currency strength metrics"""
    if historical_rates is None or len(historical_rates) < 2:
        return None
    
    metrics = {
        'Current Rate': historical_rates[-1],
        'YTD Change %': ((historical_rates[-1] / historical_rates[0]) - 1) * 100,
        'Volatility': historical_rates.std() / historical_rates.mean() * 100,
        '52-week High': historical_rates.max(),
        '52-week Low': historical_rates.min()
    }
    return metrics

def main():
    st.sidebar.header("Analysis Settings")
    
    # Time period selection
    period = st.sidebar.selectbox(
        "Select Time Period",
        ['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=3,
        format_func=lambda x: {
            '1mo': '1 Month',
            '3mo': '3 Months',
            '6mo': '6 Months',
            '1y': '1 Year',
            '2y': '2 Years',
            '5y': '5 Years'
        }[x]
    )

    # Currency strength analysis
    st.header("Currency Strength Analysis")
    
    # Create tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["Currency Trends", "Strength Metrics", "Volatility Analysis"])
    
    with tab1:
        st.subheader("Historical Exchange Rate Trends")
        
        # Plot historical rates for all major currencies
        fig_trends = go.Figure()
        
        for curr, details in CURRENCIES.items():
            if curr != 'USD' and details['symbol']:
                rates = get_historical_rates(details['symbol'], period)
                if rates is not None:
                    fig_trends.add_trace(go.Scatter(
                        x=rates.index,
                        y=rates,
                        name=f"{curr}/USD",
                        mode='lines'
                    ))
        
        fig_trends.update_layout(
            title="Currency Exchange Rates vs USD",
            xaxis_title="Date",
            yaxis_title="Exchange Rate",
            hovermode='x unified'
        )
        st.plotly_chart(fig_trends, use_container_width=True)

    with tab2:
        st.subheader("Currency Strength Metrics")
        
        # Calculate strength metrics for all currencies
        strength_data = []
        
        for curr, details in CURRENCIES.items():
            if curr != 'USD' and details['symbol']:
                rates = get_historical_rates(details['symbol'], period)
                if rates is not None:
                    metrics = calculate_currency_strength(rates)
                    if metrics:
                        metrics['Currency'] = curr
                        strength_data.append(metrics)
        
        if strength_data:
            strength_df = pd.DataFrame(strength_data)
            
            # Create a heatmap of currency strength metrics
            fig_heatmap = px.imshow(
                strength_df.set_index('Currency').select_dtypes(include=[np.number]),
                text=strength_df.set_index('Currency').select_dtypes(include=[np.number]).round(2),
                aspect="auto",
                title="Currency Strength Heatmap"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Display metrics table
            st.dataframe(strength_df.style.format({
                'Current Rate': '{:.4f}',
                'YTD Change %': '{:.2f}%',
                'Volatility': '{:.2f}%',
                '52-week High': '{:.4f}',
                '52-week Low': '{:.4f}'
            }))

    with tab3:
        st.subheader("Volatility Analysis")
        
        # Create volatility comparison chart
        volatility_data = []
        
        for curr, details in CURRENCIES.items():
            if curr != 'USD' and details['symbol']:
                rates = get_historical_rates(details['symbol'], period)
                if rates is not None:
                    daily_returns = rates.pct_change().dropna()
                    volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized volatility
                    volatility_data.append({
                        'Currency': curr,
                        'Annualized Volatility %': volatility
                    })
        
        if volatility_data:
            vol_df = pd.DataFrame(volatility_data)
            fig_vol = px.bar(
                vol_df,
                x='Currency',
                y='Annualized Volatility %',
                title="Currency Volatility Comparison",
                color='Annualized Volatility %'
            )
            st.plotly_chart(fig_vol, use_container_width=True)

    # Additional relative strength indicators
    st.header("Relative Strength Indicators")
    
    # Moving average analysis
    for curr, details in CURRENCIES.items():
        if curr != 'USD' and details['symbol']:
            rates = get_historical_rates(details['symbol'], period)
            if rates is not None:
                ma_20 = rates.rolling(window=20).mean()
                ma_50 = rates.rolling(window=50).mean()
                
                fig_ma = go.Figure()
                fig_ma.add_trace(go.Scatter(x=rates.index, y=rates, name=f"{curr}/USD", mode='lines'))
                fig_ma.add_trace(go.Scatter(x=ma_20.index, y=ma_20, name='20-day MA', line=dict(dash='dash')))
                fig_ma.add_trace(go.Scatter(x=ma_50.index, y=ma_50, name='50-day MA', line=dict(dash='dot')))
                
                fig_ma.update_layout(
                    title=f"{curr}/USD Moving Average Analysis",
                    xaxis_title="Date",
                    yaxis_title="Exchange Rate",
                    hovermode='x unified'
                )
                st.plotly_chart(fig_ma, use_container_width=True)

if __name__ == "__main__":
    main()