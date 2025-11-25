"""
Resume Evaluation Service for AI-powered resume scoring
"""
import logging
import json
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
from app.services.llm_service import LLMService
from app.services.resume_parser_service import ResumeParserService
# 通过大模型进行JD匹配，而非embedding

logger = logging.getLogger(__name__)


class ResumeEvaluationService:
    """简历评价服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dify_service = DifyService()
        self.llm_service = LLMService()
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
            logger.info(f"开始解析文件: {filename}, 大小: {len(file_content)} 字节")
            
            # 检测文档类型
            doc_type = self.resume_parser._detect_document_type(file_content, filename)
            logger.info(f"检测到文档类型: {doc_type}")
            
            resume_text = await self.resume_parser.extract_text_from_file(file_content, filename)
            logger.info(f"文件解析完成，提取到文本长度: {len(resume_text) if resume_text else 0}")
            
            if not resume_text or not resume_text.strip():
                logger.error(f"文件解析失败 - 文件名: {filename}, 文档类型: {doc_type}, 提取内容: '{resume_text[:100] if resume_text else '空'}'")
                
                # 根据文档类型提供具体的错误提示
                if doc_type == 'scanned_pdf':
                    raise ValueError(f"无法从PDF文件 '{filename}' 中提取文本内容。该PDF可能是扫描文档，只包含图片而不包含可选择的文本。请使用包含可选择文本的PDF文件，或将简历内容直接复制粘贴到文本框中。")
                elif doc_type == 'image_heavy_doc':
                    raise ValueError(f"无法从Word文件 '{filename}' 中提取有效文本内容。该文档可能主要是图片或包含大量图片内容。请使用包含文本内容的Word文档，或将简历内容直接复制粘贴到文本框中。")
                else:
                    raise ValueError(f"无法从文件 '{filename}' 中提取到有效内容。请确保文件包含可读的文本内容，而不是扫描的图片或受保护的文档。支持PDF、Word(.doc/.docx)和纯文本(.txt)格式。")
            
            # 验证提取的内容质量
            validation_result = self.resume_parser._validate_extracted_content(resume_text, filename)
            if not validation_result['is_valid']:
                logger.warning(f"内容验证失败 - 文件名: {filename}, 原因: {validation_result['reason']}")
                
                if validation_result['reason'] == 'too_short':
                    logger.warning(f"文件 '{filename}' 内容过短，但仍继续处理")
                elif validation_result['reason'] == 'no_readable_text':
                    raise ValueError(f"文件 '{filename}' 提取的内容不包含可读文本。请确保上传的是包含文本内容的文档，而不是图片或扫描件。")
            else:
                logger.info(f"内容验证通过 - 文件名: {filename}, 文本长度: {validation_result['text_length']}, 中英文: {validation_result['has_chinese']}/{validation_result['has_english']}, 关键词: {validation_result['keyword_count']}")
            
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
                "workYears": ai_result.workYears,
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

    # 根据简历内容与投递邮件的主题匹配最合适的JD
    async def evaluate_resume_auto(
        self,
        user_id: UUID,
        file_content: bytes,
        filename: str,
        subject: str,
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """无JD输入时，自动匹配最合适的JD并进行评价"""
        # 解析文本（复用 evaluate_resume 的前置逻辑）
        is_valid, message = self.resume_parser.validate_file(filename, len(file_content))
        if not is_valid:
            raise ValueError(message)
        resume_text = await self.resume_parser.extract_text_from_file(file_content, filename)
        if not resume_text or not resume_text.strip():
            raise ValueError("无法从简历中提取有效文本")
        # 自动匹配 JD
        #拼接主题与邮件正文
        jd_id = await self._match_best_jd(subject=subject, resume_text= resume_text, create_by=str(user_id))
        if not jd_id:
            raise ValueError("未匹配到合适的职位描述")
        # 调用已有评价流程
        return await self.evaluate_resume(
            user_id=user_id,
            file_content=file_content,
            filename=filename,
            job_description_id=jd_id,
            conversation_id=conversation_id
        )

    async def _match_best_jd(self, subject:str ,resume_text: str,create_by: str) -> Optional[UUID]:
        """通过大模型服务判断最匹配的JD"""
        # 取所有 JD
        result = await self.db.execute(select(JobDescription).where(JobDescription.created_by == create_by))
        jds: List[JobDescription] = [row[0] for row in result.all()]
        if not jds:
            return None

        # 组装简洁的 JD 选项，避免超长提示
        jd_options = [
            {
                "id": str(jd.id),
                "title": jd.title
            }
            for jd in jds
        ]
        # 构造提示词
        prompt = (
            "你是一个职位匹配助手。如果候选人投递邮件的主题中包括了他要投递的岗位，则从给定的JD列表中选择最匹配的一项。"
            "如果投递邮件主题中没有要投递的岗位，则从候选人的简历内容，去从给定的JD列表中选择最匹配的一项。"
            "输出要求：不要给出匹配理由，直接输出jd id的值"
        )
        try:
            # 使用通用 LLM 服务进行匹配，而不是 Dify 工作流
            import json as _json
            jd_compact = _json.dumps(jd_options, ensure_ascii=False)[:12000]
            llm_input = (
                f"{prompt}\n\n候选人投递邮件主题：{subject}\n\n候选人简历：\n{resume_text[:8000]}\n\nJD列表(JSON)：\n{jd_compact}\n\n"
                " "
            )
            jd_id_str = await self.llm_service.generate_response(message=llm_input)
            print(f"LLM JD匹配结果：{jd_id_str}")
            if not jd_id_str:
                raise ValueError("匹配结果不包含jd_id")
            # 返回UUID
            for jd in jds:
                if str(jd.id) in jd_id_str:
                    print(f"LLM JD匹配成功：{jd.title}")
                    return jd.id
            return None
        except Exception as e:
            logger.error(f"LLM JD匹配失败，回退关键词匹配: {e}")
            # 回退：按关键词匹配（简单匹配）
            keywords = ["Java", "Python", "前端", "后端", "AI", "算法", "产品", "测试"]
            scores = []
            lower_text = resume_text.lower()
            for jd in jds:
                agg = " ".join([jd.title or "", jd.requirements or "", jd.skills or ""]).lower()
                score = sum(1 for kw in keywords if kw.lower() in lower_text and kw.lower() in agg)
                scores.append(score)
            import numpy as np
            best_idx = int(np.argmax(scores)) if scores else 0
            return jds[best_idx].id if jds else None
    
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
        """获取评价模型 - 使用评分标准的content字段作为评价依据"""
        try:
            # 查询与JD关联的评分标准
            result = await self.db.execute(
                select(ScoringCriteria).where(ScoringCriteria.job_description_id == jd_id)
            )
            criteria = result.scalar_one_or_none()

            # 返回默认模型
            return criteria.content
            
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
            
            # 调用Dify API (使用工作流类型2进行简历评价)
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
                logger.info(f"开始解析AI响应，原始文本长度: {len(answer_text)}")
                
                # 尝试直接解析JSON
                if answer_text.startswith('{') and answer_text.endswith('}'):
                    result_data = json.loads(answer_text)
                    logger.info(f"直接JSON解析成功，数据字段: {list(result_data.keys())}")
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
                # 处理年龄字段
                try:
                    age_value = int(result_data.get('age')) if result_data.get('age') else 0
                except (ValueError, TypeError):
                    age_value = 0  # 解析失败时默认设为0

                # 构建AI评价结果
                ai_result = AIEvaluationResult(
                    evaluation_metrics=metrics,
                    total_score=result_data.get('total_score', 0),
                    name=result_data.get('name', ''),
                    position=result_data.get('position', ''),
                    workYears=str(result_data.get('workYears', '')),
                    教育水平=result_data.get('education', ''),
                    年龄=age_value,
                    sex=result_data.get('sex', ''),
                    school=result_data.get('school', '')
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
                work_years=ai_result.workYears,
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
            query = select(ResumeEvaluation).where(ResumeEvaluation.user_id == user_id).order_by(ResumeEvaluation.total_score.desc())
            
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
