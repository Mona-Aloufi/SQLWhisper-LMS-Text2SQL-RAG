# 👂 SQLWhisper: Context-Aware Text-to-SQL Engine

## 🚦 Status & License
| Status | License | Deployment |
|--------|---------|------------|
| Active | MIT     | Hugging Face |

---

## 🎯 Overview

**The Problem**  
Many users need to query databases quickly using natural language, but not everyone knows SQL. Writing complex queries manually is slow and prone to errors, limiting efficient data exploration and decision-making.

**The Solution**  
SQLWhisper is a context-aware Text-to-SQL engine that converts natural language queries into accurate SQL statements. It provides a **confidence score** for each query and incorporates a **feedback loop** to continuously improve performance.

---

## 🏗️ Architecture

SQLWhisper consists of four main components, designed for accuracy, scalability, and continuous learning:

1. **Data Curation**  
   Generates and organizes (NL, SQL) pairs using generic example databases for testing and evaluation.

2. **RAG System (Schema Retrieval)**  
   Retrieves the most relevant database schema snippets (tables, columns) to enhance the model’s context, improving SQL accuracy and reducing errors.

3. **Query Generation & Confidence Scoring**  
   Transforms natural language queries into SQL and assigns a confidence score to indicate reliability.

4. **Feedback & Learning Loop**  
   Logs low-confidence or inaccurate queries for review, creating new examples to continuously refine the model.

---

## ✨ Key Features

- **Text-to-SQL Generation**: Converts natural language queries into executable SQL.  
- **Schema-Retrieval Augmented Generation (RAG)**: Dynamically adds relevant database schema to prompts for more accurate queries.  
- **Confidence Scoring**: Each generated SQL query includes a reliability score.  
- **Feedback Loop**: Low-confidence or failed queries are logged for continuous improvement.  

---

## 🧑‍💻 Use Cases

- Query large databases without SQL expertise.  
- Assess query reliability using confidence scores.  
- Continuously refine model performance through feedback loops.  
- Flexible for any analytical or organizational database scenario.

---

## ⚙️ Setup and Run

**Prerequisites**  
- Python 3.9+  
- pip package installer  
- Access to the database schema (for RAG)  
- Access to a sandbox database (for testing)

**Environment Setup**  
```bash
# Clone the repository
git clone [repository_link]
cd SQLWhisper

# Install required packages
pip install -r requirements.txt
