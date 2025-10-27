# speech-to-text-to-speech

Simple locally hosted speech-to-text-to-speech application inspired by Zentreya's TTS setup. Supports multiple STT engines (Whisper, Parakeet) and TTS services (Speakerbot, NeuTTS, Piper, StyleTTS2).

## Features

- 🎤 Real-time audio capture from microphone
- 🧠 **Multiple STT options:** OpenAI Whisper or NVIDIA Parakeet-TDT (ultra-fast, multilingual)
- 🔌 **Multiple TTS options:** Speakerbot WebSocket, NeuTTS Air, Piper, or StyleTTS2
- 🎭 Voice cloning support with NeuTTS Air and StyleTTS2
- 🔊 Queue-based audio playback with output device selection (local TTS)
- ⚙️ Configurable via environment variables
- 🐳 Docker support with GPU passthrough
- 🚀 Easy setup with automated installation scripts

## 📚 Tutorials

**For Non-Technical Users:**
- 🆕 **[Windows Setup Guide](WINDOWS_SETUP.md)** - **RECOMMENDED** - Complete automated setup with one-click installation of all dependencies (Python, FFmpeg, CUDA, espeak-ng)
- [Windows Setup Guide with Local NeuTTS (FREE, Offline)](WINDOWS_NEUTTS_LOCAL_TTS_TUTORIAL.md) - Alternative beginner-friendly guide for manual setup with local text-to-speech and voice cloning
- [Windows Setup Guide with Google Cloud TTS and Streamer Bot](WINDOWS_GOOGLE_CLOUD_TTS_STREAMER_BOT_TUTORIAL.md) - Comprehensive guide for cloud-based TTS with Streamer Bot integration

## Requirements

- Python 3.8 or higher
- PortAudio (for microphone input)
- FFmpeg (for Whisper audio processing)
- CUDA-capable GPU (optional, but recommended for better performance)

## Quick Start

> 🚀 **New!** Automated Windows installer now available! See [INSTALL_GUIDE.md](INSTALL_GUIDE.md) for all installation options.

### Windows (Recommended Methods)

#### Method 1: Fully Automated Setup ⭐ (Easiest)

Automatically installs **everything** including Python, FFmpeg, CUDA, and espeak-ng:

1. Clone or download this repository
2. **Right-click `setup.bat`** → Select **"Run as Administrator"**
3. Follow the prompts (takes 20-30 minutes)
4. Edit `.env` file to configure
5. Run `run.bat`

📖 **Full guide:** [WINDOWS_SETUP.md](WINDOWS_SETUP.md)

#### Method 2: Quick Setup (If you have Python)

If you already have Python 3.8+ installed:

1. Clone the repository
2. Double-click `install.bat`
3. Edit `.env` file
4. Run `run.bat`

*Note: Requires FFmpeg and espeak-ng to be installed separately*

#### Method 3: Check Your System First

Not sure what you need? Run the system check:

1. Double-click `check-system.bat`
2. See what's installed and get recommendations
3. Follow the suggested installation method

### Linux/macOS

#### Automated Setup Scripts (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/caesarakalaeii/speech-to-text-to-speech.git
cd speech-to-text-to-speech
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Configure your settings:
```bash
# Edit .env to set your TTS service and configuration
nano .env
```

4. Run the application:
```bash
source venv/bin/activate
python main.py
```

### Method 2: Docker Setup (with GPU support)

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

For GPU support, ensure you have:
- NVIDIA Docker runtime installed
- Compatible NVIDIA drivers

## Configuration

Edit the `.env` file to customize settings:

```bash
# STT Service: whisper or parakeet
STT_SERVICE=whisper

# Whisper model size (if STT_SERVICE=whisper)
WHISPER_MODEL=base

# Parakeet model (if STT_SERVICE=parakeet)
PARAKEET_MODEL=nvidia/parakeet-tdt-0.6b-v3

# TTS Service: speakerbot, neutts, piper, or styletts2
TTS_SERVICE=speakerbot

# Speakerbot settings (if TTS_SERVICE=speakerbot)
SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080
VOICE_NAME=Sally

# NeuTTS Air settings (if TTS_SERVICE=neutts)
NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
NEUTTS_BACKBONE_DEVICE=cpu
NEUTTS_REF_AUDIO=samples/reference.wav
NEUTTS_REF_TEXT=samples/reference.txt

# Piper settings (if TTS_SERVICE=piper)
PIPER_VOICE_PATH=

# StyleTTS2 settings (if TTS_SERVICE=styletts2)
STYLETTS2_REF_AUDIO=samples/reference.wav

# Audio settings
SAMPLE_RATE=16000
CHUNK_DURATION=3.0
SILENCE_THRESHOLD=0.01
MIN_SPEECH_DURATION=0.5
```

### STT (Speech-to-Text) Service Options

#### Whisper (Default)
- OpenAI's Whisper speech recognition model
- Well-established and reliable
- Multiple model sizes available (tiny to large)
- Set `STT_SERVICE=whisper` in `.env`
- Included in base installation
- Choose model size with `WHISPER_MODEL`:
  - `tiny`: Fastest, least accurate (~1GB RAM)
  - `base`: Good balance (~1GB RAM) - **Default**
  - `small`: Better accuracy (~2GB RAM)
  - `medium`: High accuracy (~5GB RAM)
  - `large`: Best accuracy (~10GB RAM)

#### Parakeet TDT
- NVIDIA's Parakeet-TDT model - ultra-fast transcription
- **Transcribes 60 minutes of audio per second**
- Supports 25 European languages with automatic language detection
- Set `STT_SERVICE=parakeet` in `.env`
- Install dependencies: `pip install -r requirements-parakeet.txt`
- Requires PyTorch (automatically configured for CPU or CUDA)
- Model automatically downloads on first use (~600MB)
- Best with GPU but works well on CPU

### TTS Service Options

#### Speakerbot (Default)
- Connects to a local Speakerbot instance via WebSocket
- Requires Speakerbot to be running locally
- Set `TTS_SERVICE=speakerbot` in `.env`
- Configure `SPEAKERBOT_WEBSOCKET_URL` and `VOICE_NAME`

#### NeuTTS Air
- Uses the locally-run NeuTTS Air neural TTS model (https://github.com/neuphonic/neutts-air)
- Runs entirely on your device - no API calls or internet required
- Supports instant voice cloning from a reference audio sample
- **Queue-based audio playback**: Generated speech is played through a selected output device
- **Output device selection**: GUI dialog allows you to choose your preferred audio output
- Set `TTS_SERVICE=neutts` in `.env`
- Install additional dependencies: `pip install -r requirements-neutts.txt`
- Install espeak: `brew install espeak` (macOS) or `sudo apt install espeak` (Linux)
- Configure reference audio and text files for voice cloning
- Choose backbone model based on your device:
  - `neuphonic/neutts-air-q4-gguf`: Recommended for most devices (with llama-cpp-python)
  - `neuphonic/neutts-air-q8-gguf`: Better quality, more resources
  - `neuphonic/neutts-air`: Full PyTorch model, highest quality but slowest

#### Piper
- Fast local TTS with ONNX models
- Pre-trained voices only (no voice cloning)
- Very lightweight and runs efficiently on CPU
- Set `TTS_SERVICE=piper` in `.env`
- Install dependencies: `pip install -r requirements-piper.txt`
- Voice models auto-download on first use or download from HuggingFace

#### StyleTTS2
- Modern neural TTS with voice cloning
- Clone voices from 3-15 second audio samples
- Set `TTS_SERVICE=styletts2` in `.env`
- Install dependencies: `pip install -r requirements-styletts2.txt`
- Requires PyTorch
- Optional reference audio for voice cloning

## Manual Installation

If you prefer manual installation:

### Windows

```cmd
REM Install ffmpeg (using Chocolatey or Scoop)
choco install ffmpeg
REM OR: scoop install ffmpeg
REM OR download from: https://www.gyan.dev/ffmpeg/builds/

REM Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

REM Install Python dependencies
pip install -r requirements.txt

REM Note: If PyAudio installation fails, download a pre-built wheel from:
REM https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
REM Then install with: pip install PyAudio-X.X.X-cpXX-cpXX-win_amd64.whl

REM Copy and configure environment
copy .env.example .env
notepad .env
```

### Linux/Ubuntu

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip portaudio19-dev ffmpeg

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env
```

### macOS

```bash
# Install system dependencies
brew install portaudio ffmpeg

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
nano .env
```

## Usage

Once running, the application will:

1. Start listening to your microphone
2. Detect speech segments based on audio energy
3. Transcribe speech using Whisper
4. Generate speech using your configured TTS service (Speakerbot or NeuTTS Air)

Press `Ctrl+C` to stop the application.

## Troubleshooting

### No audio input detected

- Check microphone permissions
- Verify microphone is selected as default input device
- Adjust `SILENCE_THRESHOLD` in `.env` (lower = more sensitive)
- **Windows**: Check Privacy Settings > Microphone and ensure apps have access

### High CPU usage

- Use a smaller Whisper model (`tiny` or `base`)
- Increase `CHUNK_DURATION` to process less frequently

### TTS service connection fails

**For Speakerbot:**
- Verify Speakerbot is running
- Check `SPEAKERBOT_WEBSOCKET_URL` in `.env`
- Ensure firewall allows WebSocket connections

**For NeuTTS Air:**
- Verify you installed dependencies: `pip install -r requirements-neutts.txt`
- Check espeak is installed (`brew install espeak` or `sudo apt install espeak`)
- Verify reference audio and text files exist and are in correct format
- Check that backbone model is downloaded (happens automatically on first run)
- Ensure sufficient RAM/VRAM for the model (Q4 GGUF needs ~2GB)

### PyAudio installation fails on Windows

- Install Microsoft C++ Build Tools from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- OR download a pre-built PyAudio wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
- Install the wheel with: `pip install PyAudio-X.X.X-cpXX-cpXX-win_amd64.whl`

### FFmpeg not found on Windows

- Install using Chocolatey: `choco install ffmpeg`
- OR install using Scoop: `scoop install ffmpeg`
- OR download from https://www.gyan.dev/ffmpeg/builds/ and add to PATH

### CUDA/GPU errors with Docker

- Ensure NVIDIA Docker runtime is installed
- Check GPU drivers are up to date
- Remove GPU configuration from `docker-compose.yml` to run on CPU

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI Whisper for speech recognition
- Inspired by Zentreya's TTS setup
