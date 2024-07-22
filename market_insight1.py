import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
from pprint import pprint
import time
from markdown_pdf import MarkdownPdf, Section

# Load API key and configure generative model
#api_key = os.getenv("gemini_api_key")
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
        You are an expert data analyst specializing in data science for travel agencies,Based on the travel agency metrics and market metrics given, can you provide a detailed analysis with insights and recommendations, covering and comparing each major metric like by how much % the agency is doing better than the market in terms of profits, or what is the trending destination, or what's customers preferred travel type or scope of improvement based on customer sentiment index or what is the sentiment of reviews (or what is one common theme), looking at the insights, generate some valuable recommendations on how the agency can do better.
        """
        
        # Generate the response from the model
        response = model.generate_content([prompt, str(agency_metrics), str(market_metrics)])
        analysis = response.text

        def stream_data():
            for word in analysis.split(" "):
                yield word + " "
                time.sleep(0.1)

        st.subheader('Detailed Analysis and Recommendations')
        st.write_stream(stream_data)
        #st.write(analysis)

        pdf = MarkdownPdf()
        pdf.add_section(Section(analysis , toc=False))
        pdf.save('output2.pdf')

        with open("output2.pdf","rb") as pdf_file:
            st.download_button(
                label="Download Analysis and Charts as PDF",
                data=pdf_file,
                file_name="market_insights.pdf",
                mime="application/pdf"
            )
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
