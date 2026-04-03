<p align="center">
    <br>
    <img src="https://github.com/beanszero1/ekhoa/blob/main/badge.png" width="200"/>
    <br>
</p>

<p align="center">
  <a href="README_zh.md">中文</a> &nbsp ｜ &nbsp English &nbsp
</p>
<p align="center">
<img src="https://img.shields.io/badge/python-3.13-blue">
<a href="https://github.com/beanszero1/ekhoa/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
<a href="https://github.com/beanszero1/ekhoa/pulls"><img src="https://img.shields.io/badge/PR-welcome-55EB99.svg" alt="PRs Welcome"></a>
<p>


<p align="center">
  <a href="https://github.com/beanszero1/ekhoa"> 📖 GitHub Repository</a>
<p>

> ⭐ If you like this project, please click the "Star" button in the upper right corner to support us. Your support is our motivation to move forward!

## 📝 Introduction

Ekhoa is an open-source Chinese voice assistant based on Raspberry Pi 5. The system uses a fine-tuned qwen2.5-0.5B-Q8_0 model specifically optimized for legal case Q&A, intelligently identifies question types, and provides accurate answers. It supports offline speech recognition, speech synthesis, OLED screen real-time display. The modular design facilitates expansion and is suitable for home assistants, educational learning, and privacy-sensitive intelligent interaction scenarios.

## ✨ Key Features

- **🎯 Intelligent Task Classification**: Automatically distinguishes between legal cases and general questions
- **🔒 Local-First**: Qwen2.5 model runs locally to protect privacy
- **🎤 Offline Speech**: SenseVoice speech recognition, no cloud required
- **📺 Visual Feedback**: OLED screen displays conversation content in real-time
- **🧩 Modular Design**: Each component can be independently replaced and upgraded

## 📸 Screenshots

<div align="center">
  <img src="https://github.com/beanszero1/ekhoa/blob/main/pic/example1.png" width="300"/>
  <img src="https://github.com/beanszero1/ekhoa/blob/main/pic/example2.png" width="300"/>
  <img src="https://github.com/beanszero1/ekhoa/blob/main/pic/example3.png" width="300"/>
</div>

## 🎉 What's New


- 🔥 **[2026.04.02]** Added WebUI interface with text chat and voice input support, fixed audio format conversion, and optimized AI timeout settings
- 🔥 **[2026.03.23]** Added support for llama.cpp deployment instead of Ollama
- 🔥 **[2026.03.23]** Enhanced recording experience with timing display during and after audio recording
- 🔥 **[2026.02.27]** Transitioned from Dify platform to fine-tuned qwen2.5-0.5B-Q8_0 model for legal case Q&A
- 🔥 **[2026.02.27]** Added OLED screen module to display each user-AI conversation
- 🔥 **[2026.02.05]** Integrated Alibaba Bailian SDK with multi-round conversation memory functionality
- 🔥 **[2026.02.05]** Refactored TTS module to support queue management and pseudo-streaming speech output
- 🔥 **[2026.01.26]** Upgraded ASR from Vosk offline recognition to SenseVoice recognition service, supporting automatic multi-language recognition
- 🔥 **[2026.01.26]** Added spacebar recording control, supporting manual start/stop recording
- 🔥 **[2026.01.26]** Unified logging system and optimized audio buffer processing

<details><summary>More</summary>

- 🔥 **[2025.12.15]** Initial project release with basic voice assistant functionality
</details>

## 🛠️ Hardware Requirements

- **Raspberry Pi 5** with at least 8GB RAM
- **Microphone**: USB microphone supporting 16kHz sampling rate
- **Speaker or Headphone** for audio output
- **OLED Display** (optional, for visual feedback)
- **Power Supply**: Official Raspberry Pi 5 power supply recommended

## 💻 Software Dependencies

### System Dependencies
- **Python**: 3.13
- **Operating System**: Raspberry Pi OS 64-bit
- **Chinese Language Pack**: Required for Chinese speech recognition
- **Audio Drivers**: ALSA sound system

### Python Packages
All Python dependencies are listed in `requirements.txt`. Key packages include:
- `pyaudio` for audio input/output
- `requests` for API communication
- `pillow` for OLED display
- `luma.oled` for OLED screen control

## 🚀 Quick Start

### 1. Configure Chinese Environment

```bash
# 1. Open Raspberry Pi configuration tool
sudo raspi-config

# 2. Select "Localisation Options" -> "Locale"
# 3. Find "zh_CN.UTF-8 UTF-8" in the language list, select with spacebar
# 4. Press Enter to confirm, system will start configuring Chinese environment
# 5. Reboot Raspberry Pi after completion
sudo reboot

# 6. Install Chinese input method
sudo apt-get install -y fcitx-googlepinyin

# 7. Reboot again to activate input method
sudo reboot
```

### 2. Install System Dependencies and Python Packages

```bash
sudo apt install espeak espeak-ng python3-pyaudio libasound2-dev
    
# Activate virtual environment
source ~/your_venv/bin/activate

pip install -r requirements.txt
```

### 3. use llama.cpp

```bash

cd ~/ekhoa/llama.cpp/release/bin

./llama-server -m ~/your_model.gguf

```



#### Model Features

- **Fine-tuned for Legal Q&A**: Specially optimized for Chinese legal case questions
- **Local Execution**: Runs entirely on your Raspberry Pi, ensuring privacy
- **Low Resource Requirements**: Q8_0 quantization balances quality and performance
- **Smart Classification**: Automatically distinguishes between legal cases and general questions

#### How It Works

1. The system uses the fine-tuned qwen2.5-0.5B-Q8_0 model for all legal-related questions
2. General questions are handled by the standard Qwen2.5 model
3. The question classification happens automatically based on the content

**Note**: The fine-tuned model is included with the project and will be used automatically when legal questions are detected.

## 📖 Usage Guide

### Starting the Program

```bash
# Install system dependencies
sudo apt install espeak espeak-ng python3-pyaudio libasound2-dev ffmpeg

# Activate virtual environment
source ~/your_venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Start all services (llama.cpp, SenseVoice, main program)
cd ~/path/to/ekhoa/script
./start_all.sh

# Or start WebUI separately
cd ~/path/to/ekhoa/ekhoa
python webui.py
```

### Interaction Methods

**Command Line Mode:**
1. After program starts, system service check will be performed
2. After check passes, voice assistant will prompt "Voice assistant startup complete, ready to serve you"
3. Speak directly into microphone to start conversation
4. Say wake words (default: "Assistant", "Hello", "Please", "Help") to trigger conversation

**WebUI Mode:**
1. Open browser and visit `http://127.0.0.1:5000`
2. Use text input or click microphone button for voice input

## ⚙️ Configuration

All configurations are in the `config.py` file. Main configuration parameters are as follows:

### AI Model Configuration
```python
AI_MODEL = "qwen2.5-0.5B-Q8_0"     # Local  model
OLLAMA_URL = "http://127.0.0.1:8080/api/chat"  # llama.cpp service address
```

### Speech Recognition Configuration
```python
SENSEVOICE_API_URL = "http://127.0.0.1:7860/api/v1/asr"  # SenseVoice service address
SAMPLE_RATE = 16000       # Audio sampling rate
```

### OLED Display Configuration
```python
OLED_ENABLED = True                           # Whether to enable OLED display
OLED_WIDTH = 128                              # OLED screen width
OLED_HEIGHT = 64                              # OLED screen height
OLED_FONT_SIZE = 10                           # Font size (10px)
OLED_STARTUP_ANIMATION_DURATION = 2.0         # Startup animation duration (seconds)
OLED_SHOW_BORDER = False                      # Whether to show complete border
```

### 
## 🔧 Troubleshooting

### 1. No Audio Output

Create `.asoundrc` file in `/home/your_username/` directory to bind Raspberry Pi audio input and output.

```bash
sudo nano ~/.asoundrc
```

Input the following content (port number 2 is used here, device port numbers can be checked using `arecord -l` and `aplay -l`):

```
# Default playback device
pcm.!default {
    type plug
    slave {
        pcm "hw:2,0"
    }
}

# Default recording device
pcm.!dsnoop {
    type dsnoop
    ipc_key 1024
    slave {
        pcm "hw:2,0"
    }
}

# Default control device
ctl.!default {
    type hw
    card 2
}
```

### 2. Common Issues and Solutions

- **Microphone not detected**: Check USB connection and run `arecord -l` to verify
- **Speech recognition not working**: Ensure SenseVoice service is running on port 7860
- **OLED display not showing**: Check I2C connection and install `luma.oled` library
- **Ollama model not loading**: Verify Ollama service is running on port 11434

## 🧩 API Extensions

The project uses modular design, allowing easy replacement or extension:

- **ASR Module**: Replace with other speech recognition engines
- **TTS Module**: Replace with other speech synthesis engines  
- **AI Module**: Replace with other local AI models
- **Display Module**: Replace OLED with other display types
- **Wake Word Module**: Customize wake word detection logic



## 📸 Screenshots

<div align="center">
  <img src="https://github.com/beanszero1/ekhoa/blob/main/pic/example1.png" width="700"/>
  <br><br>
  <img src="https://github.com/beanszero1/ekhoa/blob/main/pic/example2.png" width="700"/>
  <br><br>
  <img src="https://github.com/beanszero1/ekhoa/blob/main/pic/example3.png" width="700"/>
</div>

## ❤️ Community & Support

Welcome to join our community to communicate with other developers and get help.

We provide support through the following channels:

- **GitHub Issues**: For bug reports, feature requests, and discussions
- **GitHub Discussions**: For community discussions and Q&A
- **Email**: For direct inquiries and support

If you have questions about Ekhoa or need help with implementation, feel free to reach out!

## 👷‍♂️ Contributing

We welcome contributions from the community! If you want to add new features, improve documentation, or fix bugs, please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

Please ensure your code follows the existing style and includes appropriate tests.

## 📚 Citation

If you use Ekhoa in your research or project, please cite our work:

```bibtex
@misc{ekhoa_2026,
    title={{Ekhoa}: Raspberry Pi Voice Assistant with Local AI},
    author={Beanszero1},
    year={2026},
    url={https://github.com/beanszero1/ekhoa}
}
```

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=beanszero1/ekhoa&type=Date)](https://star-history.com/#beanszero1/ekhoa&Date)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [QwenLM](https://github.com/QwenLM) for the Qwen2.5 model
- [llama.cpp](https://github.com/ggml-org/llama.cpp#) for making your local GGUF model run faster
- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) for speech recognition
- Raspberry Pi community for hardware support
