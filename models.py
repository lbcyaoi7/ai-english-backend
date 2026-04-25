from pydantic import BaseModel, Field
from typing import List, Optional

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="用户输入的英文句子")
    scenario: str = Field(..., description="场景：ielts, interview, daily")

class AnalyzeResponse(BaseModel):
    score: float = Field(..., ge=0, le=10, description="评分 0-10")
    issues: List[str] = Field(..., description="问题列表")
    suggestions: List[str] = Field(..., description="优化建议")
    improved: str = Field(..., description="优化后的句子")
    record_id: Optional[int] = Field(None, description="记录ID，可用于保存")

class SaveRequest(BaseModel):
    text: str
    scenario: str
    score: float
    issues: List[str]
    suggestions: List[str]
    improved: str

class RecordResponse(BaseModel):
    id: int
    text: str
    scenario: str
    score: float
    issues: str
    suggestions: str
    improved: str
    created_at: str

class HistoryResponse(BaseModel):
    records: List[RecordResponse]