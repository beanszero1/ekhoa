# -*- coding: utf-8 -*-
"""
配置文件模块
包含常量配置和全局变量
"""

# --- 全局变量 ---
exit_flag = False
recording_flag = False  # 录音状态标志，空格键控制
audio_buffer = bytearray()  # 录音数据缓冲区
processing_pending = False  # 是否有待处理的录音缓冲区

# --- ASR配置 ---
# SenseVoice FastAPI 配置
SENSEVOICE_API_URL = "http://127.0.0.1:7860/api/v1/asr"  # FastAPI端点地址
SENSEVOICE_LANGUAGE = "auto"  
SENSEVOICE_TIMEOUT = 30  # API请求超时时间（秒）

# 音频参数（用于录音）
SAMPLE_RATE = 16000  # 音频采样率
FRAMES_PER_BUFFER = 4000  # 音频缓冲区大小
CHANNELS = 1  # 音频通道数

# --- TTS配置 ---
TTS_RATE = 200  # 语音合成语速
TTS_VOLUME = 0.8  # 语音合成音量

# --- AI模型配置 ---
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
AI_MODEL = "qwen2.5:0.5b"     
AI_TIMEOUT = 60  # AI请求超时时间（秒）
SERVICE_CHECK_TIMEOUT = 5  # 服务检查超时时间

# --- llama.cpp 配置 ---
LLAMACPP_API_BASE_URL = "http://127.0.0.1:8080"  # llama.cpp 服务地址

# --- 唤醒词配置 ---
WAKE_WORDS = ["助手", "你好", "请问", "帮助"]

# --- DIFY配置 ---
DIFY_API_BASE_URL = "http://192.168.31.218:5001"  # DIFY服务地址
DIFY_API_ENDPOINT = "/v1/chat-messages"  # DIFY API端点
DIFY_API_KEY_ENV = "DIFY_API_KEY"  # 环境变量名称
DIFY_RESPONSE_MODE = "blocking"  # 响应模式：blocking阻塞式，streaming流式
DIFY_USER_ID = "raspberry-pi-voice-assistant"  # 用户ID
DIFY_TIMEOUT = 30  # API请求超时时间（秒）

# --- 任务分类配置 ---
CLASSIFICATION_PROMPT = """
请判断以下问题类型：
1. 法律案例：涉及具体案件、违法行为、判罚、纠纷等（如：过马路撞到人、邻居噪音投诉、盗窃、金融犯罪）
2. 通用问题：日常对话、知识问答、闲聊等
3. 其他专业知识：特定领域专业知识（医学、工程、编程，人工智能，嵌入式(单片机)等）
只需回答"法律案例"、"通用问题"或"其他专业知识"。
"""

UNKNOWN_REPLY = "对不起，这个问题我不了解"  # 其他专业知识的回复

# --- TTS队列配置 ---
TTS_QUEUE_SIZE = 10  # TTS队列大小
TTS_STREAM_DELIMITERS = ["。", "，", "！", "？", "；", ".", ",", "!", "?", ";"]  # 句子分割符号

# --- 系统提示词 ---
SYSTEM_PROMPT = """
你是一个基础法律问答助手,作用是回答用户有关法律相关的问题。
请仔细理解用户的问题，然后给出有帮助的回答。
回答不要分点作答，用一句话概括。
回答要简洁，控制在30~40字之内。
如果用户的问题不清楚，可以请求澄清。
"""

# --- OLED显示配置 ---
OLED_ENABLED = True  # 是否启用OLED显示
OLED_WIDTH = 128  # OLED屏幕宽度
OLED_HEIGHT = 64  # OLED屏幕高度
OLED_FONT_SIZE = 10  # 字体大小 (10px)
OLED_LINE_HEIGHT = 12  # 行高
OLED_I2C_PORT = 1  # I2C端口
OLED_I2C_ADDRESS = 0x3C  # I2C地址 (通常为0x3C或0x3D)
OLED_STARTUP_ANIMATION_DURATION = 7.0  # 开机动画持续时间
OLED_SHOW_BORDER = False  # 是否显示完整边框 

# --- 音频处理配置 ---
MIN_TEXT_LENGTH = 2  # 最小文本长度
MIN_NON_WAKE_TEXT_LENGTH = 3 # 非唤醒词的最小文本长度
