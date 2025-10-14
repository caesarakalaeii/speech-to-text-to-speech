# Quick Start Guide

Get up and running in 5 minutes!

## Windows Users (Easiest Method)

### 🚀 Automated Installation (Recommended)

1. **Right-click `setup.bat` → "Run as Administrator"**
   - Installs everything automatically (Python, FFmpeg, CUDA, espeak-ng)
   - Takes 20-30 minutes
   - Requires internet connection

2. **Edit `.env` file** (created automatically)
   - Choose TTS service: `speakerbot` or `neutts`
   - Set Whisper model size: `tiny`, `base`, `small`, `medium`, or `large`

3. **Double-click `run.bat`**

**That's it!** See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed troubleshooting.

### Alternative: Manual Setup

If you already have Python 3.8+ installed:

1. **Run `install.bat`** (no admin required)
2. **Edit `.env`**
3. **Run `run.bat`**

*Note: You'll need to manually install FFmpeg and espeak-ng for this method.*

## Linux/macOS Users

### Automated Installation

```bash
chmod +x install.sh
./install.sh
```

Then edit `.env` and run:
```bash
./run.sh
```

### Manual Installation

```bash
# Install system dependencies
# Ubuntu/Debian:
sudo apt-get install python3 python3-pip portaudio19-dev ffmpeg espeak-ng

# macOS:
brew install portaudio ffmpeg espeak-ng

# Create virtual environment and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run
python main.py
```

## Configuration Basics

Edit the `.env` file:

### Choose TTS Service

```bash
TTS_SERVICE=speakerbot  # External WebSocket TTS
# OR
TTS_SERVICE=neutts      # Local TTS with voice cloning (requires espeak-ng)
```

### Speakerbot Setup

```bash
TTS_SERVICE=speakerbot
SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080
VOICE_NAME=Sally
```

### NeuTTS Air Setup (Local, Offline)

```bash
TTS_SERVICE=neutts
NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
NEUTTS_BACKBONE_DEVICE=cpu  # or 'cuda' for GPU
NEUTTS_REF_AUDIO=samples/reference.wav  # Your voice sample (3-15 sec)
NEUTTS_REF_TEXT=samples/reference.txt   # Transcription of sample
```

### Whisper Model (Speech Recognition)

```bash
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
# tiny:   Fastest (~1GB RAM)
# base:   Balanced (recommended)
# small:  Better quality (~2GB RAM)
# medium: High quality (~5GB RAM)
# large:  Best quality (~10GB RAM)
```

## GPU Acceleration (Optional)

### Windows
Run `setup.bat` and select "Yes" when asked about CUDA installation.

Then edit `.env`:
```bash
NEUTTS_BACKBONE_DEVICE=cuda
NEUTTS_CODEC_DEVICE=cuda
```

### Linux
Install CUDA toolkit for your distribution, then:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Common Issues

### "Python not found" (Windows)
- Install Python from python.org, check "Add to PATH" during installation
- Or run `setup.bat` which installs it automatically

### "FFmpeg not found"
- Windows: Run `setup.bat` OR install with `choco install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`

### "espeak-ng not found" (NeuTTS only)
- Windows: Run `setup.bat` OR download from https://github.com/espeak-ng/espeak-ng/releases
- Linux: `sudo apt-get install espeak-ng`
- macOS: `brew install espeak-ng`

### No audio detected
- Check microphone permissions (especially on Windows 10/11)
- Lower `SILENCE_THRESHOLD` in .env (try `0.005`)
- Select correct microphone in the GUI that appears on startup

### Slow performance
- Use smaller Whisper model: `WHISPER_MODEL=tiny`
- Enable GPU acceleration (see above)
- For NeuTTS: Use `neuphonic/neutts-air-q4-gguf` model

## Need More Help?

- **Windows Users:** See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for complete guide
- **General Docs:** See [README.md](README.md) for full documentation
- **Configuration:** See `.env.example` for all options
- **Issues:** Open an issue on GitHub

## Next Steps

1. ✅ Get it running (you're here!)
2. 📝 Configure `.env` for your use case
3. 🎤 Test with your microphone
4. 🔊 Choose and configure TTS service
5. 🎛️ Fine-tune settings for performance
6. 🎭 (Optional) Set up voice cloning with NeuTTS

Happy voice streaming! 🎉
