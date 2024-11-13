import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from neo4j import GraphDatabase
from transformers import T5ForConditionalGeneration, T5Tokenizer
from sentence_transformers import SentenceTransformer, util

# Neo4j database connection function
def connect_to_neo4j(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

def store_papers_in_neo4j(driver, papers):
    with driver.session() as session:
        for paper in papers:
            session.run(
                """
                MERGE (p:Paper {title: $title, summary: $summary, link: $link, year: $year})
                """,
                title=paper["title"],
                summary=paper["summary"],
                link=paper["link"],
                year=paper["year"]
            )

def fetch_arxiv_papers(topic, year):
    base_url = 'http://export.arxiv.org/api/query?search_query=all:'
    url = f"{base_url}{topic}&start=0&max_results=50"  # Adjust max_results if needed
    response = requests.get(url)
    
    if response.status_code != 200:
        return f"Error fetching data from ArXiv API. Status Code: {response.status_code}"

    root = ET.fromstring(response.content)
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        published_year = int(published.split('-')[0])

        if published_year >= year:
            papers.append({
                "title": title, 
                "summary": summary, 
                "link": link, 
                "year": published_year
            })
    
    return papers

# Load the Sentence-BERT model (you can choose different models like 'all-MiniLM-L6-v2' for efficiency)
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

def query_relevant_papers(driver, user_query):
    # Embed the user query
    user_query_embedding = sbert_model.encode(user_query, convert_to_tensor=True)
    
    with driver.session() as session:
        # Retrieve all papers
        result = session.run("MATCH (p:Paper) RETURN p.title AS title, p.summary AS summary")
        
        papers = []
        for record in result:
            title = record["title"]
            summary = record["summary"]
            # Embed each paper's title and summary
            paper_embedding = sbert_model.encode(summary, convert_to_tensor=True)
            
            # Calculate cosine similarity between the user query and paper summary
            similarity_score = util.pytorch_cos_sim(user_query_embedding, paper_embedding).item()
            
            papers.append({"title": title, "summary": summary, "similarity": similarity_score})
    
    # Sort papers by similarity score in descending order
    papers = sorted(papers, key=lambda x: x["similarity"], reverse=True)
    
    # Return the top relevant papers
    return papers[:10]  # Adjust the number to return top N papers as needed

# Initialize Hugging Face text generation model (T5 model for generating research ideas and summaries)
t5_model = T5ForConditionalGeneration.from_pretrained("t5-base")
t5_tokenizer = T5Tokenizer.from_pretrained("t5-base")

def generate_research_ideas(context):
    input_text = (
        f"Generate future research ideas for a review paper based on the given Context\n"
        f"Context: {context}"
    )
    input_ids = t5_tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    output = t5_model.generate(input_ids, max_new_tokens=300, num_beams=5, early_stopping=True)
    return t5_tokenizer.decode(output[0], skip_special_tokens=True)

def generate_review_summary(context):
    # Refined prompt to generate a structured review paper summarizing research opportunities
    input_text = (
        f"Create a structured review paper summarizing the research opportunities in the field of Large Language Models (LLMs). "
        f"Based on the following context, identify key trends, challenges, gaps, and future opportunities for research.\n"
        f"Context: {context}"
    )
    input_ids = t5_tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    output = t5_model.generate(input_ids, max_new_tokens=500, num_beams=5, early_stopping=True)
    return t5_tokenizer.decode(output[0], skip_special_tokens=True)

def generate_improvement_plan(context):
    # Refined prompt to generate an improvement plan based on key research, highlighting novel contributions
    input_text = (
        f"Develop an improvement plan for advancing research in Large Language Models (LLMs). "
        f"Based on the following context, identify areas for improvement, propose novel contributions, and suggest possible research directions.\n"
        f"Context: {context}"
    )
    input_ids = t5_tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    output = t5_model.generate(input_ids, max_new_tokens=500, num_beams=5, early_stopping=True)
    return t5_tokenizer.decode(output[0], skip_special_tokens=True)

def generate_new_research_directions(context):
    # Refined prompt to generate new research directions based on combined insights from multiple papers
    input_text = (
        f"Based on the following context from multiple papers, combine insights to propose new and actionable research directions in the field of Large Language Models (LLMs). "
        f"Consider identifying gaps, emerging trends, and innovative approaches that could drive the field forward.\n"
        f"Context: {context}"
    )
    input_ids = t5_tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    output = t5_model.generate(input_ids, max_new_tokens=500, num_beams=5, early_stopping=True)
    return t5_tokenizer.decode(output[0], skip_special_tokens=True)


def generate_query_answer(context, user_query):
    # Updated prompt to generate detailed answers
    input_text = (
        f"Answer the following query in a detailed manner, utilizing the context from research papers provided below. "
        "Please provide a comprehensive explanation and include examples where applicable.\n"
        f"Query: {user_query}\n"
        f"Context: {context}"
    )
    input_ids = t5_tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    output = t5_model.generate(input_ids, max_length=700, num_beams=5, early_stopping=True)
    return t5_tokenizer.decode(output[0], skip_special_tokens=True)

def main():
    st.title("Academic Research Paper Assistant Application")
    
    # Neo4j connection details
    neo4j_uri = "neo4j+s://08604d40.databases.neo4j.io"
    neo4j_user = "neo4j"
    neo4j_password = "TKs7thScxvjWy62MdpKqNkTQw97-gD5V6ENJt7n4DQo"

    topic = st.text_input("Enter the topic you want to search for:")
    year_input = st.number_input("Enter the starting year (e.g., 2020):", min_value=1900, max_value=datetime.now().year, step=1, value=2020)
    
    if st.button("Fetch and Store Papers"):
        if topic and year_input and neo4j_uri and neo4j_user and neo4j_password:
            with st.spinner("Fetching papers..."):
                papers = fetch_arxiv_papers(topic, year_input)
                
                if isinstance(papers, str):
                    st.error(papers)
                elif not papers:
                    st.info("No papers found for the given topic and year range.")
                else:
                    # Display the fetched papers
                    st.header("Fetched Papers")
                    for paper in papers:
                        st.subheader(paper["title"])
                        st.write(f"**Summary**: {paper['summary']}")
                        st.write(f"**Link**: [View Paper]({paper['link']})")
                        st.write(f"**Published Year**: {paper['year']}")
                        st.write("---")

                    with st.spinner("Connecting to Neo4j and storing data..."):
                        driver = connect_to_neo4j(neo4j_uri, neo4j_user, neo4j_password)
                        try:
                            store_papers_in_neo4j(driver, papers)
                            st.success("Papers successfully stored in the Neo4j database.")
                        except Exception as e:
                            st.error(f"An error occurred while storing data in Neo4j: {e}")
                        finally:
                            driver.close()
        else:
            st.warning("Please enter all required fields.")

    st.header("User Query and Generate Research Ideas")
    user_query = st.text_input("Enter your query:")

    if st.button("Generate Answer and Research Ideas"):
        if user_query:
            with st.spinner("Querying the database and generating answer..."):
                driver = connect_to_neo4j(neo4j_uri, neo4j_user, neo4j_password)
                try:
                    relevant_papers = query_relevant_papers(driver, user_query)
                    if relevant_papers:
                        # Combine summaries of relevant papers as context
                        context = " ".join([paper["summary"] for paper in relevant_papers])
                        
                        # Generate the answer to the user's query
                        query_answer = generate_query_answer(context, user_query)
                        st.write("**Answer to Your Query:**")
                        st.write(query_answer)
                        
                        # Generate detailed research ideas using T5 model
                        research_ideas = generate_research_ideas(context)
                        st.write("**Detailed Research Ideas and Directions:**")
                        st.write(research_ideas)
                        
                        # Generate a structured review paper summarizing research opportunities
                        review_summary = generate_review_summary(context)
                        st.write("**Structured Review Paper Summarizing Research Opportunities:**")
                        st.write(review_summary)
                        
                        # Generate an improvement plan based on key research, including novel contributions
                        improvement_plan = generate_improvement_plan(context)
                        st.write("**Improvement Plan Based on Key Research:**")
                        st.write(improvement_plan)
                        
                        # Combine insights from multiple papers to propose new research directions
                        new_research_directions = generate_new_research_directions(context)
                        st.write("**New Research Directions Based on Combined Insights:**")
                        st.write(new_research_directions)
                    
                    else:
                        st.info("No relevant papers found for the query.")
                except Exception as e:
                    st.error(f"An error occurred while querying data: {e}")
                finally:
                    driver.close()

if __name__ == "__main__":
    main()
