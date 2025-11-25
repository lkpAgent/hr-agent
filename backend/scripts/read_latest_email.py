import sys
import argparse
import os
from pathlib import Path
from sqlalchemy import create_engine, text

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.utils.email_utils import EmailConfig as ReaderConfig, EmailReader


def get_engine():
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(sync_url, echo=False, pool_pre_ping=True)


def get_email_config(engine, email_addr=None):
    with engine.connect() as conn:
        if email_addr:
            result = conn.execute(
                text(
                    """
                    SELECT id, name, email, imap_server, imap_port, imap_ssl,
                           smtp_server, smtp_port, smtp_ssl, password,
                           fetch_interval, auto_fetch, status, connection_status
                    FROM email_configs
                    WHERE email = :email
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                ),
                {"email": email_addr},
            )
        else:
            result = conn.execute(
                text(
                    """
                    SELECT id, name, email, imap_server, imap_port, imap_ssl,
                           smtp_server, smtp_port, smtp_ssl, password,
                           fetch_interval, auto_fetch, status, connection_status
                    FROM email_configs
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                )
            )
        row = result.fetchone()
        if not row:
            return None
        cols = result.keys()
        return dict(zip(cols, row))


def read_latest_email(cfg, from_email=None, subject=None, output_dir=None):
    reader_cfg = ReaderConfig(
        host=cfg["imap_server"],
        port=int(cfg["imap_port"] or 993),
        username=cfg["email"],
        password=cfg.get("password") or "",
        use_ssl=bool(cfg.get("imap_ssl", True)),
        protocol="IMAP",
    )
    reader = EmailReader(reader_cfg)
    if not reader.connect():
        print("连接邮箱失败")
        return 1
    try:
        reader.select_folder("INBOX")
        all_ids = reader.search_emails(["ALL"]) or []
        if not all_ids:
            print("没有邮件")
            return 0
        take = all_ids[-200:] if len(all_ids) > 200 else all_ids
        base_dir = Path(output_dir) if output_dir else (Path(__file__).parent.parent / "downloads" / "emails")
        os.makedirs(base_dir, exist_ok=True)
        saved_attachments = 0
        for mid in take:
            target_msg = reader.get_email(mid)
            print("主题:", target_msg.subject)
            print("发件人:", target_msg.sender)
            print("时间:", target_msg.date.isoformat())
            body = target_msg.body.strip() if target_msg.body else (target_msg.html_body or "")
            snippet = body[:1000]
            print("内容:\n", snippet)
            for att in (target_msg.attachments or []):
                fname = att.get("filename") or "attachment"
                content = att.get("content")
                if not content:
                    continue
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
                    saved_attachments += 1
                    print("保存附件:", str(target_path))
                except Exception:
                    pass

        print("保存附件数:", saved_attachments)

        return 0
    finally:
        reader.disconnect()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", dest="email", default=None)
    parser.add_argument("--from-email", dest="from_email", default=None)
    parser.add_argument("--subject", dest="subject", default=None)
    parser.add_argument("--output-dir", dest="output_dir", default=None)
    args = parser.parse_args()
    engine = get_engine()
    cfg = get_email_config(engine, args.email)
    if not cfg:
        print("未找到邮箱配置")
        sys.exit(1)
    code = read_latest_email(cfg, from_email=args.from_email, subject=args.subject, output_dir=args.output_dir)
    sys.exit(code)


if __name__ == "__main__":
    main()
