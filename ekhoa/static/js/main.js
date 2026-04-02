/**
 * Ekhoa WebUI 前端交互逻辑
 */

// 全局状态
const state = {
    currentConversationId: null,
    conversations: {},
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    recordingStartTime: null,
    recordingTimer: null
};

// DOM 元素
const elements = {
    sidebar: document.querySelector('.sidebar'),
    menuToggle: document.getElementById('menuToggle'),
    newChatBtn: document.getElementById('newChatBtn'),
    conversationsList: document.getElementById('conversationsList'),
    currentTitle: document.getElementById('currentTitle'),
    clearBtn: document.getElementById('clearBtn'),
    chatContainer: document.getElementById('chatContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesContainer: document.getElementById('messagesContainer'),
    messageInput: document.getElementById('messageInput'),
    voiceBtn: document.getElementById('voiceBtn'),
    sendBtn: document.getElementById('sendBtn'),
    recordingIndicator: document.getElementById('recordingIndicator'),
    recordingTime: document.getElementById('recordingTime'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer'),
    sensevoiceStatus: document.getElementById('sensevoiceStatus'),
    llamacppStatus: document.getElementById('llamacppStatus')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadConversations();
    checkServiceStatus();
});

// 事件监听器初始化
function initEventListeners() {
    // 菜单切换
    elements.menuToggle.addEventListener('click', toggleSidebar);
    
    // 新建对话
    elements.newChatBtn.addEventListener('click', createNewConversation);
    
    // 清空对话
    elements.clearBtn.addEventListener('click', clearAllConversations);
    
    // 发送消息
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 自动调整输入框高度
    elements.messageInput.addEventListener('input', autoResizeTextarea);
    
    // 语音按钮
    elements.voiceBtn.addEventListener('click', toggleRecording);
    
    // 点击侧边栏外部关闭
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            !elements.sidebar.contains(e.target) && 
            !elements.menuToggle.contains(e.target)) {
            elements.sidebar.classList.remove('open');
        }
    });
}

// 切换侧边栏
function toggleSidebar() {
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.toggle('open');
    } else {
        elements.sidebar.classList.toggle('collapsed');
    }
}

// 自动调整文本框高度
function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 150) + 'px';
}

// 加载对话列表
async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        const data = await response.json();
        
        if (data.success) {
            state.conversations = {};
            renderConversationsList(data.conversations);
            
            if (data.current_conversation_id) {
                selectConversation(data.current_conversation_id);
            }
        }
    } catch (error) {
        showToast('加载对话列表失败', 'error');
        console.error('加载对话列表失败:', error);
    }
}

// 渲染对话列表
function renderConversationsList(conversations) {
    elements.conversationsList.innerHTML = '';
    
    if (conversations.length === 0) {
        elements.conversationsList.innerHTML = `
            <div class="no-conversations" style="text-align: center; color: var(--text-muted); padding: 20px;">
                暂无对话
            </div>
        `;
        return;
    }
    
    conversations.forEach(conv => {
        state.conversations[conv.id] = conv;
        
        const item = document.createElement('div');
        item.className = 'conversation-item' + (conv.id === state.currentConversationId ? ' active' : '');
        item.dataset.id = conv.id;
        item.innerHTML = `
            <span class="conv-title">${escapeHtml(conv.title)}</span>
            <button class="delete-btn" onclick="deleteConversation('${conv.id}', event)">
                <i class="fas fa-trash-alt"></i>
            </button>
        `;
        
        item.addEventListener('click', (e) => {
            if (!e.target.closest('.delete-btn')) {
                selectConversation(conv.id);
            }
        });
        
        elements.conversationsList.appendChild(item);
    });
}

// 选择对话
async function selectConversation(conversationId) {
    if (state.currentConversationId === conversationId) return;
    
    state.currentConversationId = conversationId;
    
    // 更新UI
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.toggle('active', item.dataset.id === conversationId);
    });
    
    // 加载对话内容
    try {
        const response = await fetch(`/api/conversation/${conversationId}`);
        const data = await response.json();
        
        if (data.success) {
            renderConversation(data.conversation);
            elements.currentTitle.textContent = data.conversation.title || '新对话';
            
            // 移动端关闭侧边栏
            if (window.innerWidth <= 768) {
                elements.sidebar.classList.remove('open');
            }
        }
    } catch (error) {
        showToast('加载对话失败', 'error');
        console.error('加载对话失败:', error);
    }
}

// 渲染对话内容
function renderConversation(conversation) {
    state.currentConversationId = conversation.id;
    
    if (!conversation.messages || conversation.messages.length === 0) {
        elements.welcomeScreen.classList.remove('hidden');
        elements.messagesContainer.classList.remove('visible');
        elements.messagesContainer.innerHTML = '';
        return;
    }
    
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.classList.add('visible');
    elements.messagesContainer.innerHTML = '';
    
    conversation.messages.forEach(msg => {
        appendMessage(msg, false);
    });
    
    scrollToBottom();
}

// 追加消息
function appendMessage(msg, scroll = true) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.role}`;
    
    const content = escapeHtml(msg.content);
    let metaHtml = '';
    
    if (msg.role === 'user') {
        // 用户消息
        if (msg.voice) {
            metaHtml = `
                <div class="message-meta">
                    <span class="voice-indicator">
                        <i class="fas fa-microphone"></i>
                        语音输入
                    </span>
                </div>
            `;
        }
    } else {
        // 助手消息
        let timingsHtml = '';
        if (msg.timings) {
            timingsHtml = renderTimings(msg.timings, msg.voice);
        }
        
        metaHtml = `
            <div class="message-meta">
                ${timingsHtml}
                <button class="audio-play-btn" onclick="playAudio('${escapeHtml(msg.content)}')">
                    <i class="fas fa-volume-up"></i>
                    播放
                </button>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        ${metaHtml}
    `;
    
    elements.messagesContainer.appendChild(messageDiv);
    
    if (scroll) {
        scrollToBottom();
    }
}

// 显示正在输入的动画
function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-message';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(typingDiv);
    scrollToBottom();
}

// 隐藏正在输入的动画
function hideTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}

// 渲染时间统计
function renderTimings(timings, isVoice = false) {
    const items = [];
    
    if (isVoice && timings.record) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-microphone"></i>
                录音: ${timings.record}ms
            </span>
        `);
    }
    
    if (timings.asr) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-headphones"></i>
                识别: ${timings.asr}ms
            </span>
        `);
    }
    
    if (timings.classify) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-tags"></i>
                分类: ${timings.classify}ms
            </span>
        `);
    }
    
    if (timings.ai) {
        items.push(`
            <span class="timing-item">
                <i class="fas fa-brain"></i>
                AI: ${timings.ai}ms
            </span>
        `);
    }
    
    if (timings.total) {
        items.push(`
            <span class="timing-item" style="font-weight: bold; color: var(--text-secondary);">
                <i class="fas fa-clock"></i>
                总计: ${timings.total}ms
            </span>
        `);
    }
    
    return `<div class="timings">${items.join('')}</div>`;
}

// 获取问题类型样式类
function getQueryTypeClass(type) {
    const classes = {
        '法律案例': 'legal',
        '通用问题': 'general',
        '其他专业知识': 'other'
    };
    return classes[type] || 'general';
}

// 获取问题类型名称
function getQueryTypeName(type) {
    return type || '通用问题';
}

// 创建新对话
async function createNewConversation() {
    try {
        const response = await fetch('/api/conversation/new', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            state.currentConversationId = data.conversation_id;
            loadConversations();
            renderConversation(data.conversation);
            elements.currentTitle.textContent = '新对话';
            
            // 移动端关闭侧边栏
            if (window.innerWidth <= 768) {
                elements.sidebar.classList.remove('open');
            }
        }
    } catch (error) {
        showToast('创建对话失败', 'error');
        console.error('创建对话失败:', error);
    }
}

// 删除对话
async function deleteConversation(conversationId, event) {
    event.stopPropagation();
    
    if (!confirm('确定要删除这个对话吗？')) return;
    
    try {
        const response = await fetch(`/api/conversation/${conversationId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            if (state.currentConversationId === conversationId) {
                state.currentConversationId = null;
                elements.welcomeScreen.classList.remove('hidden');
                elements.messagesContainer.classList.remove('visible');
                elements.messagesContainer.innerHTML = '';
                elements.currentTitle.textContent = '新对话';
            }
            loadConversations();
            showToast('对话已删除', 'success');
        }
    } catch (error) {
        showToast('删除对话失败', 'error');
        console.error('删除对话失败:', error);
    }
}

// 清空所有对话
async function clearAllConversations() {
    if (!confirm('确定要清空所有对话吗？此操作不可恢复。')) return;
    
    try {
        const response = await fetch('/api/clear', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            state.currentConversationId = null;
            state.conversations = {};
            elements.welcomeScreen.classList.remove('hidden');
            elements.messagesContainer.classList.remove('visible');
            elements.messagesContainer.innerHTML = '';
            elements.currentTitle.textContent = '新对话';
            loadConversations();
            showToast('所有对话已清空', 'success');
        }
    } catch (error) {
        showToast('清空失败', 'error');
        console.error('清空失败:', error);
    }
}

// 发送消息
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message) return;
    
    // 显示消息容器
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.classList.add('visible');
    
    // 添加用户消息
    appendMessage({ role: 'user', content: message });
    
    // 清空输入框
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    
    // 显示正在输入动画
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: state.currentConversationId
            })
        });
        
        const data = await response.json();
        
        // 隐藏正在输入动画
        hideTypingIndicator();
        
        if (data.success) {
            state.currentConversationId = data.conversation_id;
            
            // 添加助手消息
            appendMessage({
                role: 'assistant',
                content: data.reply,
                timings: data.timings
            });
            
            // 更新标题
            if (!state.conversations[data.conversation_id]) {
                loadConversations();
            }
            elements.currentTitle.textContent = message.slice(0, 20) + (message.length > 20 ? '...' : '');
        } else {
            showToast(data.error || '发送失败', 'error');
        }
    } catch (error) {
        hideTypingIndicator();
        showToast('发送失败，请检查网络连接', 'error');
        console.error('发送失败:', error);
    }
}

// 切换录音状态
async function toggleRecording() {
    if (state.isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

// 开始录音
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            } 
        });
        
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];
        state.recordingStartTime = Date.now();
        
        state.mediaRecorder.ondataavailable = (event) => {
            state.audioChunks.push(event.data);
        };
        
        state.mediaRecorder.onstop = () => {
            processRecording();
            stream.getTracks().forEach(track => track.stop());
        };
        
        state.mediaRecorder.start();
        state.isRecording = true;
        
        // 更新UI
        elements.voiceBtn.classList.add('recording');
        elements.recordingIndicator.classList.add('visible');
        
        // 开始计时
        state.recordingTimer = setInterval(updateRecordingTime, 100);
        
    } catch (error) {
        showToast('无法访问麦克风，请检查权限设置', 'error');
        console.error('麦克风访问失败:', error);
    }
}

// 停止录音
function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        
        // 更新UI
        elements.voiceBtn.classList.remove('recording');
        elements.recordingIndicator.classList.remove('visible');
        
        // 停止计时
        if (state.recordingTimer) {
            clearInterval(state.recordingTimer);
            state.recordingTimer = null;
        }
    }
}

// 更新录音时间显示
function updateRecordingTime() {
    const elapsed = Date.now() - state.recordingStartTime;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const displaySeconds = seconds % 60;
    elements.recordingTime.textContent = 
        `${minutes.toString().padStart(2, '0')}:${displaySeconds.toString().padStart(2, '0')}`;
}

// 处理录音
async function processRecording() {
    if (state.audioChunks.length === 0) {
        showToast('录音为空', 'error');
        return;
    }
    
    const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
    
    // 显示消息容器
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.classList.add('visible');
    
    // 显示正在输入动画
    showTypingIndicator();
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        if (state.currentConversationId) {
            formData.append('conversation_id', state.currentConversationId);
        }
        
        const response = await fetch('/api/voice', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // 隐藏正在输入动画
        hideTypingIndicator();
        
        if (data.success) {
            state.currentConversationId = data.conversation_id;
            
            // 添加用户消息
            appendMessage({
                role: 'user',
                content: data.recognized_text,
                voice: true
            });
            
            // 添加助手消息
            appendMessage({
                role: 'assistant',
                content: data.reply,
                voice: true,
                timings: data.timings
            });
            
            // 更新标题
            loadConversations();
            elements.currentTitle.textContent = data.recognized_text.slice(0, 20) + 
                (data.recognized_text.length > 20 ? '...' : '');
        } else {
            showToast(data.error || '语音识别失败', 'error');
        }
    } catch (error) {
        hideTypingIndicator();
        showToast('语音处理失败', 'error');
        console.error('语音处理失败:', error);
    }
}

// 播放音频
async function playAudio(text) {
    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        if (response.ok) {
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
            
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };
        } else {
            showToast('语音合成失败', 'error');
        }
    } catch (error) {
        showToast('播放失败', 'error');
        console.error('播放失败:', error);
    }
}

// 检查服务状态
async function checkServiceStatus() {
    // 检查 SenseVoice 状态
    try {
        const response = await fetch('/api/conversations', { 
            method: 'GET',
            signal: AbortSignal.timeout(3000)
        });
        if (response.ok) {
            elements.sensevoiceStatus.classList.add('online');
        } else {
            elements.sensevoiceStatus.classList.add('offline');
        }
    } catch {
        elements.sensevoiceStatus.classList.add('offline');
    }
    
    // llama.cpp 状态通过实际调用才能确认，这里暂时显示为在线
    elements.llamacppStatus.classList.add('online');
}

// 显示加载状态
function showLoading() {
    elements.loadingOverlay.classList.add('visible');
}

// 隐藏加载状态
function hideLoading() {
    elements.loadingOverlay.classList.remove('visible');
}

// 显示 Toast 提示
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? 'check-circle' : 
                 type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 滚动到底部
function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 全局函数暴露
window.deleteConversation = deleteConversation;
window.playAudio = playAudio;