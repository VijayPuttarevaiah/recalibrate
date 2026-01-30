from fastapi import APIRouter

router = APIRouter()

@router.post("/verify")
def verify_email():
    pass