# 🎙️ Speech-to-Text-to-Speech - Start Here!

Welcome! This guide will help you get started quickly.

## 🎯 What is this?

This application captures your voice, converts it to text using AI (Whisper), and then sends it to a text-to-speech service. Perfect for streamers, content creators, or anyone who needs voice transformation!

## 🚀 I just want to get started! (Windows)

### Super Quick Start (3 clicks!)

1. **Right-click** `check-system.bat` → **Run**
   - Checks what you have installed
   - Tells you exactly what to do next

2. Follow the recommendation (usually: right-click `setup.bat` → **Run as Administrator**)

3. When done, double-click `run.bat`

**That's it!** The installers handle everything automatically.

---

## 📖 Documentation Guide

We have several guides depending on your needs:

### New Users (Start Here!)

1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
   - Quickest path to a working setup
   - Minimal reading, maximum results

2. **[INSTALL_GUIDE.md](INSTALL_GUIDE.md)** - Choose your installation method
   - Compare all installation options
   - Platform-specific guides
   - Disk space and requirements

### Windows Users

3. **[WINDOWS_SETUP.md](WINDOWS_SETUP.md)** - Complete Windows guide
   - Detailed setup instructions
   - Troubleshooting for common Windows issues
   - GPU/CUDA setup
   - System requirements

### Reference Documentation

4. **[README.md](README.md)** - Full project documentation
   - Features overview
   - All configuration options
   - Advanced usage
   - Docker setup

5. **[.env.example](.env.example)** - Configuration reference
   - All available settings
   - Explanations for each option
   - Example values

### Alternative Setups

6. **[WINDOWS_GOOGLE_CLOUD_TTS_STREAMER_BOT_TUTORIAL.md](WINDOWS_GOOGLE_CLOUD_TTS_STREAMER_BOT_TUTORIAL.md)**
   - Using Google Cloud TTS instead of local TTS
   - Streamer Bot integration

---

## 🔧 Installation Tools

### Batch Scripts (Windows)

- **`check-system.bat`** - Check what's installed, get recommendations
- **`setup.bat`** - Fully automated installer (installs Python, FFmpeg, CUDA, espeak)
- **`install.bat`** - Quick installer (requires Python already installed)
- **`run.bat`** - Run the application

### Shell Scripts (Linux/macOS)

- **`install.sh`** - Automated installer
- **`run.sh`** - Run the application

### Advanced

- **`setup-windows.ps1`** - PowerShell installer (called by setup.bat)
- **`install.py`** - Python installer script (called by install.bat)

---

## ❓ FAQ

### Which installer should I use?

**Windows:**
- Don't know what you have? → Run `check-system.bat` first
- Nothing installed? → Use `setup.bat` (installs everything)
- Have Python? → Use `install.bat` (faster)

**Linux/Mac:**
- Use `install.sh` (handles everything)

### Do I need CUDA?

**No, but it helps!**
- Without CUDA: Works fine on CPU (slower)
- With CUDA: 3-10x faster with NVIDIA GPU
- `setup.bat` will ask if you want CUDA

### What TTS service should I use?

**Two options:**

1. **Speakerbot** (default)
   - External WebSocket service
   - Lightweight, no extra dependencies
   - Requires Speakerbot running separately

2. **NeuTTS Air** (optional)
   - Completely offline and free
   - Voice cloning from short samples
   - Higher quality, needs more resources
   - Requires espeak-ng

The installer will ask which you prefer.

### How much disk space do I need?

- **Minimum**: 2 GB (base install)
- **Recommended**: 5 GB (includes models)
- **With NeuTTS**: 10 GB (includes AI models)
- **With CUDA**: 15 GB (includes GPU toolkit)

### Will this work on my computer?

**Minimum Requirements:**
- Windows 10/11, Linux, or macOS
- 4 GB RAM
- 2 GB free disk space
- Microphone
- Internet connection (for initial setup)

**Recommended:**
- 8 GB+ RAM
- NVIDIA GPU (for CUDA acceleration)
- 10 GB free disk space

---

## 🆘 Help! Something's wrong

### Windows Issues

1. **"Python not found"**
   - Run `setup.bat` (installs Python automatically)
   - Or install from python.org, check "Add to PATH"

2. **"FFmpeg not found"**
   - Run `setup.bat` (installs FFmpeg automatically)
   - Or install: `choco install ffmpeg`

3. **"espeak-ng not found"** (NeuTTS only)
   - Run `setup.bat` (installs espeak-ng automatically)
   - Or download from: https://github.com/espeak-ng/espeak-ng/releases

4. **PyAudio fails to install**
   - Run `setup.bat` (handles this automatically)
   - See [WINDOWS_SETUP.md](WINDOWS_SETUP.md#pyaudio-installation-fails)

5. **No microphone detected**
   - Check Windows Settings → Privacy → Microphone
   - Ensure apps have microphone access

### General Issues

- **More help:** See [WINDOWS_SETUP.md](WINDOWS_SETUP.md#troubleshooting)
- **Configuration:** Check [.env.example](.env.example)
- **Still stuck?** Open an issue on GitHub

---

## 📝 Quick Configuration

After installation, edit `.env`:

### Choose TTS Service
```bash
TTS_SERVICE=speakerbot  # External service
# OR
TTS_SERVICE=neutts      # Local with voice cloning
```

### Choose Whisper Model
```bash
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
```

### For GPU Acceleration
```bash
NEUTTS_BACKBONE_DEVICE=cuda  # Change from 'cpu' to 'cuda'
```

**Full configuration guide:** See [.env.example](.env.example)

---

## 🎓 Next Steps

1. ✅ **Install** (you're reading this!)
2. 📝 **Configure** - Edit `.env` file
3. 🎤 **Test** - Run `run.bat` and speak into microphone
4. 🎭 **Customize** - Set up voice cloning (optional)
5. 🎛️ **Optimize** - Adjust settings for your system

---

## 🌟 Features

- 🎤 Real-time voice capture
- 🧠 Local AI speech recognition (OpenAI Whisper)
- 🔌 Multiple TTS options (Speakerbot or NeuTTS)
- 🎭 Voice cloning support (NeuTTS)
- 🚀 GPU acceleration (optional)
- ⚙️ Easy configuration
- 🔒 Completely offline capable (with NeuTTS)

---

## 📚 Learn More

- **Project README:** [README.md](README.md)
- **GitHub Repository:** https://github.com/caesarakalaeii/speech-to-text-to-speech
- **Report Issues:** https://github.com/caesarakalaeii/speech-to-text-to-speech/issues
- **Contribute:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

GNU Affero General Public License v3.0 - See [LICENSE](LICENSE)

---

**Ready to get started? Run `check-system.bat` (Windows) or read [QUICKSTART.md](QUICKSTART.md)!**

Happy streaming! 🎉
