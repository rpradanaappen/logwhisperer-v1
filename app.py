import requests
import streamlit as st
from elasticsearch import Elasticsearch, exceptions
from summarizer import Summarizer
import openai
from datetime import datetime, timedelta
from streamlit_lottie import st_lottie

# ---- OPENAI CONFIG ----
username = ""
password = ""
# openai.api_key = ''
# es = Elasticsearch(
#     ['https://quadrant-observability.es.us-east-1.aws.found.io'],
#     http_auth=(username, password),
#     port=443,
#     use_ssl=True,
#     verify_certs=False,
#     http_compress=True,
#     scheme='https',
# )

result_buffer = []

def check_elasticsearch_connection():
    try:
        es.ping()
        st.success("Connected to Elasticsearch! 🔗")
    except exceptions.ConnectionError:
        st.error("Unable to connect to Elasticsearch. Check your connection details.")

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Log Whisperer", page_icon=":robot:", layout="wide")

def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ---- LOAD LOTTIE ASSETS ----
lottie_bug = load_lottieurl("https://lottie.host/61f952a7-8a6c-4d8c-8ee3-35829f1858a8/xXx2VkCpcF.json")

#  ---- SIDEBAR ----
with st.container():
    openai.api_key = st.sidebar.text_input(
        "First, enter your OpenAI API key", type="password"
    )
    st.write("")
    st.sidebar.caption(
        "No OpenAI API key? Get yours [here!](https://openai.com/blog/api-no-waitlist/)"
    )
    image_arrow = st.sidebar.image(
        "Gifs/blue_grey_arrow.gif",
    )

# ---- HEADER ----
with st.container():
    st.subheader("The AI Driven Error Logging and Analysis")
    st.title("Log Whisperer")

# ---- ABOUT ----
with st.container():
    st.write("---")
    left_column, right_column = st.columns(2)
    with left_column:
        st.header("What is Log Whisperer?")
        st.write("Tired of spending hours for searching root causes of your app errors? Here's some nifty solution to help you 👇")
        st.write("Log Whisperer will help you to analyze your log files to find errors in the code and give you recommendations on how to solve them")
    with right_column:
        st_lottie(lottie_bug, height=300, key="coding")

# ---- FORM ----
with st.container():
    st.write("---")
    st.header("Let's begin analyzing your log file")
    st.write("##")

    if "counter" not in st.session_state:
        st.session_state.counter = 0

    def increment():
        st.session_state.counter += 1

    with st.form("analyze_form"):
            elasticsearch_index = st.text_input("Elasticsearch Index")
            col1, col2 = st.columns(2, gap="small")

            with col1:
                log_group = st.text_input("AWS Cloudwatch Log Group")

            with col2:
                search_query = st.text_input("Search Query")

            col1, col2 = st.columns(2, gap="small")

            with col1:
                start_date = st.date_input("Select Start Date:")

            with col2:
                end_date = st.date_input("Select End Date:")

            st.write("")

            submitted = st.form_submit_button("Analyze Logs", on_click=increment)