from fastapi import FastAPI

from app.api.orders import router as orders_router

app = FastAPI(
    title="AI Order Processing Agent",
    version="0.1.0",
    description="B2B order processing with deterministic validation and human-in-the-loop review.",
)

app.include_router(orders_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
