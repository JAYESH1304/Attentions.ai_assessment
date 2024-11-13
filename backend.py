from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from neo4j import GraphDatabase
import requests
import os
import xml.etree.ElementTree as ET
from transformers import T5ForConditionalGeneration, T5Tokenizer
from sentence_transformers import SentenceTransformer, util
from bs4 import BeautifulSoup

# Load environment variables for Neo4j credentials
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://08604d40.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "TKs7thScxvjWy62MdpKqNkTQw97-gD5V6ENJt7n4DQo")

app = FastAPI()

# Define the request body model for query papers
class QueryPapersRequest(BaseModel):
    user_query: str
    neo4j_uri: str = NEO4J_URI
    neo4j_user: str = NEO4J_USERNAME
    neo4j_password: str = NEO4J_PASSWORD

# Neo4j database connection function
def connect_to_neo4j(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

# Fetch the full content of the paper from ArXiv
def fetch_full_paper_content(link):
    try:
        response = requests.get(link)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Error fetching paper content. Status Code: {response.status_code}")
        
        # Use BeautifulSoup to extract the content from the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Assuming the full text is in a section with class 'abstract' (This may need to be customized based on ArXiv's HTML structure)
        content = soup.find('blockquote', {'class': 'abstract'})
        if content:
            return content.get_text().strip()
        else:
            return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the paper content: {str(e)}")

# Fetch ArXiv papers based on topic and year
def fetch_arxiv_papers(topic, year):
    base_url = 'http://export.arxiv.org/api/query?search_query=all:'
    url = f"{base_url}{topic}&start=0&max_results=50"  # Adjust max_results if needed
    response = requests.get(url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Error fetching data from ArXiv API. Status Code: {response.status_code}")

    root = ET.fromstring(response.content)
    papers = []
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        link = entry.find('{http://www.w3.org/2005/Atom}id').text
        published = entry.find('{http://www.w3.org/2005/Atom}published').text
        published_year = int(published.split('-')[0])

        if published_year >= year:
            # Fetch the main content of the paper
            paper_content = fetch_full_paper_content(link)
            papers.append({
                "title": title, 
                "content": paper_content,  # Store the full content instead of the summary
                "link": link, 
                "year": published_year
            })
    
    return papers

# Sentence-BERT model for query embedding
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

# Query relevant papers from Neo4j and calculate similarity
def query_relevant_papers(driver, user_query):
    user_query_embedding = sbert_model.encode(user_query, convert_to_tensor=True)
    
    with driver.session() as session:
        result = session.run("MATCH (p:Paper) RETURN p.title AS title, p.content AS content")
        
        papers = []
        for record in result:
            title = record["title"]
            content = record["content"]
            paper_embedding = sbert_model.encode(content, convert_to_tensor=True)
            similarity_score = util.pytorch_cos_sim(user_query_embedding, paper_embedding).item()
            papers.append({"title": title, "content": content, "similarity": similarity_score})
    
    papers = sorted(papers, key=lambda x: x["similarity"], reverse=True)
    return papers[:10]  # Return top 10 papers

# Initialize Hugging Face model (T5 for text generation)
t5_model = T5ForConditionalGeneration.from_pretrained("t5-base")
t5_tokenizer = T5Tokenizer.from_pretrained("t5-base")

# Generate research ideas based on context
def generate_research_ideas(context):
    input_text = f"Generate future research ideas for a review paper based on the given Context\nContext: {context}"
    input_ids = t5_tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    output = t5_model.generate(input_ids, max_new_tokens=300, num_beams=5, early_stopping=True)
    return t5_tokenizer.decode(output[0], skip_special_tokens=True)

# FastAPI endpoints
class PaperRequest(BaseModel):
    topic: str
    year: int

@app.post("/fetch_papers/")  # Fetch papers from ArXiv based on topic and year
async def fetch_papers(request: PaperRequest):
    papers = fetch_arxiv_papers(request.topic, request.year)
    return {"papers": papers}

@app.post("/query_papers/")  # Query papers from Neo4j and generate research ideas
async def query_papers(request: QueryPapersRequest):
    # Extract Neo4j credentials from request body
    user_query = request.user_query
    neo4j_uri = request.neo4j_uri
    neo4j_user = request.neo4j_user
    neo4j_password = request.neo4j_password
    
    # Connect to Neo4j with provided credentials
    driver = connect_to_neo4j(neo4j_uri, neo4j_user, neo4j_password)
    
    # Fetch relevant papers based on user query
    papers = query_relevant_papers(driver, user_query)
    
    # Generate a context from the top 10 papers' content
    context = " ".join([paper["content"] for paper in papers if paper["content"]])  # Use paper content instead of summary
    
    # Generate future research ideas based on the context
    research_ideas = generate_research_ideas(context)
    
    return {"relevant_papers": papers, "research_ideas": research_ideas}
