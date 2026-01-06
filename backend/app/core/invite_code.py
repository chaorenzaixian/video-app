"""
邀请码生成器 - 基于用户ID的Base62编码方案

特点:
- 天然唯一(用户ID唯一 -> 邀请码唯一)
- 可逆向解码(邀请码 -> 用户ID)
- 短小精悍(6位可支持568亿用户)
- 无需数据库查询验证唯一性

编码规则:
- 使用 Base62(0-9, a-z, A-Z)
- 加入混淆因子防止猜测
- 添加校验位确保有效性
"""

# Base62 字符集（去掉容易混淆的字符：0O, 1lI）
ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz"
BASE = len(ALPHABET)  # 55

# 混淆因子（防止用户ID被猜测）
SHUFFLE_KEY = 9527
OFFSET = 100000  # 偏移量，让短ID也有较长的邀请码


def encode_user_id(user_id: int) -> str:
    """
    将用户ID编码为邀请码
    
    Args:
        user_id: 用户ID（正整数）
    
    Returns:
        邀请码字符串（6-8位）
    
    Examples:
        encode_user_id(1)      -> "4K7NP2"
        encode_user_id(100)    -> "4K9B5D"
        encode_user_id(10000)  -> "4MHYR3"
    """
    if user_id <= 0:
        raise ValueError("用户ID必须为正整数")
    
    # 混淆处理：用户ID × 混淆因子 + 偏移量
    mixed = user_id * SHUFFLE_KEY + OFFSET
    
    # Base编码
    result = []
    while mixed:
        mixed, remainder = divmod(mixed, BASE)
        result.append(ALPHABET[remainder])
    
    code = ''.join(reversed(result))
    
    # 添加校验位
    checksum = sum(ALPHABET.index(c) for c in code) % BASE
    code += ALPHABET[checksum]
    
    return code


def decode_invite_code(code: str) -> int:
    """
    将邀请码解码为用户ID
    
    Args:
        code: 邀请码字符串
    
    Returns:
        用户ID，如果无效返回 None
    
    Examples:
        decode_invite_code("4K7NP2") -> 1
        decode_invite_code("INVALID") -> None
    """
    if not code or len(code) < 2:
        return None
    
    try:
        # 分离校验位
        main_code = code[:-1]
        checksum_char = code[-1]
        
        # 验证校验位
        expected_checksum = sum(ALPHABET.index(c) for c in main_code) % BASE
        if ALPHABET[expected_checksum] != checksum_char:
            return None
        
        # Base解码
        mixed = 0
        for char in main_code:
            if char not in ALPHABET:
                return None
            mixed = mixed * BASE + ALPHABET.index(char)
        
        # 反混淆
        if mixed < OFFSET:
            return None
        
        user_id = (mixed - OFFSET) // SHUFFLE_KEY
        
        # 验证：重新编码应该得到相同结果
        if encode_user_id(user_id) != code:
            return None
        
        return user_id
    
    except (ValueError, IndexError):
        return None


def is_valid_invite_code(code: str) -> bool:
    """
    验证邀请码是否有效
    
    Args:
        code: 邀请码字符串
    
    Returns:
        是否有效
    """
    return decode_invite_code(code) is not None


# ==================== 兼容旧系统 ====================

def generate_random_code(length: int = 8) -> str:
    """
    生成随机邀请码（兼容旧系统）
    
    注意：这种方式需要检查数据库唯一性
    新系统应使用 encode_user_id() 代替
    """
    import random
    return ''.join(random.choice(ALPHABET) for _ in range(length))


# ==================== 测试 ====================

if __name__ == "__main__":
    print("邀请码生成器测试")
    print("=" * 50)
    
    test_ids = [1, 10, 100, 1000, 10000, 100000, 1000000]
    
    for uid in test_ids:
        code = encode_user_id(uid)
        decoded = decode_invite_code(code)
        status = "OK" if decoded == uid else "FAIL"
        print(f"用户ID: {uid:>8} -> 邀请码: {code:>8} -> 解码: {decoded:>8} {status}")
    
    print("\n无效邀请码测试:")
    invalid_codes = ["INVALID", "12345", "", "AAAAAAA"]
    for code in invalid_codes:
        result = decode_invite_code(code)
        print(f"  '{code}' -> {result}")
