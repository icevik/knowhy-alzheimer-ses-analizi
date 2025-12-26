from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import participants, analyze, results, reports
from app.core.database import engine, Base

app = FastAPI(title="TUBITAK Voice Analyzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(participants.router, prefix="/api/participants", tags=["participants"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✓ Veritabani tablolari basariyla olusturuldu")
    except Exception as e:
        print(f"✗ Veritabani tablolari olusturulurken hata: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.get("/")
async def root():
    return {"message": "TUBITAK Voice Analyzer API"}

