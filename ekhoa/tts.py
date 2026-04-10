# -*- coding: utf-8 -*-
"""
语音合成模块 (TTS)
使用 pyttsx3 进行离线语音合成，支持队列和伪流式输出
"""

import pyttsx3
import io
import queue
import sys
import threading
import time

import os

# 添加utils目录到Python路径，以便导入子目录中的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
import logging_utils

from config import TTS_RATE, TTS_VOLUME, TTS_QUEUE_SIZE

# 设置日志
logger = logging_utils.setup_module_logging("tts")

# 全局变量
engine = None
tts_queue = None
tts_thread = None
tts_running = False


def _init_engine():
    global engine
    if engine is not None:
        return
    
    # 临时重定向stdout和stderr以抑制pyttsx3的所有输出
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    # 使用一个完全静默的StringIO对象
    silent_output = io.StringIO()
    sys.stdout = silent_output
    sys.stderr = silent_output
    
    try:
        # 在完全静默的环境中初始化TTS引擎
        engine = pyttsx3.init()
        
        # 继续在静默环境中设置语音属性
        voices = engine.getProperty('voices')
        found_zh = False
        for v in voices:
            if 'zh' in v.id or 'chinese' in v.name.lower():
                engine.setProperty('voice', v.id)
                found_zh = True
                # 只记录到日志，不输出到控制台
                logger.debug(f"TTS 已切换中文: {v.id}")
                break

        if not found_zh:
            try:
                engine.setProperty('voice', 'zh')
            except:
                pass

        engine.setProperty('rate', TTS_RATE)  
        engine.setProperty('volume', TTS_VOLUME)
        
    except Exception as e:
        # 恢复stdout/stderr后记录错误
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        logger.error(f"TTS引擎初始化失败: {e}")
        raise
    finally:
        # 确保恢复stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def _tts_worker():
    """TTS工作线程，从队列获取文本并合成语音"""
    global engine, tts_running
    
    _init_engine()
    
    while tts_running:
        try:
            # 从队列获取文本，最多等待1秒
            text = tts_queue.get(timeout=1)
            if text is None:  # 停止信号
                break
                
            # 输出到控制台 - 简化输出，避免重复
            # 清除当前行，然后在新行输出
            sys.stdout.write('\r')  # 回到行首
            sys.stdout.flush()
            # 输出助手回复（覆盖可能存在的"正在思考..."消息）
            sys.stdout.write(f'助手: {text}\n')
            sys.stdout.flush()
            
            # 临时重定向stdout/stderr以抑制pyttsx3输出
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            silent_output = io.StringIO()
            sys.stdout = silent_output
            sys.stderr = silent_output
            
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS 错误: {e}")
            finally:
                # 恢复stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
            tts_queue.task_done()
            
        except queue.Empty:
            # 队列为空，继续等待
            continue
        except Exception as e:
            logger.error(f"TTS工作线程错误: {e}")
            time.sleep(0.1)


def _start_tts_system():
    """启动TTS队列系统"""
    global tts_queue, tts_thread, tts_running
    
    if tts_queue is None:
        tts_queue = queue.Queue(maxsize=TTS_QUEUE_SIZE)
    
    if tts_thread is None or not tts_thread.is_alive():
        tts_running = True
        tts_thread = threading.Thread(target=_tts_worker, daemon=True)
        tts_thread.start()
        logger.info("TTS队列系统已启动")


def speak(text):
    """ 文字转语音输出（兼容原有接口） """
    _start_tts_system()
    
    try:
        # 将文本放入队列
        tts_queue.put(text, block=True, timeout=5)
        logger.debug(f"TTS队列添加文本: {text[:50]}...")
    except queue.Full:
        logger.warning("TTS队列已满，丢弃文本")
    except Exception as e:
        logger.error(f"添加TTS队列失败: {e}")
        # 回退到直接合成
        _speak_direct(text)


def speak_stream(text):
    """
    流式语音输出（用于流式文本）
    与speak()相同，但语义上表示流式输入的一部分
    """
    speak(text)


def _speak_direct(text):
    """直接合成语音（不使用队列，用于错误恢复）"""
    global engine
    if engine is None:
        _init_engine()
    
    # 输出助手消息（与_tts_worker保持一致的格式）
    sys.stdout.write('\r')  # 回到行首
    sys.stdout.flush()
    sys.stdout.write(f'助手: {text}\n')
    sys.stdout.flush()
    
    # 临时重定向stdout和stderr以抑制pyttsx3运行时的输出
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    silent_output = io.StringIO()
    sys.stdout = silent_output
    sys.stderr = silent_output
    
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logger.error(f"直接TTS错误: {e}")
    finally:
        # 恢复stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def cleanup_tts():
    """清理TTS资源"""
    global tts_running, tts_thread
    
    if tts_running:
        tts_running = False
        # 发送停止信号
        if tts_queue:
            try:
                tts_queue.put(None, block=False)
            except:
                pass
        
        if tts_thread and tts_thread.is_alive():
            tts_thread.join(timeout=2)
            logger.info("TTS工作线程已停止")
    
    # 注意：不清理engine，因为可能被重用
