import asyncio
import sys
import os

# 获取项目根目录路径（假设项目根目录包含 app 和 script 文件夹）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.utils.document_utils import extract_text_from_file

if __name__ == '__main__':
    file_path = r'E:\workspace-py\hr-agent\backend\智联招聘_王文江_软件测试_中文_20181119_1542607907603.doc'
    # file_path = r'E:\个人文件\安云数智.律为\项目相关\AI+设计\数据样本\new\老年人下肢外骨骼智能辅具设计研究.pdf'
    # file_path = r'E:\个人文件\安云数智.律为\项目相关\AI+设计\数据样本\new\人体外骨骼柔性结构设计与仿真分析.pdf'
    # file_path = r'E:\个人文件\安云数智.律为\项目相关\HRagent培训课件内容\阿莫西林胶囊使用说明书.docx'
    # file_path = r'E:\个人文件\安云数智.律为\项目相关\HRagent培训课件内容\阿奇霉素颗粒说明书用法用量.doc'
    # file_path = r'E:\个人文件\安云数智.律为\项目相关\HRagent培训课件内容\李(1).docx'
    # file_path = r'E:\个人文件\安云数智.律为\项目相关\HRagent培训课件内容\湖南省水文条例_20250731.docx'
    # file_path = r'E:\个人文件\安云数智.律为\项目相关\HRagent培训课件内容\【测试工程师_长沙 7-10K】郑微微 5年.pdf'
    file_path = r'E:\个人文件\安云数智.律为\项目相关\AI知识竞赛\中国电子院E起创-“AI+”创新应用大赛报名表 -数字孪生下的利润预测模型0411 - 副本.doc'
    file_path = r'E:\个人文件\安云数智.律为\产品相关\HR智能体平台\智联招聘_张为1_大数据开发_中文_20181119_1542608584687.docx'
    text = asyncio.run(extract_text_from_file(file_path))
    print("=== 提取的纯文本 ===")
    print(text)