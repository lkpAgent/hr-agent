from typing import List


def _merge_short_chunks(chunks: List[str], min_length: int = 50, max_length: int = 1000) -> List[str]:
    """
    合并过短的文本块，优先选择合并后长度更短的方案

    Args:
        chunks: 文本块列表
        min_length: 最小长度阈值，小于此长度的块会被合并
        max_length: 最大长度阈值，合并后的块不能超过此长度

    Returns:
        合并后的文本块列表
    """
    if not chunks:
        return []

    merged_chunks = []
    i = 0

    while i < len(chunks):
        current_chunk = chunks[i]
        current_length = len(current_chunk)

        # 如果当前块长度足够，直接保留
        if current_length >= min_length:
            merged_chunks.append(current_chunk)
            i += 1
            continue

        # 当前块过短，需要合并
        # 计算与前面块合并后的长度
        prev_merged_length = float('inf')
        if merged_chunks:
            prev_merged_length = len(merged_chunks[-1]) + current_length + 1  # +1 是空格

        # 计算与后面块合并后的长度
        next_merged_length = float('inf')
        if i + 1 < len(chunks):
            next_merged_length = current_length + len(chunks[i + 1]) + 1  # +1 是空格

        # 检查合并是否超过最大长度限制
        can_merge_with_prev = (prev_merged_length <= max_length and merged_chunks)
        can_merge_with_next = (next_merged_length <= max_length and i + 1 < len(chunks))

        # 决策：选择合并后长度更短的方案
        if can_merge_with_prev and can_merge_with_next:
            # 前后都可以合并，选择合并后长度更短的
            if prev_merged_length <= next_merged_length:
                # 与前面的块合并
                merged_chunks[-1] += " " + current_chunk
                i += 1
            else:
                # 与后面的块合并，跳过下一个块
                chunks[i + 1] = current_chunk + " " + chunks[i + 1]
                i += 1

        elif can_merge_with_prev:
            # 只能与前面的块合并
            merged_chunks[-1] += " " + current_chunk
            i += 1

        elif can_merge_with_next:
            # 只能与后面的块合并，跳过下一个块
            chunks[i + 1] = current_chunk + " " + chunks[i + 1]
            i += 1

        else:
            # 无法合并，保留原样
            merged_chunks.append(current_chunk)
            i += 1

    return merged_chunks


def test_merge_short_chunks():
    """测试合并功能"""


    # 测试用例1: 正常情况
    chunks1 = [
        "这是一个很短的段落1"*10,  # 8个字符
        "这是一个很短的段落2" * 5,  # 8个字符
        "这是一个中等长度的段落段落"*5,  # 25个字符
        "这是一个很短的段落3" * 5,  # 8个字符
        "这是一个很短的段落4" * 5,  # 8个字符
        "这是一个很短的段落5" * 5,  # 8个字符
        "这是一个很长的段落6" * 50,  # 350个字符
        "这是一个很短的段落7" * 5,  # 8个字符
    ]

    result1 = _merge_short_chunks(chunks1, min_length=100, max_length=500)
    print("测试用例1结果:", result1)

    # 测试用例2: 多个短段落
    chunks2 = [
        "短1",
        "短2",
        "短3",
        "正常长度的段落" * 10,
        "短4"
    ]

    result2 = _merge_short_chunks(chunks2, min_length=10, max_length=100)
    print("测试用例2结果:", result2)

    # 测试用例3: 边界情况
    chunks3 = [
        "a" * 45,  # 45字符，小于min_length=50
        "b" * 500,  # 500字符，很大
        "c" * 45  # 45字符，小于min_length
    ]

    result3 = _merge_short_chunks(chunks3, min_length=50, max_length=600)
    print("测试用例3结果:", result3)


if __name__ == "__main__":
    test_merge_short_chunks()