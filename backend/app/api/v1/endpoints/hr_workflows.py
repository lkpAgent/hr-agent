"""
HR Workflows API endpoints
Handles various HR automation tasks through Dify workflows
"""
from typing import Any, Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import json

from app.core.database import get_db
from app.schemas.user import User as UserSchema
from app.schemas.job_description import (
    JobDescriptionCreate, 
    JobDescriptionUpdate, 
    JobDescriptionResponse,
    JobDescriptionListResponse
)
from app.schemas.scoring_criteria import (
    ScoringCriteriaCreate,
    ScoringCriteriaUpdate,
    ScoringCriteriaResponse,
    ScoringCriteriaListResponse
)
from app.models.job_description import JobDescription
from app.models.scoring_criteria import ScoringCriteria
from app.models.resume_evaluation import ResumeEvaluation
from app.services.dify_service import DifyService
from app.api.deps import get_current_user
from app.core.logging import logger

router = APIRouter()


from pydantic import BaseModel

class JDGenerateRequest(BaseModel):
    requirements: str
    position_title: str = None
    department: str = None
    experience_level: str = None
    conversation_id: str = None
    stream: bool = True

class ScoringCriteriaGenerateRequest(BaseModel):
    jd_content: str
    job_title: str = None
    requirements: Dict = None
    conversation_id: str = None
    stream: bool = True

@router.post("/generate-jd")
async def generate_job_description(
    request: JDGenerateRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    生成岗位JD (Job Description)
    工作流类型: type=1
    """
    try:
        dify_service = DifyService()
        
        # 构建查询内容
        query_parts = [f"请基于给定要求，生成岗位JD。要求如下：{request.requirements}"]
        
        if request.position_title:
            query_parts.append(f"岗位名称：{request.position_title}")
        if request.department:
            query_parts.append(f"部门：{request.department}")
        if request.experience_level:
            query_parts.append(f"经验要求：{request.experience_level}")
        
        query = "\n".join(query_parts)
        
        # 额外输入参数
        additional_inputs = {}
        if request.position_title:
            additional_inputs["position_title"] = request.position_title
        if request.department:
            additional_inputs["department"] = request.department
        if request.experience_level:
            additional_inputs["experience_level"] = request.experience_level
        
        if request.stream:
            # 流式响应
            async def generate_stream():
                async for chunk in dify_service.call_workflow_stream(
                    workflow_type=1,
                    query=query,
                    conversation_id=request.conversation_id,
                    additional_inputs=additional_inputs
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # 同步响应
            result = await dify_service.call_workflow_sync(
                workflow_type=2,
                query=query,
                conversation_id=request.conversation_id,
                additional_inputs=additional_inputs
            )
            return result
            
    except Exception as e:
        logger.error(f"Error generating JD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成JD失败: {str(e)}"
        )


@router.post("/evaluate-resume")
async def evaluate_resume(
    resume_content: str = Form(..., description="简历内容"),
    job_requirements: str = Form(None, description="岗位要求"),
    evaluation_criteria: str = Form(None, description="评价标准"),
    conversation_id: str = Form(None, description="对话ID"),
    stream: bool = Form(True, description="是否流式返回"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    简历评价模型
    工作流类型: type=2
    """
    try:
        dify_service = DifyService()
        
        # 构建查询内容
        query_parts = [f"请对以下简历进行评价：\n{resume_content}"]
        
        if job_requirements:
            query_parts.append(f"\n岗位要求：{job_requirements}")
        if evaluation_criteria:
            query_parts.append(f"\n评价标准：{evaluation_criteria}")
        
        query = "\n".join(query_parts)
        
        # 额外输入参数
        additional_inputs = {}
        if job_requirements:
            additional_inputs["job_requirements"] = job_requirements
        if evaluation_criteria:
            additional_inputs["evaluation_criteria"] = evaluation_criteria
        
        if stream:
            # 流式响应
            async def generate_stream():
                async for chunk in dify_service.call_workflow_stream(
                    workflow_type=2,
                    query=query,
                    conversation_id=conversation_id,
                    additional_inputs=additional_inputs
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # 同步响应
            result = await dify_service.call_workflow_sync(
                workflow_type=2,
                query=query,
                conversation_id=conversation_id,
                additional_inputs=additional_inputs
            )
            return result
            
    except Exception as e:
        logger.error(f"Error evaluating resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"简历评价失败: {str(e)}"
        )


@router.post("/generate-interview-plan")
async def generate_interview_plan(
    position_title: str = Form(..., description="岗位名称"),
    candidate_background: str = Form(None, description="候选人背景"),
    interview_type: str = Form(None, description="面试类型"),
    interview_duration: str = Form(None, description="面试时长"),
    conversation_id: str = Form(None, description="对话ID"),
    stream: bool = Form(True, description="是否流式返回"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    生成面试方案
    工作流类型: type=3
    """
    try:
        dify_service = DifyService()
        
        # 构建查询内容
        query_parts = [f"请为{position_title}岗位生成面试方案。"]
        
        if candidate_background:
            query_parts.append(f"候选人背景：{candidate_background}")
        if interview_type:
            query_parts.append(f"面试类型：{interview_type}")
        if interview_duration:
            query_parts.append(f"面试时长：{interview_duration}")
        
        query = "\n".join(query_parts)
        
        # 额外输入参数
        additional_inputs = {
            "position_title": position_title
        }
        if candidate_background:
            additional_inputs["candidate_background"] = candidate_background
        if interview_type:
            additional_inputs["interview_type"] = interview_type
        if interview_duration:
            additional_inputs["interview_duration"] = interview_duration
        
        if stream:
            # 流式响应
            async def generate_stream():
                async for chunk in dify_service.call_workflow_stream(
                    workflow_type=3,
                    query=query,
                    conversation_id=conversation_id,
                    additional_inputs=additional_inputs
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # 同步响应
            result = await dify_service.call_workflow_sync(
                workflow_type=3,
                query=query,
                conversation_id=conversation_id,
                additional_inputs=additional_inputs
            )
            return result
            
    except Exception as e:
        logger.error(f"Error generating interview plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成面试方案失败: {str(e)}"
        )


@router.post("/custom-workflow")
async def call_custom_workflow(
    workflow_type: int = Form(..., description="工作流类型"),
    query: str = Form(..., description="查询内容"),
    additional_inputs: str = Form(None, description="额外输入参数(JSON格式)"),
    conversation_id: str = Form(None, description="对话ID"),
    stream: bool = Form(True, description="是否流式返回"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    调用自定义工作流
    支持任意类型的工作流调用
    """
    try:
        dify_service = DifyService()
        
        # 解析额外输入参数
        parsed_inputs = {}
        if additional_inputs:
            try:
                parsed_inputs = json.loads(additional_inputs)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="additional_inputs必须是有效的JSON格式"
                )
        
        if stream:
            # 流式响应
            async def generate_stream():
                async for chunk in dify_service.call_workflow_stream(
                    workflow_type=workflow_type,
                    query=query,
                    conversation_id=conversation_id,
                    additional_inputs=parsed_inputs
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # 同步响应
            result = await dify_service.call_workflow_sync(
                workflow_type=workflow_type,
                query=query,
                conversation_id=conversation_id,
                additional_inputs=parsed_inputs
            )
            return result
            
    except Exception as e:
        logger.error(f"Error calling custom workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"调用工作流失败: {str(e)}"
        )


@router.get("/workflow-types")
async def get_workflow_types(
    current_user: UserSchema = Depends(get_current_user)
) -> Any:
    """
    获取支持的工作流类型列表
    """
    try:
        dify_service = DifyService()
        
        workflow_types = []
        for i in range(1, 6):  # 支持类型1-5
            workflow_types.append({
                "type": i,
                "description": dify_service.get_workflow_type_description(i)
            })
        
        return {
            "workflow_types": workflow_types,
            "total": len(workflow_types)
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流类型失败: {str(e)}"
        )


# JD Management APIs

@router.post("/jd/save", response_model=JobDescriptionResponse)
async def save_job_description(
    jd_data: JobDescriptionCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    保存生成的JD到数据库
    """
    try:
        # 创建新的JD记录
        jd = JobDescription(
            title=jd_data.title,
            department=jd_data.department,
            experience_level=jd_data.experience_level,
            education=jd_data.education,
            location=jd_data.location,
            salary_range=jd_data.salary_range,
            job_type=jd_data.job_type,
            skills=jd_data.skills,
            content=jd_data.content,
            requirements=jd_data.requirements,
            status=jd_data.status,
            meta_data=jd_data.meta_data,
            conversation_id=jd_data.conversation_id,
            user_id=current_user.id
        )
        
        db.add(jd)
        await db.commit()
        await db.refresh(jd)
        
        logger.info(f"JD saved successfully: {jd.id}")
        return jd
        
    except Exception as e:
        logger.error(f"Error saving JD: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存JD失败: {str(e)}"
        )


@router.put("/jd/{jd_id}", response_model=JobDescriptionResponse)
async def update_job_description(
    jd_id: str,
    jd_data: JobDescriptionUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    更新已保存的JD
    """
    try:
        # 查找JD记录
        result = await db.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id,
                JobDescription.user_id == current_user.id,
                JobDescription.is_active == True
            )
        )
        jd = result.scalar_one_or_none()
        
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JD not found"
            )
        
        # 更新字段
        update_data = jd_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(jd, field, value)
        
        await db.commit()
        await db.refresh(jd)
        
        logger.info(f"JD updated successfully: {jd.id}")
        return jd
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating JD: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新JD失败: {str(e)}"
        )


@router.get("/jd/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    jd_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取指定的JD
    """
    try:
        result = await db.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id,
                JobDescription.user_id == current_user.id,
                JobDescription.is_active == True
            )
        )
        jd = result.scalar_one_or_none()
        
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JD not found"
            )
        
        return jd
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting JD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取JD失败: {str(e)}"
        )


@router.get("/jd", response_model=JobDescriptionListResponse)
async def list_job_descriptions(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取用户的JD列表
    """
    try:
        # 构建查询条件
        query = select(JobDescription).where(
            JobDescription.user_id == current_user.id,
            JobDescription.is_active == True
        )
        
        if status_filter:
            query = query.where(JobDescription.status == status_filter)
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * size
        query = query.order_by(JobDescription.created_at.desc()).offset(offset).limit(size)
        
        result = await db.execute(query)
        jds = result.scalars().all()
        
        pages = (total + size - 1) // size
        
        return JobDescriptionListResponse(
            items=jds,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error listing JDs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取JD列表失败: {str(e)}"
        )


@router.delete("/jd/{jd_id}")
async def delete_job_description(
    jd_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    删除JD（软删除）
    """
    try:
        result = await db.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id,
                JobDescription.user_id == current_user.id,
                JobDescription.is_active == True
            )
        )
        jd = result.scalar_one_or_none()
        
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JD not found"
            )
        
        # 软删除
        jd.is_active = False
        await db.commit()
        
        logger.info(f"JD deleted successfully: {jd.id}")
        return {"message": "JD deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting JD: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除JD失败: {str(e)}"
        )


@router.post("/generate-scoring-criteria")
async def generate_scoring_criteria(
    request: ScoringCriteriaGenerateRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    生成简历评分标准
    基于JD内容生成对应的简历评分标准
    """
    try:
        dify_service = DifyService()
        
        # 构建查询内容
        query_parts = [
            f"请基于以下JD内容，生成详细的简历评分标准：\n{request.jd_content}",
            "\n请生成包含以下维度的评分标准：",
            "1. 技能匹配度（40%）",
            "2. 工作经验匹配度（30%）", 
            "3. 教育背景匹配度（15%）",
            "4. 项目经验匹配度（15%）",
            "\n每个维度请提供具体的评分细则和分数区间。"
        ]
        
        if request.job_title:
            query_parts.append(f"\n岗位名称：{request.job_title}")
            
        if request.requirements:
            if request.requirements.get('experience'):
                query_parts.append(f"经验要求：{request.requirements['experience']}")
            if request.requirements.get('education'):
                query_parts.append(f"学历要求：{request.requirements['education']}")
            if request.requirements.get('skills'):
                skills = request.requirements['skills']
                if isinstance(skills, list):
                    query_parts.append(f"技能要求：{', '.join(skills)}")
                else:
                    query_parts.append(f"技能要求：{skills}")
        
        query = "\n".join(query_parts)
        
        # 额外输入参数
        additional_inputs = {
            "jd_content": request.jd_content
        }
        if request.job_title:
            additional_inputs["job_title"] = request.job_title
        if request.requirements:
            additional_inputs["requirements"] = json.dumps(request.requirements, ensure_ascii=False)
        
        if request.stream:
            # 流式响应
            async def generate_stream():
                async for chunk in dify_service.call_workflow_stream(
                    workflow_type=2,  # 使用type=2用于评分标准生成
                    query=query,
                    conversation_id=request.conversation_id,
                    additional_inputs=additional_inputs
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # 同步响应
            result = await dify_service.call_workflow_sync(
                workflow_type=1,
                query=query,
                conversation_id=request.conversation_id,
                additional_inputs=additional_inputs
            )
            return result
        
    except Exception as e:
        logger.error(f"Error generating scoring criteria: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成评分标准失败: {str(e)}"
        )


# Scoring Criteria Management APIs

@router.post("/scoring-criteria/save", response_model=ScoringCriteriaResponse)
async def save_scoring_criteria(
    criteria_data: ScoringCriteriaCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    保存生成的评分标准到数据库
    """
    try:
        # 创建新的评分标准记录
        criteria = ScoringCriteria(
            title=criteria_data.title,
            job_title=criteria_data.job_title,
            content=criteria_data.content,
            criteria_data=criteria_data.criteria_data,
            total_score=criteria_data.total_score,
            scoring_dimensions=criteria_data.scoring_dimensions,
            status=criteria_data.status,
            meta_data=criteria_data.meta_data,
            conversation_id=criteria_data.conversation_id,
            job_description_id=criteria_data.job_description_id,
            user_id=current_user.id
        )
        
        db.add(criteria)
        await db.commit()
        await db.refresh(criteria)
        
        logger.info(f"Scoring criteria saved successfully: {criteria.id}")
        return criteria
        
    except Exception as e:
        logger.error(f"Error saving scoring criteria: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存评分标准失败: {str(e)}"
        )


@router.put("/scoring-criteria/{criteria_id}", response_model=ScoringCriteriaResponse)
async def update_scoring_criteria(
    criteria_id: str,
    criteria_data: ScoringCriteriaUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    更新已保存的评分标准
    """
    try:
        # 查找评分标准记录
        result = await db.execute(
            select(ScoringCriteria).where(
                ScoringCriteria.id == criteria_id,
                ScoringCriteria.user_id == current_user.id,
                ScoringCriteria.is_active == True
            )
        )
        criteria = result.scalar_one_or_none()
        
        if not criteria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scoring criteria not found"
            )
        
        # 更新字段
        update_data = criteria_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(criteria, field, value)
        
        await db.commit()
        await db.refresh(criteria)
        
        logger.info(f"Scoring criteria updated successfully: {criteria.id}")
        return criteria
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scoring criteria: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新评分标准失败: {str(e)}"
        )


@router.get("/scoring-criteria/{criteria_id}", response_model=ScoringCriteriaResponse)
async def get_scoring_criteria(
    criteria_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取单个评分标准详情
    """
    try:
        result = await db.execute(
            select(ScoringCriteria).where(
                ScoringCriteria.id == criteria_id,
                ScoringCriteria.user_id == current_user.id,
                ScoringCriteria.is_active == True
            )
        )
        criteria = result.scalar_one_or_none()
        
        if not criteria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scoring criteria not found"
            )
        
        return criteria
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scoring criteria: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评分标准失败: {str(e)}"
        )


@router.get("/scoring-criteria", response_model=ScoringCriteriaListResponse)
async def get_scoring_criteria_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    job_description_id: Optional[str] = Query(None, description="关联的JD ID"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取评分标准列表
    """
    try:
        # 构建查询条件
        query_conditions = [
            ScoringCriteria.user_id == current_user.id,
            ScoringCriteria.is_active == True
        ]
        
        if job_description_id:
            query_conditions.append(ScoringCriteria.job_description_id == job_description_id)
        
        # 查询总数
        count_result = await db.execute(
            select(func.count(ScoringCriteria.id)).where(*query_conditions)
        )
        total = count_result.scalar()
        
        # 查询数据
        offset = (page - 1) * size
        result = await db.execute(
            select(ScoringCriteria)
            .where(*query_conditions)
            .order_by(ScoringCriteria.updated_at.desc())
            .offset(offset)
            .limit(size)
        )
        criteria_list = result.scalars().all()
        
        # 计算总页数
        pages = (total + size - 1) // size
        
        return ScoringCriteriaListResponse(
            items=criteria_list,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Error getting scoring criteria list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评分标准列表失败: {str(e)}"
        )


@router.delete("/scoring-criteria/{criteria_id}")
async def delete_scoring_criteria(
    criteria_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    删除评分标准（软删除）
    """
    try:
        result = await db.execute(
            select(ScoringCriteria).where(
                ScoringCriteria.id == criteria_id,
                ScoringCriteria.user_id == current_user.id,
                ScoringCriteria.is_active == True
            )
        )
        criteria = result.scalar_one_or_none()
        
        if not criteria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scoring criteria not found"
            )
        
        # 软删除
        criteria.is_active = False
        await db.commit()
        
        logger.info(f"Scoring criteria deleted successfully: {criteria.id}")
        return {"message": "评分标准删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scoring criteria: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除评分标准失败: {str(e)}"
        )


@router.post("/generate-interview-plan-by-resume")
async def generate_interview_plan_by_resume(
    resume_id: str = Form(..., description="简历ID"),
    conversation_id: str = Form(None, description="对话ID"),
    stream: bool = Form(True, description="是否流式返回"),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    根据简历ID生成面试方案
    工作流类型: type=4
    """
    try:
        # 查询简历评价记录
        result = await db.execute(
            select(ResumeEvaluation).where(
                ResumeEvaluation.id == resume_id,
                ResumeEvaluation.user_id == current_user.id
            )
        )
        resume_evaluation = result.scalar_one_or_none()
        
        if not resume_evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="简历记录未找到"
            )
        
        # 查询关联的JD
        jd_result = await db.execute(
            select(JobDescription).where(
                JobDescription.id == resume_evaluation.job_description_id,
                JobDescription.user_id == current_user.id
            )
        )
        job_description = jd_result.scalar_one_or_none()
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联的职位描述未找到"
            )
        

        # 构建简历内容
        jianli_content = resume_evaluation.resume_content
        
        dify_service = DifyService()
        
        # 构建查询内容
        query = f"请根据简历和JD要求生成面试方案。"
        
        # 额外输入参数
        additional_inputs = {
            "jianli": jianli_content,
            "jd": job_description.content
        }
        
        if stream:
            # 流式响应
            async def generate_stream():
                async for chunk in dify_service.call_workflow_stream(
                    workflow_type=4,
                    query=query,
                    conversation_id=conversation_id,
                    additional_inputs=additional_inputs
                ):
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            # 同步响应
            result = await dify_service.call_workflow_sync(
                workflow_type=4,
                query=query,
                conversation_id=conversation_id,
                additional_inputs=additional_inputs
            )
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating interview plan by resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成面试方案失败: {str(e)}"
        )