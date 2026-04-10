# -*- coding: utf-8 -*-
"""
键盘监听模块
提供非阻塞键盘输入检测功能
"""

import sys
import select
import termios
import tty

import config
import asr

def setup_keyboard_listener():
    # 保存当前终端设置
    old_settings = termios.tcgetattr(sys.stdin)
    # 设置非阻塞模式
    tty.setraw(sys.stdin.fileno())
    return old_settings

def check_key_press():
    """检查是否有按键输入，检测q键退出和空格键切换录音状态"""
    # 检查是否有键盘输入
    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
        key = sys.stdin.read(1)
        
        # 检测q键
        if key == 'q' or key == 'Q':
            sys.stdout.write('\r\nQ键被按下，准备退出...\r\n')
            sys.stdout.flush()
            config.exit_flag = True
            return True
        
        # 检测空格键
        if key == ' ':
            # 切换录音状态
            new_recording_flag = not config.recording_flag
            if new_recording_flag:
                # 开始录音：清空缓冲区
                config.audio_buffer.clear()
                sys.stdout.write('\r\n[空格键按下] 开始录音...\r\n')
                sys.stdout.flush()
                asr.reset_recognizer()  # 重置识别器，开始新的录音
            else:
                # 停止录音：标记需要处理缓冲区
                sys.stdout.write('\r\n[空格键按下] 停止录音，正在处理...\r\n')
                sys.stdout.flush()
                config.processing_pending = True
            
            config.recording_flag = new_recording_flag
            return False  # 不退出，只是切换状态
    
    return False

def restore_keyboard_settings(old_settings):
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
