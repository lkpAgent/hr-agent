import re
import subprocess
from io import StringIO

import PyPDF2
import docx2txt
import olefile
from bs4 import BeautifulSoup
import fitz
from docx import Document
from oletools import oleobj, olevba


def extract_text_from_pdf(file_path: str):
    text = ''
    with open(file_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()
def extract_text_from_pdf2(file_path: str):
    """
        完全避免使用有问题的pdfminer低级API
        """
    text = ""

    # 方法1: 优先使用PyMuPDF (最可靠)
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text and page_text.strip():
                text += page_text + "\n"
        doc.close()
        if text.strip():
            print("PyMuPDF解析成功")
            # return text.strip()
        print(text)
    except Exception as e:
        print(f"PyMuPDF失败: {e}")


    # 方法3: 使用PyPDF2
    try:
        text = ''
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
        if text.strip():
            print("PyPDF2解析成功")
            return text.strip()
    except Exception as e:
        print(f"PyPDF2失败: {e}")

    # 方法4: 如果必须用pdfminer，只使用高级API
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(file_path)
        if text.strip():
            print("pdfminer高级API解析成功")
            return text.strip()
    except ImportError:
        print("pdfminer不可用，跳过")
    except Exception as e:
        print(f"pdfminer高级API失败: {e}")

    return ""
def extract_text_from_html(html_content: str) -> str:
    """从HTML内容中提取纯文本"""
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 移除脚本和样式标签
    for script in soup(["script", "style"]):
        script.decompose()

    # 获取纯文本
    text = soup.get_text()

    # 清理文本
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    return text


def extract_text_from_doc(file_path):
    """
    从 .doc 文件中提取文本内容，保持基本分段
    传入文件路径，返回文本内容字符串
    """
    try:
        # 检查文件是否为有效的 OLE 文档
        if not olefile.isOleFile(file_path):
            return None

        ole = olefile.OleFileIO(file_path)
        text_content = ""

        # 检查是否存在 WordDocument 流
        if ole.exists('WordDocument'):
            stream = ole.openstream('WordDocument')
            data = stream.read()
            text_content = parse_word_document_content(data)

        ole.close()
        return text_content if text_content.strip() else None

    except Exception as e:
        print(f"提取文本失败: {e}")
        return None


def parse_word_document_content(data):
    """
    解析 WordDocument 流的二进制数据，提取文本内容
    """
    text_parts = []

    # 尝试不同的编码和偏移量来解码文本
    encoding_attempts = [
        ('utf-16-le', 0x400),  # 最常见的编码和偏移
        ('utf-16-le', 0x200),
        ('utf-16-le', 0x600),
        ('utf-8', 0x400),
        ('latin-1', 0x400),
    ]

    for encoding, offset in encoding_attempts:
        try:
            if offset < len(data):
                decoded_text = data[offset:].decode(encoding, errors='ignore')
                cleaned_text = clean_and_preserve_paragraphs(decoded_text)
                if is_meaningful_text(cleaned_text):
                    return cleaned_text
        except:
            continue

    # 如果上述方法都失败，尝试二进制扫描
    return extract_text_by_binary_scan(data)


def clean_and_preserve_paragraphs(text):
    """
    清理文本并保持基本的分段结构
    """
    # 替换各种换行符为统一的换行符
    text = re.sub(r'\r\n', '\n', text)  # Windows 换行
    text = re.sub(r'\r', '\n', text)  # Mac 换行

    # 移除控制字符和特殊字符，但保留换行符
    text = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f]', ' ', text)

    # 合并过多的连续空白字符，但保留换行符
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # 清理每行的空白
        line = re.sub(r'[^\S\n]+', ' ', line.strip())
        if line and is_meaningful_line(line):
            cleaned_lines.append(line)

    # 重新组合文本，保留段落结构
    result = '\n'.join(cleaned_lines)

    # 确保文本以合理的分段结束
    return result.strip()


def is_meaningful_text(text):
    """
    判断文本是否有意义（包含足够的可读内容）
    """
    if len(text) < 50:  # 文本太短
        return False

    # 计算字母数字字符的比例
    alnum_count = sum(1 for c in text if c.isalnum())
    if alnum_count / len(text) < 0.1:  # 至少10%是字母数字
        return False

    # 检查是否包含常见单词
    common_words = ['的', '是', '在', '和', '有', '为', '了', '中', '与', '就',
                    'the', 'and', 'is', 'in', 'of', 'to', 'a', 'for', 'with', 'on']

    word_count = sum(1 for word in common_words if word in text.lower())
    return word_count >= 3  # 至少包含3个常见单词


def is_meaningful_line(line):
    """
    判断单行文本是否有意义
    """
    if len(line.strip()) < 2:  # 行太短
        return False

    # 计算字母数字字符比例
    alnum_count = sum(1 for c in line if c.isalnum())
    return alnum_count / len(line) > 0.2  # 至少20%是字母数字


def extract_text_by_binary_scan(data):
    """
    通过二进制扫描提取文本（备用方法）
    """
    text_parts = []
    current_word = []

    for byte in data:
        # ASCII 可打印字符
        if 32 <= byte <= 126:
            current_word.append(chr(byte))
        else:
            # 遇到非打印字符时，保存当前单词
            if len(current_word) >= 3:  # 至少3个字符才认为是单词
                word = ''.join(current_word)
                if any(c.isalpha() for c in word):  # 包含至少一个字母
                    text_parts.append(word)
            current_word = []

    # 处理最后一个单词
    if len(current_word) >= 3:
        word = ''.join(current_word)
        if any(c.isalpha() for c in word):
            text_parts.append(word)

    # 将单词组合成文本，每10个单词换行
    if text_parts:
        lines = []
        for i in range(0, len(text_parts), 10):
            lines.append(' '.join(text_parts[i:i + 10]))
        return '\n'.join(lines)

    return ""



def parse_doc_content(data):
    """
    解析 WordDocument 流的二进制数据
    参考: https://msdn.microsoft.com/en-us/library/cc313153(v=office.12).aspx
    """
    text_parts = []

    # 尝试不同的编码解析
    encodings = [ 'gbk','utf-8','utf-16-le', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            # 跳过文件头（通常是 0-512 字节）
            # 实际文本内容通常在特定偏移量开始
            decoded = data[512:].decode(encoding, errors='ignore')

            # 过滤出可打印字符和常见空白字符
            clean_text = ''.join(
                char for char in decoded
                if char.isprintable() or char in '\n\r\t '
            )

            # 移除过多的连续空白
            import re
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()

            if len(clean_text) > 10:  # 如果有足够长的文本
                text_parts.append(clean_text)
                break

        except UnicodeDecodeError:
            continue

    return ' '.join(text_parts) if text_parts else ""

def read_html_doc(file_path: str) -> str:
    """读取HTML格式的.doc文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 提取纯文本
        text = extract_text_from_html(html_content)
        return text

    except Exception as e:
        try:
            doc = Document(file_path)
            full_text = []
            for paragraph in doc.paragraphs:
                full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except Exception as e:
            print(f"docx Document读取失败: {e}")
            try:
                text = docx2txt.process(file_path)
                return text
            except Exception as e:
                print(f"docx2txt读取失败: {e}")
                try:
                    result = subprocess.run(
                        ['catdoc', '-w', file_path],  # -w 保留换行格式
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='ignore'
                    )

                    if result.returncode == 0:
                        return result.stdout
                    else:
                        print(f"catdoc 错误: {result.stderr}")
                        return None
                except Exception as e:
                    print(f"subprocess读取失败: {e}")
                    result = extract_text_from_doc(file_path)
                    return result


# 使用示例
file_path = r'E:\workspace-py\hr-agent\backend\智联招聘_王文江_软件测试_中文_20181119_1542607907603.doc'
file_path = r'E:\个人文件\安云数智.律为\项目相关\AI+设计\数据样本\new\老年人下肢外骨骼智能辅具设计研究.pdf'
file_path = r'E:\个人文件\安云数智.律为\项目相关\HRagent培训课件内容\阿奇霉素颗粒说明书用法用量.doc'
text = read_html_doc(file_path)

print("=== 提取的纯文本 ===")
print(text)