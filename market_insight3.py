import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
import time
import io
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from markdown_pdf import MarkdownPdf, Section

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

def plot_to_temp_file(fig):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        fig.write_image(tmpfile.name)
        return tmpfile.name

def create_charts(agency_metrics, market_metrics):
    try:
        # Pie chart for product categories
        agency_products = agency_metrics['kpis']['products']['by_category']
        agency_pie = px.pie(values=list(agency_products.values()), names=list(agency_products.keys()), title='Agency Product Categories')

        market_products = market_metrics['market_overview']['metrics']['products']['avg_by_category']
        market_pie = px.pie(values=list(market_products.values()), names=list(market_products.keys()), title='Market Average Product Categories')

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

        return agency_pie, market_pie, bar_fig, line_fig

    except KeyError as e:
        st.error(f"Error: Missing key in metrics JSON - {e}")
        return None, None, None, None
    except Exception as e:
        st.error(f"Error creating charts: {e}")
        return None, None, None, None

if st.button('Generate Analysis'):
    try:
        if agency_file is None or market_file is None:
            st.error("Please upload both agency and market metrics JSON files.")
            st.stop()

        # Read the uploaded files
        agency_metrics = json.load(agency_file)
        market_metrics = json.load(market_file)

        # Prompt for generative model
        prompt = """
        You are an expert data analyst specializing in data science for travel agencies,Based on the travel agency metrics and market metrics given, can you provide a detailed analysis with insights and recommendations, covering and comparing each major metric like by how much % the agency is doing better than the market in terms of profits, or what is the trending destination, or what's customers preferred travel type or scope of improvement based on customer sentiment index or what is the sentiment of reviews (or what is one common theme), looking at the insights, generate concise insights and concise 
        some valuable  recommendations on how the agency can do better.
        """

        # Generate the response from the model
        response = model.generate_content([prompt, str(agency_metrics), str(market_metrics)])
        analysis = response.text

        def stream_data():
            for word in analysis.split(" "):
                yield word + " "
                time.sleep(0.1)

        st.subheader('Detailed Analysis and Recommendations')
        st.write_stream(stream_data())

        # Generate charts
        st.subheader('Visual Analysis')
        agency_pie, market_pie, bar_fig, line_fig = create_charts(agency_metrics, market_metrics)

        if agency_pie is not None and market_pie is not None and bar_fig is not None and line_fig is not None:
            # Display charts in Streamlit
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(agency_pie)
            with col2:
                st.plotly_chart(market_pie)

            col3, col4 = st.columns(2)
            with col3:
                st.plotly_chart(bar_fig)
            with col4:
                st.plotly_chart(line_fig)

            # Save charts as temporary files
            chart_files = [
                plot_to_temp_file(agency_pie),
                plot_to_temp_file(market_pie),
                plot_to_temp_file(bar_fig),
                plot_to_temp_file(line_fig)
            ]

            # Create PDF
            pdf = MarkdownPdf()
            pdf.add_section(Section(analysis, toc=False))
            pdf.save('output2.pdf')

            with open("output2.pdf", "rb") as pdf_file:
                st.download_button(
                    label="Download as PDF",
                    data=pdf_file,
                    file_name="market_insights.pdf",
                    mime="application/pdf"
                )

            # Clean up temporary files
            for file in chart_files:
                os.unlink(file)

    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error(str(e))  # Add this line to get more details about the error