# Complete Windows Setup Guide: Speech-to-Text-to-Speech with Local NeuTTS Air

This beginner-friendly tutorial will guide you through setting up the speech-to-text-to-speech application on a Windows machine with **local text-to-speech** using NeuTTS Air. Everything runs on your computer—no internet connection or cloud services required after the initial setup!

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Installing System Requirements](#part-1-installing-system-requirements)
4. [Part 2: Setting Up the Speech-to-Text Application](#part-2-setting-up-the-speech-to-text-application)
5. [Part 3: Installing NeuTTS Air Dependencies](#part-3-installing-neutts-air-dependencies)
6. [Part 4: Setting Up Voice Cloning (Reference Audio)](#part-4-setting-up-voice-cloning-reference-audio)
7. [Part 5: Running and Testing](#part-5-running-and-testing)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tips](#performance-tips)

---

## Overview

This setup allows you to:
- Capture audio from your microphone in real-time
- Transcribe speech locally using OpenAI Whisper (no internet needed)
- Generate speech using NeuTTS Air's neural voice cloning (runs on your PC)
- Clone any voice from a short audio sample (3-15 seconds)
- Run everything offline after initial setup

**Why use NeuTTS Air instead of cloud services?**
- ✅ **Completely FREE** - No API costs or monthly fees
- ✅ **Runs offline** - No internet connection needed
- ✅ **Privacy** - All processing stays on your computer
- ✅ **Voice cloning** - Use any voice from a short audio sample
- ✅ **No limits** - Generate unlimited speech

**Architecture Flow:**
```
Your Microphone → Whisper STT (local) → NeuTTS Air (local) → Audio Output
```

---

## Prerequisites

Before starting, ensure you have:

- **Windows 10 or Windows 11** (64-bit)
- **Administrative access** to your computer
- **At least 4GB of RAM** (8GB+ recommended)
  - The Q4 GGUF model needs about 2GB RAM
  - The Q8 GGUF model needs about 3GB RAM
  - The full PyTorch model needs about 4GB RAM
- **At least 5GB of free disk space** for models and dependencies
- **Internet connection** for initial download (models and software)
- **A working microphone** for audio input
- **Basic computer skills** - We'll guide you through everything step by step!

**Note:** You do NOT need:
- A credit card
- A Google account
- Any paid cloud services
- An expensive GPU (works on CPU)

---

## Part 1: Installing System Requirements

### Step 1.1: Install Python

Python is the programming language that runs this application.

1. **Download Python:**
   - Visit [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Download **Python 3.11** or **Python 3.10** (recommended)
   - **Important:** Python 3.8 or higher is required

2. **Install Python:**
   - Run the downloaded installer (double-click the file)
   - ⚠️ **CRITICAL:** Check the box **"Add Python to PATH"** at the bottom of the first screen
   - Click **"Install Now"**
   - Wait for installation to complete (may take a few minutes)
   - Click **"Close"** when finished

3. **Verify Installation:**
   - Press `Win + R` on your keyboard
   - Type `cmd` and press Enter (this opens Command Prompt)
   - Type: `python --version` and press Enter
   - You should see something like `Python 3.11.x`
   - Type: `pip --version` and press Enter
   - You should see pip version information
   
   **If you see an error:** Python is not in your PATH. Reinstall Python and make sure to check the "Add Python to PATH" box.

### Step 1.2: Install FFmpeg

FFmpeg is a tool that helps process audio files. Whisper needs it to work properly.

**Option A: Install via Chocolatey (Easiest Method)**

1. **Install Chocolatey (a package manager for Windows):**
   - Right-click the **Start button**
   - Click **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**
   - If a User Account Control window appears, click **"Yes"**
   - Copy and paste this command (right-click in PowerShell to paste):
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
     ```
   - Press Enter and wait for installation to complete
   - Close PowerShell and open a new PowerShell as Administrator

2. **Install FFmpeg using Chocolatey:**
   ```powershell
   choco install ffmpeg
   ```
   - Type `Y` when prompted and press Enter
   - Wait for installation to complete (may take a few minutes)

**Option B: Manual Installation (If Option A doesn't work)**

1. Visit [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Download the file named **"ffmpeg-release-essentials.zip"**
3. Extract the ZIP file to `C:\ffmpeg`
4. Add FFmpeg to your system PATH:
   - Press `Win + Pause/Break` or search for **"Environment Variables"** in Start menu
   - Click **"Environment Variables"**
   - Under **"System Variables"**, find **"Path"** and click **"Edit"**
   - Click **"New"** and type: `C:\ffmpeg\bin`
   - Click **"OK"** on all dialogs
5. **Restart Command Prompt** to apply the changes

**Verify FFmpeg Installation:**
- Open a new Command Prompt (Win + R, type `cmd`, press Enter)
- Type: `ffmpeg -version` and press Enter
- You should see version information

If you see an error, FFmpeg is not installed correctly. Try the manual installation method or restart your computer.

### Step 1.3: Install espeak-ng

espeak-ng is a text-to-speech engine that NeuTTS Air uses for phoneme processing.

1. **Download espeak-ng:**
   - Visit [https://github.com/espeak-ng/espeak-ng/releases](https://github.com/espeak-ng/espeak-ng/releases)
   - Find the latest release
   - Download the file named **`espeak-ng-X.XX-x64.msi`** (where X.XX is the version number)

2. **Install espeak-ng:**
   - Run the downloaded installer (double-click the `.msi` file)
   - Follow the installation wizard with default settings
   - Click **"Next"** → **"Next"** → **"Install"**
   - Click **"Finish"** when done

3. **Verify Installation:**
   - Open Command Prompt (Win + R, type `cmd`, press Enter)
   - Type: `espeak-ng --version` and press Enter
   - You should see version information

**If espeak-ng is not found:**
- The installer should add it to PATH automatically
- If not, add `C:\Program Files\eSpeak NG` to your PATH (same process as FFmpeg above)
- Restart Command Prompt after adding to PATH

### Step 1.4: Install Git (Optional but Recommended)

Git makes it easy to download the project and get updates.

1. Download Git from [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Run the installer with default settings (just keep clicking "Next")
3. Verify: Open Command Prompt and type `git --version`

**If you don't want to install Git:** You can download the project as a ZIP file in the next section.

---

## Part 2: Setting Up the Speech-to-Text Application

### Step 2.1: Download the Project

**Option A: Using Git (Recommended)**

1. Open Command Prompt (Win + R, type `cmd`, press Enter)
2. Navigate to your Documents folder:
   ```cmd
   cd %USERPROFILE%\Documents
   ```
3. Download the project:
   ```cmd
   git clone https://github.com/caesarakalaeii/speech-to-text-to-speech.git
   ```
4. Enter the project folder:
   ```cmd
   cd speech-to-text-to-speech
   ```

**Option B: Download as ZIP (If you don't have Git)**

1. Visit [https://github.com/caesarakalaeii/speech-to-text-to-speech](https://github.com/caesarakalaeii/speech-to-text-to-speech)
2. Click the green **"Code"** button
3. Click **"Download ZIP"**
4. Extract the ZIP file to a location like `C:\Users\YourName\Documents\speech-to-text-to-speech`
5. Open Command Prompt and navigate to the folder:
   ```cmd
   cd %USERPROFILE%\Documents\speech-to-text-to-speech
   ```

### Step 2.2: Run the Automated Setup Script

The project includes an automated setup script that makes installation easy.

1. **In Command Prompt, in the project folder, run:**
   ```cmd
   setup.bat
   ```

2. **What the script does:**
   - ✅ Checks that Python and FFmpeg are installed
   - ✅ Creates a Python virtual environment (isolated space for this project)
   - ✅ Installs all required Python packages
   - ✅ Creates a configuration file (`.env`)

3. **Wait for the script to complete** (may take 5-10 minutes depending on your internet speed)

**If PyAudio installation fails:**

PyAudio is a library for recording audio. It sometimes fails to install on Windows. If this happens:

1. Visit [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
2. Download the file matching your Python version and system:
   - For **Python 3.11** on **64-bit Windows**: `PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl`
   - For **Python 3.10** on **64-bit Windows**: `PyAudio‑0.2.13‑cp310‑cp310‑win_amd64.whl`
3. Save the file to your Downloads folder
4. Install it manually:
   ```cmd
   venv\Scripts\activate.bat
   pip install "%USERPROFILE%\Downloads\PyAudio-0.2.13-cp311-cp311-win_amd64.whl"
   ```
   (Adjust the filename if you downloaded a different version)

---

## Part 3: Installing NeuTTS Air Dependencies

NeuTTS Air requires additional Python packages that are not included in the basic setup.

### Step 3.1: Activate the Virtual Environment

First, activate the virtual environment (this ensures packages are installed in the right place):

```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` appear at the beginning of your command prompt line. This means the virtual environment is active.

### Step 3.2: Install NeuTTS Dependencies

Install the required packages for NeuTTS Air:

```cmd
pip install -r requirements-neutts.txt
```

**This will install:**
- PyTorch (deep learning library)
- Transformers (AI model library)
- phonemizer (converts text to phonemes)
- soundfile (audio file handling)
- llama-cpp-python (for faster GGUF models)
- And other supporting libraries

**This may take 10-20 minutes** depending on your internet connection. The PyTorch package is large (around 2GB).

**If installation fails:**
- Make sure you have stable internet connection
- Make sure you have enough disk space (at least 5GB free)
- Try running the command again
- See the [Troubleshooting](#troubleshooting) section below

### Step 3.3: Choose Your Model Type

NeuTTS Air offers three model types. For most users, we recommend starting with the **Q4 GGUF model** (smallest and fastest):

| Model Type | Size | Speed | Quality | Best For |
|------------|------|-------|---------|----------|
| **Q4 GGUF** ✅ | ~1.5GB | Fastest | Good | Most users, older PCs |
| **Q8 GGUF** | ~2.5GB | Fast | Better | Users with 8GB+ RAM |
| **Full PyTorch** | ~4GB | Slower | Best | Powerful PCs, best quality |

You'll configure which model to use in the next section. The model will download automatically the first time you run the application.

---

## Part 4: Setting Up Voice Cloning (Reference Audio)

NeuTTS Air's superpower is **voice cloning**—it can imitate any voice from just a short audio sample!

### Step 4.1: Prepare Your Reference Audio

You need two files:
1. **An audio recording** (3-15 seconds of someone speaking)
2. **A text transcription** of exactly what was said in the recording

**Where to get reference audio:**
- Record yourself or a friend speaking
- Use a clip from a YouTube video
- Download sample voices from the [NeuTTS Air repository](https://github.com/neuphonic/neutts-air/tree/main/samples)

**Audio Requirements:**
- **Format:** WAV file (`.wav`)
- **Length:** 3-15 seconds (sweet spot is 5-10 seconds)
- **Content:** Clear, natural speech
- **Quality:** Mono (1 channel), 16-44 kHz sample rate
- **Background:** Minimal background noise

**Good examples:**
- "Hello, my name is Sarah, and I'm excited to try this text-to-speech system."
- "Hi there! This is a test recording for voice cloning. I hope it works well."

**What to avoid:**
- Very loud background music or noise
- Multiple people talking at once
- Whispering or shouting
- Audio that's too quiet or distorted

### Step 4.2: Create Reference Files

**Option A: Use the Provided Samples (Easiest)**

The project includes a samples folder where you can place your files.

1. Download sample files from [NeuTTS Air repository](https://github.com/neuphonic/neutts-air/tree/main/samples)
2. Save them in the `samples` folder of the project:
   - `samples\reference.wav` (the audio file)
   - `samples\reference.txt` (the transcription)

**Option B: Use Your Own Voice**

1. **Record audio:**
   - Open **Voice Recorder** (search for it in Start menu)
   - Click the microphone button to record
   - Speak clearly for 5-10 seconds
   - Click stop
   - Right-click the recording and select **"Open file location"**
   - Right-click the file → **"Convert to"** → Save as **WAV format**

2. **Transcribe the audio:**
   - Listen to your recording
   - Open Notepad
   - Type exactly what was said (word-for-word, including "um", "uh", etc.)
   - Save as `reference.txt`

3. **Move files to samples folder:**
   - Copy both files to the `samples` folder in your project
   - Rename them to `reference.wav` and `reference.txt`

**Option C: Convert from MP3 or other formats**

If you have audio in MP3 or another format:

```cmd
ffmpeg -i your-audio.mp3 -ar 24000 -ac 1 samples\reference.wav
```

This converts your audio to the correct format (24kHz, mono, WAV).

### Step 4.3: Transcribe Your Audio (if needed)

If you don't know exactly what was said in your audio:

**Manual transcription:**
- Listen carefully and type out every word
- Include stutters, "um", "uh", pauses as natural speech
- Save as plain text file

**Use Whisper to transcribe:**
You can actually use the Whisper model in this project to transcribe your audio!

```cmd
venv\Scripts\activate.bat
python -c "import whisper; model = whisper.load_model('base'); result = model.transcribe('samples/reference.wav'); print(result['text']); open('samples/reference.txt', 'w').write(result['text'])"
```

This will automatically transcribe your audio and save it to `reference.txt`.

### Step 4.4: Verify Your Files

Make sure your files are in the right place:

```cmd
dir samples
```

You should see:
- `reference.wav` (your audio file)
- `reference.txt` (your transcription file)

Open `reference.txt` in Notepad to verify the text looks correct.

---

## Part 5: Configuration and Running

### Step 5.1: Configure the Application

1. **Open the configuration file:**
   ```cmd
   notepad .env
   ```

2. **Update these settings for NeuTTS:**

   ```env
   # Set TTS service to NeuTTS
   TTS_SERVICE=neutts

   # NeuTTS Air Backbone Model (choose one)
   # For most users, use Q4 GGUF (fastest, smallest)
   NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
   
   # Alternative options:
   # NEUTTS_BACKBONE=neuphonic/neutts-air-q8-gguf     # Better quality, needs more RAM
   # NEUTTS_BACKBONE=neuphonic/neutts-air              # Best quality, slowest

   # Device for backbone model
   NEUTTS_BACKBONE_DEVICE=cpu

   # Codec model (don't change this)
   NEUTTS_CODEC=neuphonic/neucodec
   NEUTTS_CODEC_DEVICE=cpu

   # Path to your reference files
   NEUTTS_REF_AUDIO=samples/reference.wav
   NEUTTS_REF_TEXT=samples/reference.txt

   # Whisper model size (start with 'base')
   WHISPER_MODEL=base

   # Audio settings (these are fine as defaults)
   SAMPLE_RATE=16000
   CHUNK_DURATION=3.0
   SILENCE_THRESHOLD=0.01
   MIN_SPEECH_DURATION=0.5
   ```

3. **Save and close** the file (File → Save in Notepad, then close)

**Understanding the settings:**

- **TTS_SERVICE=neutts** - Use NeuTTS instead of Speakerbot
- **NEUTTS_BACKBONE** - Which AI model to use (Q4 GGUF is recommended)
- **NEUTTS_BACKBONE_DEVICE=cpu** - Run on CPU (change to `cuda` if you have NVIDIA GPU)
- **NEUTTS_REF_AUDIO/TEXT** - Your reference voice files
- **WHISPER_MODEL** - Speech recognition accuracy (base is good balance)

**Whisper Model Options:**
- `tiny` - Fastest, least accurate (~1GB RAM)
- `base` - **Recommended** - Good balance (~1GB RAM)
- `small` - Better accuracy (~2GB RAM)
- `medium` - High accuracy (~5GB RAM)
- `large` - Best accuracy (~10GB RAM)

### Step 5.2: Run the Application for the First Time

1. **Make sure you're in the project folder:**
   ```cmd
   cd %USERPROFILE%\Documents\speech-to-text-to-speech
   ```

2. **Run the application:**
   ```cmd
   run.bat
   ```

   Or manually:
   ```cmd
   venv\Scripts\activate.bat
   python main.py
   ```

3. **First run will take several minutes:**
   - Whisper will download its model (~100-1000MB depending on size)
   - NeuTTS will download the backbone and codec models (~1.5-4GB)
   - Models are cached, so subsequent runs are much faster
   
   **Be patient!** This is normal and only happens once.

4. **Microphone Selection:**
   - A window will appear showing available microphones
   - Select your microphone from the list
   - Click **"OK"**

5. **Check the console output:**
   You should see messages like:
   ```
   Loading Whisper model: base
   Loading NeuTTS Air...
   Loading backbone model: neuphonic/neutts-air-q4-gguf
   Loading codec model: neuphonic/neucodec
   Loading reference audio: samples/reference.wav
   NeuTTS Air ready!
   Audio recording started
   Listening for speech...
   ```

### Step 5.3: Test Your Setup

1. **Speak into your microphone:**
   - Say something clearly: "Hello, this is a test of the speech to text system."
   - Wait a few seconds for processing

2. **What should happen:**
   - The console shows "Processing audio..."
   - Whisper transcribes your speech
   - The transcription appears in the console
   - NeuTTS generates speech in the cloned voice
   - You hear the audio played back

3. **If you hear the cloned voice speaking your words—SUCCESS!** 🎉

**Troubleshooting if it doesn't work:** See the [Troubleshooting](#troubleshooting) section below.

---

## Troubleshooting

### Python Issues

**"Python is not recognized as an internal or external command"**
- Python is not in your PATH
- Solution: Reinstall Python and check "Add Python to PATH" during installation
- Or add Python manually to PATH in System Environment Variables

**"pip is not recognized"**
- pip is not installed or not in PATH
- Solution: Reinstall Python or run `python -m pip` instead of `pip`

### FFmpeg Issues

**"FFmpeg not found" error when running**
- FFmpeg is not installed or not in PATH
- Solution 1: Install via Chocolatey: `choco install ffmpeg`
- Solution 2: Manual installation (see Step 1.2 above)
- Solution 3: Restart your computer after installing FFmpeg

**How to verify FFmpeg is working:**
```cmd
ffmpeg -version
```
If this shows version info, FFmpeg is installed correctly.

### espeak-ng Issues

**"espeak-ng not found" error**
- espeak-ng is not installed or not in PATH
- Solution: Download and install from [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases)
- After installing, restart Command Prompt

**Phonemizer errors:**
- Make sure espeak-ng is installed and in PATH
- Try running: `espeak-ng --version`
- If that doesn't work, reinstall espeak-ng

### PyAudio Issues

**PyAudio installation fails during setup**
- This is common on Windows
- Solution: Download pre-built wheel from [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- Install manually: `pip install PyAudio-0.2.13-cp311-cp311-win_amd64.whl`

**"No audio input detected"**
- Check Windows microphone permissions
- Right-click speaker icon → "Sound settings" → Make sure microphone is enabled
- Windows Settings → Privacy → Microphone → Allow apps to access microphone
- Try selecting a different microphone in the app

### NeuTTS Installation Issues

**"Could not install llama-cpp-python"**
- This package can be tricky on Windows
- Solution 1: Install Visual Studio Build Tools from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Solution 2: Try installing a pre-built wheel
- Solution 3: Use PyTorch models instead of GGUF (set `NEUTTS_BACKBONE=neuphonic/neutts-air`)

**PyTorch installation fails or is very slow**
- PyTorch is a large package (~2GB)
- Make sure you have stable internet
- Make sure you have at least 5GB free disk space
- Try installing separately: `pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`

**"Out of memory" errors**
- You don't have enough RAM for the selected model
- Solution: Use a smaller model (Q4 GGUF instead of Q8 or full PyTorch)
- Solution: Close other programs to free up RAM
- Solution: Add more RAM to your computer (if possible)

### Model Download Issues

**Models fail to download**
- Check your internet connection
- The first run downloads 1.5-4GB of model files
- If download fails, delete the cache folder and try again:
  ```cmd
  rmdir /s %USERPROFILE%\.cache\huggingface
  ```

**"Model not found" errors**
- Model names are case-sensitive
- Check spelling in `.env` file
- Make sure `NEUTTS_BACKBONE` is set to one of:
  - `neuphonic/neutts-air-q4-gguf`
  - `neuphonic/neutts-air-q8-gguf`
  - `neuphonic/neutts-air`

### Audio Issues

**No audio is played back**
- Check your Windows audio output device
- Make sure speakers/headphones are connected and turned on
- Check volume is not muted
- Try a different output device

**Microphone not detected**
- Go to Windows Settings → System → Sound
- Under "Input", make sure your microphone is listed and selected
- Test your microphone by speaking—the input level should move
- Grant microphone permissions to apps

**Poor transcription quality**
- Speak more clearly and slowly
- Reduce background noise
- Use a better microphone
- Try a larger Whisper model (`small` or `medium` instead of `base`)
- Adjust `SILENCE_THRESHOLD` in `.env` (lower = more sensitive)

**Generated speech sounds robotic or wrong**
- Check your reference audio quality
- Use a longer reference audio sample (8-12 seconds)
- Make sure reference transcription exactly matches the audio
- Try a different backbone model (Q8 GGUF or full PyTorch)
- Record a new reference audio with clearer speech

### Performance Issues

**Application is very slow**
- Your computer may not have enough resources
- Solution 1: Use smaller Whisper model (`tiny` or `base`)
- Solution 2: Use Q4 GGUF backbone (smallest and fastest)
- Solution 3: Increase `CHUNK_DURATION` to process less frequently
- Solution 4: Close other programs to free up resources

**High CPU usage**
- This is normal for AI models running on CPU
- Solutions:
  - Use smaller models
  - Process longer chunks less frequently
  - If you have NVIDIA GPU, set `NEUTTS_BACKBONE_DEVICE=cuda`

### Reference Audio Issues

**"Reference audio file not found"**
- Check that `samples/reference.wav` exists
- Check spelling in `.env` file
- Make sure path uses forward slashes or backslashes correctly
- Try absolute path: `C:\Users\YourName\Documents\speech-to-text-to-speech\samples\reference.wav`

**"Invalid audio format"**
- Reference audio must be WAV format
- Convert with: `ffmpeg -i your-audio.mp3 -ar 24000 -ac 1 samples\reference.wav`
- Make sure it's mono (1 channel) and 16-44kHz

**Voice cloning doesn't sound like the reference**
- Reference audio is too short or poor quality
- Record a longer, clearer sample (8-12 seconds recommended)
- Speak naturally in complete sentences
- Reduce background noise
- Make sure transcription exactly matches audio

### Getting Help

If you're still stuck:

1. **Check the GitHub Issues:** [github.com/caesarakalaeii/speech-to-text-to-speech/issues](https://github.com/caesarakalaeii/speech-to-text-to-speech/issues)
2. **Read the main README:** More technical details available
3. **Check NeuTTS Air documentation:** [github.com/neuphonic/neutts-air](https://github.com/neuphonic/neutts-air)
4. **Open a new issue:** Describe your problem with error messages and system info

---

## Performance Tips

### Optimize for Your Computer

**If you have a low-end PC:**
```env
WHISPER_MODEL=tiny
NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
CHUNK_DURATION=5.0
```

**If you have a mid-range PC:**
```env
WHISPER_MODEL=base
NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
CHUNK_DURATION=3.0
```

**If you have a high-end PC:**
```env
WHISPER_MODEL=small
NEUTTS_BACKBONE=neuphonic/neutts-air-q8-gguf
CHUNK_DURATION=3.0
```

**If you have NVIDIA GPU:**
```env
WHISPER_MODEL=medium
NEUTTS_BACKBONE=neuphonic/neutts-air
NEUTTS_BACKBONE_DEVICE=cuda
NEUTTS_CODEC_DEVICE=cuda
CHUNK_DURATION=3.0
```

### Speed vs Quality Trade-offs

**Faster response (lower quality):**
- Use `tiny` or `base` Whisper model
- Use `neuphonic/neutts-air-q4-gguf` backbone
- Shorter `CHUNK_DURATION` (2.0-3.0 seconds)

**Better quality (slower response):**
- Use `small` or `medium` Whisper model  
- Use `neuphonic/neutts-air-q8-gguf` or full PyTorch backbone
- Longer `CHUNK_DURATION` (4.0-5.0 seconds)

### Reduce Latency

1. **Use smaller models** - Biggest impact on speed
2. **Shorter audio chunks** - Faster detection, but may cut off words
3. **Lower SILENCE_THRESHOLD** - Detects speech faster
4. **Close other programs** - Free up CPU and RAM

### Improve Quality

1. **Use larger models** - Better transcription and generation
2. **Better microphone** - Clearer input = better output
3. **Quiet environment** - Less background noise
4. **Better reference audio** - Higher quality voice cloning
5. **Longer reference audio** - 10-15 seconds is ideal

---

## Advanced Tips

### Using Different Voices

You can create multiple reference audio files and switch between them:

1. Create folders for each voice:
   ```cmd
   mkdir samples\voice1
   mkdir samples\voice2
   ```

2. Put reference files in each folder:
   ```
   samples\voice1\reference.wav
   samples\voice1\reference.txt
   samples\voice2\reference.wav
   samples\voice2\reference.txt
   ```

3. Switch voices by changing `.env`:
   ```env
   NEUTTS_REF_AUDIO=samples/voice1/reference.wav
   NEUTTS_REF_TEXT=samples/voice1/reference.txt
   ```

### GPU Acceleration

If you have an NVIDIA graphics card:

1. **Check if you have CUDA installed:**
   ```cmd
   nvidia-smi
   ```

2. **Install PyTorch with CUDA support:**
   ```cmd
   venv\Scripts\activate.bat
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Update `.env` to use GPU:**
   ```env
   NEUTTS_BACKBONE_DEVICE=cuda
   NEUTTS_CODEC_DEVICE=cuda
   ```

This can make generation 5-10x faster!

### Creating High-Quality Reference Audio

For best voice cloning results:

1. **Record in a quiet room** with minimal echo
2. **Use a good microphone** (even a smartphone is better than laptop mic)
3. **Speak naturally** - Don't read robotically
4. **8-12 seconds is ideal** - Not too short, not too long
5. **Clear, consistent volume** - Not too quiet or too loud
6. **One speaker only** - No background voices
7. **Include variety** - Different words, tones, expressions

**Converting to the right format:**
```cmd
ffmpeg -i your-audio.mp3 -ar 24000 -ac 1 -sample_fmt s16 samples\reference.wav
```

### Batch Processing

To transcribe multiple audio files at once, you can create a simple script:

```cmd
venv\Scripts\activate.bat
python -c "import whisper; model = whisper.load_model('base'); import os; [print(f'{f}: {model.transcribe(f)[\"text\"]}') for f in os.listdir('samples') if f.endswith('.wav')]"
```

---

## Conclusion

Congratulations! You now have a fully local speech-to-text-to-speech system running on your Windows PC! 🎉

### What You've Accomplished

- ✅ Installed all required software (Python, FFmpeg, espeak-ng)
- ✅ Set up the speech-to-text-to-speech application
- ✅ Installed NeuTTS Air for local voice generation
- ✅ Created reference audio for voice cloning
- ✅ Successfully transcribed your voice and heard it played back
- ✅ All running locally without internet or cloud services!

### Next Steps

1. **Experiment with different voices** - Try various reference audio samples
2. **Optimize settings** - Tune for your hardware and preferences
3. **Create voice libraries** - Build a collection of different voices
4. **Integrate with other apps** - Use for streaming, gaming, accessibility
5. **Share your experience** - Help others in the community!

### Comparison: Cloud vs Local TTS

| Feature | Cloud TTS (Google, etc.) | Local TTS (NeuTTS) |
|---------|-------------------------|---------------------|
| **Cost** | Pay per use, monthly fees | Completely free |
| **Internet** | Required | Not required after setup |
| **Privacy** | Data sent to cloud | Everything stays local |
| **Speed** | Depends on connection | Depends on your PC |
| **Voice Quality** | Excellent | Very good |
| **Voice Options** | Pre-made voices | Any voice you can record |
| **Limits** | API quotas/rate limits | Only your hardware |

### Useful Resources

- **Project Repository:** [github.com/caesarakalaeii/speech-to-text-to-speech](https://github.com/caesarakalaeii/speech-to-text-to-speech)
- **NeuTTS Air:** [github.com/neuphonic/neutts-air](https://github.com/neuphonic/neutts-air)
- **OpenAI Whisper:** [github.com/openai/whisper](https://github.com/openai/whisper)
- **Sample Voices:** [github.com/neuphonic/neutts-air/tree/main/samples](https://github.com/neuphonic/neutts-air/tree/main/samples)

### Getting Support

If you need help:

1. **Re-read the [Troubleshooting](#troubleshooting) section** - Most issues are covered there
2. **Check GitHub Issues** - Someone may have had the same problem
3. **Open a new issue** - Provide error messages and system details
4. **Join community discussions** - Get help from other users

### Share Your Feedback

This guide was created to help beginners set up local TTS on Windows. If you found it helpful, or if something was confusing, please let us know by:

- Opening a GitHub issue
- Contributing improvements
- Sharing your success story

---

**Enjoy your local speech-to-text-to-speech system! 🎙️✨**

*Remember: Everything runs on your computer, is completely free, and respects your privacy!*
