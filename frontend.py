# frontend.py
import streamlit as st
import requests

# FastAPI backend URL (adjust to match the actual URL of the FastAPI server)
API_URL = "http://127.0.0.1:8000"

# Streamlit interface
def fetch_and_store_papers():
    topic = st.text_input("Enter the topic you want to search for:")
    year_input = st.number_input("Enter the starting year (e.g., 2020):", min_value=1900, max_value=2024, step=1, value=2020)
    
    if st.button("Fetch Papers"):
        if topic and year_input:
            response = requests.post(f"{API_URL}/fetch_papers/", json={"topic": topic, "year": year_input})
            if response.status_code == 200:
                papers = response.json().get("papers", [])
                st.write(papers)
            else:
                st.error(f"Failed to fetch papers: {response.json().get('detail', 'Unknown error')}")
        else:
            st.warning("Please enter all required fields.")

def query_and_generate_ideas():
    user_query = st.text_input("Enter your query:")
    neo4j_uri = "neo4j+s://08604d40.databases.neo4j.io"
    neo4j_user = "neo4j"
    neo4j_password = "TKs7thScxvjWy62MdpKqNkTQw97-gD5V6ENJt7n4DQo"
    
    if st.button("Generate Answer and Research Ideas"):
        if user_query and neo4j_uri and neo4j_user and neo4j_password:
            response = requests.post(f"{API_URL}/query_papers/", json={
                "user_query": user_query,
                "neo4j_uri": neo4j_uri,
                "neo4j_user": neo4j_user,
                "neo4j_password": neo4j_password
            })
            if response.status_code == 200:
                data = response.json()
                st.write("**Relevant Papers:**")
                st.write(data["relevant_papers"])
                st.write("**Research Ideas:**")
                st.write(data["research_ideas"])
            else:
                st.error(f"Failed to generate answer: {response.json().get('detail', 'Unknown error')}")
        else:
            st.warning("Please enter all required fields.")

# Main interface
st.title("Academic Research Paper Assistant Application")
fetch_and_store_papers()
query_and_generate_ideas()
