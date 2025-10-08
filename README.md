# speech-to-text-to-speech

Simple locally hosted Whisper application to generate speech transcriptions and send them to a Speakerbot websocket endpoint, inspired by Zentreya's TTS setup.

## Features

- 🎤 Real-time audio capture from microphone
- 🧠 Local speech-to-text using OpenAI Whisper
- 🔌 Multiple TTS service options: Speakerbot WebSocket or Neuphonic API
- ⚙️ Configurable via environment variables
- 🐳 Docker support with GPU passthrough
- 🚀 Easy setup with automated bash script

## 📚 Tutorials

**NEW!** [Complete Windows Setup Guide with Google Cloud TTS and Streamer Bot](WINDOWS_GOOGLE_CLOUD_TTS_STREAMER_BOT_TUTORIAL.md) - A comprehensive step-by-step tutorial covering everything from installation to advanced configuration.

## Requirements

- Python 3.8 or higher
- PortAudio (for microphone input)
- FFmpeg (for Whisper audio processing)
- CUDA-capable GPU (optional, but recommended for better performance)

## Quick Start

### Method 1: Automated Setup Scripts

#### Windows

1. Clone the repository:
```cmd
git clone https://github.com/caesarakalaeii/speech-to-text-to-speech.git
cd speech-to-text-to-speech
```

2. Run the setup script:
```cmd
setup.bat
```

3. Configure your settings:
   - Open `.env` in your favorite text editor
   - Set your TTS service (speakerbot or neuphonic)
   - Configure the appropriate settings for your chosen TTS service

4. Run the application:
```cmd
run.bat
```

#### Linux/macOS

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
# TTS Service: speakerbot or neuphonic
TTS_SERVICE=speakerbot

# Speakerbot WebSocket URL (used when TTS_SERVICE=speakerbot)
SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080
VOICE_NAME=Sally

# Neuphonic API settings (used when TTS_SERVICE=neuphonic)
NEUPHONIC_API_KEY=your_neuphonic_api_key_here
NEUPHONIC_VOICE_ID=your_voice_id_here

# Whisper model size: tiny, base, small, medium, large
# Larger models are more accurate but slower
WHISPER_MODEL=base

# Audio settings
SAMPLE_RATE=16000
CHUNK_DURATION=3.0

# Speech detection threshold (0.0 to 1.0)
SILENCE_THRESHOLD=0.01

# Minimum speech duration in seconds
MIN_SPEECH_DURATION=0.5
```

### TTS Service Options

#### Speakerbot (Default)
- Connects to a local Speakerbot instance via WebSocket
- Requires Speakerbot to be running locally
- Set `TTS_SERVICE=speakerbot` in `.env`
- Configure `SPEAKERBOT_WEBSOCKET_URL` and `VOICE_NAME`

#### Neuphonic
- Uses the Neuphonic TTS API (https://www.neuphonic.com/)
- Requires a Neuphonic API key
- Set `TTS_SERVICE=neuphonic` in `.env`
- Configure `NEUPHONIC_API_KEY` and `NEUPHONIC_VOICE_ID`
- Sign up at https://www.neuphonic.com/ to get your API key

### Whisper Model Options

- `tiny`: Fastest, least accurate (~1GB RAM)
- `base`: Good balance (~1GB RAM) - **Default**
- `small`: Better accuracy (~2GB RAM)
- `medium`: High accuracy (~5GB RAM)
- `large`: Best accuracy (~10GB RAM)

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
4. Send transcriptions to your configured TTS service (Speakerbot or Neuphonic)

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

**For Neuphonic:**
- Verify your API key is correct
- Check you have an active subscription
- Ensure you have internet connectivity

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
