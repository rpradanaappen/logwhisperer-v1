import requests
import streamlit as st
from elasticsearch import Elasticsearch, exceptions
from summarizer import Summarizer
import openai
from datetime import datetime, timedelta
from streamlit_lottie import st_lottie

# ---- OPENAI CONFIG ----
username = ""
password = "123456"
password2 = "testerwelcome123456"
es = Elasticsearch(
    [''],
    http_auth=(username, password),
    port=443,
    use_ssl=True,
    verify_certs=False,
    http_compress=True,
    scheme='https',
)
result_buffer = []

# ---- FUNCTIONS ----
def check_elasticsearch_connection():
    try:
        es.ping()
        st.success("Connected to Elasticsearch! 🔗")
    except exceptions.ConnectionError:
        st.error("Unable to connect to Elasticsearch. Check your connection details.")

def search_elasticsearch(log_group, start_date, end_date):
    error_query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": start_date, "lte": end_date}}},
                    {"term": {"aws.cloudwatch.log_group": {"value": log_group}}},
                    {"regexp": {"message": ".*error.*"}}
                ]
            }
        }
    }

    result = es.search(index='logs-*', body=error_query)

    hits = result['hits']['hits']
    return hits

def process_buffer():
    if result_buffer:
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt='\n\n'.join(result_buffer),
            max_tokens=200,
            temperature=0.5
        )

        if 'choices' in response and response['choices']:
            if 'text' in response['choices'][0]:
                summaries = response['choices'][0]['text'].split('\n\n')
                for summary in summaries:
                    st.text(f"Summarized Message: {summary}")
            else:
                st.error(f'Unexpected OpenAI response format')
        else:
            st.error(f'Unexpected OpenAI response format')

        result_buffer.clear()

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
    openai.api_key = 'sk-BhbewUhwe7273bHGU'
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
        st.write("Log Whisperer will help you to analyze your log files to find errors in the code and give you recommendations on how to solve them")
        st.write("Tired of spending hours for searching root causes of your app errors? Here's some nifty solution to help you 👇")
    with right_column:
        st_lottie(lottie_bug, height=300, key="coding")

# ---- FORM ----
with st.container():
    st.write("---")
    st.header("Let's begin analyzing your log file")
    st.write("##")

    def analyze():
        check_elasticsearch_connection()
        start_date_str = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
        end_date_str = (end_date + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00.000Z")
        hits = search_elasticsearch(log_group, start_date_str, end_date_str)

        for hit in hits:
            generate_summary(hit)

        process_buffer()

    with st.form("analyze_form"):
        col1, col2 = st.columns(2, gap="small")

        with col1:
            elasticsearch_index = st.text_input("Elasticsearch Index")

        with col2:
            log_group = st.text_input("AWS Cloudwatch Log Group")

        col1, col2 = st.columns(2, gap="small")

        with col1:
            start_date = st.date_input("Select Start Date:")

        with col2:
            end_date = st.date_input("Select End Date:")

        st.write("")

        submitted = st.form_submit_button("Analyze Logs", on_click=analyze)
            
    def generate_summary(message):
        try:
            timestamp = message['_source'].get('@timestamp', 'N/A')  # Use get to handle missing key
            original_message = message['_source']['message'].strip()  # Trim whitespace

            # Limit the length of the original message to fit within the model's context
            max_context_length = 4096  # Adjust as needed
            truncated_message = original_message[:max_context_length]

            # Summarize the truncated log message using extractive summarization
            # summarizer = Summarizer()
            # summarized_message = summarizer(truncated_message)

            # Include the summarized message in the prompt for OpenAI
            prompt = (
                f"analyze the following message:\n\n"
                f"Original Message ({timestamp}): {truncated_message}\n\n"
                "Your analysis should include 'Error Identification,' 'Root Cause Analysis,' and 'Resolutions.'"
            )

            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt,
                max_tokens=200,  # Adjust this value as needed
                temperature=0.5
            )

            # Check if the response has the expected structure
            if 'choices' in response and response['choices']:
                # Ensure the 'text' key is present in the first choice
                if 'text' in response['choices'][0]:
                    summary = response['choices'][0]['text']

                    with st.expander("Timestamp: "+timestamp):
                        st.text("Original Message ("+timestamp+"): "+original_message)
                        st.write("")
                        st.text(summary)
                else:
                    print(f'Unexpected OpenAI response format: {message}')
                    print(response)
            else:
                print(f'Unexpected OpenAI response format: {message}')
                print(response)
                
        except Exception as e:
            print(f"Error generating summary from OpenAI: {e}")