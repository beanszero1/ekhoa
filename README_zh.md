<p align="center">
    <br>
    <img src="https://github.com/beanszero1/ekhoa/blob/main/badge.png" width="200"/>
    <br>
</p>

<p align="center">
  中文 &nbsp ｜ &nbsp <a href="README.md">English</a> &nbsp
</p>
<p align="center">
<img src="https://img.shields.io/badge/python-3.13-blue">
<a href="https://github.com/beanszero1/ekhoa/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="许可证"></a>
<a href="https://github.com/beanszero1/ekhoa/pulls"><img src="https://img.shields.io/badge/PR-welcome-55EB99.svg" alt="PRs欢迎"></a>
<p>


<p align="center">
  <a href="https://github.com/beanszero1/ekhoa"> 📖 GitHub 仓库</a>
<p>

> ⭐ 如果你喜欢这个项目，请在右上角点击"Star"按钮支持我们。你的支持是我们前进的动力！

## 📝 简介

Ekhoa 是一个基于树莓派5的开源中文语音助手。该系统使用专门为法律案件问答优化的微调版 qwen2.5-0.5B-Q8_0 模型，智能识别问题类型并提供准确回答。支持离线语音识别、语音合成、OLED屏幕实时显示。模块化设计便于扩展，适用于家庭助手、教育学习和注重隐私的智能交互场景。

## ✨ 主要特性

- **🎯 智能任务分类**：自动区分法律案件和一般问题
- **🔒 本地优先**：Qwen2.5 模型在本地运行，保护隐私
- **🎤 离线语音**：SenseVoice 语音识别，无需云端服务
- **📺 视觉反馈**：OLED屏幕实时显示对话内容
- **🧩 模块化设计**：每个组件可独立替换和升级



## 🎉 最新动态


- 🔥 **[2026.03.23]** 添加了对 llama.cpp 部署的支持，替代 Ollama
- 🔥 **[2026.03.23]** 增强录音体验，在音频录制期间和之后显示计时
- 🔥 **[2026.02.27]** 从 Dify 平台过渡到微调版 qwen2.5-0.5B-Q8_0 模型用于法律案件问答
- 🔥 **[2026.02.27]** 添加了 OLED 屏幕模块，显示每个用户-AI 对话
- 🔥 **[2026.02.05]** 集成阿里云百炼 SDK，具有多轮对话记忆功能
- 🔥 **[2026.02.05]** 添加了智能问题分类系统，自动区分法律案件、一般问题和其他专业知识
- 🔥 **[2026.02.05]** 重构 TTS 模块，支持队列管理和伪流式语音输出
- 🔥 **[2026.01.26]** 将 ASR 从 Vosk 离线识别升级到 SenseVoice 识别服务，支持自动多语言识别
- 🔥 **[2026.01.26]** 添加空格键录音控制，支持手动开始/停止录音
- 🔥 **[2026.01.26]** 统一日志系统并优化音频缓冲区处理

<details><summary>更多</summary>

- 🔥 **[2025.12.15]** 初始项目发布，具有基本语音助手功能
</details>

## 🛠️ 硬件要求

- **树莓派5** 至少 8GB RAM
- **麦克风**：支持 16kHz 采样率的 USB 麦克风
- **扬声器或耳机** 用于音频输出
- **OLED 显示屏**（可选，用于视觉反馈）
- **电源**：推荐使用官方树莓派5电源

## 💻 软件依赖

### 系统依赖
- **Python**：3.13
- **操作系统**：树莓派 OS 64位
- **中文语言包**：中文语音识别所需
- **音频驱动**：ALSA 声音系统

### Python 包
所有 Python 依赖项都列在 `requirements.txt` 中。关键包包括：
- `pyaudio` 用于音频输入/输出
- `requests` 用于 API 通信
- `pillow` 用于 OLED 显示
- `luma.oled` 用于 OLED 屏幕控制

## 🚀 快速开始

### 1. 配置中文环境

```bash
# 1. 打开树莓派配置工具
sudo raspi-config

# 2. 选择"Localisation Options" -> "Locale"
# 3. 在语言列表中找到"zh_CN.UTF-8 UTF-8"，用空格键选择
# 4. 按 Enter 确认，系统将开始配置中文环境
# 5. 完成后重启树莓派
sudo reboot

# 6. 安装中文输入法
sudo apt-get install -y fcitx-googlepinyin

# 7. 再次重启以激活输入法
sudo reboot
```

### 2. 安装系统依赖和 Python 包

```bash
sudo apt install espeak espeak-ng python3-pyaudio libasound2-dev
    
# 激活虚拟环境
source ~/your_venv/bin/activate

pip install -r requirements.txt
```

### 3. 使用 llama.cpp

```bash

cd ~/ekhoa/llama.cpp/release/bin

./llama-server -m ~/your_model.gguf

```



#### 模型特性

- **为法律问答微调**：专门针对中文法律案件问题优化
- **本地执行**：完全在你的树莓派上运行，确保隐私
- **低资源需求**：Q8_0 量化在质量和性能之间取得平衡



## 📖 使用指南

### 启动程序

```bash
# 安装系统依赖
sudo apt install espeak espeak-ng python3-pyaudio libasound2-dev

# 激活虚拟环境
source ~/your_venv/bin/activate

# 安装 Python 包
pip install -r requirements.txt

# 启动 SenseVoice API 服务（首次启动可能会自动下载模型文件）
cd ~/path/to/ekhoa/SenseVoice
python api.py
 
# 运行主程序
cd ~/path/to/ekhoa/code
python main.py
```

### 交互方式

1. 程序启动后，将执行系统服务检查
2. 检查通过后，语音助手会提示"语音助手启动完成，准备为您服务"
3. 直接对着麦克风说话开始对话
4. 说出唤醒词（默认："助手"、"你好"、"请"、"帮助"）来触发对话

## ⚙️ 配置

所有配置都在 `config.py` 文件中。主要配置参数如下：

### AI 模型配置
```python
AI_MODEL = "qwen2.5-0.5B-Q8_0"     # 本地模型
OLLAMA_URL = "http://127.0.0.1:8080/api/chat"  # llama.cpp 服务地址
```

### 语音识别配置
```python
SENSEVOICE_API_URL = "http://127.0.0.1:7860/api/v1/asr"  # SenseVoice 服务地址
SAMPLE_RATE = 16000       # 音频采样率
```

### OLED 显示配置
```python
OLED_ENABLED = True                           # 是否启用 OLED 显示
OLED_WIDTH = 128                              # OLED 屏幕宽度
OLED_HEIGHT = 64                              # OLED 屏幕高度
OLED_FONT_SIZE = 10                           # 字体大小（10px）
OLED_STARTUP_ANIMATION_DURATION = 2.0         # 启动动画持续时间（秒）
OLED_SHOW_BORDER = False                      # 是否显示完整边框
```

### 
## 🔧 故障排除

### 1. 没有音频输出

在 `/home/your_username/` 目录中创建 `.asoundrc` 文件，绑定树莓派音频输入和输出。

```bash
sudo nano ~/.asoundrc
```

输入以下内容（这里使用端口号 2，设备端口号可以使用 `arecord -l` 和 `aplay -l` 检查）：

```
# 默认播放设备
pcm.!default {
    type plug
    slave {
        pcm "hw:2,0"
    }
}

# 默认录音设备
pcm.!dsnoop {
    type dsnoop
    ipc_key 1024
    slave {
        pcm "hw:2,0"
    }
}

# 默认控制设备
ctl.!default {
    type hw
    card 2
}
```

### 2. 常见问题及解决方案

- **麦克风未检测到**：检查 USB 连接并运行 `arecord -l` 验证
- **语音识别不工作**：确保 SenseVoice 服务在端口 7860 上运行
- **OLED 显示不显示**：检查 I2C 连接并安装 `luma.oled` 库
- **Ollama 模型未加载**：验证 Ollama 服务在端口 11434 上运行

## 🧩 API 扩展

项目采用模块化设计，允许轻松替换或扩展：

- **ASR 模块**：替换为其他语音识别引擎
- **TTS 模块**：替换为其他语音合成引擎  
- **AI 模块**：替换为其他本地 AI 模型
- **显示模块**：将 OLED 替换为其他显示类型
- **唤醒词模块**：自定义唤醒词检测逻辑



## 👷‍♂️ 贡献

我们欢迎社区的贡献！如果你想添加新功能、改进文档或修复错误，请：

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 提交拉取请求

请确保你的代码遵循现有风格并包含适当的测试。

## 📚 引用

如果你在研究或项目中使用 Ekhoa，请引用我们的工作：

```bibtex
@misc{ekhoa_2026,
    title={{Ekhoa}: Raspberry Pi Voice Assistant with Local AI},
    author={Beanszero1},
    year={2026},
    url={https://github.com/beanszero1/ekhoa}
}
```

## ⭐ Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=beanszero1/ekhoa&type=Date)](https://star-history.com/#beanszero1/ekhoa&Date)

## 📄 许可证

本项目采用 MIT 许可证 - 详情请见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [QwenLM](https://github.com/QwenLM) 提供Qwen2.5模型
- [llama.cpp](https://github.com/ggml-org/llama.cpp#) 让本地部署的大模型运行效率更高
- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 提供离线语音识别
- 树莓派社区提供硬件支持
