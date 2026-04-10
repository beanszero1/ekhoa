# -*- coding: utf-8 -*-

import os
import sys
import time

import config
import model_api
import asr
import tts
import oled_display

# 添加utils目录到Python路径，以便导入子目录中的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

# 导入utils目录中的模块
import check_utils
import keyboard_listener
import logging_utils

# 设置日志记录
logger = logging_utils.setup_module_logging("main")

def check_services():
    """检查所需服务是否可用"""
    print("检查系统服务...")
    logger.info("检查系统服务...")
    return check_utils.check_all_services()


def _oled_tts_stream_callback(sentence):
    """
    集成了OLED显示的TTS流式回调函数
    1. 将AI输出显示到OLED屏幕
    2. 将句子添加到TTS队列进行语音合成
    """
    if sentence and sentence.strip():
        # 显示AI输出到OLED
        if config.OLED_ENABLED:
            try:
                oled_display.display_ai_output(sentence.strip())
            except Exception as e:
                logger.error(f"OLED显示AI输出失败: {e}")
        
        # 添加到TTS队列进行语音合成
        tts.speak_stream(sentence.strip())


def process_recorded_audio():
    """处理已录音的音频缓冲区（支持流式输出）"""
    if len(config.audio_buffer) == 0:
        sys.stdout.write("\r录音缓冲区为空，跳过处理\n")
        sys.stdout.flush()
        return
    
    sys.stdout.write(f"\r处理录音数据，长度: {len(config.audio_buffer)} 字节\n")
    sys.stdout.flush()
    
    # 调用ASR识别整个缓冲区
    user_text = asr.recognize_buffer(config.audio_buffer)
    
    if user_text and len(user_text) > config.MIN_TEXT_LENGTH - 1:
        sys.stdout.write(f"\r识别结果: {user_text}\n")
        sys.stdout.flush()
        
        # 显示用户输入到OLED
        if config.OLED_ENABLED:
            try:
                oled_display.display_user_input(user_text)
            except Exception as e:
                logger.error(f"OLED显示用户输入失败: {e}")
        
        # 简单唤醒词检测
        has_wake_word = any(keyword in user_text for keyword in config.WAKE_WORDS)
        should_process = has_wake_word or len(user_text) > config.MIN_NON_WAKE_TEXT_LENGTH - 1
        
        if should_process:
            sys.stdout.write("\r正在思考...\n")
            sys.stdout.flush()
            
            # 使用集成了OLED显示的回调函数
            model_api.ask_ai(user_text, use_stream_callback=_oled_tts_stream_callback, conversation_history=None)
    else:
        sys.stdout.write("\r未识别到有效语音\n")
        sys.stdout.flush()
    
    # 清空缓冲区以备下次录音
    config.audio_buffer.clear()

def main():
    """主循环"""
    # 初始化OLED显示（如果启用）
    if config.OLED_ENABLED:
        try:
            oled_display.get_oled_instance()
            print("OLED初始化完成")
        except Exception as e:
            logger.error(f"OLED初始化失败: {e}")
    
    print("\n语音助手就绪！")
    print("提示：按下 空格键 开始/停止录音，按下 Q 键可以退出程序")
    
    # 设置键盘监听
    old_settings = keyboard_listener.setup_keyboard_listener()
    
    try:
        while not config.exit_flag:
            # 检查键盘输入
            if keyboard_listener.check_key_press():
                break
                
            # 检查是否有待处理的录音
            if config.processing_pending:
                process_recorded_audio()
                config.processing_pending = False
                
            # 检查音频输入
            data = asr.get_audio_data()
            if len(data) == 0: 
                continue

            # 如果在录音状态，将音频数据累积到缓冲区
            if config.recording_flag:
                config.audio_buffer.extend(data)
            # 不在录音状态时，不收集数据

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n用户中断，退出系统")
    except Exception as e:
        print(f"系统错误: {e}")
    finally:
        # 显示OLED关机动画（如果启用）
        if config.OLED_ENABLED:
            try:
                oled_display.show_shutdown_animation()
            except Exception as e:
                logger.error(f"显示关机动画失败: {e}")
        
        keyboard_listener.restore_keyboard_settings(old_settings)
        asr.cleanup_asr()
        print("资源清理完成")

if __name__ == "__main__":
    # 先初始化OLED（如果启用），这样程序启动就能立即显示动画
    if config.OLED_ENABLED:
        try:
            oled_display.get_oled_instance()
            print("OLED开机动画显示中...")
        except Exception as e:
            logger.error(f"OLED初始化失败: {e}")
    
    # 然后检查服务
    if check_services():
        main()
    else:
        print("服务检查失败，请解决上述问题后重试")
