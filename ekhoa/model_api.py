# -*- coding: utf-8 -*-
"""
AI模型API模块
通过Ollama与模型进行交互，集成DIFY API调用
"""

import os
import json
import requests
import config

# DIFY会话管理（conversation_id）
_dify_conversation_id = None


def classify_query(text):
    """
    使用qwen3对用户问题进行分类
    Returns: "法律案例", "通用问题", "其他专业知识" 或分类失败时的默认值
    """
    try:
        response = requests.post(config.OLLAMA_URL, json={
            "model": config.AI_MODEL,
            "messages": [
                {'role': 'system', 'content': config.CLASSIFICATION_PROMPT},
                {'role': 'user', 'content': text}
            ],
            "stream": False
        }, timeout=config.AI_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            classification = result['message']['content'].strip()
            
            # 简化分类结果
            if "法律案例" in classification:
                return "法律案例"
            elif "通用问题" in classification:
                return "通用问题"
            elif "其他专业知识" in classification:
                return "其他专业知识"
            else:
                # 如果没有明确分类，默认作为通用问题处理
                return "通用问题"
        else:
            return "通用问题"  # 分类失败时默认处理为通用问题
            
    except Exception as e:
        # 分类失败时默认处理为通用问题
        return "通用问题"


def ask_ai_dify_stream(text, conversation_history=None):
    """
    使用DIFY API进行调用
    在用户问题后添加"将回答总结成30~50字左右"以缩短回答
    使用DIFY的conversation_id机制实现多轮对话记忆
    
    Args:
        text: 当前用户问题
        conversation_history: 保留参数，仅用于兼容性
        
    Returns: 生成器，只产生一个完整的回答文本
    """
    global _dify_conversation_id
    
    # 获取API Key
    api_key = os.getenv(config.DIFY_API_KEY_ENV)
    if not api_key:
        yield f"错误：环境变量{config.DIFY_API_KEY_ENV}未设置"
        return
    
    try:
        # 构建请求URL
        url = f"{config.DIFY_API_BASE_URL}{config.DIFY_API_ENDPOINT}"
        
        # 构建prompt：在用户问题后添加总结要求
        prompt_with_summary = f"{text}。将回答总结成30~50字左右"
        
        # 请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 请求数据
        payload = {
            "inputs": {},  # 输入参数
            "query": prompt_with_summary,  # 用户输入的问题（包含总结要求）
            "response_mode": config.DIFY_RESPONSE_MODE,
            "conversation_id": _dify_conversation_id or "",  # 使用之前保存的conversation_id（如果有）
            "user": config.DIFY_USER_ID
        }
        
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=config.DIFY_TIMEOUT
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析响应数据
        result = response.json()
        
        # 提取回答文本
        full_text = result.get("answer", "")
        if not full_text:
            full_text = result.get("text", "")  # 备用字段
        
        # 更新conversation_id用于下一轮对话
        new_conversation_id = result.get("conversation_id", "")
        if new_conversation_id:
            _dify_conversation_id = new_conversation_id
        
        if not full_text:
            yield "DIFY API返回空响应"
            return
        
        # 清理文本：移除markdown格式，去除多余空白
        def clean_text(text):
            if not text:
                return text
            
            # 移除markdown粗体符号
            text = text.replace('**', '')
            text = text.replace('*', '')
            text = text.replace('__', '')
            
            # 移除其他markdown符号
            import re
            text = re.sub(r'#{1,6}\s+', '', text)  # 移除标题
            text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)  # 移除代码块
            text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # 移除链接
            
            # 去除多余空白
            text = ' '.join(text.split())
            
            # 确保文本以合适的标点结束
            if text and text[-1] not in '。！？.!?':
                text += '。'
                
            return text
        
        cleaned_text = clean_text(full_text)
        
        # 返回完整文本（不分割句子）
        yield cleaned_text
            
    except requests.exceptions.RequestException as e:
        # 发生请求异常时重置conversation_id
        _dify_conversation_id = None
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                yield f"DIFY API调用失败: {e} - {error_detail}"
            except:
                yield f"DIFY API调用失败: {e} - {e.response.text}"
        else:
            yield f"DIFY API调用失败: {e}"
    except Exception as e:
        # 发生其他异常时重置conversation_id
        _dify_conversation_id = None
        yield f"DIFY API调用失败: {str(e)}"


def _build_general_messages(text, conversation_history=None):
    """构建通用问答消息列表。"""
    messages = [{'role': 'system', 'content': config.SYSTEM_PROMPT}]

    if conversation_history:
        recent_history = conversation_history[-20:]  # 最近10轮（20条消息）
        for msg in recent_history:
            role = 'user' if msg['role'] == 'user' else 'assistant'
            messages.append({'role': role, 'content': msg['content']})

    messages.append({'role': 'user', 'content': text})
    return messages


def ask_ai_general(text, conversation_history=None):
    """
    处理通用问题（使用原有qwen3逻辑）
    支持对话历史上下文
    
    Args:
        text: 当前用户问题
        conversation_history: 对话历史列表，格式 [{'role': 'user/assistant', 'content': '...'}]
    """
    try:
        messages = _build_general_messages(text, conversation_history)
        
        # 尝试请求本地 LLM
        response = requests.post(config.OLLAMA_URL, json={
            "model": config.AI_MODEL,
            "messages": messages,
            "stream": False
        }, timeout=config.AI_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            reply = result['message']['content'].strip()
            return reply
        else:
            return "抱歉，AI服务暂时不可用"
            
    except requests.exceptions.ConnectionError:
        return "无法连接到AI服务，请检查Ollama是否启动"
    except requests.exceptions.Timeout:
        return "AI响应超时，请稍后再试"
    except Exception as e:
        return f"处理请求时出现错误: {str(e)}"


def ask_ai_general_stream(text, conversation_history=None):
    """
    流式处理通用问题，按文本片段返回模型输出。

    Args:
        text: 当前用户问题
        conversation_history: 对话历史列表

    Yields:
        str: 模型返回的文本片段
    """
    messages = _build_general_messages(text, conversation_history)

    try:
        with requests.post(
            config.OLLAMA_URL,
            json={
                "model": config.AI_MODEL,
                "messages": messages,
                "stream": True
            },
            timeout=config.AI_TIMEOUT,
            stream=True
        ) as response:
            if response.status_code != 200:
                raise RuntimeError("抱歉，AI服务暂时不可用")

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                try:
                    result = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if result.get('error'):
                    raise RuntimeError(result['error'])

                chunk = result.get('message', {}).get('content', '')
                if chunk:
                    yield chunk

    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("无法连接到AI服务，请检查Ollama是否启动") from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("AI响应超时，请稍后再试") from exc
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"处理请求时出现错误: {str(exc)}") from exc


def ask_ai(text, use_stream_callback=None, conversation_history=None):
    """
    主AI问答函数，保持向后兼容
    新增use_stream_callback参数用于流式处理回调
    新增conversation_history参数用于对话记忆
    
    Args:
        text: 用户输入的文本
        use_stream_callback: 可选回调函数，用于流式处理文本片段
        conversation_history: 可选，对话历史列表
        
    Returns:
        如果使用回调函数则返回None，否则返回完整回复文本
        恢复原有行为：使用回调时不返回文本，避免重复输出
    """
    # 1. 分类问题
    query_type = classify_query(text)
    
    # 2. 根据类型处理
    if query_type == "法律案例":
        # 使用DIFY API处理法律案例（ask_ai_dify_stream返回生成器）
        full_response = ""
        for sentence in ask_ai_dify_stream(text, conversation_history):
            full_response += sentence + " "
        
        full_response = full_response.strip()
        if not full_response:
            full_response = "DIFY API无返回结果"
        
        # 如果提供了回调函数，调用它并返回None（避免重复输出）
        if use_stream_callback is not None:
            # 无论是否有回复内容，只要使用了回调就返回None
            if full_response:
                use_stream_callback(full_response)
            return None
        else:
            # 没有回调，返回完整回复文本
            return full_response
            
    elif query_type == "通用问题":
        # 通用问题目前不支持历史
        reply = ask_ai_general(text)
        
        # 如果提供了回调函数，调用它并返回None
        if use_stream_callback is not None:
            if reply:
                use_stream_callback(reply)
            return None
        else:
            return reply
        
    else:  # "其他专业知识"
        reply = config.UNKNOWN_REPLY
        
        # 如果提供了回调函数，调用它并返回None
        if use_stream_callback is not None:
            if reply:
                use_stream_callback(reply)
            return None
        else:
            return reply
