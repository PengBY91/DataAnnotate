"""
排序标注验证工具
"""
from typing import Tuple, Optional

def validate_ranking(ranking_str: str, max_range: Optional[int] = None) -> Tuple[bool, str]:
    """
    验证排序输入是否合法
    
    Args:
        ranking_str: 用户输入的排序字符串，如 "213" 或 "21"
        max_range: 最大排序范围（可选），如果提供则检查元素数量不超过此值
    
    Returns:
        (是否合法, 错误消息)
    
    规则：
    1. 只能包含数字
    2. 不能有重复数字
    3. 必须是从1开始的连续数字的排列（如：123、21、132等）
    4. 如果提供max_range，排序长度不能超过max_range
    
    Examples:
        validate_ranking("213", 3) -> (True, "有效")  # 3个元素，1-3的排列
        validate_ranking("21", 3) -> (True, "有效")   # 2个元素，1-2的排列，小于max_range
        validate_ranking("132", 5) -> (True, "有效")  # 3个元素，1-3的排列，小于max_range
        validate_ranking("124", 3) -> (False, "排序必须是从1开始的连续数字，不能跳过") # 缺少2
        validate_ranking("113", 3) -> (False, "排序不能有重复数字")
        validate_ranking("12345", 3) -> (False, "排序长度不能超过最大范围3") # 超过max_range
    """
    # 检查是否为空
    if not ranking_str or not ranking_str.strip():
        return False, "排序不能为空"
    
    ranking_str = ranking_str.strip()
    
    # 检查是否只包含数字
    if not ranking_str.isdigit():
        return False, "排序只能包含数字"
    
    # 转换为数字列表
    try:
        numbers = [int(d) for d in ranking_str]
    except ValueError:
        return False, "排序格式错误"
    
    # 获取实际的排序长度
    actual_length = len(numbers)
    
    # 如果提供了max_range，检查长度不超过
    if max_range is not None and actual_length > max_range:
        return False, f"排序长度不能超过最大范围{max_range}"
    
    # 检查长度至少为1
    if actual_length < 1:
        return False, "排序至少需要1个元素"
    
    # 检查是否有重复
    if len(numbers) != len(set(numbers)):
        return False, "排序不能有重复数字"
    
    # 检查是否包含0或负数
    if any(n <= 0 for n in numbers):
        return False, "排序必须从1开始的正整数"
    
    # 核心验证：必须是从1到actual_length的排列（不能跳过数字）
    # 例如：213是1-3的排列（合法），124不是1-3的排列（缺少2，非法）
    expected_set = set(range(1, actual_length + 1))
    actual_set = set(numbers)
    
    if actual_set != expected_set:
        missing = expected_set - actual_set
        extra = actual_set - expected_set
        
        if missing:
            return False, f"排序必须是从1开始的连续数字，不能跳过。缺少: {sorted(missing)}"
        if extra:
            max_allowed = actual_length
            return False, f"排序包含超出范围的数字: {sorted(extra)}，最大应为{max_allowed}"
        
        return False, f"排序必须是1到{actual_length}的排列"
    
    return True, "有效"


def format_ranking(ranking_str: str) -> list:
    """
    将排序字符串转换为列表
    
    Args:
        ranking_str: 如 "213"
    
    Returns:
        [2, 1, 3]
    """
    return [int(d) for d in ranking_str.strip()]


def ranking_to_string(ranking_list: list) -> str:
    """
    将排序列表转换为字符串
    
    Args:
        ranking_list: [2, 1, 3]
    
    Returns:
        "213"
    """
    return ''.join(str(n) for n in ranking_list)

