"""
Resume Parser Service for extracting text from various file formats
"""
import logging
import os
import hashlib
import tempfile
from typing import BinaryIO, Tuple, Optional
from uuid import UUID
import mimetypes

logger = logging.getLogger(__name__)


class ResumeParserService:
    """Service for parsing resume files and extracting text content"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.doc', '.docx'}
    SUPPORTED_MIME_TYPES = {
        'application/pdf',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """验证文件是否符合要求"""
        # 检查文件大小
        if file_size > self.max_file_size:
            return False, f"文件大小超过限制 ({self.max_file_size / 1024 / 1024}MB)"
        
        # 检查文件扩展名
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.SUPPORTED_EXTENSIONS:
            return False, f"不支持的文件格式。支持的格式: {', '.join(self.SUPPORTED_EXTENSIONS)}"
        
        return True, "文件验证通过"
    
    async def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """从文件中提取文本内容"""
        try:
            _, ext = os.path.splitext(filename.lower())
            
            if ext == '.txt':
                return await self._extract_from_txt(file_content)
            elif ext == '.pdf':
                return await self._extract_from_pdf(file_content)
            elif ext == '.doc':
                return await self._extract_from_doc(file_content)
            elif ext == '.docx':
                return await self._extract_from_docx(file_content)
            else:
                raise ValueError(f"不支持的文件格式: {ext}")
                
        except Exception as e:
            logger.error(f"提取文本内容失败: {e}")
            raise Exception(f"文件解析失败: {str(e)}")
    
    async def _extract_from_txt(self, file_content: bytes) -> str:
        """从TXT文件提取文本"""
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    return file_content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用utf-8并忽略错误
            return file_content.decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.error(f"TXT文件解析失败: {e}")
            raise
    
    async def _extract_from_pdf(self, file_content: bytes) -> str:
        """从PDF文件提取文本"""
        try:
            # 使用PyPDF2或pdfplumber库
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_content = []
            
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
            
            return '\n'.join(text_content)
            
        except ImportError:
            # 如果没有安装PyPDF2，尝试使用pdfplumber
            try:
                import pdfplumber
                import io
                
                with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                    text_content = []
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                    
                    return '\n'.join(text_content)
                    
            except ImportError:
                logger.error("PDF解析库未安装，请安装 PyPDF2 或 pdfplumber")
                raise Exception("PDF解析功能不可用，请联系管理员")
                
        except Exception as e:
            logger.error(f"PDF文件解析失败: {e}")
            raise Exception(f"PDF文件解析失败: {str(e)}")
    
    async def _extract_from_doc(self, file_content: bytes) -> str:
        """从DOC文件提取文本"""
        try:
            import docx2txt
            import io
            
            # 将字节内容写入临时文件
            with tempfile.NamedTemporaryFile(suffix='.doc', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # 使用docx2txt提取文本
                text = docx2txt.process(temp_file_path)
                return text
            finally:
                # 清理临时文件
                os.unlink(temp_file_path)
                
        except ImportError:
            logger.error("DOC解析库未安装，请安装 docx2txt")
            raise Exception("DOC文件解析功能不可用，请联系管理员")
            
        except Exception as e:
            logger.error(f"DOC文件解析失败: {e}")
            raise Exception(f"DOC文件解析失败: {str(e)}")
    
    async def _extract_from_docx(self, file_content: bytes) -> str:
        """从DOCX文件提取文本"""
        try:
            from docx import Document
            import io
            
            # 从字节流创建Document对象
            doc = Document(io.BytesIO(file_content))
            
            # 提取所有段落的文本
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # 提取表格中的文本
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_content.append(cell.text)
            
            return '\n'.join(text_content)
            
        except ImportError:
            logger.error("DOCX解析库未安装，请安装 python-docx")
            raise Exception("DOCX文件解析功能不可用，请联系管理员")
            
        except Exception as e:
            logger.error(f"DOCX文件解析失败: {e}")
            raise Exception(f"DOCX文件解析失败: {str(e)}")
    
    def get_file_info(self, filename: str, file_content: bytes) -> dict:
        """获取文件基本信息"""
        file_size = len(file_content)
        file_hash = hashlib.sha256(file_content).hexdigest()
        _, ext = os.path.splitext(filename.lower())
        
        return {
            'filename': filename,
            'file_type': ext.lstrip('.'),
            'file_size': file_size,
            'file_hash': file_hash,
            'mime_type': mimetypes.guess_type(filename)[0]
        }