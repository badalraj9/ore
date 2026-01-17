from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import init_db
from routers import query, ingest, extract, process, search, analyze

# Initialize DB
init_db()

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(query.router, prefix="/api/v1/query", tags=["query"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["ingest"])
app.include_router(extract.router, prefix="/api/v1/extract", tags=["extract"])
app.include_router(process.router, prefix="/api/v1/process", tags=["process"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["analyze"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to ORE: Open Research Engine"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
