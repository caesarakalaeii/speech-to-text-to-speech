# Complete Windows Setup Guide: Speech-to-Text-to-Speech with Google Cloud TTS on Streamer Bot

This comprehensive tutorial will guide you through setting up the speech-to-text-to-speech application on a Windows machine, integrating it with Google Cloud Text-to-Speech (TTS) and Streamer Bot for streaming applications.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Installing System Requirements](#part-1-installing-system-requirements)
4. [Part 2: Setting Up the Speech-to-Text Application](#part-2-setting-up-the-speech-to-text-application)
5. [Part 3: Google Cloud TTS Setup](#part-3-google-cloud-tts-setup)
6. [Part 4: Streamer Bot Installation and Configuration](#part-4-streamer-bot-installation-and-configuration)
7. [Part 5: Connecting Everything Together](#part-5-connecting-everything-together)
8. [Part 6: Testing Your Setup](#part-6-testing-your-setup)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)

---

## Overview

This setup allows you to:
- Capture audio from your microphone in real-time
- Transcribe speech locally using OpenAI Whisper
- Send transcriptions to Streamer Bot via WebSocket
- Use Google Cloud TTS in Streamer Bot to generate high-quality speech output
- Integrate with streaming platforms (Twitch, YouTube, etc.)

**Architecture Flow:**
```
Your Microphone → This App (Whisper STT) → WebSocket → Streamer Bot (Google Cloud TTS) → Audio Output
```

---

## Prerequisites

Before starting, ensure you have:

- **Windows 10 or Windows 11** (64-bit)
- **Administrative access** to your computer
- **At least 4GB of RAM** (8GB+ recommended for better models)
- **Internet connection** for downloading software and accessing Google Cloud
- **Google Account** for Google Cloud Platform
- **Credit card** for Google Cloud (free tier available, won't charge unless exceeded)
- **A working microphone** for audio input
- **Basic familiarity with command line** (we'll guide you through everything)

---

## Part 1: Installing System Requirements

### Step 1.1: Install Python

1. **Download Python:**
   - Visit [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Download Python 3.11 or 3.10 (recommended for best compatibility)
   - **Important:** Python 3.8 or higher is required

2. **Install Python:**
   - Run the downloaded installer
   - ⚠️ **CRITICAL:** Check the box "Add Python to PATH" at the bottom of the first screen
   - Click "Install Now"
   - Wait for installation to complete
   - Click "Close" when finished

3. **Verify Installation:**
   - Open Command Prompt (Press `Win + R`, type `cmd`, press Enter)
   - Type: `python --version`
   - You should see something like `Python 3.11.x`
   - Type: `pip --version`
   - You should see pip version information

### Step 1.2: Install FFmpeg

FFmpeg is required for Whisper to process audio files.

**Option A: Install via Chocolatey (Recommended)**

1. **Install Chocolatey (if not already installed):**
   - Open PowerShell as Administrator (Right-click Start → "Windows PowerShell (Admin)" or "Terminal (Admin)")
   - Run:
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
     ```
   - Close and reopen PowerShell as Administrator

2. **Install FFmpeg:**
   ```powershell
   choco install ffmpeg
   ```
   - Type `Y` when prompted
   - Wait for installation to complete

**Option B: Install via Scoop**

1. **Install Scoop (if not already installed):**
   - Open PowerShell (non-admin is fine)
   - Run:
     ```powershell
     Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
     irm get.scoop.sh | iex
     ```

2. **Install FFmpeg:**
   ```powershell
   scoop install ffmpeg
   ```

**Option C: Manual Installation**

1. Download FFmpeg from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Download the "ffmpeg-release-essentials.zip" file
3. Extract to `C:\ffmpeg`
4. Add to PATH:
   - Open System Properties (Win + Pause/Break or search "Environment Variables")
   - Click "Environment Variables"
   - Under "System Variables", find "Path" and click "Edit"
   - Click "New" and add `C:\ffmpeg\bin`
   - Click "OK" on all dialogs
5. **Restart Command Prompt** to apply changes

**Verify FFmpeg Installation:**
```cmd
ffmpeg -version
```
You should see version information.

### Step 1.3: Install Git (Optional but Recommended)

1. Download Git from [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Run the installer with default settings
3. Verify: `git --version`

---

## Part 2: Setting Up the Speech-to-Text Application

### Step 2.1: Clone or Download the Repository

**Option A: Using Git (Recommended)**
```cmd
cd %USERPROFILE%\Documents
git clone https://github.com/caesarakalaeii/speech-to-text-to-speech.git
cd speech-to-text-to-speech
```

**Option B: Download ZIP**
1. Visit [https://github.com/caesarakalaeii/speech-to-text-to-speech](https://github.com/caesarakalaeii/speech-to-text-to-speech)
2. Click "Code" → "Download ZIP"
3. Extract to a location like `C:\Users\YourName\Documents\speech-to-text-to-speech`
4. Open Command Prompt and navigate:
   ```cmd
   cd %USERPROFILE%\Documents\speech-to-text-to-speech
   ```

### Step 2.2: Run the Automated Setup Script

The repository includes an automated setup script that will:
- Create a Python virtual environment
- Install all required dependencies
- Create a configuration file

Run the setup:
```cmd
setup.bat
```

**What the script does:**
1. Checks for Python and FFmpeg
2. Creates a virtual environment in the `venv` folder
3. Installs all Python packages from `requirements.txt`
4. Creates a `.env` file from the template

**If PyAudio installation fails:**
- The setup script will show instructions
- Download a pre-built wheel from [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- Choose the file matching your Python version and system (e.g., `PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl` for Python 3.11 on 64-bit Windows)
- Install it manually:
  ```cmd
  venv\Scripts\activate.bat
  pip install path\to\downloaded\PyAudio-0.2.13-cp311-cp311-win_amd64.whl
  ```

### Step 2.3: Configure the Application

1. **Open the `.env` file** in a text editor (Notepad, Notepad++, VS Code, etc.):
   ```cmd
   notepad .env
   ```

2. **Update the configuration:**
   ```env
   # Streamer Bot WebSocket URL (we'll set this up in Part 4)
   SPEAKERBOT_WEBSOCKET_URL=ws://localhost:7585/speak
   
   # Whisper model size: tiny, base, small, medium, large
   # Start with 'base' for good balance of speed and accuracy
   WHISPER_MODEL=base
   
   # Audio settings
   SAMPLE_RATE=16000
   CHUNK_DURATION=3.0
   
   # Speech detection threshold (0.0 to 1.0)
   # Lower = more sensitive, Higher = less sensitive
   SILENCE_THRESHOLD=0.01
   
   # Minimum speech duration in seconds
   MIN_SPEECH_DURATION=0.5
   
   # Voice name for Streamer Bot (we'll configure voices in Part 4)
   VOICE_NAME=en-US-Neural2-C
   ```

3. **Save and close** the file

**Understanding Whisper Models:**
- `tiny`: ~1GB RAM, fastest, less accurate - good for testing
- `base`: ~1GB RAM, good balance - **recommended for most users**
- `small`: ~2GB RAM, better accuracy - good if you have resources
- `medium`: ~5GB RAM, high accuracy - for powerful machines
- `large`: ~10GB RAM, best accuracy - requires significant resources

---

## Part 3: Google Cloud TTS Setup

Google Cloud Text-to-Speech provides high-quality, natural-sounding voices with extensive language support.

### Step 3.1: Create a Google Cloud Account

1. **Visit Google Cloud Platform:**
   - Go to [https://cloud.google.com/](https://cloud.google.com/)
   - Click "Get started for free" or "Console"

2. **Sign in with your Google Account**

3. **Set up billing:**
   - You'll need to add a credit card
   - **Free Tier:** Google Cloud offers:
     - Up to 1 million characters per month for Standard voices (free)
     - Up to 4 million characters per month for WaveNet/Neural2 voices (free)
   - You won't be charged unless you exceed these limits

### Step 3.2: Create a New Project

1. **In the Google Cloud Console:**
   - Click the project dropdown at the top (says "Select a project")
   - Click "New Project"
   - Name it something like "Streaming-TTS" or "StreamerBot-TTS"
   - Click "Create"
   - Wait for the project to be created (may take a few seconds)
   - Select your new project from the dropdown

### Step 3.3: Enable the Text-to-Speech API

1. **Navigate to APIs & Services:**
   - In the left sidebar, click "APIs & Services" → "Library"
   - Or search for "API Library" in the search bar

2. **Enable Text-to-Speech API:**
   - In the search box, type "Text-to-Speech"
   - Click on "Cloud Text-to-Speech API"
   - Click "Enable"
   - Wait for it to enable (usually takes 10-30 seconds)

### Step 3.4: Create Service Account Credentials

1. **Navigate to Credentials:**
   - Click "APIs & Services" → "Credentials" in the left sidebar

2. **Create Service Account:**
   - Click "Create Credentials" at the top
   - Select "Service Account"
   - Fill in the details:
     - **Service account name:** `streamerbot-tts`
     - **Service account ID:** (auto-filled)
     - **Description:** "Service account for Streamer Bot TTS"
   - Click "Create and Continue"

3. **Grant Permissions:**
   - In "Grant this service account access to project":
     - Select role: "Basic" → "Editor" or "Cloud Text-to-Speech User"
   - Click "Continue"
   - Click "Done"

4. **Create and Download Key:**
   - Find your new service account in the list
   - Click on it to open details
   - Go to the "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON" format
   - Click "Create"
   - **A JSON file will download automatically** - this is your credentials file
   - ⚠️ **IMPORTANT:** Keep this file secure! It provides access to your Google Cloud project

5. **Save the Credentials File:**
   - Rename the downloaded file to something simple like `google-cloud-tts-credentials.json`
   - Move it to a secure location, such as:
     - `C:\Users\YourName\.google-cloud\` (create this folder if it doesn't exist)
   - **Remember this path** - you'll need it for Streamer Bot

### Step 3.5: Explore Available Voices

1. **Test voices in the Cloud Console:**
   - Go to [https://cloud.google.com/text-to-speech](https://cloud.google.com/text-to-speech)
   - Click "Try it"
   - Or visit: [https://cloud.google.com/text-to-speech#demo](https://cloud.google.com/text-to-speech#demo)

2. **Try different voices:**
   - Type sample text
   - Select language (e.g., "English (United States)")
   - Select voice name (e.g., "en-US-Neural2-C", "en-US-Wavenet-D")
   - Choose speaking rate and pitch
   - Click "Speak it"

3. **Note down your preferred voice names** for later configuration

**Popular Voice Options:**
- **English (US) Neural2:** `en-US-Neural2-A` through `en-US-Neural2-J`
- **English (US) WaveNet:** `en-US-Wavenet-A` through `en-US-Wavenet-J`
- **English (US) Standard:** `en-US-Standard-A` through `en-US-Standard-J`

Each letter (A-J) represents a different voice with unique characteristics.

---

## Part 4: Streamer Bot Installation and Configuration

Streamer Bot is a versatile automation tool for streamers that we'll use to receive transcriptions and generate TTS output.

### Step 4.1: Download and Install Streamer Bot

1. **Download Streamer Bot:**
   - Visit [https://streamer.bot/](https://streamer.bot/)
   - Click "Download" 
   - Download the latest version (look for the Windows installer)

2. **Install Streamer Bot:**
   - Run the downloaded installer
   - Follow the installation wizard
   - Choose installation location (default is fine)
   - Complete the installation

3. **Launch Streamer Bot:**
   - Start Streamer Bot from the Start Menu or desktop shortcut
   - On first launch, you may need to configure basic settings
   - Complete the initial setup wizard if prompted

### Step 4.2: Configure Google Cloud TTS in Streamer Bot

1. **Open Streamer Bot Settings:**
   - In Streamer Bot, go to "Settings" (gear icon) or Menu → "Settings"

2. **Navigate to Text-to-Speech Settings:**
   - Look for "Text-to-Speech" or "TTS" in the settings menu
   - Or check under "Integrations" → "Text-to-Speech"

3. **Add Google Cloud TTS Provider:**
   - Click "Add TTS Provider" or similar option
   - Select "Google Cloud Text-to-Speech"

4. **Configure Google Cloud TTS:**
   - **Service Account Key File:** Browse to your `google-cloud-tts-credentials.json` file
   - Click "Load" or "Verify" to test the credentials
   - You should see a success message

5. **Configure Default Voice:**
   - Select a voice from the dropdown (e.g., `en-US-Neural2-C`)
   - Set speaking rate: 1.0 (normal speed)
   - Set pitch: 0.0 (normal pitch)
   - Test the voice by typing text and clicking "Test"

### Step 4.3: Enable WebSocket Server in Streamer Bot

The WebSocket server allows our speech-to-text application to communicate with Streamer Bot.

1. **Open WebSocket Settings:**
   - In Streamer Bot, go to "Servers/Clients" tab or "Settings" → "WebSocket"

2. **Enable WebSocket Server:**
   - Check/Enable "WebSocket Server"
   - **Port:** `7585` (default, or choose another - remember it for later)
   - **Host:** `127.0.0.1` or `localhost`
   - **Auto Start:** Enable this so it starts automatically

3. **Configure WebSocket Endpoints:**
   - Ensure the endpoint `/speak` is available or create it
   - This will receive our transcription messages

4. **Save Settings and Restart if Prompted**

### Step 4.4: Create a Streamer Bot Action for TTS

Now we'll create an action that receives transcriptions and speaks them using Google Cloud TTS.

1. **Create a New Action:**
   - Go to the "Actions" tab
   - Click "Add Action" or "+" button
   - Name it: `TTS Speak from WebSocket`

2. **Add WebSocket Trigger:**
   - In the action editor, go to "Triggers"
   - Click "Add Trigger"
   - Select "WebSocket" → "WebSocket Custom Server"
   - **Endpoint:** `/speak`
   - **Method:** Any or POST
   - Save the trigger

3. **Add TTS Sub-Action:**
   - In the action editor, go to "Sub-Actions"
   - Click "Add Sub-Action"
   - Find and select "Text-to-Speech" → "Speak with Google Cloud TTS"
   
4. **Configure the Sub-Action:**
   - **Message:** `%message%` (this variable will contain the transcribed text)
   - **Voice:** Select your preferred voice from the dropdown
   - **Speaking Rate:** `1.0` (or adjust to preference)
   - **Pitch:** `0.0` (or adjust to preference)
   - You can add additional sub-actions like:
     - "Set Variable" to log messages
     - "Write to File" to keep a transcript log
     - "Send Message to Channel" to display on stream

5. **Enable the Action:**
   - Make sure the action is enabled (toggle switch)
   - Click "Save" or "OK"

### Step 4.5: Advanced Streamer Bot Configuration (Optional)

**Queue Management:**
- In Streamer Bot settings, configure TTS queue settings:
  - Maximum queue size
  - Auto-skip after duration
  - Interrupt current speech

**Voice Commands:**
- Add commands like `!skip` to skip current TTS
- Add `!clear` to clear TTS queue
- Add `!voice [name]` to change voices on the fly

**Filtering:**
- Add filters to block certain words or phrases
- Set maximum message length
- Configure rate limiting per user

---

## Part 5: Connecting Everything Together

Now we'll connect the speech-to-text application to Streamer Bot.

### Step 5.1: Verify WebSocket Configuration

1. **Confirm Streamer Bot WebSocket is Running:**
   - In Streamer Bot, check that the WebSocket server shows as "Connected" or "Running"
   - Note the URL (should be `ws://localhost:7585` or your configured port)

2. **Update `.env` file in the speech-to-text application:**
   ```cmd
   cd %USERPROFILE%\Documents\speech-to-text-to-speech
   notepad .env
   ```

3. **Set the WebSocket URL:**
   ```env
   SPEAKERBOT_WEBSOCKET_URL=ws://localhost:7585/speak
   ```
   - If you changed the port in Streamer Bot, update it here
   - The `/speak` endpoint must match what you configured in Streamer Bot

4. **Set the Voice Name:**
   ```env
   VOICE_NAME=en-US-Neural2-C
   ```
   - Use the same voice name you configured in Streamer Bot
   - This tells the application which voice to request

5. **Save the file**

### Step 5.2: Start the Application

1. **Open Command Prompt in the project directory:**
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

3. **Initial Startup:**
   - **First run:** Whisper will download the model (~100-1000MB depending on model size)
   - This may take several minutes depending on your internet speed
   - Subsequent runs will be much faster

4. **Microphone Selection:**
   - A window may appear asking you to select your microphone
   - Choose your preferred input device
   - Click "OK" or "Select"

5. **Check the Console Output:**
   - You should see logs indicating:
     - Whisper model loaded
     - Connected to Speakerbot WebSocket
     - Audio recording started
     - Waiting for speech input

---

## Part 6: Testing Your Setup

### Step 6.1: Basic Functionality Test

1. **Ensure everything is running:**
   - ✅ Streamer Bot is open and WebSocket server is active
   - ✅ Speech-to-text application is running
   - ✅ Console shows "Connected to Speakerbot"

2. **Speak into your microphone:**
   - Say something clearly: "Hello, this is a test of the text to speech system"
   - Wait a moment for processing

3. **Observe the process:**
   - **In the console:** You should see transcription logs
   - **In Streamer Bot:** Check the logs for incoming WebSocket messages
   - **Audio Output:** You should hear the transcribed text spoken back via Google Cloud TTS

### Step 6.2: Troubleshooting Common Issues

**No audio detected:**
- Check Windows sound settings (Right-click speaker icon → "Sound settings")
- Ensure your microphone is set as the default input device
- Check microphone privacy settings (Windows Settings → Privacy → Microphone)
- Speak louder or adjust `SILENCE_THRESHOLD` in `.env` (try `0.005` for more sensitivity)

**Transcription not accurate:**
- Speak more clearly and slower
- Reduce background noise
- Try a larger Whisper model (e.g., `small` or `medium`)
- Adjust `CHUNK_DURATION` to allow longer speech segments

**WebSocket connection fails:**
- Verify Streamer Bot WebSocket server is running
- Check the port number matches in both applications
- Check Windows Firewall isn't blocking the connection
- Try using `ws://127.0.0.1:7585/speak` instead of `localhost`

**TTS not playing:**
- Verify Google Cloud credentials are correct in Streamer Bot
- Check Streamer Bot logs for error messages
- Ensure the voice name exists (try a different voice)
- Check audio output device is correctly set in Streamer Bot

### Step 6.3: Performance Optimization

1. **Optimize for your hardware:**
   - **Low-end PC:** Use `WHISPER_MODEL=tiny` or `base`
   - **Mid-range PC:** Use `WHISPER_MODEL=base` or `small`
   - **High-end PC:** Use `WHISPER_MODEL=small` or `medium`

2. **Adjust latency settings:**
   - Shorter `CHUNK_DURATION` = faster response, more frequent processing
   - Longer `CHUNK_DURATION` = fewer interruptions, higher latency
   - Recommended: `3.0` seconds for natural speech

3. **Reduce CPU usage:**
   - Use smaller Whisper model
   - Increase `CHUNK_DURATION`
   - Close other resource-intensive applications

---

## Troubleshooting

### Python Issues

**"Python is not recognized as an internal or external command":**
- Python is not in PATH
- Reinstall Python and check "Add Python to PATH"
- Or manually add Python to PATH in System Environment Variables

**Module import errors:**
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt --upgrade
```

### FFmpeg Issues

**"FFmpeg not found" error:**
- Verify installation: `ffmpeg -version`
- Restart Command Prompt after installation
- Check PATH environment variable includes FFmpeg bin directory

### PyAudio Issues

**PyAudio installation fails:**
1. Download wheel from [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
2. Install: `pip install PyAudio-0.2.13-cp311-cp311-win_amd64.whl`
3. Restart the setup

**No audio input detected:**
- Check Device Manager for audio devices
- Update audio drivers
- Test microphone in Windows Sound settings
- Try different microphone

### Google Cloud Issues

**"Authentication failed" error:**
- Verify credentials JSON file path is correct
- Check the service account has Text-to-Speech permissions
- Regenerate credentials if needed

**"API not enabled" error:**
- Ensure Text-to-Speech API is enabled in Google Cloud Console
- Wait a few minutes for API activation to propagate

**Billing not set up:**
- Add payment method in Google Cloud Console
- Billing → Payment Methods → Add Payment Method

**Quota exceeded:**
- Check usage in Google Cloud Console
- Monitor your free tier limits
- Consider upgrading to paid tier if needed

### Streamer Bot Issues

**WebSocket won't start:**
- Check if port 7585 is already in use
- Try a different port (remember to update `.env`)
- Restart Streamer Bot
- Check Windows Firewall settings

**TTS not working:**
- Verify action is enabled
- Check trigger is correctly configured
- Review Streamer Bot logs for errors
- Test Google Cloud TTS directly in settings

**Messages not received:**
- Verify WebSocket endpoint matches (e.g., `/speak`)
- Check Streamer Bot logs for incoming WebSocket messages
- Test WebSocket connection with a tool like Postman or curl

### Network Issues

**Firewall blocking connection:**
```cmd
netsh advfirewall firewall add rule name="Streamer Bot WebSocket" dir=in action=allow protocol=TCP localport=7585
```

**Port already in use:**
- Change the port in both Streamer Bot and `.env`
- Check what's using the port: `netstat -ano | findstr :7585`

---

## Advanced Configuration

### Custom Voice Selection

Edit `.env` to change voices dynamically:
```env
VOICE_NAME=en-US-Wavenet-D
```

Or create multiple profiles with different voice configurations.

### OBS Integration

**Display transcriptions on stream:**
1. In Streamer Bot, add a "Set Text GDI+" sub-action
2. Point it to an OBS text source
3. Set the text to `%message%`

**Create TTS alerts:**
1. Add sub-actions to show images/animations
2. Trigger sound effects
3. Display text overlays

### Streaming Platform Integration

**Twitch:**
- Connect Streamer Bot to Twitch
- Add channel point rewards that trigger TTS
- Create commands like `!tts [message]`

**YouTube:**
- Connect Streamer Bot to YouTube
- Read super chat messages with TTS
- Announce new subscribers

### Multiple Language Support

1. **Update Streamer Bot action to detect language**
2. **Use language-specific voices:**
   - Spanish: `es-ES-Neural2-A`
   - French: `fr-FR-Neural2-A`
   - Japanese: `ja-JP-Neural2-B`
   - And many more...

### Performance Monitoring

**Monitor resource usage:**
- Task Manager → Performance tab
- Watch CPU, RAM, GPU usage
- Adjust model size accordingly

**Log analysis:**
- Review application logs for patterns
- Monitor transcription accuracy
- Track WebSocket connection stability

### Backup and Recovery

**Backup your configuration:**
1. Copy `.env` file
2. Export Streamer Bot configuration
3. Save Google Cloud credentials securely

**Version control:**
```cmd
git init
git add .env
git commit -m "My working configuration"
```
(Remember to add `.env` to `.gitignore` if sharing publicly)

---

## Conclusion

You now have a complete setup for:
- ✅ Real-time speech transcription using OpenAI Whisper
- ✅ High-quality text-to-speech using Google Cloud TTS
- ✅ Integration with Streamer Bot for streaming applications
- ✅ WebSocket communication between components

### Next Steps

1. **Customize your setup:**
   - Experiment with different voices
   - Adjust audio settings for your environment
   - Create custom Streamer Bot actions

2. **Expand functionality:**
   - Add chat commands
   - Create TTS queues
   - Implement voice filters

3. **Optimize performance:**
   - Fine-tune for your hardware
   - Monitor resource usage
   - Adjust quality vs. speed trade-offs

4. **Share and contribute:**
   - Report issues on GitHub
   - Contribute improvements
   - Share your configuration with the community

### Useful Resources

- **Project Repository:** [https://github.com/caesarakalaeii/speech-to-text-to-speech](https://github.com/caesarakalaeii/speech-to-text-to-speech)
- **Streamer Bot:** [https://streamer.bot/](https://streamer.bot/)
- **Google Cloud TTS Documentation:** [https://cloud.google.com/text-to-speech/docs](https://cloud.google.com/text-to-speech/docs)
- **OpenAI Whisper:** [https://github.com/openai/whisper](https://github.com/openai/whisper)

### Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review application logs
3. Open an issue on GitHub
4. Join the community discussions

---

**Happy Streaming! 🎙️🎮🎬**
