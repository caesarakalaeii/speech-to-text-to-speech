# Installation Guide

Choose your installation method based on your platform and preferences.

## 🪟 Windows Users

### Option 1: Fully Automated Setup (RECOMMENDED) ⭐

**Perfect for beginners or anyone who wants everything set up automatically.**

#### What it does:
- ✅ Installs Python 3.11
- ✅ Installs FFmpeg (audio processing)
- ✅ Installs espeak-ng (for NeuTTS voice synthesis)
- ✅ Optionally installs CUDA Toolkit (for GPU acceleration)
- ✅ Creates virtual environment
- ✅ Installs all Python dependencies
- ✅ Configures the application

#### How to use:
1. **Right-click on `setup.bat`** in the repository folder
2. Select **"Run as Administrator"**
3. Follow the prompts
4. Wait 20-30 minutes for installation
5. Edit `.env` file to configure
6. Run `run.bat`

📖 **Full guide:** [WINDOWS_SETUP.md](WINDOWS_SETUP.md)

---

### Option 2: Semi-Automatic Setup

**Use this if you already have Python 3.8+ installed.**

#### Prerequisites:
- Python 3.8 or higher (in PATH)

#### How to use:
1. Double-click `install.bat`
2. Follow prompts to install Python packages
3. Manually install FFmpeg and espeak-ng if needed
4. Edit `.env` file
5. Run `run.bat`

**Note:** You'll need to install FFmpeg and espeak-ng yourself:
- FFmpeg: https://www.gyan.dev/ffmpeg/builds/
- espeak-ng: https://github.com/espeak-ng/espeak-ng/releases

---

### Option 3: Manual Installation

**For advanced users who want full control.**

See the "Manual Installation" section in [README.md](README.md#manual-installation).

---

## 🐧 Linux Users

### Automated Installation

```bash
chmod +x install.sh
./install.sh
```

This will:
- Install system dependencies (via apt/yum/pacman)
- Create virtual environment
- Install Python packages
- Set up configuration

Then:
```bash
# Edit configuration
nano .env

# Run application
./run.sh
```

### Manual Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip portaudio19-dev ffmpeg espeak-ng
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

**Other distributions:** See [README.md](README.md#manual-installation)

---

## 🍎 macOS Users

### Automated Installation

```bash
chmod +x install.sh
./install.sh
```

### Manual Installation

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install portaudio ffmpeg espeak-ng

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run
python main.py
```

---

## 🐳 Docker Installation

For all platforms with Docker installed:

```bash
docker-compose up --build
```

For GPU support, ensure you have NVIDIA Docker runtime installed.

See [README.md](README.md#method-2-docker-setup-with-gpu-support) for details.

---

## Quick Comparison

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Windows Automated** | Everything installed automatically, no prior setup needed | Requires admin rights, large download | Beginners, anyone wanting easy setup |
| **Windows Semi-Auto** | No admin required, faster | Must have Python, manual FFmpeg/espeak install | Users with Python already installed |
| **Linux/Mac Auto** | Quick setup, handles most dependencies | May need sudo for system packages | Most Linux/Mac users |
| **Manual** | Full control, understand what's installed | More time consuming, need to know what you're doing | Advanced users, troubleshooting |
| **Docker** | Isolated environment, reproducible | Requires Docker knowledge, larger footprint | DevOps, containerized deployments |

---

## What Gets Installed?

### System Dependencies
- **Python 3.8+**: Programming language runtime
- **FFmpeg**: Audio/video processing (used by Whisper)
- **espeak-ng**: Phoneme synthesis (required only for NeuTTS)
- **CUDA Toolkit** (optional): GPU acceleration for neural networks

### Python Packages

**Base requirements** (`requirements.txt`):
- openai-whisper: Speech-to-text AI model
- numpy: Numerical computation library
- pyaudio: Audio I/O
- python-dotenv: Configuration management
- websockets: WebSocket client for Speakerbot

**NeuTTS requirements** (`requirements-neutts.txt`, optional):
- torch: PyTorch deep learning framework
- transformers: Hugging Face NLP library
- phonemizer: Text-to-phoneme conversion
- soundfile, librosa: Audio file processing
- neucodec: Neural audio codec
- llama-cpp-python: GGUF model support (faster)

### Disk Space Requirements

- **Minimum**: 2 GB (base installation, tiny Whisper model)
- **Recommended**: 5 GB (base + small Whisper model)
- **With NeuTTS**: 8-10 GB (includes PyTorch and NeuTTS models)
- **With CUDA**: 13-15 GB (adds CUDA toolkit ~3GB)
- **Full installation**: 15-20 GB (everything + large Whisper model)

---

## After Installation

1. **Configure the application**
   - Edit `.env` file
   - Choose TTS service (speakerbot or neutts)
   - Select Whisper model size
   - Configure audio settings

2. **Run the application**
   - Windows: `run.bat`
   - Linux/Mac: `./run.sh` or `python main.py`

3. **First run**
   - Select your microphone
   - Select output device (NeuTTS only)
   - Models will download on first use (one-time, may take 5-10 minutes)

📖 **Configuration guide:** See [.env.example](.env.example)

📖 **Quick start:** See [QUICKSTART.md](QUICKSTART.md)

---

## Getting Help

- **Windows setup issues**: See [WINDOWS_SETUP.md](WINDOWS_SETUP.md)
- **General documentation**: See [README.md](README.md)
- **Configuration reference**: See [.env.example](.env.example)
- **Quick start guide**: See [QUICKSTART.md](QUICKSTART.md)
- **Report issues**: Open an issue on GitHub

---

## Platform-Specific Notes

### Windows 10/11
- Microphone permissions: Settings > Privacy > Microphone
- May need to allow Python through Windows Firewall
- Windows Defender may scan downloaded files (slows first run)

### Linux
- May need to add user to `audio` group: `sudo usermod -a -G audio $USER`
- PulseAudio or ALSA required for audio I/O
- Some distributions need `python3-venv` package

### macOS
- Microphone permissions: System Preferences > Security & Privacy > Microphone
- May need to allow terminal app microphone access
- Apple Silicon (M1/M2) uses CPU-only PyTorch (no CUDA)

### WSL (Windows Subsystem for Linux)
- Audio I/O may not work properly
- Better to use native Windows installation
- If using WSL2, may need PulseAudio passthrough

---

## License

This project is licensed under the GNU Affero General Public License v3.0 - see [LICENSE](LICENSE) for details.
