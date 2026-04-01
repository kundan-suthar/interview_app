from fastapi import APIRouter, Response

router = APIRouter()

@router.post("/logout")
async def logout(response: Response):
    print("🔥 custom logout called")

    response.delete_cookie(
        key="refresh_token",
        path="/",
    )

    return {"message": "Logged out successfully"}