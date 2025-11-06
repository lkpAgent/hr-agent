from typing import Dict,List

def allocate_question_scores(total_score: int, counts: Dict[str, int]) -> Dict[str, List[int]]:
    # 仅支持三种题型：单选题、多选题、简答题
    weights = {
        "single_choice": 2,
        "multiple_choice": 3,
        "short_answer": 5,
    }

    # 初始化每题分值列表
    scores: Dict[str, List[int]] = {
        t: [0] * max(0, counts.get(t, 0)) for t in ["single_choice", "multiple_choice", "short_answer"]
    }

    # 计算加权题量总和
    weighted_total = 0
    for t, w in weights.items():
        weighted_total += counts.get(t, 0) * w

    if weighted_total <= 0 or total_score <= 0:
        return scores

    # 基础单位分和剩余分
    base_unit = total_score // weighted_total
    remainder = total_score % weighted_total

    # 先按权重为每题分配基础分值
    for t, w in weights.items():
        c = counts.get(t, 0)
        if c > 0:
            base_per_question = w * base_unit
            scores[t] = [base_per_question] * c

    # 将剩余分数依次分配给“最后几题”：先简答题末尾，后多选题末尾，再单选题末尾
    distribution_order = ["short_answer", "multiple_choice", "single_choice"]
    while remainder > 0:
        allocated_this_round = False
        for t in distribution_order:
            arr = scores.get(t, [])
            # 从末尾开始为每题加 1 分，直到该类型题目遍历完或剩余分数为 0
            for i in range(len(arr) - 1, -1, -1):
                if remainder <= 0:
                    break
                arr[i] += 1
                remainder -= 1
                allocated_this_round = True
        if not allocated_this_round:
            # 没有任何题目可分配（例如题量为 0），避免死循环
            break

    return scores

if __name__ == '__main__':
    total_score = 100
    counts = {'multiple_choice': 10, 'short_answer': 5, 'single_choice': 4}
    scores = allocate_question_scores(total_score, counts)
    print(scores)