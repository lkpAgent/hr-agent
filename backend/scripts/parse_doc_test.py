import re
from typing import Optional

import olefile
import struct

from bs4 import BeautifulSoup


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


def read_html_doc(file_path: str) -> str:
    """读取HTML格式的.doc文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 提取纯文本
        text = extract_text_from_html(html_content)
        return text

    except Exception as e:
        return f"读取失败: {e}"


# 使用示例
file_path = r'E:\workspace-py\hr-agent\backend\智联招聘_王文江_软件测试_中文_20181119_1542607907603.doc'
html_content = read_html_doc(file_path)

print("=== 提取的纯文本 ===")
print(html_content)