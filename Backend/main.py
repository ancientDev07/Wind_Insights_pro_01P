from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.upload import router as upload_router
from api.project import router as project_router
from config.config import settings
from core.database import engine

from models.company import Company
from models.project import Project
from models.dataset import Dataset
from models.asset import Asset
from models.base import Base

Base.metadata.create_all(bind=engine)
print(Base.metadata.tables.keys())


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(
    upload_router,
    prefix=settings.API_V1_PREFIX,
    tags=["Upload"]
)
app.include_router(
    project_router,
    prefix=settings.API_V1_PREFIX,
    tags=["Projects"]
)

@app.get("/")
async def health_check():

    return {
        "status": "healthy",
        "application": settings.APP_NAME
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=settings.PORT)