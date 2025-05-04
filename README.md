# DNASequenceAnalysis-APIDevelopment
# 🧬 DNA Sequence Analysis & API Development

This project provides a FastAPI-based backend to analyze ancient DNA samples using generated sequences and compares their similarities. It also includes an "Ask Me Anything" feature powered by Gemini AI.

## 🚀 Features

- Upload CSV files with ancient DNA sample data.
- Generate DNA sequences from sample attributes.
- Compare generated sequences for similarity using motif-based scoring.
- Ask domain-related questions using Google's Gemini Pro API.
- Cleanly structured and easily extendable FastAPI app.
- Swagger UI interface at `/docs`.

### Install all dependencies:
```bash
pip install -r requirements.txt
```

### ▶️ Running the App
Start the FastAPI server using:

```bash
uvicorn main:app --reload
```

The server will run at:
http://127.0.0.1:8000.
Visit http://127.0.0.1:8000/docs to explore and test the API.

### 📤 API Endpoints

**1. POST /upload-csv/**
 Upload a .csv file with the columns: id, region, age, seed.

Response:
```bash
{
  "message": "Data uploaded and parsed successfully.",
  "total_records": 878
}
```
**2. GET /generate-sequence/?id=id_0001**
  Generates a DNA sequence for a sample based on its region, age, and seed.

**3. POST /compare-sequences/**
  Compare two sample sequences for similarity.

Body Example:
```bash
{
  "id1": "id_0001",
  "id2": "id_0002"
}
```

- **4. POST /ask-me-anything/**
  Ask a general question using Gemini Pro.

```bash
{
  "question": "What are motifs in DNA?"
}
```

