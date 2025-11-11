# 👂 SQLWhisper: Context-Aware Text-to-SQL Engine

---

## 🚦 Status & License
| Status | License | Deployment |
|--------|---------|------------|
| 🟢 Active | MIT     | Hugging Face |

---

## 🎯 Overview

### 🔹 The Problem  
Many users need to query databases quickly using natural language, but not everyone knows SQL. Writing complex queries manually is slow and prone to errors, limiting efficient data exploration and decision-making.

### 🔹 The Solution  
**SQLWhisper** is a context-aware Text-to-SQL engine that converts natural language queries into accurate SQL statements. It provides:  
- **Confidence scoring** for each query  
- A **feedback loop** to continuously improve model performance  

---

## 🏗️ Architecture

SQLWhisper is built with four main components designed for **accuracy, scalability, and learning**:

1. **🗂️ Data Curation**  
   Generates and organizes (NL, SQL) pairs using example databases for testing and evaluation.

2. **🔍 RAG System (Schema Retrieval)**  
   Retrieves relevant database schema snippets (tables, columns) to enhance context, improving SQL accuracy.

3. **📝 Query Generation & Confidence Scoring**  
   Converts natural language queries into SQL and assigns a confidence score to indicate reliability.

4. **♻️ Feedback & Learning Loop**  
   Logs low-confidence or incorrect queries to create new examples, continuously refining the model.

---

## ✨ Key Features

- **💬 Text-to-SQL Generation** – Converts natural language queries into executable SQL  
- **📚 Schema-Retrieval Augmented Generation (RAG)** – Dynamically adds relevant schema to prompts for accuracy  
- **📊 Confidence Scoring** – Reliability score included with each query  
- **🔄 Feedback Loop** – Logs and improves low-confidence outputs over time  

---

## 🧑‍💻 Use Cases

- Query databases without SQL knowledge  
- Evaluate query reliability via confidence scores  
- Continuously improve model accuracy with feedback  
- Adaptable to any analytical or organizational database environment  

---

## ⚙️ Setup and Run

### 🛠️ Prerequisites
- Python 3.9+  
- pip package installer  
- Access to the database schema (for RAG)  
- Access to a sandbox database (for testing)

### 🚀 Environment Setup
```bash
# Clone the repository
git clone [repository_link]
cd SQLWhisper

# Install dependencies
pip install -r requirements.txt
