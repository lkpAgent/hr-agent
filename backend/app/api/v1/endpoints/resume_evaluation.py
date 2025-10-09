"""
简历评价相关的API接口
"""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import User as UserSchema
from app.schemas.resume_evaluation import (
    ResumeEvaluationResponse,
    ResumeEvaluationListResponse,
    ResumeUploadRequest,
    ResumeEvaluationResult
)
from app.services.resume_evaluation_service import ResumeEvaluationService

router = APIRouter()


@router.post("/evaluate", response_model=ResumeEvaluationResult)
async def evaluate_resume(
    file: UploadFile = File(...),
    jd_id: str = Form(...),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    上传简历并进行AI评价
    """
    try:
        service = ResumeEvaluationService(db)
        result = await service.evaluate_resume(
            file=file,
            jd_id=jd_id,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"简历评价失败: {str(e)}"
        )


@router.get("/history", response_model=ResumeEvaluationListResponse)
async def get_evaluation_history(
    skip: int = 0,
    limit: int = 20,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取用户的简历评价历史记录
    """
    try:
        service = ResumeEvaluationService(db)
        evaluations = await service.get_user_evaluations(
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        return ResumeEvaluationListResponse(
            evaluations=evaluations,
            total=len(evaluations),
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价历史失败: {str(e)}"
        )


@router.get("/{evaluation_id}", response_model=ResumeEvaluationResponse)
async def get_evaluation_detail(
    evaluation_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取特定评价结果的详细信息
    """
    try:
        service = ResumeEvaluationService(db)
        evaluation = await service.get_evaluation_detail(
            evaluation_id=evaluation_id,
            user_id=current_user.id
        )
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评价记录不存在"
            )
        
        return evaluation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价详情失败: {str(e)}"
        )


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    删除评价记录
    """
    try:
        service = ResumeEvaluationService(db)
        success = await service.delete_evaluation(
            evaluation_id=evaluation_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评价记录不存在"
            )
        
        return {"message": "评价记录删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除评价记录失败: {str(e)}"
        )


@router.get("/supported-formats")
async def get_supported_formats() -> Any:
    """
    获取支持的文件格式
    """
    return {
        "supported_formats": [
            {
                "extension": ".pdf",
                "description": "PDF文档",
                "max_size_mb": 10
            },
            {
                "extension": ".txt",
                "description": "纯文本文件",
                "max_size_mb": 5
            },
            {
                "extension": ".doc",
                "description": "Word文档(旧版)",
                "max_size_mb": 10
            },
            {
                "extension": ".docx",
                "description": "Word文档",
                "max_size_mb": 10
            }
        ],
        "max_file_size_mb": 10,
        "allowed_mime_types": [
            "application/pdf",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
    }