"""
面试方案相关的API接口
"""
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import User as UserSchema
from app.schemas.interview_plan import (
    InterviewPlanCreate,
    InterviewPlanUpdate,
    InterviewPlanResponse,
    InterviewPlanListResponse,
    InterviewPlanSaveRequest,
    InterviewPlanGenerateRequest
)
from app.models.interview_plan import InterviewPlan
from app.models.resume_evaluation import ResumeEvaluation

router = APIRouter()


@router.post("/", response_model=InterviewPlanResponse)
async def create_interview_plan(
    plan_data: InterviewPlanCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    创建面试方案
    """
    try:
        # 验证简历评价是否存在且属于当前用户
        result = await db.execute(
            select(ResumeEvaluation).where(
                and_(
                    ResumeEvaluation.id == plan_data.resume_evaluation_id,
                    ResumeEvaluation.user_id == current_user.id
                )
            )
        )
        resume_evaluation = result.scalar_one_or_none()
        
        if not resume_evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="简历评价记录未找到或无权限访问"
            )
        
        # 创建面试方案
        interview_plan = InterviewPlan(
            candidate_name=plan_data.candidate_name,
            candidate_position=plan_data.candidate_position,
            content=plan_data.content,
            resume_evaluation_id=plan_data.resume_evaluation_id,
            user_id=current_user.id
        )
        
        db.add(interview_plan)
        await db.commit()
        await db.refresh(interview_plan)
        
        return interview_plan
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建面试方案失败: {str(e)}"
        )


@router.put("/{plan_id}", response_model=InterviewPlanResponse)
async def update_interview_plan(
    plan_id: UUID,
    plan_data: InterviewPlanUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    更新面试方案
    """
    try:
        # 查询面试方案
        result = await db.execute(
            select(InterviewPlan).where(
                and_(
                    InterviewPlan.id == plan_id,
                    InterviewPlan.user_id == current_user.id
                )
            )
        )
        interview_plan = result.scalar_one_or_none()
        
        if not interview_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="面试方案未找到或无权限访问"
            )
        
        # 更新字段
        update_data = plan_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(interview_plan, field, value)
        
        await db.commit()
        await db.refresh(interview_plan)
        
        return interview_plan
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新面试方案失败: {str(e)}"
        )


@router.post("/{plan_id}/save", response_model=InterviewPlanResponse)
async def save_interview_plan_content(
    plan_id: UUID,
    save_data: InterviewPlanSaveRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    保存面试方案内容（用于前端编辑后保存）
    """
    try:
        # 查询面试方案
        result = await db.execute(
            select(InterviewPlan).where(
                and_(
                    InterviewPlan.id == plan_id,
                    InterviewPlan.user_id == current_user.id
                )
            )
        )
        interview_plan = result.scalar_one_or_none()
        
        if not interview_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="面试方案未找到或无权限访问"
            )
        
        # 更新内容
        interview_plan.content = save_data.content
        if save_data.candidate_name:
            interview_plan.candidate_name = save_data.candidate_name
        if save_data.candidate_position:
            interview_plan.candidate_position = save_data.candidate_position
        
        await db.commit()
        await db.refresh(interview_plan)
        
        return interview_plan
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存面试方案失败: {str(e)}"
        )


@router.get("/{plan_id}", response_model=InterviewPlanResponse)
async def get_interview_plan(
    plan_id: UUID,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取面试方案详情
    """
    try:
        result = await db.execute(
            select(InterviewPlan).where(
                and_(
                    InterviewPlan.id == plan_id,
                    InterviewPlan.user_id == current_user.id
                )
            )
        )
        interview_plan = result.scalar_one_or_none()
        
        if not interview_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="面试方案未找到或无权限访问"
            )
        
        return interview_plan
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取面试方案失败: {str(e)}"
        )


@router.get("/", response_model=InterviewPlanListResponse)
async def list_interview_plans(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    resume_evaluation_id: Optional[UUID] = Query(None, description="简历评价ID"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取面试方案列表
    """
    try:
        # 构建查询条件
        conditions = [InterviewPlan.user_id == current_user.id]
        
        if resume_evaluation_id:
            conditions.append(InterviewPlan.resume_evaluation_id == resume_evaluation_id)
        

        
        # 查询总数
        count_result = await db.execute(
            select(InterviewPlan).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())
        
        # 分页查询
        offset = (page - 1) * size
        result = await db.execute(
            select(InterviewPlan)
            .where(and_(*conditions))
            .order_by(InterviewPlan.created_at.desc())
            .offset(offset)
            .limit(size)
        )
        interview_plans = result.scalars().all()
        
        # 计算总页数
        pages = (total + size - 1) // size
        
        return InterviewPlanListResponse(
            items=interview_plans,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取面试方案列表失败: {str(e)}"
        )


@router.delete("/{plan_id}")
async def delete_interview_plan(
    plan_id: UUID,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    删除面试方案
    """
    try:
        result = await db.execute(
            select(InterviewPlan).where(
                and_(
                    InterviewPlan.id == plan_id,
                    InterviewPlan.user_id == current_user.id
                )
            )
        )
        interview_plan = result.scalar_one_or_none()
        
        if not interview_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="面试方案未找到或无权限访问"
            )
        
        await db.delete(interview_plan)
        await db.commit()
        
        return {"message": "面试方案删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除面试方案失败: {str(e)}"
        )


@router.post("/save-generated", response_model=InterviewPlanResponse)
async def save_generated_interview_plan(
    plan_data: InterviewPlanCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    保存生成的面试方案内容
    """
    try:
        # 验证简历评价是否存在且属于当前用户
        result = await db.execute(
            select(ResumeEvaluation).where(
                and_(
                    ResumeEvaluation.id == plan_data.resume_evaluation_id,
                    ResumeEvaluation.user_id == current_user.id
                )
            )
        )
        resume_evaluation = result.scalar_one_or_none()
        
        if not resume_evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="简历评价记录未找到或无权限访问"
            )
        
        # 检查是否已存在面试方案
        existing_result = await db.execute(
            select(InterviewPlan).where(
                and_(
                    InterviewPlan.resume_evaluation_id == plan_data.resume_evaluation_id,
                    InterviewPlan.user_id == current_user.id
                )
            )
        )
        existing_plan = existing_result.scalar_one_or_none()
        
        if existing_plan:
            # 如果已存在，更新内容
            existing_plan.candidate_name = plan_data.candidate_name
            existing_plan.candidate_position = plan_data.candidate_position
            existing_plan.content = plan_data.content
            await db.commit()
            await db.refresh(existing_plan)
            return existing_plan
        
        # 创建新的面试方案
        interview_plan = InterviewPlan(
            candidate_name=plan_data.candidate_name,
            candidate_position=plan_data.candidate_position,
            content=plan_data.content,
            resume_evaluation_id=plan_data.resume_evaluation_id,
            user_id=current_user.id
        )
        
        db.add(interview_plan)
        await db.commit()
        await db.refresh(interview_plan)
        
        return interview_plan
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存面试方案失败: {str(e)}"
        )