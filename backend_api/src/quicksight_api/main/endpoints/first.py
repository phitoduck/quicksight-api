from fastapi import APIRouter

router = APIRouter()

@router.get("/hello")
def get_hello():
    return {"message": "Hello"}