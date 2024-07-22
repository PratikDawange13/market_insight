import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
from pprint import pprint
import time

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
        Based on the agency metrics and market metrics, can you provide a detailed analysis with insights, 
        like by how much % the agency is doing better than the market in terms of profits, or what is the sentiment 
        of reviews (or what is one common theme), looking at the insights, generate some valuable recommendations 
        on how the agency can do better.
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
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
