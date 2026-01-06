"""
AI服务
集成OpenAI进行视频内容分析
"""
import base64
import httpx
from typing import Optional
from app.core.config import settings


class AIService:
    """AI服务"""
    
    @staticmethod
    async def analyze_video(
        title: str,
        description: Optional[str],
        thumbnail_path: Optional[str]
    ) -> dict:
        """
        分析视频内容
        返回摘要和标签
        """
        if not settings.OPENAI_API_KEY:
            return {"summary": None, "tags": None}
        
        # 构建提示词
        prompt = f"""
        请分析以下视频内容，并提供：
        1. 一段简短的摘要（不超过200字）
        2. 5-10个相关标签（用逗号分隔）
        
        视频标题：{title}
        视频描述：{description or '无'}
        
        请以JSON格式返回，格式如下：
        {{"summary": "摘要内容", "tags": "标签1,标签2,标签3"}}
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "你是一个视频内容分析助手"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # 解析JSON响应
                    import json
                    try:
                        data = json.loads(content)
                        return {
                            "summary": data.get("summary"),
                            "tags": data.get("tags")
                        }
                    except json.JSONDecodeError:
                        return {"summary": content, "tags": None}
                else:
                    print(f"OpenAI API错误: {response.status_code}")
                    return {"summary": None, "tags": None}
                    
        except Exception as e:
            print(f"AI分析异常: {e}")
            return {"summary": None, "tags": None}
    
    @staticmethod
    async def generate_video_description(title: str) -> str:
        """根据标题生成视频描述"""
        if not settings.OPENAI_API_KEY:
            return ""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {"role": "system", "content": "你是一个视频描述生成助手"},
                            {"role": "user", "content": f"请为标题为'{title}'的视频生成一段吸引人的描述，不超过100字"}
                        ],
                        "temperature": 0.8
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                return ""
        except Exception as e:
            print(f"生成描述异常: {e}")
            return ""
    
    @staticmethod
    async def moderate_content(content: str) -> dict:
        """内容审核"""
        if not settings.OPENAI_API_KEY:
            return {"flagged": False, "categories": {}}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/moderations",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={"input": content},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    moderation = result["results"][0]
                    return {
                        "flagged": moderation["flagged"],
                        "categories": moderation["categories"]
                    }
                return {"flagged": False, "categories": {}}
        except Exception as e:
            print(f"内容审核异常: {e}")
            return {"flagged": False, "categories": {}}









