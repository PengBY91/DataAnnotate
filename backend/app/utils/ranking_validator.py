"""
排序标注验证工具
"""
from typing import Tuple

def validate_ranking(ranking_str: str, expected_count: int = None) -> Tuple[bool, str]:
    """
    验证排序输入是否合法
    
    Args:
        ranking_str: 用户输入的排序字符串，如 "213"
        expected_count: 期望的元素数量，如果为None则自动从输入推断
    
    Returns:
        (是否合法, 错误消息)
    
    Examples:
        validate_ranking("213", 3) -> (True, "")
        validate_ranking("132", 3) -> (True, "")
        validate_ranking("124", 3) -> (False, "排序必须是1到3的排列")
        validate_ranking("113", 3) -> (False, "排序不能有重复数字")
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
    
    # 如果没有指定期望数量，从输入推断
    if expected_count is None:
        expected_count = len(numbers)
    
    # 检查长度是否匹配
    if len(numbers) != expected_count:
        return False, f"排序长度应为{expected_count}位"
    
    # 检查是否有重复
    if len(numbers) != len(set(numbers)):
        return False, "排序不能有重复数字"
    
    # 检查是否是1到n的排列
    expected_set = set(range(1, expected_count + 1))
    actual_set = set(numbers)
    
    if actual_set != expected_set:
        return False, f"排序必须是1到{expected_count}的排列"
    
    # 检查是否包含0或负数
    if any(n <= 0 for n in numbers):
        return False, "排序必须从1开始"
    
    return True, ""


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

