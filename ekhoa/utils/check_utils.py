# -*- coding: utf-8 -*-
"""
检查工具模块
提供系统服务检查功能
"""

import requests
import logging_utils
import config

# 设置日志
logger = logging_utils.setup_module_logging("check_utils")


def check_sensevoice_service():
    """
    检查SenseVoice FastAPI服务是否可用
    
    Returns:
        tuple: (bool, str) 是否可用, 错误信息
    """
    try:
        # 尝试访问根路径或健康检查端点
        response = requests.get(config.SENSEVOICE_API_URL.replace('/api/v1/asr', '').rstrip('/'), timeout=5)
        # 接受200-399的状态码
        if 200 <= response.status_code < 400:
            return True, f"SenseVoice FastAPI服务在线 (HTTP {response.status_code})"
        else:
            return False, f"SenseVoice服务返回HTTP {response.status_code}"
    except Exception as e:
        return False, f"无法连接到SenseVoice FastAPI服务: {e}"


def check_llamacpp_service():
    """
    检查llama.cpp OpenAI兼容API服务是否可用
    
    Returns:
        tuple: (bool, str, list) 是否可用, 错误信息, 可用模型列表
    """
    try:
        # 检查llama.cpp OpenAI兼容API的健康端点
        models_url = f"{config.LLAMACPP_API_BASE_URL}/models"
        response = requests.get(models_url, timeout=config.SERVICE_CHECK_TIMEOUT)
        if response.status_code == 200:
            # OpenAI兼容API返回格式
            result = response.json()
            if "data" in result:
                models = result["data"]
                model_names = [m["id"] for m in models if "id" in m]
                return True, "llama.cpp服务正常", model_names
            else:
                # 如果没有data字段，至少服务是可用的
                return True, "llama.cpp服务正常", ["unknown"]
        else:
            return False, f"llama.cpp服务返回HTTP {response.status_code}", []
    except Exception as e:
        return False, f"无法连接llama.cpp服务: {e}", []

def check_all_services():
    """
    检查所有所需服务是否可用
    
    Returns:
        bool: 所有服务是否可用
    """
    logger.info("开始检查系统服务...")
    
    print("检查SenseVoice服务...")
    # 检查SenseVoice服务
    sensevoice_ok, sensevoice_msg = check_sensevoice_service()
    if not sensevoice_ok:
        print(f"SenseVoice服务异常: {sensevoice_msg}")
        logger.error(f"SenseVoice服务异常: {sensevoice_msg}")
        return False
    print(f"SenseVoice服务正常")
    logger.info(f"SenseVoice服务正常")
    
    print("检查llama.cpp服务...")
    # 检查llama.cpp服务
    llamacpp_ok, llamacpp_msg, models = check_llamacpp_service()
    if not llamacpp_ok:
        print(f"llama.cpp服务异常: {llamacpp_msg}")
        logger.error(f"llama.cpp服务异常: {llamacpp_msg}")
        return False
    print(f"llama.cpp服务正常")
    logger.info(f"llama.cpp服务正常")
    
    if models and models != ["unknown"]:
        print(f"可用模型: {models}")
        logger.info(f"可用模型: {models}")
        # 检查是否有所需模型（模型名可能不同，仅作提示）
        if config.AI_MODEL not in models:
            warning_msg = f"配置的模型 '{config.AI_MODEL}' 可能在服务中不存在，将尝试使用可用模型"
            print(f"注意: {warning_msg}")
            logger.warning(warning_msg)
    else:
        info_msg = f"使用llama.cpp服务（127.0.0.1:8080），配置模型: {config.AI_MODEL}"
        print(f"信息: {info_msg}")
        logger.info(info_msg)
    
 
    return True
