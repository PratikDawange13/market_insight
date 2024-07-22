import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# Load environment variables
load_dotenv()

# Configure API key
api_key = st.secrets["gemini_api_key"]  
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title('Market Insights')

st.header('Upload Metrics in JSON Format')

col1, col2 = st.columns(2)

with col1:
    agency_file = st.file_uploader("Upload Agency Metrics JSON File", type="json")

with col2:
    market_file = st.file_uploader("Upload Market Metrics JSON File", type="json")

def create_charts(agency_metrics, market_metrics):
    # Pie chart for product categories
    agency_products = agency_metrics['kpis']['products']['by_category']
    agency_pie = px.pie(values=agency_products.values(), names=agency_products.keys(), title='Agency Product Categories')
    
    market_products = market_metrics['market_overview']['metrics']['products']['avg_by_category']
    market_pie = px.pie(values=market_products.values(), names=market_products.keys(), title='Market Average Product Categories')
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(agency_pie)
    with col2:
        st.plotly_chart(market_pie)
    
    # Bar chart for Sales comparison
    kpis_to_compare = ['sales']
    agency_sales = [agency_metrics['kpis']['sales']['total_revenue']]
    market_sales = [market_metrics['market_overview']['metrics']['sales']['avg_total_revenue']]
    
    bar_fig = go.Figure(data=[
        go.Bar(name='Agency', x=kpis_to_compare, y=agency_sales),
        go.Bar(name='Market Average', x=kpis_to_compare, y=market_sales)
    ])
    
    bar_fig.update_layout(barmode='group', title='Sales Comparison: Agency vs Market Average', xaxis_title='KPIs', yaxis_title='Values')
    
    # Line chart for Bookings and Reviews comparison
    line_kpis = ['bookings', 'reviews']
    agency_values = [agency_metrics['kpis']['bookings']['total'],
                     agency_metrics['kpis']['reviews']['total_count']]
    market_values = [market_metrics['market_overview']['metrics']['bookings']['avg_total'],
                     market_metrics['market_overview']['metrics']['reviews']['avg_total_count']]
    
    line_fig = go.Figure()
    line_fig.add_trace(go.Scatter(x=line_kpis, y=agency_values, mode='lines+markers', name='Agency'))
    line_fig.add_trace(go.Scatter(x=line_kpis, y=market_values, mode='lines+markers', name='Market Average'))
    
    line_fig.update_layout(title='Bookings and Reviews Comparison: Agency vs Market Average', xaxis_title='KPIs', yaxis_title='Values')
    
    # Display bar chart and line chart in the same row
    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(bar_fig)
    with col4:
        st.plotly_chart(line_fig)

if st.button('Generate Analysis'):
    try:
        # Read the uploaded files
        if agency_file is not None:
            agency_metrics = json.load(agency_file)
        else:
            st.error("Please upload the agency metrics JSON file.")
            st.stop()
        
        if market_file is not None:
            market_metrics = json.load(market_file)
        else:
            st.error("Please upload the market metrics JSON file.")
            st.stop()
        
        # Prompt for generative model 
        prompt = """
        Based on the agency metrics and market metrics, can you provide a detailed analysis with insights, like by how much % the agency is doing better than the market in terms of profits, or what is the sentiment of reviews (or what is one common theme), looking at the insights, generate some valuable recommendations on how the agency can do better.
        """
        
        # Generate the response from the model
        response = model.generate_content([prompt, str(agency_metrics), str(market_metrics)])
        analysis = response.text
        
        def stream_data():
            for word in analysis.split(" "):
                yield word + " "
                time.sleep(0.1)
        
        st.subheader('Detailed Analysis and Recommendations')
        st.write(stream_data)
        
        # Generate and display charts
        st.subheader('Visual Analysis')
        create_charts(agency_metrics, market_metrics)
        
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")