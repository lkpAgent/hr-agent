"""
Intent routing endpoint: classify user query and return frontend route
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import User as UserSchema
from app.services.llm_service import LLMService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.enhanced_document_service import EnhancedDocumentService
from app.services.kb_selection_service import KBSelectionService

router = APIRouter()

# Intent to route mapping
INTENT_ROUTES = {
    "jd": "/recruitment/jd-generator",
    "interview_plan": "/recruitment/smart-interview",
    "exam_generate": "/training/exam-generator",
    "kb_qa": "/assistant/qa",
}

# Keyword heuristics for fast intent detection
KEYWORDS = [
    ("jd", ["写jd", "生成jd", "职位描述", "岗位职责", "招聘jd", "job description", "JD"]),
    ("interview_plan", ["面试方案", "面试流程", "面试题", "面试计划", "生成面试", "安排面试"]),
    ("exam_generate", ["试卷", "生成试卷", "考试", "题库", "出题", "考试试卷", "自动阅卷"]),
    ("kb_qa", ["知识库", "问答", "根据知识库", "查文档", "文档问答", "FAQ", "QA"]),
]

async def classify_intent_with_llm(query: str) -> str:
    """Fallback to LLM to classify intent among predefined categories."""
    llm = LLMService()
    # Constrained classification prompt to return one of the labels
    prompt = (
        "你是HR系统的路由分类器。根据用户输入在以下意图中选择一个，并只返回对应标签：\n"
        "- jd: 生成/撰写职位JD\n"
        "- interview_plan: 生成面试方案/流程/题目\n"
        "- exam_generate: 生成考试试卷/出题/考试管理\n"
        "- kb_qa: 基于知识库的问答/查询文档\n\n"
        f"用户输入：{query}\n\n"
        "输出：仅返回上述四个标签之一，不要解释。"
    )
    try:
        result = await llm.generate_response(prompt)
        intent = result.strip().lower()
        # sanitize to known intents
        if intent not in INTENT_ROUTES:
            # try simple normalization
            if "jd" in intent:
                return "jd"
            if "interview" in intent or "面试" in intent:
                return "interview_plan"
            if "exam" in intent or "考试" in intent or "试卷" in intent:
                return "exam_generate"
            if "kb" in intent or "知识" in intent or "问答" in intent:
                return "kb_qa"
            # default
            return "kb_qa"
        return intent
    except Exception:
        # On failure, default to knowledge QA
        return "kb_qa"

def classify_intent_fast(query: str) -> str:
    q = query.lower()
    for intent, words in KEYWORDS:
        for w in words:
            if w.lower() in q:
                return intent
    return ""  # not matched

@router.post("/route")
async def route_by_intent(
    payload: Dict[str, Any],
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Classify user query and return frontend route and intent.
    Body: { "query": "用户输入内容" }
    """
    query = (payload or {}).get("query", "").strip()
    if not query:
        return {"intent": "kb_qa", "route": INTENT_ROUTES["kb_qa"], "query": query}

    # try fast keywords first
    intent = classify_intent_fast(query)
    if not intent:
        intent = await classify_intent_with_llm(query)

    route = INTENT_ROUTES.get(intent, INTENT_ROUTES["kb_qa"])

    # If knowledge base Q&A, use KBSelectionService to auto-select KB
    kb_id = None
    if intent == "kb_qa":
        try:
            selector = KBSelectionService(db)
            result = await selector.select_kb_for_question(
                question=query,
                user_id=current_user.id,
                max_candidates=200,
            )
            kb_id = result["knowledge_base_id"]
        except Exception:
            kb_id = None

    return {"intent": intent, "route": route, "query": query, "kb_id": kb_id}