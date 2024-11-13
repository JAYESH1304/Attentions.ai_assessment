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
