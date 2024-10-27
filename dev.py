from fastapi.middleware.cors import CORSMiddleware

from doveseed.app import app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
)
