"""
HR Workflows API endpoints
Handles various HR automation tasks through Dify workflows
"""
from typing import Any, Optional, Dict, List
from uuid import UUID

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
from app.models.exam import Exam
from app.models.exam_result import ExamResult
from app.services.dify_service import DifyService
from app.services.kb_selection_service import KBSelectionService
from app.api.deps import get_current_user
from app.core.logging import logger
from sqlalchemy import or_
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

# 新增：需求解析请求/响应模型
class RequirementParseRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None

class RequirementParseResponse(BaseModel):
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    job_type: Optional[str] = None
    skills: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    additional_requirements: Optional[str] = None

@router.post("/parse-requirements")
async def parse_requirements(
    request: RequirementParseRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    将用户自然语言需求解析为结构化字段，供前端表单自动填充
    示例输入："JAVA开发工程师、3-5年工作经验、工作地点北京，薪资15000-20000"
    返回JSON字段：job_title, location, salary, experience, education, job_type, skills, benefits, department, additional_requirements
    """
    try:
        dify_service = DifyService()
        prompt = (
            "你是一个招聘助手。请从以下中文需求中提取结构化字段，并严格以JSON格式返回。\n"
            "不要添加解释，不要返回除JSON外的任何内容。\n"
            "需求文本：\n" + request.text + "\n\n"
            "JSON字段定义：{\n"
            "  \"job_title\": 岗位名称（如JAVA开发工程师、财务经理），\n"
            "  \"department\": 部门（如技术部、财务部，若无法判断可为空），\n"
            "  \"location\": 工作地点（城市名），\n"
            "  \"salary\": 薪资范围（原样返回，如15000-20000或25-35K），\n"
            "  \"experience\": 工作经验（如3-5年、5年以上），\n"
            "  \"education\": 学历要求（如本科、专科，若未提及可为空），\n"
            "  \"job_type\": 工作性质（如全职、兼职，若未提及可为空），\n"
            "  \"skills\": 技能标签数组（如[\"Java\", \"Spring\"]），\n"
            "  \"benefits\": 福利数组（如[\"五险一金\", \"带薪年假\"]），\n"
            "  \"additional_requirements\": 其他补充要求（原文提炼）。\n"
            "}\n"
            "示例返回：{\n"
            "  \"job_title\": \"JAVA开发工程师\",\n"
            "  \"department\": \"技术部\",\n"
            "  \"location\": \"北京\",\n"
            "  \"salary\": \"15000-20000\",\n"
            "  \"experience\": \"3-5年\",\n"
            "  \"education\": \"本科\",\n"
            "  \"job_type\": \"全职\",\n"
            "  \"skills\": [\"Java\", \"Spring\", \"MySQL\"],\n"
            "  \"benefits\": [\"五险一金\", \"带薪年假\"],\n"
            "  \"additional_requirements\": \"具备良好的沟通能力\"\n"
            "}"
        )

        ai_response = await dify_service.call_workflow_sync(
            workflow_type=1,
            query=prompt,
            conversation_id=request.conversation_id,
            additional_inputs={"task": "parse_requirements"}
        )

        answer_text = ""
        if isinstance(ai_response, dict):
            if "answer" in ai_response:
                answer_text = ai_response["answer"]
            elif "data" in ai_response and isinstance(ai_response["data"], dict) and "answer" in ai_response["data"]:
                answer_text = ai_response["data"]["answer"]
            else:
                answer_text = json.dumps(ai_response, ensure_ascii=False)
        else:
            answer_text = str(ai_response)

        json_str = answer_text.strip()
        if "```" in json_str:
            if "```json" in json_str:
                start = json_str.find("```json") + 7
            else:
                start = json_str.find("```") + 3
            end = json_str.find("```", start)
            if end > start:
                json_str = json_str[start:end].strip()

        parsed: Dict[str, Any] = {}
        try:
            parsed = json.loads(json_str)
        except Exception:
            import re
            text = request.text
            parsed = {
                "job_title": None,
                "department": None,
                "location": None,
                "salary": None,
                "experience": None,
                "education": None,
                "job_type": None,
                "skills": [],
                "benefits": [],
                "additional_requirements": text
            }
            title_match = re.search(r"([A-Za-z]+开发工程师|[\u4e00-\u9fa5A-Za-z]+经理|[\u4e00-\u9fa5A-Za-z]+工程师)", text)
            if title_match:
                parsed["job_title"] = title_match.group(1)
            exp_match = re.search(r"(\d+\s*-\s*\d+年|\d+年以上)", text)
            if exp_match:
                parsed["experience"] = exp_match.group(1).replace(" ", "")
            loc_match = re.search(r"北京|上海|深圳|广州|杭州|南京|成都|重庆|苏州|武汉|西安", text)
            if loc_match:
                parsed["location"] = loc_match.group(0)
            sal_match = re.search(r"(\d+\s*-\s*\d+K|\d+\s*-\s*\d+|\d+K\s*-\s*\d+K)", text, re.IGNORECASE)
            if sal_match:
                parsed["salary"] = sal_match.group(1).replace(" ", "")
            edu_match = re.search(r"本科|专科|硕士|博士", text)
            if edu_match:
                parsed["education"] = edu_match.group(0)
            jobtype_match = re.search(r"全职|兼职|实习", text)
            if jobtype_match:
                parsed["job_type"] = jobtype_match.group(0)

        result = RequirementParseResponse(
            job_title=parsed.get("job_title"),
            department=parsed.get("department"),
            location=parsed.get("location"),
            salary=parsed.get("salary"),
            experience=parsed.get("experience"),
            education=parsed.get("education"),
            job_type=parsed.get("job_type"),
            skills=parsed.get("skills") or [],
            benefits=parsed.get("benefits") or [],
            additional_requirements=parsed.get("additional_requirements")
        )
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error parsing requirements: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析需求失败: {str(e)}"
        )

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
            user_id=current_user.id,
            created_by=current_user.id,
            updated_by=current_user.id
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
        jd.updated_by = current_user.id
        
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
            f"请基于以下JD内容，生成详细的简历评分标准。JD内容：\n{request.jd_content}",
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
            user_id=current_user.id,
            created_by=current_user.id,
            updated_by=current_user.id
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
        criteria.updated_by = current_user.id
        
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


# ==================== 试卷管理相关API ====================

# 知识库文件信息模型
class KnowledgeFileInfo(BaseModel):
    id: str
    fileName: Optional[str] = None

# 试卷生成请求模型
class ExamGenerateRequest(BaseModel):
    title: str
    subject: str
    description: Optional[str] = None
    difficulty: str = "medium"
    duration: int = 90
    total_score: int = 100
    question_types: List[str] = []
    question_counts: Dict[str, int] = {}
    knowledge_files: List[str] = []  # 文档ID列表
    special_requirements: Optional[str] = None
    conversation_id: Optional[str] = None
    stream: bool = True

# 试题数据模型
class QuestionData(BaseModel):
    id: str
    number: int
    text: str
    type: str
    score: int
    correct_answers: str
    explanation: str
    options: List[Dict[str, str]] = []

# 试卷数据模型
class ExamCreateRequest(BaseModel):
    title: str
    subject: str
    description: Optional[str] = None
    difficulty: str = "medium"
    duration: int = 90
    total_score: int = 100
    question_types: List[str] = []
    question_counts: Dict[str, int] = {}
    knowledge_files: List[KnowledgeFileInfo] = []
    special_requirements: Optional[str] = None
    content: Optional[str] = None  # 原始试卷内容
    questions: List[QuestionData] = []  # 结构化试题数据

class ExamResponse(BaseModel):
    id: str
    title: str
    subject: str
    description: Optional[str] = None
    difficulty: str
    duration: int
    total_score: int
    question_types: List[str]
    question_counts: Dict[str, int]
    knowledge_files: List[str]
    special_requirements: Optional[str] = None
    content: Optional[str] = None
    created_at: str
    updated_at: str

# 新增：试卷意图解析请求/响应模型
class ExamIntentParseRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None

class ExamIntentParseResponse(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    total_score: Optional[int] = 100
    difficulty: Optional[str] = "medium"  # easy/medium/hard
    duration: Optional[int] = 90
    question_counts: Dict[str, int] = {}
    special_requirements: Optional[str] = None
    knowledge_files: List[KnowledgeFileInfo] = []

@router.post("/papers/parse-intent")
async def parse_exam_intent(
    request: ExamIntentParseRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    将自然语言试卷意图解析为结构化字段，供前端表单自动填充
    支持解析：标题/科目、总分、难度、时长、题量（单选/多选/简答/填空）、特殊要求
    """
    import re
    try:
        dify_service = DifyService()
        prompt = (
            "你是考试出题助手。请从以下中文需求中提取结构化字段，并严格以JSON格式返回。\n"
            "不要添加解释，不要返回除JSON外的任何内容。\n"
            "需求文本：\n" + request.text + "\n\n"
            "JSON字段定义：{\n"
            "  \"title\": 试卷标题（若未提及可从语义中提取或留空）,\n"
            "  \"subject\": 科目（如Java、市场营销，若未提及可留空）,\n"
            "  \"total_score\": 整数，总分（若未提及，默认100）,\n"
            "  \"difficulty\": 难度（easy/medium/hard）,\n"
            "  \"duration\": 整数，考试时长（分钟）,\n"
            "  \"question_counts\": 对象，包含各题型数量，如{\n"
            "    \"single_choice\": 单选题数量（整数，若未提及默认为5）,\n"
            "    \"multiple_choice\": 多选题数量（整数，若未提及默认为5）,\n"
            "    \"short_answer\": 简答题数量（整数，若未提及默认为2）\n"
            "  },\n"
            "  \"special_requirements\": 其他补充要求（原文提炼，若无则空字符串）\n"
            "}\n"
            "示例返回：{\n"
            "  \"title\": \"Java基础测试\",\n"
            "  \"subject\": \"Java\",\n"
            "  \"total_score\": 100,\n"
            "  \"difficulty\": \"medium\",\n"
            "  \"duration\": 90,\n"
            "  \"question_counts\": {\n"
            "    \"single_choice\": 10,\n"
            "    \"multiple_choice\": 5,\n"
            "    \"short_answer\": 2,\n"
            "    \"fill_blank\": 0\n"
            "  },\n"
            "  \"special_requirements\": \"题目覆盖集合、泛型、异常处理等\"\n"
            "}"
        )

        ai_response = await dify_service.call_workflow_sync(
            workflow_type=5,
            query=prompt,
            conversation_id=request.conversation_id,
            additional_inputs={"task": "parse_exam_intent"}
        )

        answer_text = ""
        if isinstance(ai_response, dict):
            if "answer" in ai_response:
                answer_text = ai_response["answer"]
            else:
                try:
                    answer_text = json.dumps(ai_response, ensure_ascii=False)
                except Exception:
                    answer_text = ""
        elif isinstance(ai_response, str):
            answer_text = ai_response

        parsed: Dict[str, Any] = {}
        if answer_text:
            try:
                parsed = json.loads(answer_text)
            except json.JSONDecodeError:
                parsed = {}

        text = request.text
        def find_int(pattern: str) -> Optional[int]:
            m = re.search(pattern, text)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return None
            return None

        difficulty_map = {
            '简单': 'easy', '易': 'easy', '基础': 'easy',
            '中等': 'medium', '一般': 'medium',
            '困难': 'hard', '难': 'hard', '高级': 'hard'
        }
        difficulty = parsed.get('difficulty') or next((difficulty_map[k] for k in difficulty_map if k in text), None) or 'medium'

        total_score = parsed.get('total_score')
        if not isinstance(total_score, int):
            total_score = find_int(r"总分[:：]?\s*(\d+)") or find_int(r"(\d+)\s*分") or 100

        duration = parsed.get('duration')
        if not isinstance(duration, int):
            duration = find_int(r"时长[:：]?\s*(\d+)\s*分钟") or find_int(r"(\d+)\s*分钟") or 90

        qc = parsed.get('question_counts') or {}
        def qc_val(key: str, patterns: List[str]) -> int:
            v = qc.get(key)
            if isinstance(v, int) and v >= 0:
                return v
            for p in patterns:
                res = find_int(p)
                if isinstance(res, int):
                    return res
            return 0

        single_choice = qc_val('single_choice', [r"单选题\s*(\d+)", r"单选\s*(\d+)"])
        multiple_choice = qc_val('multiple_choice', [r"多选题\s*(\d+)", r"多选\s*(\d+)"])
        short_answer = qc_val('short_answer', [r"简答题\s*(\d+)", r"简答\s*(\d+)"])
        fill_blank = qc_val('fill_blank', [r"填空题\s*(\d+)", r"填空\s*(\d+)"])

        title = parsed.get('title') or (re.search(r"(试卷名称|标题)[:：]?\s*([^\n]+)", text) and re.search(r"(试卷名称|标题)[:：]?\s*([^\n]+)", text).group(2).strip())
        subject = parsed.get('subject') or (re.search(r"(科目|主题)[:：]?\s*([^\n]+)", text) and re.search(r"(科目|主题)[:：]?\s*([^\n]+)", text).group(2).strip())
        if not subject and title:
            subject = title

        special_requirements = parsed.get('special_requirements')
        if not special_requirements:
            m = re.search(r"(要求|注意事项|其他)[:：]?\s*(.+)", text)
            special_requirements = m.group(2).strip() if m else ""

        result = ExamIntentParseResponse(
            title=title,
            subject=subject,
            total_score=total_score,
            difficulty=difficulty,
            duration=duration,
            question_counts={
                'single_choice': single_choice,
                'multiple_choice': multiple_choice,
                'short_answer': short_answer,
                'fill_blank': fill_blank
            },
            special_requirements=special_requirements
        )

        # 自动选择最匹配的知识库文档，填充 knowledge_files
        try:
            selector = KBSelectionService(db)
            question = "".join([
                subject or "",
                " ",
                title or "",
                " ",
                special_requirements or "",
            ]).strip() or (request.text if hasattr(request, 'text') else '')
            selection = await selector.select_kb_for_question(
                question=question,
                user_id=current_user.id,
                max_candidates=200,
            )
            knowledge_files: List[KnowledgeFileInfo] = []
            if selection and selection.get("document_id"):
                knowledge_files.append(
                    KnowledgeFileInfo(
                        id=str(selection.get("document_id")),
                        fileName=selection.get("filename")
                    )
                )
            result.knowledge_files = knowledge_files
        except Exception as se:
            logger.warning(f"KB auto-selection failed: {se}")

        return result
    except Exception as e:
        logger.error(f"Error parsing exam intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"试卷意图解析失败: {str(e)}"
        )

# 生成试卷
@router.post("/papers/generate")
async def generate_exam(
    request: ExamGenerateRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    基于文档内容生成试卷
    """
    try:
        from app.services.enhanced_document_service import EnhancedDocumentService
        
        # 初始化服务
        dify_service = DifyService()
        document_service = EnhancedDocumentService(db)
        
        # 若未提供知识库文档，自动选择最匹配文档
        if not request.knowledge_files:
            try:
                selector = KBSelectionService(db)
                selection_question = " ".join([
                    request.subject or "",
                    request.title or "",
                    request.description or "",
                    request.special_requirements or "",
                ]).strip()
                selection = await selector.select_kb_for_question(
                    question=selection_question,
                    user_id=current_user.id,
                    max_candidates=200,
                )
                if selection and selection.get("document_id"):
                    request.knowledge_files = [str(selection.get("document_id"))]
            except Exception as se:
                logger.warning(f"KB auto-selection failed: {se}")
        
        # 读取文档内容
        file_contents = []
        if request.knowledge_files:
            for file_id in request.knowledge_files:
                try:
                    # 获取文档信息
                    document = await document_service.get_document_by_id(file_id, current_user.id)
                    if document and document.extracted_content:
                        file_contents.append({
                            "filename": document.filename,
                            "content": document.extracted_content
                        })
                except Exception as e:
                    logger.warning(f"Failed to read document {file_id}: {e}")
                    continue
        
        # 合并文档内容
        combined_content = ""
        if file_contents:
            content_parts = []
            for file_info in file_contents:
                content_parts.append(f"=== {file_info['filename']} ===\n{file_info['content']}")
            combined_content = "\n\n".join(content_parts)
        
        # 构建试卷生成查询
        query_parts = [f"请基于以下文档内容生成一份{request.subject}试卷"]
        
        if request.title:
            query_parts.append(f"试卷标题：{request.title}")
        
        if request.description:
            query_parts.append(f"试卷描述：{request.description}")
        
        # if request.difficulty:
        #     difficulty_map = {
        #         'easy': '简单',
        #         'medium': '中等',
        #         'hard': '困难'
        #     }
        #     query_parts.append(f"难度等级：{difficulty_map.get(request.difficulty, request.difficulty)}")
        #
        # if request.duration:
        #     query_parts.append(f"考试时长：{request.duration}分钟")
        
        if request.question_types:
            types_str = "、".join(request.question_types)
            query_parts.append(f"题目类型：{types_str}")
        
        if request.question_counts:
            counts_parts = []
            for q_type, count in request.question_counts.items():
                if count > 0:
                    counts_parts.append(f"{q_type}：{count}题")
            if counts_parts:
                query_parts.append(f"题目数量：{', '.join(counts_parts)}")
        if request.total_score:
            query_parts.append(f"试卷总分：{request.total_score}")
        if request.special_requirements:
            query_parts.append(f"特殊要求：{request.special_requirements}")
        
        query = "\n".join(query_parts)
        
        # 准备额外输入参数
        additional_inputs = {
            "fileContent": combined_content,
        }
        
        if request.title:
            additional_inputs["title"] = request.title
        if request.description:
            additional_inputs["description"] = request.description
        if request.question_types:
            additional_inputs["question_types"] = request.question_types
        if request.question_counts:
            additional_inputs["question_counts"] = request.question_counts
        if request.special_requirements:
            additional_inputs["special_requirements"] = request.special_requirements
        
        # 附加自动选择的元信息，便于工作流提示词使用
        if request.knowledge_files:
            additional_inputs["kb_selection"] = {
                "selected_document_id": request.knowledge_files[0],
                "selected_document_filename": None,
                "selected_kb_id": selection.get("knowledge_base_id") if 'selection' in locals() and selection else None,
                "kb_selection_confidence": selection.get("confidence", 0.0) if 'selection' in locals() and selection else 0.0,
            }
        
        if request.stream:
            # 流式响应
            async def generate_stream():
                async for chunk in dify_service.call_workflow_stream(
                    workflow_type=5,  # 使用类型5进行试卷生成
                    query=query,
                    # conversation_id=request.conversation_id,
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
                workflow_type=5,
                query=query,
                conversation_id=request.conversation_id,
                additional_inputs=additional_inputs
            )
            return result
            
    except Exception as e:
        logger.error(f"Error generating exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成试卷失败: {str(e)}"
        )

# 获取试卷列表
@router.get("/papers")
async def get_exam_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取试卷列表
    """
    try:
        from app.models.exam import Exam
        from sqlalchemy import select, func, or_
        
        # 构建查询
        query = select(Exam)
        
        # 应用搜索过滤
        if search:
            search_filter = or_(
                Exam.title.ilike(f"%{search}%"),
                Exam.subject.ilike(f"%{search}%"),
                Exam.description.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # 获取总数
        count_query = select(func.count(Exam.id))
        if search:
            count_query = count_query.where(search_filter)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 应用分页和排序
        query = query.order_by(Exam.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        exams = result.scalars().all()
        
        # 转换为响应格式
        exam_list = []
        for exam in exams:
            exam_dict = {
                "id": exam.id,
                "title": exam.title,
                "subject": exam.subject,
                "description": exam.description,
                "difficulty": exam.difficulty,
                "duration": exam.duration,
                "total_score": exam.total_score,
                "question_types": exam.question_types or [],
                "question_counts": exam.question_counts or {},
                "knowledge_files": exam.knowledge_files or [],
                "special_requirements": exam.special_requirements or "",
                "created_at": exam.created_at.isoformat() if exam.created_at else None,
                "updated_at": exam.updated_at.isoformat() if exam.updated_at else None
            }
            exam_list.append(exam_dict)
        
        return {
            "items": exam_list,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting exam list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取试卷列表失败: {str(e)}"
        )

# 保存试卷
@router.post("/papers")
async def save_exam(
    exam_data: ExamCreateRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    保存试卷到数据库
    """
    try:
        from app.models.exam import Exam, Question
        
        # 创建试卷实例
        exam = Exam(
            title=exam_data.title,
            subject=exam_data.subject,
            description=exam_data.description,
            difficulty=exam_data.difficulty,
            duration=exam_data.duration,
            total_score=exam_data.total_score,
            question_types=exam_data.question_types,
            question_counts=exam_data.question_counts,
            knowledge_files=[{"id": kf.id, "fileName": kf.fileName} for kf in exam_data.knowledge_files],
            special_requirements=exam_data.special_requirements,
            content=exam_data.content,  # 保存原始试卷内容
            created_by=current_user.id,
            updated_by=current_user.id
        )
        
        # 保存到数据库
        db.add(exam)
        await db.commit()
        await db.refresh(exam)
        
        # 保存结构化试题数据
        if exam_data.questions:
            for question_data in exam_data.questions:
                question = Question(
                    exam_id=exam.id,
                    question_type=question_data.type,
                    question_text=question_data.text,
                    options=question_data.options,
                    correct_answer=question_data.correct_answers,
                    score=question_data.score,
                    order_index=question_data.number,
                    explanation=question_data.explanation,
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                db.add(question)
            
            await db.commit()
        
        # 返回保存的试卷信息
        saved_exam = {
            "id": str(exam.id),
            "title": exam.title,
            "subject": exam.subject,
            "description": exam.description,
            "difficulty": exam.difficulty,
            "duration": exam.duration,
            "total_score": exam.total_score,
            "question_types": exam.question_types,
            "question_counts": exam.question_counts,
            "knowledge_files": exam.knowledge_files,
            "special_requirements": exam.special_requirements,
            "created_at": exam.created_at.isoformat() + "Z",
            "updated_at": exam.updated_at.isoformat() + "Z",
            "created_by": str(exam.created_by)
        }
        
        logger.info(f"Exam saved successfully to database: {exam.id}")
        return saved_exam
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving exam to database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存试卷失败: {str(e)}"
        )

# 获取试卷详情
@router.get("/papers/{paper_id}")
async def get_exam_detail(
    paper_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取试卷详情
    """
    try:
        from app.models.exam import Exam, Question
        from sqlalchemy.orm import selectinload
        
        # 查询试卷及其关联的试题
        result = await db.execute(
            select(Exam)
            .options(selectinload(Exam.questions))
            .where(Exam.id == paper_id)
        )
        exam = result.scalar_one_or_none()
        
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="试卷不存在"
            )
        
        # 构建试题数据
        questions = []
        for question in sorted(exam.questions, key=lambda x: x.order_index):
            questions.append({
                "id": f"q_{question.order_index}",
                "number": question.order_index,
                "text": question.question_text,
                "type": question.question_type,
                "score": question.score,
                "correct_answers": question.correct_answer,
                "explanation": question.explanation,
                "options": question.options or []
            })
        
        # 返回试卷详情
        exam_detail = {
            "id": str(exam.id),
            "title": exam.title,
            "subject": exam.subject,
            "description": exam.description,
            "difficulty": exam.difficulty,
            "duration": exam.duration,
            "total_score": exam.total_score,
            "question_types": exam.question_types,
            "question_counts": exam.question_counts,
            "knowledge_files": exam.knowledge_files,
            "special_requirements": exam.special_requirements,
            "content": exam.content,
            "questions": questions,
            "created_at": exam.created_at.isoformat() + "Z",
            "updated_at": exam.updated_at.isoformat() + "Z",
            "created_by": str(exam.created_by)
        }
        
        logger.info(f"Exam detail retrieved successfully: {exam.id}")
        return exam_detail
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exam detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取试卷详情失败: {str(e)}"
        )

# 更新试卷
@router.put("/papers/{paper_id}")
async def update_exam(
    paper_id: str,
    exam_data: ExamCreateRequest,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新试卷
    """
    try:
        # 这里暂时返回模拟数据
        from datetime import datetime
        
        current_time = datetime.utcnow().isoformat() + "Z"
        
        updated_exam = {
            "id": paper_id,
            "title": exam_data.title,
            "subject": exam_data.subject,
            "description": exam_data.description,
            "difficulty": exam_data.difficulty,
            "duration": exam_data.duration,
            "total_score": exam_data.total_score,
            "question_types": exam_data.question_types,
            "question_counts": exam_data.question_counts,
            "knowledge_files": exam_data.knowledge_files,
            "special_requirements": exam_data.special_requirements,
            "created_at": "2024-01-01T10:00:00Z",  # 保持原创建时间
            "updated_at": current_time
        }
        
        logger.info(f"Exam updated successfully: {paper_id}")
        return updated_exam
        
    except Exception as e:
        logger.error(f"Error updating exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新试卷失败: {str(e)}"
        )

# 删除试卷
@router.delete("/papers/{paper_id}")
async def delete_exam(
    paper_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除试卷
    """
    try:
        # 查找试卷
        result = await db.execute(
            select(Exam).where(Exam.id == paper_id)
        )
        exam = result.scalar_one_or_none()
        
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="试卷不存在"
            )
        
        # 删除试卷
        await db.delete(exam)
        await db.commit()
        
        logger.info(f"Exam deleted successfully: {paper_id}")
        return {"message": "试卷删除成功", "paper_id": paper_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除试卷失败: {str(e)}"
        )

# 复制试卷
@router.post("/papers/{paper_id}/duplicate")
async def duplicate_exam(
    paper_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    复制试卷
    """
    try:
        # 这里暂时返回模拟数据
        import uuid
        from datetime import datetime
        
        new_exam_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat() + "Z"
        
        duplicated_exam = {
            "id": new_exam_id,
            "title": "Python基础知识测试 (副本)",
            "subject": "Python编程",
            "description": "测试Python基础语法和概念",
            "difficulty": "medium",
            "duration": 90,
            "total_score": 100,
            "question_types": ["单选题", "多选题", "编程题"],
            "question_counts": {"single": 10, "multiple": 5, "coding": 2},
            "knowledge_files": [],
            "special_requirements": "",
            "created_at": current_time,
            "updated_at": current_time
        }
        
        logger.info(f"Exam duplicated successfully: {paper_id} -> {new_exam_id}")
        return duplicated_exam
        
    except Exception as e:
        logger.error(f"Error duplicating exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"复制试卷失败: {str(e)}"
        )

# 预览试卷
@router.get("/papers/{paper_id}/preview")
async def preview_exam(
    paper_id: str,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    预览试卷
    """
    try:
        # 这里暂时返回模拟数据
        preview_content = {
            "id": paper_id,
            "title": "Python基础知识测试",
            "subject": "Python编程",
            "duration": 90,
            "total_score": 100,
            "questions": [
                {
                    "id": 1,
                    "type": "single_choice",
                    "question": "Python中哪个关键字用于定义函数？",
                    "options": ["def", "function", "func", "define"],
                    "correct_answer": "def",
                    "score": 5
                },
                {
                    "id": 2,
                    "type": "multiple_choice", 
                    "question": "以下哪些是Python的数据类型？",
                    "options": ["int", "str", "list", "dict"],
                    "correct_answers": ["int", "str", "list", "dict"],
                    "score": 10
                }
            ]
        }
        
        return preview_content
        
    except Exception as e:
        logger.error(f"Error previewing exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览试卷失败: {str(e)}"
        )

# 获取单个试卷（用于分享页面）
@router.get("/papers/{paper_id}/share")
async def get_exam_for_share(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个试卷（用于分享页面，无需认证）
    """
    try:
        from app.models.exam import Exam, Question
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # 查找试卷及其关联的试题
        result = await db.execute(
            select(Exam)
            .options(selectinload(Exam.questions))
            .where(Exam.id == paper_id)
        )
        exam = result.scalar_one_or_none()
        
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="试卷不存在"
            )
        
        # 构建试题列表
        questions = []
        if exam.questions:
            for question in exam.questions:
                question_data = {
                    "id": question.id,
                    "question_text": question.question_text,
                    "question_type": question.question_type,
                    "score": question.score,
                    "options": question.options if question.options else []
                }
                questions.append(question_data)
        
        # 返回试卷信息
        return {
            "id": exam.id,
            "title": exam.title,
            "subject": exam.subject,
            "description": exam.description,
            "difficulty": exam.difficulty,
            "duration": exam.duration,
            "total_score": exam.total_score,
            "content": exam.content,
            "questions": questions,
            "created_at": exam.created_at.isoformat() if exam.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取试卷失败: {str(e)}"
        )

# 考试提交请求模型
class ExamSubmitRequest(BaseModel):
    exam_id: str
    student_name: str
    department: str
    answers: Dict[str, Any]  # 学生答案
    exam_content: str  # 试卷内容

# 提交考试答案
@router.post("/papers/submit")
async def submit_exam(
    request: ExamSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    提交考试答案并调用Dify进行自动评分
    """
    try:
        from app.models.exam import Exam, Question
        from sqlalchemy.orm import selectinload
        import json
        
        # 从exam_content中解析exam_id
        exam_content = json.loads(request.exam_content)
        exam_id = request.exam_id
        
        # 从数据库获取完整的试卷信息（包括标准答案和解析）
        result = await db.execute(
            select(Exam)
            .options(selectinload(Exam.questions))
            .where(Exam.id == exam_id)
        )
        exam = result.scalar_one_or_none()
        
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="试卷不存在"
            )
        
        # 构建完整的试题信息（包含标准答案和解析）
        questions_with_answers = []
        student_answers = json.loads(request.answers) if isinstance(request.answers, str) else request.answers
        
        for question in sorted(exam.questions, key=lambda x: x.order_index):
            # 使用题目的实际ID来匹配答案
            question_id = str(question.id)
            student_answer = student_answers.get(question_id, "未作答")
            
            question_info = {
                "题目编号": question.order_index,
                "题目类型": question.question_type,
                "题目内容": question.question_text,
                "选项": question.options or [],
                "标准答案": question.correct_answer,
                "解析": question.explanation,
                "分值": question.score,
                "考生答案": student_answer
            }
            questions_with_answers.append(question_info)
        
        # 构建提交给Dify的完整查询内容
        query_parts = [
            f"考生姓名：{request.student_name}",
            f"部门：{request.department}",
            f"试卷标题：{exam.title}",
            f"试卷总分：{exam.total_score}",
            "",
            "详细题目信息（包含标准答案、解析和考生答案）：",
        ]
        
        for i, q_info in enumerate(questions_with_answers, 1):
            query_parts.extend([
                f"第{i}题：",
                f"  题目类型：{q_info['题目类型']}",
                f"  题目内容：{q_info['题目内容']}",
                f"  选项：{q_info['选项']}" if q_info['选项'] else "",
                f"  标准答案：{q_info['标准答案']}",
                f"  解析：{q_info['解析']}",
                f"  分值：{q_info['分值']}分",
                f"  考生答案：{q_info['考生答案']}",
                ""
            ])
        
        # query_parts.append("请根据以上信息对考生的答案进行评分，并给出详细的评分说明。")
        query = "\n".join(filter(None, query_parts))  # 过滤空字符串
        
        # 调用Dify进行自动评分
        dify_service = DifyService()
        result = await dify_service.call_workflow_sync(
            workflow_type=6,  # 使用类型6进行自动评分
            query=query,
            additional_inputs={"type": 6}
        )
        
        # 解析Dify返回的得分并填充到每道题的数据结构中
        questions_with_scores = []
        scores = []
        
        # 从Dify结果中提取得分字符串
        if result and "answer" in result:
            score_string = result["answer"]
            # 解析得分字符串，如 "2,2,0" -> [2, 2, 0]
            try:
                scores = [float(score.strip()) for score in score_string.split(",")]
            except (ValueError, AttributeError):
                # 如果解析失败，使用默认得分0
                scores = [0.0] * len(questions_with_answers)
        else:
            # 如果没有得分信息，使用默认得分0
            scores = [0.0] * len(questions_with_answers)
        
        # 确保得分数量与题目数量匹配
        while len(scores) < len(questions_with_answers):
            scores.append(0.0)
        
        # 将得分添加到每道题的信息中
        for i, question_info in enumerate(questions_with_answers):
            question_with_score = question_info.copy()
            question_with_score["实际得分"] = scores[i] if i < len(scores) else 0.0
            questions_with_scores.append(question_with_score)
        
        # 计算总得分
        total_score = sum(scores)
        
        # 保存考试记录到数据库
        from app.models.exam_result import ExamResult
        from datetime import datetime
        import uuid
        
        # 构建完整的考试数据JSON
        exam_data = {
            "exam_info": {
                "exam_id": exam_id,
                "title": exam.title,
                "description": exam.description,
                "total_score": exam.total_score,
                "time_limit": exam.duration,
                "instructions": exam.description or "请认真答题，注意时间限制。"
            },
            "questions": questions_with_scores,
            "student_answers": student_answers,
            "scoring_result": result,
            "submit_time": datetime.utcnow().isoformat(),
            "total_actual_score": total_score,
            "score_percentage": round((total_score / exam.total_score) * 100, 2) if exam.total_score > 0 else 0
        }
        
        # 创建考试结果记录（使用新的简化模型结构）
        exam_result = ExamResult(
            id=uuid.uuid4(),
            exam_id=exam.id,  # 添加exam_id字段
            exam_name=exam.title,
            student_name=request.student_name,
            department=request.department,
            total_possible_score=exam.total_score,
            total_actual_score=total_score,
            exam_data=exam_data,  # 保存完整的考试数据JSON
            submit_time=datetime.utcnow(),
            status="completed"
        )
        
        db.add(exam_result)
        
        # 提交数据库事务
        await db.commit()
        
        logger.info(f"Exam submitted and saved successfully for student: {request.student_name}, exam_result_id: {exam_result.id}")
        
        return {
            "message": "考试提交成功",
            "exam_result_id": str(exam_result.id),
            "student_name": request.student_name,
            "department": request.department,
            "exam_title": exam.title,
            "total_possible_score": exam.total_score,
            "total_actual_score": total_score,
            "score_percentage": round((total_score / exam.total_score) * 100, 2) if exam.total_score > 0 else 0,
            "questions": questions_with_scores,
            "scoring_result": result
        }
        
    except Exception as e:
        logger.error(f"Error submitting exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交考试失败: {str(e)}"
        )


# 获取考试结果列表
@router.get("/exam-results")
async def get_exam_results(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词（学生姓名或考试名称）"),
    exam_id: Optional[UUID] = Query(None, description="考试ID筛选"),  # 改为 UUID 类型
    department: str = Query(None, description="部门筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取考试结果列表，支持分页和筛选
    """
    try:
        from app.models.exam_result import ExamResult
        
        # 构建查询条件
        query = select(ExamResult)
        
        # 添加搜索条件
        if search:
            search_filter = or_(
                ExamResult.student_name.ilike(f"%{search}%"),
                ExamResult.exam_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # 添加考试ID筛选
        if exam_id:
            query = query.where(ExamResult.exam_id == exam_id)
        
        # 添加部门筛选
        if department:
            query = query.where(ExamResult.department.ilike(f"%{department}%"))
        
        # 获取总数
        count_query = select(func.count(ExamResult.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 添加排序和分页
        query = query.order_by(ExamResult.submit_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # 执行查询
        result = await db.execute(query)
        exam_results = result.scalars().all()
        
        # 格式化返回数据
        items = []
        for exam_result in exam_results:
            items.append({
                "exam_result_id": str(exam_result.id),
                "exam_id": str(exam_result.exam_id),
                "exam_name": exam_result.exam_name,
                "student_name": exam_result.student_name,
                "department": exam_result.department,
                "total_possible_score": exam_result.total_possible_score,
                "total_actual_score": exam_result.total_actual_score,
                "score_percentage": round((exam_result.total_actual_score / exam_result.total_possible_score) * 100, 2) if exam_result.total_possible_score > 0 else 0,
                "submit_time": exam_result.submit_time.isoformat() if exam_result.submit_time else None,
                "status": exam_result.status
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error getting exam results list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取考试结果列表失败: {str(e)}"
        )


# 获取考试结果
@router.get("/exam-results/{result_id}")
async def get_exam_result(
    result_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    根据exam_result_id获取考试结果详情
    """
    try:

        
        # 查询考试结果
        result = await db.execute(
            select(ExamResult).where(ExamResult.id == result_id)
        )
        exam_result = result.scalar_one_or_none()
        
        if not exam_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="考试结果不存在"
            )
        
        # 解析exam_data中的完整数据
        exam_data = exam_result.exam_data
        
        return {
            "exam_result_id": str(exam_result.id),
            "exam_id": str(exam_result.exam_id),
            "exam_name": exam_result.exam_name,
            "student_name": exam_result.student_name,
            "department": exam_result.department,
            "total_possible_score": exam_result.total_possible_score,
            "total_actual_score": exam_result.total_actual_score,
            "score_percentage": round((exam_result.total_actual_score / exam_result.total_possible_score) * 100, 2) if exam_result.total_possible_score > 0 else 0,
            "submit_time": exam_result.submit_time.isoformat() if exam_result.submit_time else None,
            "status": exam_result.status,
            "exam_info": exam_data.get("exam_info", {}),
            "questions": exam_data.get("questions", []),
            "scoring_result": exam_data.get("scoring_result", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exam result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取考试结果失败: {str(e)}"
        )
