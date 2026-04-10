# -*- coding: utf-8 -*-
"""
Web UI 模块
基于 Flask 实现的 Web 界面，支持文字和语音输入
"""

import os
import json
import time
import uuid
import io
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, send_file, session, Response, stream_with_context
from pydub import AudioSegment

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 导入项目模块
import config
import model_api

# 创建Flask应用，指定模板和静态文件路径
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = 'local-voice-webui-secret-key-2024'

# 会话存储 (内存中，不持久化)
sessions = {}
sessions_lock = threading.Lock()


def get_or_create_session():
    """获取或创建会话"""
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    with sessions_lock:
        if session_id not in sessions:
            sessions[session_id] = {
                'conversations': {},  # 多个对话
                'current_conversation_id': None
            }
    
    return session_id


def get_or_create_conversation(session_id, conversation_id=None):
    """获取或创建对话"""
    with sessions_lock:
        sess = sessions.get(session_id, {})
        
        if conversation_id and conversation_id in sess.get('conversations', {}):
            sess['current_conversation_id'] = conversation_id
            return conversation_id, sess['conversations'][conversation_id]
        
        # 创建新对话
        new_conversation_id = str(uuid.uuid4())
        sess['conversations'][new_conversation_id] = {
            'id': new_conversation_id,
            'title': '新对话',
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
        sess['current_conversation_id'] = new_conversation_id
        return new_conversation_id, sess['conversations'][new_conversation_id]


def build_conversation_history(conversation):
    """提取对话历史，用于构建上下文。"""
    history = []
    for msg in conversation.get('messages', []):
        history.append({
            'role': msg['role'],
            'content': msg['content']
        })
    return history


def sse_payload(data):
    """格式化 SSE 数据。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _synthesize_tts_wav(text):
    """
    使用系统 eSpeak/eSpeak-NG 生成可直接返回给浏览器播放的 WAV 数据。
    优先使用 espeak-ng，若不可用则回退到 espeak。
    """
    binary = shutil.which('espeak-ng') or shutil.which('espeak')
    if not binary:
        raise RuntimeError('未找到 espeak-ng 或 espeak，请先安装离线语音合成引擎')

    volume = max(0, min(200, int(config.TTS_VOLUME * 200)))
    rate = max(80, min(450, int(config.TTS_RATE)))
    voice_candidates = ['zh', 'cmn', 'zh-yue', None]
    last_error = None

    for voice in voice_candidates:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            cmd = [binary, '-w', tmp_path, '-s', str(rate), '-a', str(volume)]
            if voice:
                cmd.extend(['-v', voice])
            cmd.append(text)

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=20,
                check=False
            )

            if result.returncode != 0:
                stderr_text = result.stderr.decode('utf-8', errors='ignore').strip()
                last_error = stderr_text or f'{binary} 执行失败'
                continue

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                last_error = '生成的音频文件为空'
                continue

            with open(tmp_path, 'rb') as wav_file:
                return wav_file.read()
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    raise RuntimeError(last_error or '语音合成失败')


@app.route('/')
def index():
    """主页面"""
    get_or_create_session()
    return render_template('index.html')


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """获取所有对话列表"""
    session_id = get_or_create_session()
    
    with sessions_lock:
        sess = sessions.get(session_id, {})
        conversations = sess.get('conversations', {})
    
    conversation_list = []
    for conv_id, conv in conversations.items():
        conversation_list.append({
            'id': conv_id,
            'title': conv.get('title', '新对话'),
            'created_at': conv.get('created_at')
        })
    
    # 按创建时间倒序排列
    conversation_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify({
        'success': True,
        'conversations': conversation_list,
        'current_conversation_id': sessions.get(session_id, {}).get('current_conversation_id')
    })


@app.route('/api/conversation/new', methods=['POST'])
def new_conversation():
    """创建新对话"""
    session_id = get_or_create_session()
    conv_id, conv = get_or_create_conversation(session_id)
    
    return jsonify({
        'success': True,
        'conversation_id': conv_id,
        'conversation': conv
    })


@app.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """获取指定对话"""
    session_id = get_or_create_session()
    
    with sessions_lock:
        sess = sessions.get(session_id, {})
        conv = sess.get('conversations', {}).get(conversation_id)
    
    if not conv:
        return jsonify({'success': False, 'error': '对话不存在'}), 404
    
    sess['current_conversation_id'] = conversation_id
    
    return jsonify({
        'success': True,
        'conversation': conv
    })


@app.route('/api/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除对话"""
    session_id = get_or_create_session()
    
    with sessions_lock:
        sess = sessions.get(session_id, {})
        if conversation_id in sess.get('conversations', {}):
            del sess['conversations'][conversation_id]
            if sess['current_conversation_id'] == conversation_id:
                sess['current_conversation_id'] = None
    
    return jsonify({'success': True})


@app.route('/api/chat', methods=['POST'])
def chat():
    """文字聊天接口"""
    start_time = time.time()
    session_id = get_or_create_session()
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')
    
    if not user_message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400
    
    # 获取或创建对话
    conv_id, conv = get_or_create_conversation(session_id, conversation_id)
    
    # 获取对话历史（用于上下文）
    conversation_history = build_conversation_history(conv)
    
    # AI响应计时
    ai_start = time.time()
    
    # 使用对话历史进行上下文对话
    reply = model_api.ask_ai_general(user_message, conversation_history)
    
    ai_time = time.time() - ai_start
    total_time = time.time() - start_time
    
    # 更新对话标题（使用第一条消息）
    if len(conv['messages']) == 0:
        conv['title'] = user_message[:20] + ('...' if len(user_message) > 20 else '')
    
    # 添加消息到对话
    user_msg = {
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().isoformat()
    }
    assistant_msg = {
        'role': 'assistant',
        'content': reply,
        'timestamp': datetime.now().isoformat(),
        'timings': {
            'ai': round(ai_time * 1000),
            'total': round(total_time * 1000)
        }
    }
    
    conv['messages'].append(user_msg)
    conv['messages'].append(assistant_msg)
    
    return jsonify({
        'success': True,
        'conversation_id': conv_id,
        'reply': reply,
        'timings': {
            'ai': round(ai_time * 1000),
            'total': round(total_time * 1000)
        }
    })


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式文字聊天接口。"""
    start_time = time.time()
    session_id = get_or_create_session()

    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')

    if not user_message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400

    conv_id, conv = get_or_create_conversation(session_id, conversation_id)
    conversation_history = build_conversation_history(conv)

    user_msg = {
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().isoformat()
    }

    with sessions_lock:
        sess = sessions.get(session_id, {})
        conversation = sess.get('conversations', {}).get(conv_id)
        if conversation is not None:
            if len(conversation.get('messages', [])) == 0:
                conversation['title'] = user_message[:20] + ('...' if len(user_message) > 20 else '')
            conversation['messages'].append(user_msg)
            sess['current_conversation_id'] = conv_id

    def generate():
        ai_start = time.time()
        full_reply = ""

        yield sse_payload({
            'type': 'start',
            'conversation_id': conv_id
        })

        try:
            for chunk in model_api.ask_ai_general_stream(user_message, conversation_history):
                full_reply += chunk
                yield sse_payload({
                    'type': 'chunk',
                    'content': chunk,
                    'conversation_id': conv_id
                })

            ai_time = time.time() - ai_start
            total_time = time.time() - start_time
            timings = {
                'ai': round(ai_time * 1000),
                'total': round(total_time * 1000)
            }

            assistant_msg = {
                'role': 'assistant',
                'content': full_reply,
                'timestamp': datetime.now().isoformat(),
                'timings': timings
            }

            with sessions_lock:
                sess = sessions.get(session_id, {})
                conversation = sess.get('conversations', {}).get(conv_id)
                if conversation is not None:
                    conversation['messages'].append(assistant_msg)
                    sess['current_conversation_id'] = conv_id

            yield sse_payload({
                'type': 'done',
                'conversation_id': conv_id,
                'timings': timings
            })

        except Exception as exc:
            yield sse_payload({
                'type': 'error',
                'conversation_id': conv_id,
                'error': str(exc)
            })

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/voice', methods=['POST'])
def voice():
    """语音输入接口"""
    start_time = time.time()
    session_id = get_or_create_session()
    
    # 获取音频数据
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': '未收到音频文件'}), 400
    
    audio_file = request.files['audio']
    conversation_id = request.form.get('conversation_id')
    
    # 读取音频数据
    audio_data = audio_file.read()
    
    # 使用 pydub 转换音频格式
    tmp_input_path = None
    tmp_output_path = None
    
    # 音频转换计时
    convert_start = time.time()
    
    try:
        # 保存原始音频到临时文件
        with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as tmp_input:
            tmp_input_path = tmp_input.name
            tmp_input.write(audio_data)
        
        # 使用 pydub 转换为 16kHz 单声道 WAV（自动检测格式）
        audio = AudioSegment.from_file(tmp_input_path)
        
        # 转换为单声道、16kHz、16位 PCM
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio = audio.set_sample_width(2)  # 16位
        
        # 计算录音时长
        record_duration = len(audio) / 1000.0  # pydub 返回毫秒
        
        # 保存为 WAV 文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_output:
            tmp_output_path = tmp_output.name
        
        audio.export(tmp_output_path, format='wav')
        
        convert_time = time.time() - convert_start
        
        # 调用SenseVoice识别
        asr_start = time.time()
        
        # 构造请求
        with open(tmp_output_path, 'rb') as wav_file:
            files = [
                ('files', ('recording.wav', wav_file, 'audio/wav'))
            ]
            data = {
                'keys': 'audio1',
                'lang': config.SENSEVOICE_LANGUAGE
            }
            
            response = requests.post(
                config.SENSEVOICE_API_URL,
                files=files,
                data=data,
                timeout=config.SENSEVOICE_TIMEOUT
            )
        
        asr_time = time.time() - asr_start
        
        # 清理临时文件
        if tmp_input_path and os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if tmp_output_path and os.path.exists(tmp_output_path):
            os.unlink(tmp_output_path)
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'语音识别服务返回错误 ({response.status_code})，请检查SenseVoice服务是否正常'
            }), 500
        
        # 解析识别结果
        result = response.json()
        user_message = ""
        
        if isinstance(result, list) and len(result) > 0:
            user_message = result[0].get('clean_text') or result[0].get('text', '')
        elif isinstance(result, dict) and 'result' in result:
            result_list = result['result']
            if isinstance(result_list, list) and len(result_list) > 0:
                user_message = result_list[0].get('clean_text') or result_list[0].get('text', '')
        
        user_message = user_message.strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '未识别到有效语音，请重试'
            })
        
    except requests.exceptions.ConnectionError:
        # 清理临时文件
        if tmp_input_path and os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if tmp_output_path and os.path.exists(tmp_output_path):
            os.unlink(tmp_output_path)
        return jsonify({
            'success': False,
            'error': '无法连接到语音识别服务，请确保SenseVoice服务已启动 (端口7860)'
        }), 500
    except requests.exceptions.Timeout:
        # 清理临时文件
        if tmp_input_path and os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if tmp_output_path and os.path.exists(tmp_output_path):
            os.unlink(tmp_output_path)
        return jsonify({
            'success': False,
            'error': '语音识别服务响应超时，请稍后重试'
        }), 500
    except Exception as e:
        # 清理临时文件
        if tmp_input_path and os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if tmp_output_path and os.path.exists(tmp_output_path):
            os.unlink(tmp_output_path)
        return jsonify({
            'success': False,
            'error': f'语音识别错误: {str(e)}'
        }), 500
    
    # 获取或创建对话
    conv_id, conv = get_or_create_conversation(session_id, conversation_id)
    
    # 获取对话历史（用于上下文）
    conversation_history = []
    for msg in conv.get('messages', []):
        conversation_history.append({
            'role': msg['role'],
            'content': msg['content']
        })
    
    # AI响应计时
    ai_start = time.time()
    
    # 使用对话历史进行上下文对话
    reply = model_api.ask_ai_general(user_message, conversation_history)
    
    ai_time = time.time() - ai_start
    total_time = time.time() - start_time
    
    # 更新对话标题
    if len(conv['messages']) == 0:
        conv['title'] = user_message[:20] + ('...' if len(user_message) > 20 else '')
    
    # 添加消息到对话
    user_msg = {
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().isoformat(),
        'voice': True,
        'record_duration': round(record_duration * 1000)
    }
    assistant_msg = {
        'role': 'assistant',
        'content': reply,
        'timestamp': datetime.now().isoformat(),
        'timings': {
            'record': round(record_duration * 1000),
            'convert': round(convert_time * 1000),
            'asr': round(asr_time * 1000),
            'ai': round(ai_time * 1000),
            'total': round(total_time * 1000)
        }
    }
    
    conv['messages'].append(user_msg)
    conv['messages'].append(assistant_msg)
    
    return jsonify({
        'success': True,
        'conversation_id': conv_id,
        'recognized_text': user_message,
        'reply': reply,
        'timings': {
            'record': round(record_duration * 1000),
            'convert': round(convert_time * 1000),
            'asr': round(asr_time * 1000),
            'ai': round(ai_time * 1000),
            'total': round(total_time * 1000)
        }
    })


@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """文字转语音接口"""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'success': False, 'error': '文本不能为空'}), 400
    
    try:
        wav_bytes = _synthesize_tts_wav(text)

        return send_file(
            io.BytesIO(wav_bytes),
            mimetype='audio/wav',
            as_attachment=False,
            download_name='tts.wav'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'语音合成失败: {str(e)}'
        }), 500


@app.route('/api/conversation/<conversation_id>/edit', methods=['POST'])
def edit_conversation_message(conversation_id):
    """编辑用户消息并覆盖后续回复"""
    session_id = get_or_create_session()
    data = request.get_json() or {}
    new_message = data.get('message', '').strip()
    message_index = data.get('message_index')

    if not new_message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400

    try:
        message_index = int(message_index)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': '消息索引无效'}), 400

    with sessions_lock:
        sess = sessions.get(session_id, {})
        conv = sess.get('conversations', {}).get(conversation_id)
        if not conv:
            return jsonify({'success': False, 'error': '对话不存在'}), 404

        messages = list(conv.get('messages', []))

    if message_index < 0 or message_index >= len(messages):
        return jsonify({'success': False, 'error': '消息索引超出范围'}), 400

    original_msg = dict(messages[message_index])
    if original_msg.get('role') != 'user':
        return jsonify({'success': False, 'error': '只能编辑用户消息'}), 400

    prefix_messages = [dict(msg) for msg in messages[:message_index]]
    conversation_history = [
        {
            'role': msg['role'],
            'content': msg['content']
        }
        for msg in prefix_messages
    ]

    start_time = time.time()
    ai_start = time.time()
    reply = model_api.ask_ai_general(new_message, conversation_history)
    ai_time = time.time() - ai_start
    total_time = time.time() - start_time

    edited_user_msg = {
        'role': 'user',
        'content': new_message,
        'timestamp': datetime.now().isoformat(),
        'edited': True
    }

    if original_msg.get('voice'):
        edited_user_msg['voice'] = True
    if original_msg.get('record_duration') is not None:
        edited_user_msg['record_duration'] = original_msg.get('record_duration')

    assistant_msg = {
        'role': 'assistant',
        'content': reply,
        'timestamp': datetime.now().isoformat(),
        'timings': {
            'ai': round(ai_time * 1000),
            'total': round(total_time * 1000)
        }
    }

    updated_messages = prefix_messages + [edited_user_msg, assistant_msg]

    with sessions_lock:
        sess = sessions.get(session_id, {})
        conv = sess.get('conversations', {}).get(conversation_id)
        if not conv:
            return jsonify({'success': False, 'error': '对话不存在'}), 404

        conv['messages'] = updated_messages
        sess['current_conversation_id'] = conversation_id

        if message_index == 0:
            conv['title'] = new_message[:20] + ('...' if len(new_message) > 20 else '')

        updated_conversation = dict(conv)

    return jsonify({
        'success': True,
        'conversation': updated_conversation,
        'reply': reply,
        'timings': assistant_msg['timings']
    })


@app.route('/api/clear', methods=['POST'])
def clear_session():
    """清空当前会话的所有对话"""
    session_id = get_or_create_session()
    
    with sessions_lock:
        if session_id in sessions:
            sessions[session_id]['conversations'] = {}
            sessions[session_id]['current_conversation_id'] = None
    
    return jsonify({'success': True})


if __name__ == '__main__':
    print("=" * 50)
    print("语音助手 Web UI 启动中...")
    print("=" * 50)
    print(f"访问地址: http://127.0.0.1:5000")
    print(f"SenseVoice API: {config.SENSEVOICE_API_URL}")
    print(f"llama.cpp URL: {config.LLAMACPP_API_BASE_URL}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
