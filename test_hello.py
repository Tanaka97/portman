from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Portfolio Manager API is working!", "status": "success"}

@app.get("/health")
def health():
    return {"healthy": True}