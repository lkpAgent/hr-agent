"""
Resume Evaluation Service for AI-powered resume scoring
"""
import logging
import json
import re
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.resume_evaluation import ResumeEvaluation, ResumeStatus
from app.models.job_description import JobDescription
from app.models.scoring_criteria import ScoringCriteria
from app.schemas.resume_evaluation import (
    ResumeEvaluationCreate, 
    AIEvaluationResult,
    EvaluationMetric
)
from app.services.dify_service import DifyService
from app.services.resume_parser_service import ResumeParserService

logger = logging.getLogger(__name__)


class ResumeEvaluationService:
    """简历评价服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dify_service = DifyService()
        self.resume_parser = ResumeParserService()
    
    async def evaluate_resume(
        self,
        user_id: UUID,
        file_content: bytes,
        filename: str,
        job_description_id: UUID,
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """评价简历"""
        try:
            # 1. 验证文件
            is_valid, message = self.resume_parser.validate_file(filename, len(file_content))
            if not is_valid:
                raise ValueError(message)
            
            # 2. 提取文本内容
            resume_text = await self.resume_parser.extract_text_from_file(file_content, filename)
            if not resume_text.strip():
                raise ValueError("无法从文件中提取到有效内容")
            
            # 3. 获取文件信息
            file_info = self.resume_parser.get_file_info(filename, file_content)
            
            # 4. 获取JD信息
            jd = await self._get_job_description(job_description_id)
            if not jd:
                raise ValueError("职位描述不存在")
            
            # 5. 获取评价模型
            evaluation_model = await self._get_evaluation_model(job_description_id)
            
            # 6. 调用Dify API进行评价
            ai_result, raw_response = await self._call_dify_evaluation(
                resume_text=resume_text,
                evaluation_model=evaluation_model,
                jd_info=jd
            )
            
            # 7. 保存评价结果
            evaluation_record = await self._save_evaluation_result(
                user_id=user_id,
                file_info=file_info,
                resume_text=resume_text,
                ai_result=ai_result,
                job_description_id=job_description_id,
                conversation_id=conversation_id,
                raw_response=raw_response
            )
            
            # 8. 返回完整结果
            return {
                "id": evaluation_record.id,
                "evaluation_metrics": [metric.model_dump() for metric in ai_result.evaluation_metrics],
                "total_score": ai_result.total_score,
                "name": ai_result.name,
                "position": ai_result.position,
                "workYears": (self._parse_work_years_to_float(ai_result.workYears) or 0.0),
                "education": ai_result.教育水平,
                "age": ai_result.年龄,
                "sex": ai_result.sex,
                "school": ai_result.school,
                "resume_content": resume_text,
                "original_filename": file_info['filename'],
                "created_at": evaluation_record.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"简历评价失败: {e}")
            raise
    
    async def _get_job_description(self, jd_id: UUID) -> Optional[JobDescription]:
        """获取职位描述"""
        try:
            result = await self.db.execute(
                select(JobDescription).where(JobDescription.id == jd_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取职位描述失败: {e}")
            return None
    
    async def _get_evaluation_model(self, jd_id: UUID) -> str:
        """获取评价模型"""
        try:
            # 查询与JD关联的评分标准
            result = await self.db.execute(
                select(ScoringCriteria).where(ScoringCriteria.job_description_id == jd_id)
            )
            criteria = result.scalar_one_or_none()
            
            if criteria and criteria.evaluation_model:
                return criteria.evaluation_model
            
            # 如果没有找到特定的评价模型，返回默认模型
            return self._get_default_evaluation_model()
            
        except Exception as e:
            logger.error(f"获取评价模型失败: {e}")
            return self._get_default_evaluation_model()
    
    def _get_default_evaluation_model(self) -> str:
        """获取默认评价模型"""
        return """
        请根据以下职位要求对简历进行评价，并按照指定的JSON格式返回结果：

        评价维度：
        1. 学历匹配度 (0-20分)
        2. 工作经验匹配度 (0-25分)
        3. 技能匹配度 (0-25分)
        4. 项目经验匹配度 (0-20分)
        5. 综合素质 (0-10分)

        请提取简历中的以下信息：
        - 姓名
        - 应聘岗位
        - 工作年限
        - 教育水平
        - 年龄
        - 性别
        - 毕业院校

        返回格式必须是有效的JSON：
        {
          "evaluation_metrics": [
            {
              "name": "学历",
              "score": 15,
              "max": 20,
              "reason": "本科学历，符合岗位要求"
            }
          ],
          "total_score": 85,
          "name": "张三",
          "position": "前端开发工程师",
          "workYears": "3年",
          "education": "本科",
          "age": 28,
          "sex": "男",
          "school": "上海理工大学"
        }
        """
    
    async def _call_dify_evaluation(
        self,
        resume_text: str,
        evaluation_model: str,
        jd_info: JobDescription
    ) -> tuple[AIEvaluationResult, str]:
        """调用Dify API进行简历评价"""
        try:
            # 构建评价提示词
            evaluation_prompt = f"""
            {evaluation_model}
            
            职位信息：
            - 职位名称: {jd_info.title}
            - 部门: {jd_info.department or "未知部门"}
            - 职位要求: {jd_info.requirements}
            - 技能要求: {jd_info.skills}
            - 教育要求: {jd_info.education}
            - 工作经验要求: {jd_info.experience_level or "不限"}
            
            简历内容：
            {resume_text}
            
            请严格按照JSON格式返回评价结果。
            """
            
            # 调用Dify API (使用工作流类型3进行简历评价)
            response = await self.dify_service.call_workflow_sync(
                workflow_type=3,  # 简历评价工作流
                query=evaluation_prompt,
                additional_inputs={
                    "resume_text": resume_text,
                    "job_title": jd_info.title,
                    "job_requirements": jd_info.requirements,
                    "job_skills": jd_info.skills,
                    "job_education": jd_info.education,
                    "job_experience": jd_info.experience_level
                }
            )
            
            # 解析AI响应
            ai_result = self._parse_ai_response(response)
            raw_response = str(response)  # 保存原始响应
            return ai_result, raw_response
            
        except Exception as e:
            logger.error(f"调用Dify API失败: {e}")
            raise Exception(f"AI评价服务暂时不可用: {str(e)}")
    
    def _parse_ai_response(self, response: Dict[str, Any]) -> AIEvaluationResult:
        """解析AI响应，提取评价结果"""
        try:
            # 从Dify响应中提取答案文本
            answer_text = ""
            if "answer" in response:
                answer_text = response["answer"]
            elif "data" in response and "answer" in response["data"]:
                answer_text = response["data"]["answer"]
            else:
                # 如果没有找到answer字段，尝试从其他可能的字段获取
                answer_text = str(response)
            
            if not answer_text:
                raise ValueError("AI响应为空")
            
            # 尝试解析JSON
            try:
                # 尝试直接解析JSON
                if answer_text.startswith('{') and answer_text.endswith('}'):
                    result_data = json.loads(answer_text)
                else:
                    # 如果响应包含代码块，提取JSON部分
                    if '```json' in answer_text:
                        start = answer_text.find('```json') + 7
                        end = answer_text.find('```', start)
                        json_str = answer_text[start:end].strip()
                    elif '```' in answer_text:
                        start = answer_text.find('```') + 3
                        end = answer_text.find('```', start)
                        json_str = answer_text[start:end].strip()
                    else:
                        # 如果不是纯JSON，尝试提取JSON部分
                        json_start = answer_text.find('{')
                        json_end = answer_text.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_str = answer_text[json_start:json_end]
                        else:
                            raise ValueError("No valid JSON found in response")
                    
                    # 解析JSON
                    result_data = json.loads(json_str)
                
                # 验证必要字段
                if 'evaluation_metrics' not in result_data:
                    raise ValueError("缺少evaluation_metrics字段")
                
                if 'total_score' not in result_data:
                    raise ValueError("缺少total_score字段")
                
                # 构建评价指标列表
                metrics = []
                for metric_data in result_data.get('evaluation_metrics', []):
                    metric = EvaluationMetric(
                        name=metric_data.get('name', ''),
                        score=metric_data.get('score', 0),
                        max=metric_data.get('max', 100),
                        reason=metric_data.get('reason', '')
                    )
                    metrics.append(metric)
                
                # 规范化字段别名，兼容不同返回命名
                normalized_work_years = (
                    result_data.get('workYears')
                    or result_data.get('work_years')
                    or result_data.get('work_experience')
                    or result_data.get('工作年限')
                    or result_data.get('工作经验')
                )
                normalized_education = (
                    result_data.get('education')
                    or result_data.get('education_level')
                    or result_data.get('学历')
                    or result_data.get('教育水平')
                )
                normalized_age = result_data.get('age', result_data.get('年龄'))
                normalized_sex = (
                    result_data.get('sex')
                    or result_data.get('gender')
                    or result_data.get('性别')
                )
                normalized_school = (
                    result_data.get('school')
                    or result_data.get('毕业院校')
                    or result_data.get('院校')
                    or result_data.get('学校')
                )
                
                # 构建AI评价结果
                ai_result = AIEvaluationResult(
                    evaluation_metrics=metrics,
                    total_score=result_data.get('total_score', 0),
                    name=result_data.get('name', ''),
                    position=result_data.get('position', ''),
                    workYears=normalized_work_years or '',
                    教育水平=normalized_education or '',
                    年龄=normalized_age,
                    sex=normalized_sex or '',
                    school=normalized_school or ''
                )
                
                return ai_result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 原始响应: {answer_text}")
                # 返回默认结果
                return self._create_default_result(answer_text)
                
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            return self._create_default_result(str(e))
    
    def _create_default_result(self, raw_response: str) -> AIEvaluationResult:
        """创建默认评价结果"""
        return AIEvaluationResult(
            evaluation_metrics=[
                EvaluationMetric(
                    name="综合评价",
                    score=60,
                    max=100,
                    reason="AI解析失败，给出默认评分"
                )
            ],
            total_score=60,
            name="未知",
            position="未知",
            workYears="未知",
            教育水平="未知",
            年龄=None,
            sex="未知",
            school="未知"
        )
    
    async def _save_evaluation_result(
        self,
        user_id: UUID,
        file_info: Dict[str, Any],
        resume_text: str,
        ai_result: AIEvaluationResult,
        job_description_id: UUID,
        raw_response: str = "",
        conversation_id: Optional[UUID] = None
    ) -> ResumeEvaluation:
        """保存评价结果"""
        try:
            # 直接创建ResumeEvaluation对象
            evaluation = ResumeEvaluation(
                user_id=user_id,
                original_filename=file_info['filename'],
                file_path=file_info.get('file_path'),
                file_type=file_info['file_type'],
                file_size=file_info['file_size'],
                resume_content=resume_text,
                candidate_name=ai_result.name,
                candidate_position=ai_result.position,
                candidate_age=ai_result.年龄,
                candidate_gender=ai_result.sex,
                work_years=(self._parse_work_years_to_float(ai_result.workYears) or 0.0),
                education_level=ai_result.教育水平,
                school=ai_result.school,
                total_score=ai_result.total_score,
                evaluation_metrics=[metric.model_dump() for metric in ai_result.evaluation_metrics],
                job_description_id=job_description_id,
                conversation_id=str(conversation_id) if conversation_id else None,
                ai_response=raw_response
            )
            self.db.add(evaluation)
            await self.db.commit()
            await self.db.refresh(evaluation)
            
            return evaluation
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"保存评价结果失败: {e}")
            raise
    
    async def get_evaluation_history(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional['ResumeStatus'] = None
    ) -> List[ResumeEvaluation]:
        """获取评价历史"""
        try:
            query = select(ResumeEvaluation).where(ResumeEvaluation.user_id == user_id)
            
            # 添加状态过滤
            if status:
                query = query.where(ResumeEvaluation.status == status)
            
            query = query.order_by(ResumeEvaluation.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"获取评价历史失败: {e}")
            return []
    
    async def get_evaluation_by_id(
        self,
        evaluation_id: UUID,
        user_id: UUID
    ) -> Optional[ResumeEvaluation]:
        """根据ID获取评价结果"""
        try:
            result = await self.db.execute(
                select(ResumeEvaluation)
                .where(
                    ResumeEvaluation.id == evaluation_id,
                    ResumeEvaluation.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"获取评价结果失败: {e}")
            return None

    def _parse_work_years_to_float(self, text: Optional[str]) -> Optional[float]:
        """将工作年限字符串解析为数字（年）。支持格式如"3年"、"1.5年"、"1-3年"、"约2年"。
        - 解析到范围时取平均值；
        - 仅提取到一个数值时使用该数值；
        - 解析失败返回None。
        """
        if not text:
            return None
        s = str(text).strip().lower()
        # 常见非数值占位统一视为0（回退到调用处做 or 0.0）
        if s in {"未知", "不详", "none", "null", "n/a", "na", "--", "-", "", "应届", "应届生", "fresh"}:
            return 0.0
        # 匹配范围 "a-b" 或 "a – b"
        m_range = re.search(r"(\d+(?:\.\d+)?)\s*[\-~–—]\s*(\d+(?:\.\d+)?)", s)
        if m_range:
            try:
                a = float(m_range.group(1))
                b = float(m_range.group(2))
                return (a + b) / 2.0
            except Exception:
                pass
        # 提取第一个数字
        m_single = re.search(r"(\d+(?:\.\d+)?)", s)
        if m_single:
            try:
                return float(m_single.group(1))
            except Exception:
                return None
        return None