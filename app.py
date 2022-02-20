from fastapi.middleware.cors import CORSMiddleware
from v3data.app import app

# Allow CORS
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
