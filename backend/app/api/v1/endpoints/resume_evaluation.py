"""
Resume Evaluation API endpoints
"""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.resume_evaluation_service import ResumeEvaluationService
from app.schemas.resume_evaluation import (
    ResumeEvaluationResponse,
    ResumeEvaluationListResponse,
    ResumeEvaluationResult
)
from app.models.resume_evaluation import ResumeStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/evaluate", response_model=ResumeEvaluationResult)
async def evaluate_resume(
    file: UploadFile = File(..., description="简历文件 (支持PDF、TXT、DOC、DOCX)"),
    job_description_id: str = Form(..., description="职位描述ID"),
    conversation_id: Optional[str] = Form(None, description="对话ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传简历并进行AI评价
    
    - **file**: 简历文件，支持PDF、TXT、DOC、DOCX格式
    - **job_description_id**: 职位描述ID
    - **conversation_id**: 可选的对话ID
    """
    try:
        # 验证job_description_id格式
        try:
            jd_uuid = UUID(job_description_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的职位描述ID格式")
        
        # 验证conversation_id格式（如果提供）
        conv_uuid = None
        if conversation_id:
            try:
                conv_uuid = UUID(conversation_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的对话ID格式")
        
        # 读取文件内容
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        # 创建评价服务
        evaluation_service = ResumeEvaluationService(db)
        
        # 执行简历评价
        result = await evaluation_service.evaluate_resume(
            user_id=current_user.id,
            file_content=file_content,
            filename=file.filename,
            job_description_id=jd_uuid,
            conversation_id=conv_uuid
        )
        
        return ResumeEvaluationResult(**result)
        
    except ValueError as e:
        logger.warning(f"简历评价参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"简历评价失败: {e}")
        raise HTTPException(status_code=500, detail="简历评价服务暂时不可用")


@router.get("/history", response_model=ResumeEvaluationListResponse)
async def get_evaluation_history(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户的简历评价历史
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数限制
    - **status**: 状态过滤 (pending, rejected, interview)
    """
    try:
        if limit > 100:
            limit = 100
        
        # 验证状态参数
        status_filter = None
        if status:
            try:
                status_filter = ResumeStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的状态值，支持的状态: pending, rejected, interview")
        
        evaluation_service = ResumeEvaluationService(db)
        evaluations = await evaluation_service.get_evaluation_history(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status_filter
        )
        
        # 转换为响应格式
        evaluation_responses = []
        for evaluation in evaluations:
            response = ResumeEvaluationResponse(
                id=evaluation.id,
                original_filename=evaluation.original_filename,
                file_type=evaluation.file_type,
                resume_content=evaluation.resume_content,
                candidate_name=evaluation.candidate_name,
                candidate_position=evaluation.candidate_position,
                candidate_age=evaluation.candidate_age,
                candidate_gender=evaluation.candidate_gender,
                work_years=evaluation.work_years,
                education_level=evaluation.education_level,
                school=evaluation.school,
                total_score=evaluation.total_score,
                evaluation_metrics=evaluation.evaluation_metrics,
                job_description_id=evaluation.job_description_id,
                scoring_criteria_id=evaluation.scoring_criteria_id,
                user_id=evaluation.user_id,
                created_at=evaluation.created_at,
                updated_at=evaluation.updated_at
            )
            evaluation_responses.append(response)
        
        # 计算分页信息
        total_count = len(evaluation_responses)
        page = (skip // limit) + 1 if limit > 0 else 1
        pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        return ResumeEvaluationListResponse(
            items=evaluation_responses,
            total=total_count,
            page=page,
            size=limit,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"获取评价历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取评价历史失败")


@router.get("/supported-formats")
async def get_supported_formats():
    """
    获取支持的文件格式
    """
    return {
        "supported_extensions": [".pdf", ".txt", ".doc", ".docx"],
        "max_file_size": "10MB",
        "description": "支持PDF、TXT、DOC、DOCX格式的简历文件"
    }


@router.get("/{evaluation_id}", response_model=ResumeEvaluationResult)
async def get_evaluation_detail(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取特定评价结果的详细信息
    
    - **evaluation_id**: 评价记录ID
    """
    try:
        # 验证evaluation_id格式
        try:
            eval_uuid = UUID(evaluation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的评价ID格式")
        
        evaluation_service = ResumeEvaluationService(db)
        evaluation = await evaluation_service.get_evaluation_by_id(
            evaluation_id=eval_uuid,
            user_id=current_user.id
        )
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="评价记录不存在")
        
        # 获取关联的职位描述信息
        jd = await evaluation_service._get_job_description(evaluation.job_description_id)
        
        # 构建完整结果
        result = {
            "evaluation_id": str(evaluation.id),
            "file_info": {
                "filename": evaluation.filename,
                "file_type": evaluation.file_type,
                "file_size": evaluation.file_size,
                "file_hash": evaluation.file_hash
            },
            "resume_text": evaluation.resume_text,
            "ai_evaluation": {
                "evaluation_metrics": evaluation.evaluation_metrics,
                "total_score": evaluation.total_score,
                "candidate_name": evaluation.candidate_name,
                "candidate_position": evaluation.candidate_position,
                "work_years": evaluation.work_years,
                "education_level": evaluation.education_level,
                "age": evaluation.age,
                "gender": evaluation.gender,
                "school": evaluation.school,
                "raw_response": evaluation.ai_response
            },
            "job_description": {
                "id": str(jd.id) if jd else str(evaluation.job_description_id),
                "title": jd.title if jd else "未知职位",
                "company": jd.company if jd else "未知公司"
            },
            "created_at": evaluation.created_at.isoformat()
        }
        
        return ResumeEvaluationResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评价详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取评价详情失败")


@router.delete("/{evaluation_id}")
async def delete_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除评价记录
    
    - **evaluation_id**: 评价记录ID
    """
    try:
        # 验证evaluation_id格式
        try:
            eval_uuid = UUID(evaluation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的评价ID格式")
        
        evaluation_service = ResumeEvaluationService(db)
        evaluation = await evaluation_service.get_evaluation_by_id(
            evaluation_id=eval_uuid,
            user_id=current_user.id
        )
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="评价记录不存在")
        
        # 删除记录
        await db.delete(evaluation)
        await db.commit()
        
        return {"message": "评价记录已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除评价记录失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除评价记录失败")


@router.put("/{evaluation_id}/status")
async def update_resume_status(
    evaluation_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新简历状态
    
    - **evaluation_id**: 评价记录ID
    - **status**: 新状态 (pending, rejected, interview)
    """
    try:
        # 验证evaluation_id格式
        try:
            eval_uuid = UUID(evaluation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的评价ID格式")
        
        # 验证状态值
        try:
            new_status = ResumeStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的状态值，支持的状态: pending, rejected, interview")
        
        evaluation_service = ResumeEvaluationService(db)
        evaluation = await evaluation_service.get_evaluation_by_id(
            evaluation_id=eval_uuid,
            user_id=current_user.id
        )
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="评价记录不存在")
        
        # 更新状态
        evaluation.status = new_status
        await db.commit()
        
        return {
            "message": "状态更新成功",
            "evaluation_id": str(evaluation.id),
            "status": new_status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新简历状态失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="更新简历状态失败")