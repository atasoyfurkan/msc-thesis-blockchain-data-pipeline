from fastapi import FastAPI
from data_access.api.endpoints import router
import os

app = FastAPI()
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Data Pipeline API!"}