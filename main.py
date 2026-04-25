import os
import sys
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import dashscope
from models import AnalyzeRequest, AnalyzeResponse, SaveRequest, RecordResponse, HistoryResponse
from database import save_record, get_records, get_record_by_id

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI英语表达训练工具", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")

ANALYZE_PROMPT = """你是一个英语表达教练。

用户输入一句英语，请你完成：
1. 给出评分（0-10），考虑场景适配性
2. 指出问题（最多3条）
3. 给出优化建议
4. 给出一个更好的表达版本

输出JSON格式，不要任何其他内容：
{{"score": 8.5, "issues": ["问题1", "问题2"], "suggestions": ["建议1", "建议2"], "improved": "优化后的句子"}}

场景：{scenario}
用户输入：{text}

只输出JSON，不要解释。"""

@app.get("/")
async def root():
    return {"message": "AI英语表达训练工具 API", "version": "1.0.0"}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="输入不能为空")

    if request.scenario not in ["ielts", "interview", "daily"]:
        raise HTTPException(status_code=400, detail="无效的场景类型")

    try:
        prompt = ANALYZE_PROMPT.format(scenario=request.scenario, text=request.text)

        response = dashscope.Generation.call(
            model='qwen-plus',
            prompt=prompt,
            temperature=0.7,
            max_tokens=500
        )

        logger.debug(f"DEBUG: status_code = {response.status_code}")

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"API调用失败: {response.message}")

        output_text = response.output.text if hasattr(response.output, 'text') else str(response.output)
        logger.debug(f"DEBUG: output_text = {output_text}")

        try:
            result = json.loads(output_text)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"无法解析AI返回: {output_text[:200]}")

        logger.debug(f"DEBUG: result = {result}")

        if "score" not in result:
            raise HTTPException(status_code=500, detail=f"缺少score字段: {str(result)[:200]}")

        record_id = save_record(
            text=request.text,
            scenario=request.scenario,
            score=float(result["score"]),
            issues=result.get("issues", []),
            suggestions=result.get("suggestions", []),
            improved=result.get("improved", request.text)
        )

        return AnalyzeResponse(
            score=float(result["score"]),
            issues=result.get("issues", []),
            suggestions=result.get("suggestions", []),
            improved=result.get("improved", request.text),
            record_id=record_id
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.get("/history", response_model=HistoryResponse)
async def get_history(limit: int = 50):
    records = get_records(limit)
    return HistoryResponse(records=[RecordResponse(**r) for r in records])

@app.get("/record/{record_id}", response_model=RecordResponse)
async def get_record(record_id: int):
    record = get_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return RecordResponse(**record)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
