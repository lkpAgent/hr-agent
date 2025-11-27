"""
Service layer for recruitment email configuration and operations
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, UUID

from app.models.email_config import EmailConfig, EmailFetchLog
from app.models.resume_evaluation import ResumeEvaluation
from app.schemas.email_config import EmailConfigCreate, EmailConfigUpdate
from app.utils.email_utils import EmailConfig as ReaderConfig, EmailReader
from pathlib import Path
import os
from app.services.resume_evaluation_service import ResumeEvaluationService


class EmailConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, skip: int = 0, limit: int = 100) -> List[EmailConfig]:
        stmt = select(EmailConfig).offset(skip).limit(limit).order_by(EmailConfig.created_at.desc())
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def get(self, config_id: str) -> Optional[EmailConfig]:
        stmt = select(EmailConfig).where(EmailConfig.id == config_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: EmailConfigCreate,create_by: UUID) -> EmailConfig:
        config = EmailConfig(
            name=data.name,
            email=data.email,
            imap_server=data.imap_server,
            imap_port=data.imap_port,
            imap_ssl=data.imap_ssl,
            smtp_server=data.smtp_server,
            smtp_port=data.smtp_port,
            smtp_ssl=data.smtp_ssl,
            password=data.password,
            fetch_interval=data.fetch_interval,
            auto_fetch=data.auto_fetch,
            status=data.status,
            connection_status="unknown",
            created_by = create_by,
            updated_by = create_by
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update(self, config: EmailConfig, data: EmailConfigUpdate) -> EmailConfig:
        update_data = data.model_dump(exclude_unset=True)
        # Avoid setting empty password
        if "password" in update_data and not update_data.get("password"):
            update_data.pop("password")
        for k, v in update_data.items():
            setattr(config, k, v)
        await self.db.commit()
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete(self, config: EmailConfig) -> None:
        await self.db.delete(config)
        await self.db.commit()
        await self.db.flush()

    async def test_connection(self, config: EmailConfig, password: Optional[str] = None) -> bool:
        reader_cfg = ReaderConfig(
            host=config.imap_server,
            port=config.imap_port,
            username=config.email,
            password=password or config.password or "",
            use_ssl=config.imap_ssl,
            protocol="IMAP",
        )
        reader = EmailReader(reader_cfg)
        ok = reader.connect()
        reader.disconnect()
        config.connection_status = "connected" if ok else "error"
        await self.db.flush()
        return ok


class EmailFetchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def manual_fetch(self, config: EmailConfig) -> EmailFetchLog:
        log = EmailFetchLog(email_config_id=config.id, status="running")
        self.db.add(log)
        await self.db.flush()

        reader_cfg = ReaderConfig(
            host=config.imap_server,
            port=config.imap_port,
            username=config.email,
            password=config.password or "",
            use_ssl=config.imap_ssl,
            protocol="IMAP",
        )
        reader = EmailReader(reader_cfg)
        try:
            if not reader.connect():
                log.status = "failed"
                log.error_message = "无法连接到邮箱服务器"
                return log

            # Select INBOX and fetch last 50 emails
            reader.select_folder("INBOX")
            ids = reader.search_emails(["ALL"]) or []
            log.emails_found = len(ids)

            resumes = 0
            take = ids[-50:] if len(ids) > 50 else ids
            for msg_id in take:
                msg = reader.get_email(msg_id)
                if not msg:
                    continue
                for att in msg.attachments:
                    filename = (att.get("filename") or "").lower()
                    if filename.endswith((".pdf", ".doc", ".docx")):
                        resumes += 1

            log.resumes_extracted = resumes
            log.status = "success"
            config.last_fetch_at = datetime.utcnow()
            config.connection_status = "connected"
            return log
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            config.connection_status = "error"
            return log
        finally:
            reader.disconnect()

    async def list_logs(self, config_id: str, skip: int = 0, limit: int = 100) -> List[EmailFetchLog]:
        stmt = (
            select(EmailFetchLog)
            .where(EmailFetchLog.email_config_id == config_id)
            .offset(skip)
            .limit(limit)
            .order_by(EmailFetchLog.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def fetch_recent_attachments(
        self,
        config: EmailConfig,
        creeate_by: UUID,
        limit: int = 10,
        subject_keyword: list = None,
        output_dir: Optional[Path] = None,
    ) -> EmailFetchLog:
        """
        Fetch recent emails and download attachments when subject contains keyword.
        """
        log = EmailFetchLog(email_config_id=config.id, status="running")
        self.db.add(log)
        await self.db.flush()

        base_dir = output_dir or (Path(__file__).resolve().parent.parent.parent / "uploads" / "email_attachments" / str(config.id))
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            pass

        reader_cfg = ReaderConfig(
            host=config.imap_server,
            port=config.imap_port,
            username=config.email,
            password=config.password or "",
            use_ssl=config.imap_ssl,
            protocol="IMAP",
        )
        reader = EmailReader(reader_cfg)
        try:
            if not reader.connect():
                log.status = "failed"
                log.error_message = "无法连接到邮箱服务器"
                return log

            reader.select_folder("INBOX")
            ids = reader.search_emails(["ALL"]) or []
            if not ids:
                log.status = "success"
                log.emails_found = 0
                log.resumes_extracted = 0
                return log

            take = ids[-limit:] if len(ids) > limit else ids
            log.emails_found = len(take)
            resumes = 0
            evaluations = 0

            for msg_id in reversed(take):
                msg = reader.get_email(msg_id)
                if not msg:
                    continue
                subject = (msg.subject or "").lower()
                # 判断subject是否包含subject_keyword里的关键词
                # Set default value

                if subject_keyword and not any(keyword.lower() in subject for keyword in subject_keyword):
                    continue

                # save attachments
                for att in (msg.attachments or []):
                    fname = att.get("filename") or "attachment"
                    content = att.get("content")
                    if not content:
                        continue
                    # 去重：按原始文件名检查是否已存在评价记录
                    try:
                        print(f"检查 {fname} 是否已存在评价记录")
                        existing = await self.db.execute(select(ResumeEvaluation).where(ResumeEvaluation.user_id == creeate_by , ResumeEvaluation.original_filename == fname))
                        records = existing.scalars().first()
                        if records:
                            print(f"{fname} 已存在评价记录，跳过")
                            continue
                    except Exception as e:
                        print(f"检查 {fname} 是否已存在评价记录时出错：{e}")
                        pass
                    target_path = base_dir / fname
                    idx = 1
                    while target_path.exists():
                        stem = target_path.stem
                        suffix = target_path.suffix
                        target_path = base_dir / f"{stem}_{idx}{suffix}"
                        idx += 1
                    try:
                        with open(target_path, "wb") as f:
                            f.write(content)
                        resumes += 1
                        # 调用简历评价（自动匹配JD）
                        try:
                            ev_svc = ResumeEvaluationService(self.db)
                            user_id = config.created_by or None
                            if user_id:
                                await ev_svc.evaluate_resume_auto(user_id=user_id,subject=subject, file_content=content, filename=fname)
                                evaluations += 1
                        except Exception as e:
                            print(e)
                            pass
                    except Exception as e:
                        # skip write errors
                        print(e)
                        pass

            log.resumes_extracted = resumes
            # 可在日志中记录评估计数
            log.error_message = None
            log.status = "success"
            config.last_fetch_at = datetime.utcnow()
            config.connection_status = "connected"
            return log
        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            config.connection_status = "error"
            return log
        finally:
            reader.disconnect()
