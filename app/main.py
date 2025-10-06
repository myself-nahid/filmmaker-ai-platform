from fastapi import FastAPI
from app.api import endpoints
from app.database import engine
from app.models import models
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Filmmaker AI Platform API",
    description="APIs for video generation, image creation, and script analysis for filmmakers.",
    version="1.0.0",
)

origins = [
    "http://localhost",       
    "http://localhost:3000",  
    "http://localhost:8002",
    "http://localhost:8080",  
    "http://localhost:4200",  

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Filmmaker AI Platform API"}