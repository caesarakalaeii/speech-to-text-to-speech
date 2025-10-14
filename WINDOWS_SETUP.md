# Windows Setup Guide

Complete guide for setting up speech-to-text-to-speech on Windows, including automatic installation of all dependencies including CUDA and espeak-ng.

## Table of Contents

- [Quick Start (Automatic Installation)](#quick-start-automatic-installation)
- [Manual Installation](#manual-installation)
- [System Requirements](#system-requirements)
- [Troubleshooting](#troubleshooting)

## Quick Start (Automatic Installation)

The easiest way to set up the application on Windows is using the automated setup script. This will install **all** dependencies automatically, including:

- Python 3.11
- FFmpeg (audio processing)
- espeak-ng (text-to-speech phonetics)
- CUDA Toolkit (optional, for GPU acceleration)
- All Python dependencies

### Steps:

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/caesarakalaeii/speech-to-text-to-speech.git
   cd speech-to-text-to-speech
   ```

2. **Run the automated setup:**
   
   Right-click on `setup.bat` and select **"Run as Administrator"**
   
   Or from PowerShell (run as Administrator):
   ```powershell
   .\setup.bat
   ```

3. **Follow the prompts:**
   - The script will check for and install missing dependencies
   - You'll be asked if you want to install CUDA (for GPU acceleration)
   - You'll be asked if you want to install NeuTTS Air (local TTS with voice cloning)
   - Installation may take 20-30 minutes depending on your internet speed

4. **Configure the application:**
   
   Edit the `.env` file to configure your settings:
   - For NeuTTS: Set paths to reference audio and text files
   - For Speakerbot: Set WebSocket URL and voice name
   - Choose Whisper model size (tiny/base/small/medium/large)

5. **Run the application:**
   ```cmd
   run.bat
   ```

## Manual Installation

If you prefer to install dependencies manually or don't have administrator privileges:

### Prerequisites

Before running the manual installation, ensure you have:

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **Important:** Check "Add Python to PATH" during installation

2. **FFmpeg**
   - **Option 1 - Chocolatey:** `choco install ffmpeg`
   - **Option 2 - Scoop:** `scoop install ffmpeg`
   - **Option 3 - Manual:**
     1. Download from: https://www.gyan.dev/ffmpeg/builds/
     2. Extract to a folder (e.g., `C:\ffmpeg`)
     3. Add `C:\ffmpeg\bin` to your system PATH

3. **espeak-ng** (only needed for NeuTTS)
   - Download from: https://github.com/espeak-ng/espeak-ng/releases
   - Download the `.msi` installer (e.g., `espeak-ng-1.51-x64.msi`)
   - Run the installer
   - ⚠️ **Important:** Check "Add to PATH" during installation

4. **CUDA Toolkit** (optional, for GPU acceleration)
   - Only needed if you have an NVIDIA GPU
   - Download from: https://developer.nvidia.com/cuda-downloads
   - Install CUDA 12.1 or later for best PyTorch compatibility
   - Requires ~3GB download and 20-30 minutes to install

### Installation Steps

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/caesarakalaeii/speech-to-text-to-speech.git
   cd speech-to-text-to-speech
   ```

2. **Run the installation script:**
   ```cmd
   install.bat
   ```
   
   This will:
   - Create a Python virtual environment
   - Install base Python dependencies
   - Optionally install NeuTTS Air dependencies
   - Create configuration file

3. **Configure the application:**
   
   Edit `.env` to set your preferences (see [Configuration](#configuration) below)

4. **Run the application:**
   ```cmd
   run.bat
   ```

## Configuration

The application is configured via the `.env` file. Key settings:

### Choose TTS Service

```bash
# Use local NeuTTS Air (offline, voice cloning)
TTS_SERVICE=neutts

# Or use Speakerbot (requires external service)
TTS_SERVICE=speakerbot
```

### NeuTTS Air Settings

```bash
# Model - choose based on your system:
# - neuphonic/neutts-air-q4-gguf: Recommended for most systems (~2GB)
# - neuphonic/neutts-air-q8-gguf: Better quality, more memory (~4GB)
# - neuphonic/neutts-air: Full model, best quality, slowest (~6GB)
NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf

# Device - use 'cuda' if you have NVIDIA GPU, 'cpu' otherwise
NEUTTS_BACKBONE_DEVICE=cpu  # Change to 'cuda' for GPU acceleration
NEUTTS_CODEC_DEVICE=cpu

# Reference audio for voice cloning
# Prepare a 3-15 second audio file in .wav format
NEUTTS_REF_AUDIO=samples/reference.wav
NEUTTS_REF_TEXT=samples/reference.txt
```

### Speakerbot Settings

```bash
SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080
VOICE_NAME=Sally
```

### Whisper Model Settings

```bash
# Choose model size based on your system:
# - tiny:   Fastest, least accurate (~1GB RAM)
# - base:   Good balance (~1GB RAM) - Default
# - small:  Better accuracy (~2GB RAM)
# - medium: High accuracy (~5GB RAM)
# - large:  Best accuracy (~10GB RAM)
WHISPER_MODEL=base
```

## System Requirements

### Minimum Requirements

- **OS:** Windows 10 or later (64-bit)
- **CPU:** Dual-core processor (2 GHz or higher)
- **RAM:** 4 GB (8 GB recommended for NeuTTS)
- **Disk Space:** 5 GB free space (10 GB for NeuTTS with models)
- **Microphone:** Any USB or built-in microphone
- **Python:** 3.8 or higher

### Recommended Requirements

- **OS:** Windows 10/11 (64-bit)
- **CPU:** Quad-core processor (3 GHz or higher)
- **RAM:** 16 GB
- **GPU:** NVIDIA GPU with 4GB+ VRAM (for CUDA acceleration)
- **Disk Space:** 10 GB free space (for NeuTTS models and CUDA)

### GPU Acceleration (Optional)

For faster speech recognition and TTS generation:

- **NVIDIA GPU** with compute capability 3.5 or higher
- **CUDA Toolkit 12.1** or later
- **Updated NVIDIA drivers**

GPU provides 3-10x speed improvement but is not required.

## Troubleshooting

### Python not found

**Error:** `'python' is not recognized as an internal or external command`

**Solution:**
1. Install Python from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. If already installed, manually add Python to PATH:
   - Open "Environment Variables" in Windows settings
   - Add Python installation directory to PATH (e.g., `C:\Users\YourName\AppData\Local\Programs\Python\Python311`)

### FFmpeg not found

**Error:** FFmpeg errors or "ffmpeg not found"

**Solution:**
1. Run `setup.bat` for automatic installation, or
2. Install manually:
   - Download from https://www.gyan.dev/ffmpeg/builds/
   - Extract to `C:\ffmpeg`
   - Add `C:\ffmpeg\bin` to system PATH

### PyAudio installation fails

**Error:** `Failed to build PyAudio` or `Microsoft Visual C++ required`

**Solutions:**

**Option 1** - Use setup.bat (automatic)

**Option 2** - Install build tools:
1. Install Visual C++ Build Tools from:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. During installation, select "Desktop development with C++"
3. Restart and try again

**Option 3** - Use pre-built wheel:
1. Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Choose the correct version for your Python (e.g., `PyAudio-0.2.11-cp311-cp311-win_amd64.whl` for Python 3.11)
3. Install: `.\venv\Scripts\pip.exe install PyAudio-0.2.11-cp311-cp311-win_amd64.whl`

### espeak-ng not found (NeuTTS only)

**Error:** `espeak-ng not found` or phonemizer errors

**Solution:**
1. Run `setup.bat` for automatic installation, or
2. Install manually:
   - Download from: https://github.com/espeak-ng/espeak-ng/releases
   - Download the `.msi` installer (e.g., `espeak-ng-1.51-x64.msi`)
   - Run installer and check "Add to PATH"
   - Restart terminal/command prompt

### CUDA not working

**Error:** PyTorch not using GPU or CUDA errors

**Solution:**
1. Verify CUDA installation:
   ```cmd
   nvcc --version
   ```
2. Check GPU is detected:
   ```cmd
   nvidia-smi
   ```
3. Reinstall PyTorch with CUDA:
   ```cmd
   .\venv\Scripts\activate
   pip uninstall torch torchaudio
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
4. Update .env to use GPU:
   ```
   NEUTTS_BACKBONE_DEVICE=cuda
   NEUTTS_CODEC_DEVICE=cuda
   ```

### No microphone input detected

**Error:** Application runs but doesn't detect speech

**Solutions:**
1. **Check privacy settings:**
   - Go to Settings > Privacy > Microphone
   - Enable microphone access for apps

2. **Check microphone is working:**
   - Test in Windows Sound settings
   - Ensure it's set as default recording device

3. **Adjust sensitivity:**
   - Lower `SILENCE_THRESHOLD` in .env (e.g., `0.005`)
   - Reduce `MIN_SPEECH_DURATION` (e.g., `0.3`)

4. **Select correct microphone:**
   - Application shows microphone selector on startup
   - Choose your active microphone from the list

### Application crashes immediately

**Error:** Application exits with error

**Debug steps:**
1. Run from command line to see errors:
   ```cmd
   .\venv\Scripts\activate
   python main.py
   ```

2. Check .env file is configured correctly

3. Verify all dependencies installed:
   ```cmd
   .\venv\Scripts\pip.exe list
   ```

4. Check system resources (RAM, disk space)

### NeuTTS model download slow/fails

**Error:** Model download takes forever or fails

**Solutions:**
1. Check internet connection
2. First model download can be 1-2GB, may take 10-30 minutes
3. Models are cached, only downloaded once
4. If download fails, delete cache and retry:
   ```cmd
   rmdir /s %USERPROFILE%\.cache\huggingface
   ```

### Performance is slow

**Issue:** Speech recognition or TTS generation is very slow

**Solutions:**

**For Whisper (speech recognition):**
1. Use smaller model in .env:
   ```
   WHISPER_MODEL=tiny  # or base
   ```
2. Use GPU acceleration (install CUDA)
3. Increase `CHUNK_DURATION` to process less frequently

**For NeuTTS:**
1. Use smaller model:
   ```
   NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
   ```
2. Use GPU acceleration:
   ```
   NEUTTS_BACKBONE_DEVICE=cuda
   ```
3. Ensure espeak-ng is properly installed

## Getting Help

If you're still having issues:

1. Check the main [README.md](README.md) for general documentation
2. Review the [.env.example](.env.example) for configuration options
3. Open an issue on GitHub with:
   - Your Windows version
   - Python version (`python --version`)
   - Error messages
   - Contents of your .env file (remove sensitive info)

## Advanced Topics

### Using Multiple Audio Devices

The application allows you to:
- Select input microphone on startup (for speech recognition)
- Select output device on startup (for NeuTTS playback)

Both are shown as GUI dialogs when you run the application.

### Custom Voice Cloning (NeuTTS)

To clone a specific voice:

1. Record a 3-15 second audio sample:
   - Format: .wav file
   - Quality: 16-44kHz sample rate, mono channel
   - Content: Clear speech, no background noise

2. Create a text file with exact transcription

3. Update .env:
   ```
   NEUTTS_REF_AUDIO=path/to/your/audio.wav
   NEUTTS_REF_TEXT=path/to/your/transcription.txt
   ```

### Optimizing for Different Hardware

**Low-end PC (4GB RAM, no GPU):**
```env
WHISPER_MODEL=tiny
TTS_SERVICE=speakerbot
```

**Mid-range PC (8GB RAM, no GPU):**
```env
WHISPER_MODEL=base
TTS_SERVICE=neutts
NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
NEUTTS_BACKBONE_DEVICE=cpu
```

**High-end PC (16GB+ RAM, NVIDIA GPU):**
```env
WHISPER_MODEL=medium  # or large
TTS_SERVICE=neutts
NEUTTS_BACKBONE=neuphonic/neutts-air-q8-gguf
NEUTTS_BACKBONE_DEVICE=cuda
NEUTTS_CODEC_DEVICE=cuda
```

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
