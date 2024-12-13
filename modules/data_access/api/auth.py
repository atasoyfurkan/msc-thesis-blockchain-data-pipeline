from fastapi import Request, HTTPException
import requests
import os

JUPYTERHUB_API_URL = os.getenv("JUPYTERHUB_API_URL")

def authenticate_user(request: Request):
    """
    Validates the token by sending a request to JupyterHub API.
    """
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token missing")

    headers = {"Authorization": token}
    try:
        response = requests.get(f"{JUPYTERHUB_API_URL}/hub/api/user", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with JupyterHub API: {e}")
