# 👂 SQLWhisper: Context-Aware Text-to-SQL Engine

## 🚦 Status & License
| Status | License | Deployment |
|--------|---------|------------|
| Active | MIT     | Hugging Face |

---

## 🎯 Overview

**The Problem**  
Many users need to query databases quickly using natural language, but not everyone knows SQL. Writing complex queries manually is slow and error-prone, limiting efficient data exploration and decision-making.

**The Solution**  
SQLWhisper is a context-aware Text-to-SQL engine that converts natural language queries into accurate SQL statements. It provides a **confidence score** for each generated query and includes a **feedback loop** for continuous improvement.

---

## 🏗️ Architecture

SQLWhisper consists of four main components designed for accuracy, scalability, and learning:

1. **Data Curation**  
   Generates and structures (NL, SQL) pairs using generic example databases for testing and evaluation.

2. **RAG System (Schema Retrieval)**  
   Retrieves the most relevant database schema snippets (tables, columns) to augment the model input, improving SQL accuracy and reducing hallucinations.

3. **Query Generation & Confidence Scoring**  
   Converts natural language queries into SQL and assigns a confidence score to indicate reliability.

4. **Feedback & Learning Loop**  
   Logs inaccurate or low-confidence queries for review, generating new examples for continuous improvement.

---

## ✨ Key Features

- **Text-to-SQL Generation**: Converts natural language queries into executable SQL.  
- **Schema-Retrieval Augmented Generation (RAG)**: Dynamically injects relevant database schema into prompts for more accurate queries.  
- **Confidence Scoring**: Each SQL output includes a reliability score.  
- **Feedback Loop**: Low-confidence or failed queries are logged for model refinement.  
- **Privacy & Safety**: Queries can be executed in a sandboxed, read-only environment to prevent accidental data changes.

---

## 🧑‍💻 Use Cases

- Query large databases without SQL expertise.  
- Validate and refine queries using confidence scores.  
- Continuous model improvement via feedback loop.  
- Adaptable to any organizational or analytical database scenario.

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
