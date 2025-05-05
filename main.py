from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict
import pandas as pd
import httpx
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
# from func import s as generate_sequence_func  # temporarily disabled

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the DNA Assignment API!"}

# Enable CORS for frontend interaction if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for uploaded and processed data
ancient_data: Dict[str, Dict] = {}
generated_sequences: Dict[str, str] = {}

class CompareRequest(BaseModel):
    id1: str
    id2: str

class AskRequest(BaseModel):
    question: str

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
        df.dropna(subset=["id", "region", "age", "seed"], inplace=True)
        for _, row in df.iterrows():
            ancient_data[row["id"]] = {
                "region": row["region"],
                "age": int(row["age"]),
                "seed": row["seed"]
            }
        return {
            "message": "CSV uploaded and parsed successfully.",
            "total_records": len(ancient_data)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/generate-sequence/")
async def generate_sequence(id: str):
    print(f"Received ID for generation: {id}")
    if id not in ancient_data:
        raise HTTPException(status_code=404, detail="Sample ID not found.")
    if id in generated_sequences:
        return {"id": id, "sequence": generated_sequences[id]}
    
    try:
        # DEBUG LINE — replace real function with dummy result
        sequence = "ATCGATCGATCGATCG"
        # If it works, the issue is inside func.py
        generated_sequences[id] = sequence
        return {"id": id, "sequence": sequence}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sequence: {str(e)}")

@app.post("/compare-sequences/")
async def compare_sequences(request: CompareRequest):
    id1, id2 = request.id1, request.id2
    if id1 not in ancient_data or id2 not in ancient_data:
        raise HTTPException(status_code=404, detail="One or both sample IDs not found.")

    if id1 not in generated_sequences:
        generated_sequences[id1] = "ATCGATCGATCGATCG"
    if id2 not in generated_sequences:
        generated_sequences[id2] = "ATCGATCGATCGATCG"

    seq1 = generated_sequences[id1]
    seq2 = generated_sequences[id2]

    def get_motifs(sequence: str, k: int = 4):
        return set(sequence[i:i+k] for i in range(0, len(sequence) - k + 1, k))

    motifs1 = get_motifs(seq1)
    motifs2 = get_motifs(seq2)

    intersection = len(motifs1 & motifs2)
    union = len(motifs1 | motifs2)
    similarity = intersection / union if union > 0 else 0.0

    return {
        "id1": id1,
        "id2": id2,
        "similarity_score": round(similarity, 4)
    }

@app.post("/ask-me-anything/")
async def ask_me_anything(req: AskRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not set.")
    
    headers = {
        "Content-Type": "application/json",
        
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": req.question}]
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent",
                headers=headers,
                params={"key": GEMINI_API_KEY},
                json=payload
            )
        response.raise_for_status()
        data = response.json()

        # Safely check for Gemini reply
        if "candidates" in data and data["candidates"]:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"response": reply}
        else:
            raise HTTPException(status_code=500, detail="No response from Gemini.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=response.status_code, detail=f"Gemini API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")


# Optional: run with `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
