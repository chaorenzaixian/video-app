#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接运行此文件启动后端服务
用法: python run.py
"""
import os
import sys

# 确保当前目录是 backend 目录
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

print(f"[*] Working directory: {backend_dir}")
print("[*] Starting VOD Platform Backend...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


