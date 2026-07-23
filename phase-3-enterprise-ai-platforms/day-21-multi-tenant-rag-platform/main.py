import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents import run_rag_query, list_tenants

app = FastAPI(
    title="Day 21 - Multi-Tenant RAG Enterprise Platform",
    description="Isolated per-tenant RAG assistants by Maryam Mumtaz",
    version="1.0.0"
)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


class QueryRequest(BaseModel):
    tenant_id: str
    question: str


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Day 21 Multi-Tenant RAG Platform Running</h1>")


@app.get("/api/tenants")
async def get_tenants():
    return JSONResponse(content={"status": "success", "data": list_tenants()})


@app.post("/api/query")
async def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="A question is required.")
    if not req.tenant_id.strip():
        raise HTTPException(status_code=400, detail="A tenant must be selected.")

    try:
        results = await run_rag_query(
            tenant_id=req.tenant_id.strip(),
            question=req.question.strip(),
        )
        return JSONResponse(content={"status": "success", "data": results})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8021, reload=True)
