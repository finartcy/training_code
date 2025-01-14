import streamlit as st
import pandas as pd
import forex_python.converter as fx
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from bls import BLS
import yfinance as yf

# Set page config
st.set_page_config(page_title="Global Economic Comparison Tool", layout="wide")

# Add title
st.title("Global Economic Comparison Analysis")

# Initialize Forex converter and BLS
c = fx.CurrencyRates()
bls_client = BLS()

# Define currency dictionary with full names
CURRENCIES = {
    'USD': 'United States Dollar',
    'EUR': 'Euro',
    'GBP': 'British Pound Sterling',
    'JPY': 'Japanese Yen',
    'AUD': 'Australian Dollar',
    'CAD': 'Canadian Dollar',
    'CHF': 'Swiss Franc',
    'CNY': 'Chinese Yuan',
    'INR': 'Indian Rupee',
    'NZD': 'New Zealand Dollar',
    'SGD': 'Singapore Dollar',
    'HKD': 'Hong Kong Dollar',
    'KRW': 'South Korean Won',
    'MXN': 'Mexican Peso',
    'BRL': 'Brazilian Real'
}

def get_exchange_rates(base_currency='USD'):
    """Get current exchange rates for selected currencies"""
    rates = {}
    
    for currency in CURRENCIES.keys():
        if currency != base_currency:
            try:
                rates[currency] = c.get_rate(base_currency, currency)
            except:
                rates[currency] = None
            
    return rates

def get_inflation_data():
    """Get inflation data from BLS"""
    series_id = 'CUUR0000SA0'
    end_year = datetime.now().year
    start_year = end_year - 3
    
    try:
        data = bls_client.get_series(series_id, start_year, end_year)
        df = pd.DataFrame(data).reset_index()
        df.columns = ['date', 'value']
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        df['inflation'] = df['value'].pct_change(periods=12) * 100
        return df
    except Exception as e:
        st.error(f"Error fetching BLS data: {str(e)}")
        return None

def main():
    # Currency selection
    st.sidebar.header("Currency Settings")
    base_currency = st.sidebar.selectbox(
        "Select Base Currency",
        options=list(CURRENCIES.keys()),
        format_func=lambda x: f"{x} - {CURRENCIES[x]}"
    )
    
    target_currencies = st.sidebar.multiselect(
        "Select Target Currencies for Comparison",
        options=[curr for curr in CURRENCIES.keys() if curr != base_currency],
        default=['EUR', 'GBP', 'JPY'],
        format_func=lambda x: f"{x} - {CURRENCIES[x]}"
    )

    st.header(f"Exchange Rates (Base: {base_currency})")
    
    # Get and display exchange rates
    rates = get_exchange_rates(base_currency)
    filtered_rates = {k: v for k, v in rates.items() if k in target_currencies}
    rates_df = pd.DataFrame.from_dict(filtered_rates.items())
    rates_df.columns = ['Currency', 'Exchange Rate']
    
    # Add currency full names
    rates_df['Currency Name'] = rates_df['Currency'].map(CURRENCIES)
    
    st.dataframe(rates_df)
    
    # Create exchange rate visualization
    fig = px.bar(rates_df, x='Currency', y='Exchange Rate',
                 title=f'Exchange Rates (Base: {base_currency})',
                 hover_data=['Currency Name'])
    st.plotly_chart(fig)
    
    # Inflation Analysis
    st.header("Inflation Analysis")
    
    inflation_df = get_inflation_data()
    if inflation_df is not None:
        current_inflation = inflation_df['inflation'].dropna().iloc[-1]
        st.metric("Current US Inflation Rate", f"{current_inflation:.2f}%")
        
        fig_inflation = px.line(inflation_df.dropna(),
                              x='date', y='inflation',
                              title='US Inflation Rate Over Time')
        st.plotly_chart(fig_inflation)
    
    # Cost of Living Comparison
    st.header("Cost of Living Comparison")
    
    # Allow user to input their own costs
    st.subheader("Customize Monthly Expenses")
    col1, col2 = st.columns(2)
    
    with col1:
        housing = st.number_input("Housing (Rent/Mortgage)", value=2000)
        food = st.number_input("Food/Groceries", value=500)
        transport = st.number_input("Transportation", value=400)
        healthcare = st.number_input("Healthcare", value=500)
        utilities = st.number_input("Utilities", value=250)
    
    with col2:
        internet = st.number_input("Internet/Phone", value=150)
        insurance = st.number_input("Insurance", value=300)
        entertainment = st.number_input("Entertainment", value=200)
        misc = st.number_input("Miscellaneous", value=300)

    basic_needs = {
        'Housing': housing,
        'Food': food,
        'Transportation': transport,
        'Healthcare': healthcare,
        'Utilities': utilities,
        'Internet/Phone': internet,
        'Insurance': insurance,
        'Entertainment': entertainment,
        'Miscellaneous': misc
    }
    
    # Display basic needs breakdown
    basic_needs_df = pd.DataFrame.from_dict(basic_needs.items())
    basic_needs_df.columns = ['Category', f'Cost ({base_currency})']
    
    # Pie chart for expense breakdown
    fig_pie = px.pie(basic_needs_df, 
                     values=f'Cost ({base_currency})', 
                     names='Category',
                     title='Monthly Expenses Breakdown')
    st.plotly_chart(fig_pie)
    
    total_base = sum(basic_needs.values())
    st.metric(f"Total Monthly Cost ({base_currency})", 
              f"{total_base:,.2f} {base_currency}")
    
    # Convert to selected currencies
    st.subheader("Cost Comparison Across Selected Currencies")
    
    comparison_data = []
    for currency in target_currencies:
        if currency in rates:
            rate = rates[currency]
            converted = total_base * rate
            comparison_data.append({
                'Currency': f"{currency} ({CURRENCIES[currency]})",
                'Monthly Cost': f"{converted:,.2f}",
                'Annual Cost': f"{converted*12:,.2f}"
            })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df)

if __name__ == "__main__":
    main()