# Academic Research Paper Assistant

This project is an Academic Research Paper Assistant application built with FastAPI (for the backend) and Streamlit (for the frontend). It allows users to search for academic papers on ArXiv by topic and year and to query a Neo4j database for similar papers. The application also generates research ideas based on the content of the retrieved papers.

## Features

1. **Fetch Papers from ArXiv**: Retrieve academic papers by topic and year from the ArXiv API.
2. **Query Papers in Neo4j**: Find relevant papers stored in a Neo4j database using a Sentence-BERT model to compute semantic similarity.
3. **Generate Research Ideas**: Using the T5 model from Hugging Face, generate future research ideas based on the content of similar papers.

## Setup

### Prerequisites

- Python 3.8+
- [Neo4j Database](https://neo4j.com/download/) with credentials
- [ArXiv API Access](https://arxiv.org/help/api)
- [Hugging Face Transformers](https://huggingface.co/transformers/) and [Sentence-BERT](https://www.sbert.net/) models

### Install Dependencies

```bash
pip install fastapi uvicorn streamlit requests neo4j transformers sentence-transformers beautifulsoup4

### Environment Variables
Set the following environment variables in a .env file or directly in your environment:

NEO4J_URI: URI for your Neo4j instance
NEO4J_USERNAME: Username for Neo4j
NEO4J_PASSWORD: Password for Neo4j

Usage
Running the Backend (FastAPI)
Start the FastAPI backend:

bash
Copy code
uvicorn backend:app --reload
This will serve the API on http://127.0.0.1:8000.

Endpoints:

Fetch Papers from ArXiv: POST /fetch_papers/
Request Body:
json
Copy code
{
  "topic": "machine learning",
  "year": 2020
}
Query Neo4j and Generate Ideas: POST /query_papers/
Request Body:
json
Copy code
{
  "user_query": "neural networks",
  "neo4j_uri": "your_neo4j_uri",
  "neo4j_user": "your_neo4j_username",
  "neo4j_password": "your_neo4j_password"
}
Running the Frontend (Streamlit)
Start the Streamlit app:

bash
Copy code
streamlit run frontend.py
Open your browser to the Streamlit interface (usually http://localhost:8501), where you can:

Enter a topic and year to fetch papers from ArXiv.
Query the Neo4j database and generate future research ideas.
Project Structure
backend.py: FastAPI server that handles requests for fetching papers from ArXiv, querying Neo4j, and generating research ideas.
frontend.py: Streamlit application that serves as the user interface for input and output.
Notes
Ensure that Neo4j is properly set up and accessible.
The ArXiv API has rate limits; adjust your query parameters if necessary.
T5 and Sentence-BERT models may require significant memory. Ensure your environment has sufficient resources.
Contributing
Feel free to submit issues and pull requests.

License
This project is licensed under the MIT License.

less
Copy code

This `README.md` file provides a comprehensive overview of the project, including setup, usage, and struc
