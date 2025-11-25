"""
Email utility module for reading emails from various email servers.
"""
import imaplib
import poplib
import smtplib
import email
from email.header import decode_header
from email.message import Message
from typing import List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailConfig:
    """
    Email configuration class
    """
    def __init__(self, host: str, port: int, username: str, password: str, 
                 use_ssl: bool = True, protocol: str = "IMAP"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.protocol = protocol.upper()  # IMAP or POP3


class EmailMessage:
    """
    Email message container
    """
    def __init__(self, subject: str, sender: str, recipients: List[str], 
                 date: datetime, body: str, html_body: Optional[str] = None,
                 attachments: Optional[List[dict]] = None):
        self.subject = subject
        self.sender = sender
        self.recipients = recipients
        self.date = date
        self.body = body
        self.html_body = html_body
        self.attachments = attachments or []


class EmailReader:
    """
    Utility class for reading emails from IMAP or POP3 servers
    """

    def __init__(self, config: EmailConfig):
        self.config = config
        self.connection = None

    def connect(self) -> bool:
        """
        Connect to the email server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.config.protocol == "IMAP":
                if self.config.use_ssl:
                    self.connection = imaplib.IMAP4_SSL(self.config.host, self.config.port)
                else:
                    self.connection = imaplib.IMAP4(self.config.host, self.config.port)
                self.connection.login(self.config.username, self.config.password)


            elif self.config.protocol == "POP3":
                if self.config.use_ssl:
                    self.connection = poplib.POP3_SSL(self.config.host, self.config.port)
                else:
                    self.connection = poplib.POP3(self.config.host, self.config.port)
                self.connection.user(self.config.username)
                self.connection.pass_(self.config.password)
            else:
                raise ValueError(f"Unsupported protocol: {self.config.protocol}")
            
            logger.info(f"Successfully connected to {self.config.protocol} server {self.config.host}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {str(e)}")
            return False

    def disconnect(self):
        """
        Disconnect from the email server
        """
        if self.connection:
            try:
                if self.config.protocol == "IMAP":
                    self.connection.close()
                    self.connection.logout()
                elif self.config.protocol == "POP3":
                    self.connection.quit()
                logger.info("Disconnected from email server")
            except Exception as e:
                logger.error(f"Error while disconnecting: {str(e)}")
            finally:
                self.connection = None

    def list_folders(self) -> List[str]:
        """
        List all folders/mailboxes (IMAP only)
        
        Returns:
            List[str]: List of folder names
        """
        if not self.connection or self.config.protocol != "IMAP":
            return []
        
        try:
            status, folders = self.connection.list()
            if status == "OK":
                folder_names = []
                for folder in folders:
                    # Parse folder name from response
                    folder_str = folder.decode('utf-8') if isinstance(folder, bytes) else folder
                    # Extract folder name (usually in quotes)
                    if '"' in folder_str:
                        folder_name = folder_str.split('"')[-2]
                    else:
                        folder_name = folder_str.split()[-1]
                    folder_names.append(folder_name)
                return folder_names
            return []
        except Exception as e:
            logger.error(f"Error listing folders: {str(e)}")
            return []

    def select_folder(self, folder: str = "INBOX") -> int:
        """
        Select a folder to read emails from (IMAP only)
        
        Args:
            folder (str): Folder name, defaults to INBOX
            
        Returns:
            int: Number of messages in the folder
        """
        if not self.connection or self.config.protocol != "IMAP":
            return 0
        
        try:
            status, msg_count = self.connection.select(folder)
            if status == "OK":
                count = int(msg_count[0]) if isinstance(msg_count[0], bytes) else int(msg_count[0])
                logger.info(f"Selected folder '{folder}' with {count} messages")
                return count
            return 0
        except Exception as e:
            logger.error(f"Error selecting folder '{folder}': {str(e)}")
            return 0

    def search_emails(self, criteria: list, charset: Optional[str] = "UTF-8") -> List[int]:
        """
        Search for emails by criteria (IMAP only)
        
        Args:
            criteria (str): Search criteria (e.g., "FROM user@example.com", "SUBJECT 'test'")
            
        Returns:
            List[int]: List of email IDs matching the criteria
        """
        if not self.connection or self.config.protocol != "IMAP":
            return []
        
        try:
            # 优先使用 UTF-8 字符集，失败则回退到默认
            status, messages = self.connection.search(charset, *criteria)
            if status == "OK":
                # Convert byte strings to integers
                msg_ids = messages[0].split()
                return [int(msg_id) for msg_id in msg_ids]
            return []
        except Exception as e:
            logger.warning(f"Search with charset '{charset}' failed: {str(e)}; retrying without charset")
            try:
                status, messages = self.connection.search(None, *criteria)
                if status == "OK":
                    msg_ids = messages[0].split()
                    return [int(msg_id) for msg_id in msg_ids]
                return []
            except Exception as e2:
                logger.error(f"Error searching emails with criteria '{criteria}': {str(e2)}")
                return []

    def get_email(self, msg_id: int) -> Optional[EmailMessage]:
        """
        Retrieve a specific email by ID
        
        Args:
            msg_id (int): Message ID
            
        Returns:
            EmailMessage: Email message object or None if failed
        """
        if not self.connection:
            return None
            
        try:
            if self.config.protocol == "IMAP":
                return self._get_imap_email(msg_id)
            elif self.config.protocol == "POP3":
                return self._get_pop3_email(msg_id)
            return None
        except Exception as e:
            logger.error(f"Error retrieving email {msg_id}: {str(e)}")
            return None

    def _get_imap_email(self, msg_id: int) -> Optional[EmailMessage]:
        """
        Retrieve an email using IMAP protocol
        
        Args:
            msg_id (int): Message ID
            
        Returns:
            EmailMessage: Email message object
        """
        status, msg_data = self.connection.fetch(str(msg_id), "(RFC822)")
        if status != "OK":
            return None
            
        raw_email = msg_data[0][1]
        email_message = email.message_from_bytes(raw_email)
        return self._parse_email_message(email_message)

    def _get_pop3_email(self, msg_id: int) -> Optional[EmailMessage]:
        """
        Retrieve an email using POP3 protocol
        
        Args:
            msg_id (int): Message ID (1-based index)
            
        Returns:
            EmailMessage: Email message object
        """
        # POP3 uses 1-based indexing
        msg_lines, octets = self.connection.retr(msg_id)
        raw_email = b'\n'.join(msg_lines)
        email_message = email.message_from_bytes(raw_email)
        return self._parse_email_message(email_message)

    def _parse_email_message(self, email_message: Message) -> EmailMessage:
        """
        Parse email message into EmailMessage object
        
        Args:
            email_message (Message): Raw email message
            
        Returns:
            EmailMessage: Parsed email message
        """
        # Decode subject
        subject = self._decode_header_value(email_message.get("Subject", ""))
        
        # Get sender
        sender = self._decode_header_value(email_message.get("From", ""))
        
        # Get recipients
        to_header = email_message.get("To", "")
        recipients = [self._decode_header_value(addr) for addr in to_header.split(",")] if to_header else []
        
        # Get date
        date_str = email_message.get("Date", "")
        try:
            date = datetime.strptime(date_str[:-6], "%a, %d %b %Y %H:%M:%S") if date_str else datetime.now()
        except:
            date = datetime.now()
        
        # Get body
        body = ""
        html_body = ""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header_value(filename)
                        payload = part.get_payload(decode=True)
                        attachments.append({
                            "filename": filename,
                            "content": payload,
                            "content_type": content_type
                        })
                    continue
                
                # Process text parts
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body = part.get_payload(decode=True).decode(charset, errors="ignore")
                    except Exception:
                        body = part.get_payload()
                elif content_type == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        html_body = part.get_payload(decode=True).decode(charset, errors="ignore")
                    except Exception:
                        html_body = part.get_payload()
        else:
            # Single part message
            content_type = email_message.get_content_type()
            charset = email_message.get_content_charset() or "utf-8"
            if content_type == "text/plain":
                try:
                    body = email_message.get_payload(decode=True).decode(charset, errors="ignore")
                except Exception:
                    body = email_message.get_payload()
            elif content_type == "text/html":
                try:
                    html_body = email_message.get_payload(decode=True).decode(charset, errors="ignore")
                except Exception:
                    html_body = email_message.get_payload()
        
        return EmailMessage(
            subject=subject,
            sender=sender,
            recipients=recipients,
            date=date,
            body=body,
            html_body=html_body,
            attachments=attachments
        )

    def _decode_header_value(self, header_value: str) -> str:
        """
        Decode email header value
        
        Args:
            header_value (str): Encoded header value
            
        Returns:
            str: Decoded header value
        """
        if not header_value:
            return ""
            
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_string += part.decode(encoding)
                    except Exception:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        return decoded_string

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Example usage:
if __name__ == "__main__":
    # IMAP example
    config = EmailConfig(
        host="imap.163.com",
        port=993,
        username="15084947675@163.com",
        # password="Pengsir2023",
        password="QHcFg32mFuEgMSVi",
        protocol="IMAP"
        #QHcFg32mFuEgMSVi
    )

    with EmailReader(config) as reader:
        # For IMAP, select folder first
        reader.select_folder("INBOX")
        criteria = ['FROM', '"kunpeng55@qq.com"']
        # Search for emails
        email_ids = reader.search_emails(criteria )

        # Get latest email
        if email_ids:
            latest_email = reader.get_email(email_ids[-1])
            if latest_email:
                print(f"Subject: {latest_email.subject}")
                print(f"From: {latest_email.sender}")
                print(f"Body: {latest_email.body[:100]}...")
