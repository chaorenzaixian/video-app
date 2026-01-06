# -*- coding: utf-8 -*-
"""
AI美学评分服务
使用预训练模型评估图像美学质量
"""
import os
from typing import Optional, Dict
import numpy as np

# 全局变量，延迟加载模型
_model = None
_transform = None
_device = None
_model_loaded = False
_load_attempted = False


def _load_model():
    """延迟加载模型（首次使用时）"""
    global _model, _transform, _device, _model_loaded, _load_attempted
    
    if _load_attempted:
        return _model_loaded
    
    _load_attempted = True
    
    try:
        import torch
        import torchvision.transforms as transforms
        import torchvision.models as models
        
        print("🔄 正在加载AI美学评分模型...")
        
        # 使用CPU
        _device = torch.device("cpu")
        
        # 加载预训练的 MobileNetV2（轻量级，CPU友好）
        _model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
        _model.eval()
        _model.to(_device)
        
        # 图像预处理
        _transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        _model_loaded = True
        print("✅ AI美学评分模型加载完成")
        return True
        
    except Exception as e:
        print(f"[WARN] AI美学模型加载失败: {e}")
        _model_loaded = False
        return False


def analyze_aesthetic(image_path: str) -> Dict:
    """
    分析图像美学质量
    
    返回:
        {
            "aesthetic_score": 0-100,  # 美学评分
            "composition_score": 0-100,  # 构图评分
            "color_harmony": 0-100,  # 色彩和谐度
            "clarity_score": 0-100,  # 清晰度评分
            "feature_richness": 0-100,  # 特征丰富度
        }
    """
    result = {
        "aesthetic_score": 50,
        "composition_score": 50,
        "color_harmony": 50,
        "clarity_score": 50,
        "feature_richness": 50,
    }
    
    try:
        import cv2
        
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            return result
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 1. 基础图像分析（OpenCV）
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 清晰度（Laplacian方差）
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        clarity_score = min(100, laplacian_var / 5)  # 归一化到0-100
        
        # 色彩和谐度（颜色分布的均匀性）
        h_std = np.std(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        color_harmony = min(100, (h_std * 0.5 + s_mean * 0.3))
        
        # 2. 构图分析
        composition_score = _analyze_composition(img)
        
        # 3. AI特征分析（如果模型可用）
        feature_richness = 50
        ai_aesthetic = 50
        
        if _load_model():
            try:
                import torch
                
                # 提取特征
                input_tensor = _transform(img_rgb).unsqueeze(0).to(_device)
                
                with torch.no_grad():
                    features = _model.features(input_tensor)
                    # 特征丰富度（特征激活的多样性）
                    feature_std = features.std().item()
                    feature_mean = features.mean().item()
                    feature_richness = min(100, (feature_std * 100 + abs(feature_mean) * 20))
                    
                    # 基于特征的美学评分
                    # 高层特征的激活强度与美学相关
                    pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1)
                    top_activations = torch.topk(pooled.flatten(), k=50).values.mean().item()
                    ai_aesthetic = min(100, top_activations * 15)
                    
            except Exception as e:
                print(f"AI特征提取失败: {e}")
        
        # 4. 综合美学评分
        aesthetic_score = (
            clarity_score * 0.25 +      # 清晰度 25%
            color_harmony * 0.20 +      # 色彩 20%
            composition_score * 0.25 +   # 构图 25%
            feature_richness * 0.15 +    # 特征丰富度 15%
            ai_aesthetic * 0.15          # AI评分 15%
        )
        
        result = {
            "aesthetic_score": round(aesthetic_score, 1),
            "composition_score": round(composition_score, 1),
            "color_harmony": round(color_harmony, 1),
            "clarity_score": round(clarity_score, 1),
            "feature_richness": round(feature_richness, 1),
        }
        
    except Exception as e:
        print(f"美学分析失败: {e}")
    
    return result


def _analyze_composition(img) -> float:
    """
    分析图像构图质量
    基于三分法则和黄金分割
    """
    try:
        import cv2
        
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检测边缘
        edges = cv2.Canny(gray, 50, 150)
        
        # 三分法则区域（关键点位置）
        thirds_x = [w // 3, 2 * w // 3]
        thirds_y = [h // 3, 2 * h // 3]
        
        # 计算关键区域的边缘密度
        roi_scores = []
        roi_size = min(w, h) // 6
        
        for x in thirds_x:
            for y in thirds_y:
                x1 = max(0, x - roi_size)
                x2 = min(w, x + roi_size)
                y1 = max(0, y - roi_size)
                y2 = min(h, y + roi_size)
                
                roi = edges[y1:y2, x1:x2]
                density = np.sum(roi > 0) / roi.size if roi.size > 0 else 0
                roi_scores.append(density)
        
        # 中心区域的重要性
        center_x, center_y = w // 2, h // 2
        center_roi = edges[
            center_y - roi_size:center_y + roi_size,
            center_x - roi_size:center_x + roi_size
        ]
        center_density = np.sum(center_roi > 0) / center_roi.size if center_roi.size > 0 else 0
        
        # 构图评分：三分点有内容 + 中心适度
        thirds_score = np.mean(roi_scores) * 200
        center_score = min(50, center_density * 100)  # 中心不能太满
        
        composition = min(100, thirds_score + center_score)
        
        return composition
        
    except Exception as e:
        return 50


def get_best_frame(frame_paths: list) -> tuple:
    """
    从多个候选帧中选择美学评分最高的
    
    Args:
        frame_paths: 候选帧图片路径列表
    
    Returns:
        (最佳帧路径, 评分详情)
    """
    best_path = frame_paths[0] if frame_paths else None
    best_score = 0
    best_analysis = {}
    
    for path in frame_paths:
        analysis = analyze_aesthetic(path)
        score = analysis.get("aesthetic_score", 0)
        
        if score > best_score:
            best_score = score
            best_path = path
            best_analysis = analysis
    
    return best_path, best_analysis




# -*- coding: utf-8 -*-
"""
AI美学评分服务
使用预训练模型评估图像美学质量
"""
import os
from typing import Optional, Dict
import numpy as np

# 全局变量，延迟加载模型
_model = None
_transform = None
_device = None
_model_loaded = False
_load_attempted = False


def _load_model():
    """延迟加载模型（首次使用时）"""
    global _model, _transform, _device, _model_loaded, _load_attempted
    
    if _load_attempted:
        return _model_loaded
    
    _load_attempted = True
    
    try:
        import torch
        import torchvision.transforms as transforms
        import torchvision.models as models
        
        print("🔄 正在加载AI美学评分模型...")
        
        # 使用CPU
        _device = torch.device("cpu")
        
        # 加载预训练的 MobileNetV2（轻量级，CPU友好）
        _model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
        _model.eval()
        _model.to(_device)
        
        # 图像预处理
        _transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        _model_loaded = True
        print("✅ AI美学评分模型加载完成")
        return True
        
    except Exception as e:
        print(f"⚠️ AI美学模型加载失败: {e}")
        _model_loaded = False
        return False


def analyze_aesthetic(image_path: str) -> Dict:
    """
    分析图像美学质量
    
    返回:
        {
            "aesthetic_score": 0-100,  # 美学评分
            "composition_score": 0-100,  # 构图评分
            "color_harmony": 0-100,  # 色彩和谐度
            "clarity_score": 0-100,  # 清晰度评分
            "feature_richness": 0-100,  # 特征丰富度
        }
    """
    result = {
        "aesthetic_score": 50,
        "composition_score": 50,
        "color_harmony": 50,
        "clarity_score": 50,
        "feature_richness": 50,
    }
    
    try:
        import cv2
        
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            return result
        
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 1. 基础图像分析（OpenCV）
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 清晰度（Laplacian方差）
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        clarity_score = min(100, laplacian_var / 5)  # 归一化到0-100
        
        # 色彩和谐度（颜色分布的均匀性）
        h_std = np.std(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        color_harmony = min(100, (h_std * 0.5 + s_mean * 0.3))
        
        # 2. 构图分析
        composition_score = _analyze_composition(img)
        
        # 3. AI特征分析（如果模型可用）
        feature_richness = 50
        ai_aesthetic = 50
        
        if _load_model():
            try:
                import torch
                
                # 提取特征
                input_tensor = _transform(img_rgb).unsqueeze(0).to(_device)
                
                with torch.no_grad():
                    features = _model.features(input_tensor)
                    # 特征丰富度（特征激活的多样性）
                    feature_std = features.std().item()
                    feature_mean = features.mean().item()
                    feature_richness = min(100, (feature_std * 100 + abs(feature_mean) * 20))
                    
                    # 基于特征的美学评分
                    # 高层特征的激活强度与美学相关
                    pooled = torch.nn.functional.adaptive_avg_pool2d(features, 1)
                    top_activations = torch.topk(pooled.flatten(), k=50).values.mean().item()
                    ai_aesthetic = min(100, top_activations * 15)
                    
            except Exception as e:
                print(f"AI特征提取失败: {e}")
        
        # 4. 综合美学评分
        aesthetic_score = (
            clarity_score * 0.25 +      # 清晰度 25%
            color_harmony * 0.20 +      # 色彩 20%
            composition_score * 0.25 +   # 构图 25%
            feature_richness * 0.15 +    # 特征丰富度 15%
            ai_aesthetic * 0.15          # AI评分 15%
        )
        
        result = {
            "aesthetic_score": round(aesthetic_score, 1),
            "composition_score": round(composition_score, 1),
            "color_harmony": round(color_harmony, 1),
            "clarity_score": round(clarity_score, 1),
            "feature_richness": round(feature_richness, 1),
        }
        
    except Exception as e:
        print(f"美学分析失败: {e}")
    
    return result


def _analyze_composition(img) -> float:
    """
    分析图像构图质量
    基于三分法则和黄金分割
    """
    try:
        import cv2
        
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检测边缘
        edges = cv2.Canny(gray, 50, 150)
        
        # 三分法则区域（关键点位置）
        thirds_x = [w // 3, 2 * w // 3]
        thirds_y = [h // 3, 2 * h // 3]
        
        # 计算关键区域的边缘密度
        roi_scores = []
        roi_size = min(w, h) // 6
        
        for x in thirds_x:
            for y in thirds_y:
                x1 = max(0, x - roi_size)
                x2 = min(w, x + roi_size)
                y1 = max(0, y - roi_size)
                y2 = min(h, y + roi_size)
                
                roi = edges[y1:y2, x1:x2]
                density = np.sum(roi > 0) / roi.size if roi.size > 0 else 0
                roi_scores.append(density)
        
        # 中心区域的重要性
        center_x, center_y = w // 2, h // 2
        center_roi = edges[
            center_y - roi_size:center_y + roi_size,
            center_x - roi_size:center_x + roi_size
        ]
        center_density = np.sum(center_roi > 0) / center_roi.size if center_roi.size > 0 else 0
        
        # 构图评分：三分点有内容 + 中心适度
        thirds_score = np.mean(roi_scores) * 200
        center_score = min(50, center_density * 100)  # 中心不能太满
        
        composition = min(100, thirds_score + center_score)
        
        return composition
        
    except Exception as e:
        return 50


def get_best_frame(frame_paths: list) -> tuple:
    """
    从多个候选帧中选择美学评分最高的
    
    Args:
        frame_paths: 候选帧图片路径列表
    
    Returns:
        (最佳帧路径, 评分详情)
    """
    best_path = frame_paths[0] if frame_paths else None
    best_score = 0
    best_analysis = {}
    
    for path in frame_paths:
        analysis = analyze_aesthetic(path)
        score = analysis.get("aesthetic_score", 0)
        
        if score > best_score:
            best_score = score
            best_path = path
            best_analysis = analysis
    
    return best_path, best_analysis


