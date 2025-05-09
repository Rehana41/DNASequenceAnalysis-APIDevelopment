from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict
import pandas as pd
import httpx
import os
import random
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the DNA Assignment API!"}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
ancient_data: Dict[str, Dict] = {}
generated_sequences: Dict[str, str] = {}

class CompareRequest(BaseModel):
    id1: str
    id2: str

class AskRequest(BaseModel):
    question: str

# 🔬 Function to generate reproducible DNA sequence from seed
def generate_dna_sequence(seed: str, length: int = 64) -> str:
    random.seed(seed)
    return ''.join(random.choices("ATCG", k=length))

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
        seed = ancient_data[id]["seed"]
        sequence = generate_dna_sequence(seed)
        generated_sequences[id] = sequence
        return {"id": id, "sequence": sequence}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sequence: {str(e)}")

@app.post("/compare-sequences/")
async def compare_sequences(request: CompareRequest):
    id1, id2 = request.id1, request.id2
    if id1 not in ancient_data or id2 not in ancient_data:
        raise HTTPException(status_code=404, detail="One or both sample IDs not found.")

    # Generate sequences if not already done
    if id1 not in generated_sequences:
        generated_sequences[id1] = generate_dna_sequence(ancient_data[id1]["seed"])
    if id2 not in generated_sequences:
        generated_sequences[id2] = generate_dna_sequence(ancient_data[id2]["seed"])

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
        "Authorization": f"Bearer {GEMINI_API_KEY}"
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
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent",
                headers=headers,
                params={"key": GEMINI_API_KEY},
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        print("Gemini API full response:", data)

        if "candidates" in data and data["candidates"]:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"response": reply}
        else:
            raise HTTPException(status_code=500, detail="No response from Gemini.")

    except httpx.HTTPStatusError as e:
        print("HTTPStatusError response text:", e.response.text)
        raise HTTPException(status_code=response.status_code, detail=f"Gemini API error: {e.response.text}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("Unexpected error:", str(e), "\nTraceback:", tb)
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
