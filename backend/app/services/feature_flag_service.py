"""
功能开关/AB测试/灰度发布 服务
"""
import hashlib
import json
from typing import Any, Optional, Dict, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.redis import RedisCache


class FeatureFlagService:
    """功能开关服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_ttl = 60  # 缓存60秒
    
    async def get_flag_value(
        self,
        flag_key: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取用户的功能开关值
        
        user_context 示例:
        {
            "user_id": 12345,
            "vip_level": 3,
            "device": "ios",
            "app_version": "2.1.0",
            "region": "cn"
        }
        """
        from app.models.feature_flag import FeatureFlag, FeatureRule
        
        # 1. 尝试从缓存获取配置
        cache_key = f"feature_flag:{flag_key}"
        cached = await RedisCache.get(cache_key)
        
        if cached:
            flag_data = json.loads(cached)
        else:
            # 从数据库获取
            result = await self.db.execute(
                select(FeatureFlag).where(FeatureFlag.key == flag_key)
            )
            flag = result.scalar_one_or_none()
            
            if not flag:
                return {"enabled": False, "reason": "flag_not_found"}
            
            flag_data = {
                "id": flag.id,
                "key": flag.key,
                "flag_type": flag.flag_type,
                "is_enabled": flag.is_enabled,
                "default_value": flag.default_value,
                "variants": flag.variants,
                "rollout_percentage": flag.rollout_percentage,
                "whitelist_user_ids": flag.whitelist_user_ids,
                "start_time": flag.start_time.isoformat() if flag.start_time else None,
                "end_time": flag.end_time.isoformat() if flag.end_time else None,
            }
            
            # 缓存配置
            await RedisCache.set(cache_key, json.dumps(flag_data), expire=self.cache_ttl)
        
        # 2. 检查总开关
        if not flag_data.get("is_enabled"):
            return json.loads(flag_data.get("default_value", '{"enabled": false}'))
        
        # 3. 检查时间范围
        now = datetime.utcnow()
        start_time = flag_data.get("start_time")
        end_time = flag_data.get("end_time")
        
        if start_time:
            if now < datetime.fromisoformat(start_time):
                return json.loads(flag_data.get("default_value", '{"enabled": false}'))
        if end_time:
            if now > datetime.fromisoformat(end_time):
                return json.loads(flag_data.get("default_value", '{"enabled": false}'))
        
        # 4. 检查白名单
        user_id = user_context.get("user_id")
        whitelist = flag_data.get("whitelist_user_ids")
        if whitelist and user_id:
            try:
                whitelist_ids = json.loads(whitelist)
                if user_id in whitelist_ids:
                    return {"enabled": True, "reason": "whitelist"}
            except:
                pass
        
        # 5. 按类型处理
        flag_type = flag_data.get("flag_type", "boolean")
        
        if flag_type == "boolean":
            return {"enabled": True}
            
        elif flag_type == "percentage":
            return await self._percentage_rollout(
                flag_key,
                user_id,
                flag_data.get("rollout_percentage", 0)
            )
            
        elif flag_type == "ab_test":
            return await self._ab_test_assignment(
                flag_key,
                user_id,
                flag_data.get("variants"),
                user_context
            )
            
        elif flag_type == "rule":
            return await self._check_rules(
                flag_data.get("id"),
                user_context
            )
        
        return json.loads(flag_data.get("default_value", '{"enabled": false}'))
    
    async def _percentage_rollout(
        self,
        flag_key: str,
        user_id: int,
        percentage: int
    ) -> Dict:
        """
        百分比灰度分配
        使用一致性哈希确保同一用户始终分到同一组
        """
        if not user_id:
            return {"enabled": False, "reason": "no_user_id"}
        
        # 使用 MD5 哈希保证分配的一致性和均匀性
        hash_input = f"{flag_key}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_bucket = hash_value % 100  # 0-99
        
        enabled = user_bucket < percentage
        
        return {
            "enabled": enabled,
            "bucket": user_bucket,
            "threshold": percentage,
            "reason": "percentage_rollout"
        }
    
    async def _ab_test_assignment(
        self,
        flag_key: str,
        user_id: int,
        variants_json: str,
        user_context: Dict
    ) -> Dict:
        """
        AB测试分流
        
        variants 示例:
        [
            {"name": "control", "value": {"button_color": "blue"}, "weight": 50},
            {"name": "treatment_a", "value": {"button_color": "green"}, "weight": 30},
            {"name": "treatment_b", "value": {"button_color": "red"}, "weight": 20}
        ]
        """
        if not user_id:
            return {"variant": "control", "value": {}, "reason": "no_user_id"}
        
        try:
            variants = json.loads(variants_json) if variants_json else []
        except:
            variants = []
        
        if not variants:
            return {"variant": "control", "value": {}, "reason": "no_variants"}
        
        # 检查用户是否已有分配（保证一致性）
        cache_key = f"ab:{flag_key}:{user_id}"
        cached = await RedisCache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 计算用户桶位
        hash_input = f"{flag_key}:ab:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        user_bucket = hash_value % 100
        
        # 根据权重分配变体
        cumulative_weight = 0
        assigned_variant = variants[0]  # 默认第一个
        
        for variant in variants:
            cumulative_weight += variant.get("weight", 0)
            if user_bucket < cumulative_weight:
                assigned_variant = variant
                break
        
        result = {
            "enabled": True,
            "variant": assigned_variant["name"],
            "value": assigned_variant.get("value", {}),
            "bucket": user_bucket,
            "reason": "ab_test"
        }
        
        # 缓存分配结果（24小时）
        await RedisCache.set(cache_key, json.dumps(result), expire=86400)
        
        # 记录曝光
        await self._record_exposure(
            flag_key,
            user_id,
            assigned_variant["name"],
            user_context
        )
        
        return result
    
    async def _check_rules(
        self,
        flag_id: int,
        user_context: Dict
    ) -> Dict:
        """规则匹配"""
        from app.models.feature_flag import FeatureRule
        
        result = await self.db.execute(
            select(FeatureRule)
            .where(FeatureRule.flag_id == flag_id)
            .where(FeatureRule.is_enabled == True)
            .order_by(FeatureRule.priority)
        )
        rules = result.scalars().all()
        
        for rule in rules:
            if self._evaluate_conditions(rule.conditions, user_context):
                return json.loads(rule.value)
        
        return {"enabled": False, "reason": "no_rule_matched"}
    
    def _evaluate_conditions(
        self,
        conditions_json: str,
        context: Dict
    ) -> bool:
        """
        评估条件表达式
        
        支持的操作符:
        - eq: 等于
        - neq: 不等于
        - gt/gte: 大于/大于等于
        - lt/lte: 小于/小于等于
        - in: 在列表中
        - not_in: 不在列表中
        - contains: 包含
        """
        try:
            conditions = json.loads(conditions_json)
        except:
            return False
        
        for field, operators in conditions.items():
            field_value = context.get(field)
            
            if not isinstance(operators, dict):
                # 简写形式：{"user_id": 123} 等同于 {"user_id": {"eq": 123}}
                if field_value != operators:
                    return False
                continue
            
            for op, expected in operators.items():
                if op == "eq" and field_value != expected:
                    return False
                elif op == "neq" and field_value == expected:
                    return False
                elif op == "gt" and not (field_value is not None and field_value > expected):
                    return False
                elif op == "gte" and not (field_value is not None and field_value >= expected):
                    return False
                elif op == "lt" and not (field_value is not None and field_value < expected):
                    return False
                elif op == "lte" and not (field_value is not None and field_value <= expected):
                    return False
                elif op == "in" and field_value not in expected:
                    return False
                elif op == "not_in" and field_value in expected:
                    return False
                elif op == "contains" and expected not in str(field_value or ""):
                    return False
        
        return True
    
    async def _record_exposure(
        self,
        flag_key: str,
        user_id: int,
        variant_name: str,
        user_context: Dict
    ):
        """记录实验曝光"""
        from app.models.feature_flag import ExperimentExposure
        
        exposure = ExperimentExposure(
            flag_key=flag_key,
            user_id=user_id,
            variant_name=variant_name,
            device_type=user_context.get("device"),
            app_version=user_context.get("app_version")
        )
        self.db.add(exposure)
        # 不立即提交，让调用方控制事务
    
    async def track_event(
        self,
        flag_key: str,
        user_id: int,
        event_type: str,
        event_value: float = None,
        event_data: Dict = None
    ):
        """追踪实验事件"""
        from app.models.feature_flag import ExperimentEvent
        
        # 获取用户当前的变体分配
        cache_key = f"ab:{flag_key}:{user_id}"
        cached = await RedisCache.get(cache_key)
        
        variant_name = "unknown"
        if cached:
            try:
                data = json.loads(cached)
                variant_name = data.get("variant", "unknown")
            except:
                pass
        
        event = ExperimentEvent(
            flag_key=flag_key,
            user_id=user_id,
            variant_name=variant_name,
            event_type=event_type,
            event_value=event_value,
            event_data=json.dumps(event_data) if event_data else None
        )
        self.db.add(event)
        await self.db.commit()
    
    async def get_all_flags(
        self,
        user_context: Dict[str, Any],
        flag_keys: List[str] = None
    ) -> Dict[str, Any]:
        """批量获取功能开关"""
        from app.models.feature_flag import FeatureFlag
        
        query = select(FeatureFlag).where(FeatureFlag.is_enabled == True)
        if flag_keys:
            query = query.where(FeatureFlag.key.in_(flag_keys))
        
        result = await self.db.execute(query)
        flags = result.scalars().all()
        
        results = {}
        for flag in flags:
            results[flag.key] = await self.get_flag_value(flag.key, user_context)
        
        return results
    
    @staticmethod
    async def invalidate_cache(flag_key: str):
        """使缓存失效"""
        cache_key = f"feature_flag:{flag_key}"
        await RedisCache.delete(cache_key)


