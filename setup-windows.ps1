<#
.SYNOPSIS
    Automated Windows setup script for speech-to-text-to-speech
    
.DESCRIPTION
    This script automates the complete installation process including:
    - Chocolatey package manager (if not installed)
    - Python 3.11 (if not installed)
    - FFmpeg
    - CUDA Toolkit (optional, for GPU acceleration)
    - espeak-ng (for NeuTTS)
    - Python dependencies
    - Virtual environment setup
    
.NOTES
    This script requires Administrator privileges to install system dependencies.
    Run from PowerShell as Administrator.
#>

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Script configuration
$PYTHON_VERSION = "3.11"
$CUDA_VERSION = "12.1"  # Compatible with PyTorch 2.x

# Check if running as administrator
function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "`n✗ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "`nPlease right-click on PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Yellow
    Write-Host "Or run setup.bat which will request elevation automatically.`n" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if command exists
function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Install Chocolatey
function Install-Chocolatey {
    Write-Host "\n>>> Checking for Chocolatey package manager..." -ForegroundColor Yellow
    
    if (Test-CommandExists "choco") {
        Write-Host "✓ Chocolatey is already installed" -ForegroundColor Green
        return $true
    }
    
    Write-Host "ℹ Installing Chocolatey..." -ForegroundColor Blue
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')) | Out-Null
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Test-CommandExists "choco") {
            Write-Host "✓ Chocolatey installed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ Chocolatey installation failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Failed to install Chocolatey: $_" -ForegroundColor Red
        return $false
    }
}

# Install Python
function Install-Python {
    Write-Host "\n>>> Checking for Python..." -ForegroundColor Yellow
    
    if (Test-CommandExists "python") {
        $version = python --version 2>&1
        Write-Host "✓ Python is already installed: $version" -ForegroundColor Green
        
        # Check version
        if ($version -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 8) {
                return $true
            } else {
                Write-Host "⚠ Python version is too old (need 3.8+). Will install newer version." -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "ℹ Installing Python $PYTHON_VERSION..." -ForegroundColor Blue
    try {
        choco install python --version=3.11.9 -y | Out-Null
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Test-CommandExists "python") {
            $version = python --version 2>&1
            Write-Host "✓ Python installed: $version" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ Python installation failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Failed to install Python: $_" -ForegroundColor Red
        return $false
    }
}

# Install FFmpeg
function Install-FFmpeg {
    Write-Host "\n>>> Checking for FFmpeg..." -ForegroundColor Yellow
    
    if (Test-CommandExists "ffmpeg") {
        Write-Host "✓ FFmpeg is already installed" -ForegroundColor Green
        return $true
    }
    
    Write-Host "ℹ Installing FFmpeg..." -ForegroundColor Blue
    try {
        choco install ffmpeg -y | Out-Null
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Test-CommandExists "ffmpeg") {
            Write-Host "✓ FFmpeg installed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ FFmpeg installation failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Failed to install FFmpeg: $_" -ForegroundColor Red
        return $false
    }
}

# Install espeak-ng
function Install-ESpeak {
    Write-Host "\n>>> Checking for espeak-ng..." -ForegroundColor Yellow
    
    if (Test-CommandExists "espeak-ng") {
        Write-Host "✓ espeak-ng is already installed" -ForegroundColor Green
        return $true
    }
    
    Write-Host "ℹ Installing espeak-ng..." -ForegroundColor Blue
    Write-Host "ℹ This is required for NeuTTS Air local TTS" -ForegroundColor Blue
    
    try {
        # Try chocolatey first
        choco install espeak -y | Out-Null
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (Test-CommandExists "espeak-ng") {
            Write-Host "✓ espeak-ng installed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠ espeak-ng not found after installation" -ForegroundColor Yellow
            Write-Host "ℹ Manual installation may be required from:" -ForegroundColor Blue
            Write-Host "ℹ https://github.com/espeak-ng/espeak-ng/releases" -ForegroundColor Blue
            return $false
        }
    } catch {
        Write-Host "✗ Failed to install espeak-ng: $_" -ForegroundColor Red
        Write-Host "ℹ You can manually download and install from:" -ForegroundColor Blue
        Write-Host "ℹ https://github.com/espeak-ng/espeak-ng/releases" -ForegroundColor Blue
        return $false
    }
}

# Check for NVIDIA GPU
function Test-NvidiaGPU {
    try {
        $gpu = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" }
        return $null -ne $gpu
    } catch {
        return $false
    }
}

# Install CUDA Toolkit
function Install-CUDA {
    param([bool]$Force = $false)
    
    Write-Host "\n>>> Checking for NVIDIA GPU and CUDA..." -ForegroundColor Yellow
    
    # Check if NVIDIA GPU exists
    if (-not (Test-NvidiaGPU)) {
        Write-Host "⚠ No NVIDIA GPU detected. Skipping CUDA installation." -ForegroundColor Yellow
        Write-Host "ℹ The application will run on CPU (slower but functional)" -ForegroundColor Blue
        return $false
    }
    
    Write-Host "✓ NVIDIA GPU detected" -ForegroundColor Green
    
    # Check if CUDA is already installed (check both standard path and chocolatey path)
    $cudaStandardPath = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    $cudaChocoPath = "C:\ProgramData\chocolatey\lib\cuda"
    $cudaInstalled = $false
    $cudaPath = ""
    
    if (Test-Path $cudaStandardPath) {
        $cudaInstalled = $true
        $cudaPath = $cudaStandardPath
    } elseif (Test-Path $cudaChocoPath) {
        $cudaInstalled = $true
        $cudaPath = $cudaChocoPath
    }
    
    if ($cudaInstalled -and -not $Force) {
        Write-Host "✓ CUDA Toolkit appears to be installed at: $cudaPath" -ForegroundColor Green
        
        $install = Read-Host "Do you want to reinstall CUDA? (y/N)"
        if ($install -ne "y" -and $install -ne "Y") {
            return $true
        }
    }
    
    Write-Host "ℹ Installing CUDA Toolkit $CUDA_VERSION..." -ForegroundColor Blue
    Write-Host "⚠ This is a large download (~3GB) and may take 20-30 minutes" -ForegroundColor Yellow
    Write-Host "ℹ CUDA provides GPU acceleration for faster speech recognition and TTS" -ForegroundColor Blue
    
    $install = Read-Host "Continue with CUDA installation? (Y/n)"
    if ($install -eq "n" -or $install -eq "N") {
        Write-Host "⚠ Skipping CUDA installation. Application will use CPU." -ForegroundColor Yellow
        return $false
    }
    
    try {
        # Install CUDA via Chocolatey
        choco install cuda --version=12.1.0 -y | Out-Null
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-Host "✓ CUDA Toolkit installed successfully" -ForegroundColor Green
        Write-Host "ℹ You may need to restart your computer for CUDA to work properly" -ForegroundColor Blue
        return $true
    } catch {
        Write-Host "✗ Failed to install CUDA: $_" -ForegroundColor Red
        Write-Host "ℹ You can manually download and install CUDA from:" -ForegroundColor Blue
        Write-Host "ℹ https://developer.nvidia.com/cuda-downloads" -ForegroundColor Blue
        Write-Host "⚠ Application will continue without GPU acceleration" -ForegroundColor Yellow
        return $false
    }
}

# Create Python virtual environment
function New-VirtualEnvironment {
    Write-Host "\n>>> Setting up Python virtual environment..." -ForegroundColor Yellow
    
    if (Test-Path "venv") {
        Write-Host "⚠ Virtual environment already exists" -ForegroundColor Yellow
        $recreate = Read-Host "Recreate virtual environment? (y/N)"
        if ($recreate -eq "y" -or $recreate -eq "Y") {
            Write-Host "ℹ Removing existing virtual environment..." -ForegroundColor Blue
            Remove-Item -Recurse -Force "venv"
        } else {
            Write-Host "ℹ Using existing virtual environment" -ForegroundColor Blue
            return $true
        }
    }
    
    try {
        Write-Host "ℹ Creating virtual environment..." -ForegroundColor Blue
        python -m venv venv
        
        if (Test-Path "venv\Scripts\activate.bat") {
            Write-Host "✓ Virtual environment created successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "✗ Virtual environment creation failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Failed to create virtual environment: $_" -ForegroundColor Red
        return $false
    }
}

# Upgrade pip in virtual environment
function Update-Pip {
    Write-Host "\n>>> Upgrading pip..." -ForegroundColor Yellow
    
    try {
        & ".\venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel | Out-Null
        Write-Host "✓ pip upgraded successfully" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "⚠ Failed to upgrade pip (continuing anyway): $_" -ForegroundColor Yellow
        return $true  # Non-critical
    }
}

# Install base Python requirements
function Install-BaseRequirements {
    Write-Host "\n>>> Installing base Python requirements..." -ForegroundColor Yellow
    
    Write-Host "ℹ Installing packages:" -ForegroundColor Blue
    Write-Host "ℹ   - openai-whisper (speech recognition)" -ForegroundColor Blue
    Write-Host "ℹ   - numpy (numerical processing)" -ForegroundColor Blue
    Write-Host "ℹ   - pyaudio (audio I/O)" -ForegroundColor Blue
    Write-Host "ℹ   - python-dotenv (configuration)" -ForegroundColor Blue
    Write-Host "ℹ   - websockets (WebSocket support)" -ForegroundColor Blue
    
    try {
        & ".\venv\Scripts\pip.exe" install -r requirements.txt | Out-Null
        Write-Host "✓ Base requirements installed successfully" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Failed to install base requirements: $_" -ForegroundColor Red
        Write-Host "ℹ Trying alternative PyAudio installation method..." -ForegroundColor Blue
        
        # Try pipwin for PyAudio on Windows
        try {
            & ".\venv\Scripts\pip.exe" install pipwin | Out-Null
            & ".\venv\Scripts\pipwin.exe" install pyaudio | Out-Null
            
            # Try installing other requirements without PyAudio
            $requirements = Get-Content "requirements.txt" | Where-Object { $_ -notmatch "pyaudio" }
            $requirements | ForEach-Object {
                if ($_ -and -not $_.StartsWith("#")) {
                    & ".\venv\Scripts\pip.exe" install $_ | Out-Null
                }
            }
            
            Write-Host "✓ Requirements installed with alternative method" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "✗ Alternative installation also failed" -ForegroundColor Red
            Write-Host "ℹ You may need to manually install PyAudio from:" -ForegroundColor Blue
            Write-Host "ℹ https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio" -ForegroundColor Blue
            
            $continue = Read-Host "Continue anyway? (y/N)"
            return ($continue -eq "y" -or $continue -eq "Y")
        }
    }
}

# Ask about NeuTTS installation
function Install-NeuTTS {
    Write-Host "\n$('=' * 80)" -ForegroundColor Cyan; Write-Host "  NeuTTS Air - Local Neural TTS with Voice Cloning" -ForegroundColor Cyan; Write-Host "$('=' * 80)\n" -ForegroundColor Cyan
    
    Write-Host @"
This project supports two TTS (Text-to-Speech) options:

1. Speakerbot (default):
   • Uses external WebSocket TTS service
   • Requires Speakerbot running separately
   • Lightweight, minimal dependencies

2. NeuTTS Air (optional):
   • Completely offline, local neural TTS
   • Voice cloning from 3-15 second audio samples
   • High-quality speech synthesis
   • No API calls or subscription fees
   • Requires ~2-4GB additional disk space
   • Works better with GPU but runs on CPU

"@

    $install = Read-Host "Install NeuTTS Air dependencies? (y/N)"
    if ($install -ne "y" -and $install -ne "Y") {
        Write-Host "ℹ Skipping NeuTTS installation - will use Speakerbot" -ForegroundColor Blue
        return $false
    }
    
    Write-Host "\n>>> Installing NeuTTS Air requirements..." -ForegroundColor Yellow
    Write-Host "ℹ This will download ~1-2GB of packages and may take several minutes" -ForegroundColor Blue
    
    # Check if CUDA is available (check both standard path and chocolatey path)
    $hasCuda = (Test-Path "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA") -or (Test-Path "C:\ProgramData\chocolatey\lib\cuda")
    
    try {
        if ($hasCuda) {
            Write-Host "ℹ CUDA detected - installing PyTorch with GPU support..." -ForegroundColor Blue
            & ".\venv\Scripts\pip.exe" install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 | Out-Null
        } else {
            Write-Host "ℹ Installing PyTorch with CPU support..." -ForegroundColor Blue
            & ".\venv\Scripts\pip.exe" install torch torchaudio --index-url https://download.pytorch.org/whl/cpu | Out-Null
        }
        
        Write-Host "ℹ Installing NeuTTS dependencies..." -ForegroundColor Blue
        & ".\venv\Scripts\pip.exe" install -r requirements-neutts.txt | Out-Null
        
        Write-Host "✓ NeuTTS requirements installed successfully" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "✗ Failed to install NeuTTS requirements: $_" -ForegroundColor Red
        Write-Host "ℹ You can try manually installing later with:" -ForegroundColor Blue
        Write-Host 'ℹ   .\venv\Scripts\pip.exe install -r requirements-neutts.txt' -ForegroundColor Blue
        return $false
    }
}

# Setup .env configuration file
function Initialize-Configuration {
    param([bool]$NeuTTSInstalled)
    
    Write-Host "\n>>> Setting up configuration file..." -ForegroundColor Yellow
    
    if (Test-Path ".env") {
        Write-Host "✓ .env file already exists" -ForegroundColor Green
        $overwrite = Read-Host "Overwrite with defaults? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Host "ℹ Keeping existing .env file" -ForegroundColor Blue
            return $true
        }
    }
    
    try {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env" | Out-Null
            Write-Host "✓ Created .env from .env.example" -ForegroundColor Green
            
            # Update TTS_SERVICE based on installation
            if ($NeuTTSInstalled) {
                (Get-Content ".env") -replace "TTS_SERVICE=speakerbot", "TTS_SERVICE=neutts" | Set-Content ".env"
                Write-Host "ℹ Set TTS_SERVICE=neutts in .env" -ForegroundColor Blue
            }
        } else {
            # Create basic .env file
            $ttsService = if ($NeuTTSInstalled) { "neutts" } else { "speakerbot" }
            $envContent = @"
TTS_SERVICE=$ttsService
WHISPER_MODEL=base

# Speakerbot settings
SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080
VOICE_NAME=Sally

# NeuTTS Air settings
NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf
NEUTTS_BACKBONE_DEVICE=cpu
NEUTTS_CODEC=neuphonic/neucodec
NEUTTS_CODEC_DEVICE=cpu
NEUTTS_REF_AUDIO=samples/reference.wav
NEUTTS_REF_TEXT=samples/reference.txt

# Audio settings
SAMPLE_RATE=16000
CHUNK_DURATION=3.0
SILENCE_THRESHOLD=0.01
MIN_SPEECH_DURATION=0.5
"@
            Set-Content ".env" $envContent | Out-Null
            Write-Host "✓ Created basic .env file" -ForegroundColor Green
        }
        
        return $true
    } catch {
        Write-Host "✗ Failed to create .env file: $_" -ForegroundColor Red
        return $false
    }
}

# Print next steps
function Show-NextSteps {
    param([bool]$NeuTTSInstalled, [bool]$CudaInstalled)
    
    Write-Host "\n$('=' * 80)" -ForegroundColor Cyan; Write-Host "  Installation Complete!" -ForegroundColor Cyan; Write-Host "$('=' * 80)\n" -ForegroundColor Cyan
    
    Write-Host @"

🎉 Installation finished successfully!

$('─' * 80)
NEXT STEPS:
$('─' * 80)

1️⃣  Review and edit configuration:
   • Open and edit the .env file
   • Configure your TTS service settings
   • Set Whisper model size (tiny/base/small/medium/large)

"@

    if ($NeuTTSInstalled) {
        Write-Host @"
2️⃣  For NeuTTS Air:
   • Prepare a reference audio file (3-15 seconds, .wav format)
   • Create a text file with the transcription
   • Update NEUTTS_REF_AUDIO and NEUTTS_REF_TEXT in .env
   • Sample files are in the 'samples/' directory
   • Set NEUTTS_BACKBONE_DEVICE=cuda if you have GPU

"@
    } else {
        Write-Host @"
2️⃣  For Speakerbot:
   • Make sure Speakerbot is running
   • Update SPEAKERBOT_WEBSOCKET_URL in .env
   • Set your preferred VOICE_NAME

"@
    }

    Write-Host @"
3️⃣  Run the application:
   • Double-click run.bat
   • Or in PowerShell: .\run.bat
   • Or activate venv and run: python main.py

"@

    if ($CudaInstalled) {
        Write-Host "⚠ CUDA was installed - you may need to restart your computer for GPU acceleration to work" -ForegroundColor Yellow
    }

    if ($NeuTTSInstalled) {
        Write-Host "ℹ On first run, NeuTTS will download model files (~1-2GB)" -ForegroundColor Blue
        Write-Host "ℹ This is a one-time download and may take several minutes" -ForegroundColor Blue
    }

    Write-Host @"

$('─' * 80)
📚 Documentation:
   • README.md - Full documentation
   • .env.example - Configuration reference
   • WINDOWS_GOOGLE_CLOUD_TTS_STREAMER_BOT_TUTORIAL.md - Alternative setup
$('─' * 80)

Need help? Check the README or open an issue on GitHub!

"@
}

# Main installation flow
function Start-Installation {
    Write-Host "\n$('=' * 80)" -ForegroundColor Cyan; Write-Host "  Speech-to-Text-to-Speech Windows Setup" -ForegroundColor Cyan; Write-Host "$('=' * 80)\n" -ForegroundColor Cyan
    
    Write-Host "ℹ This installer will set up all dependencies for the speech-to-text-to-speech application" -ForegroundColor Blue
    Write-Host "ℹ This includes: Python, FFmpeg, espeak-ng, and optionally CUDA for GPU acceleration" -ForegroundColor Blue
    Write-Host ""
    
    $continue = Read-Host "Continue with installation? (Y/n)"
    if ($continue -eq "n" -or $continue -eq "N") {
        Write-Host "ℹ Installation cancelled" -ForegroundColor Blue
        exit 0
    }
    
    # Install Chocolatey
    if (-not (Install-Chocolatey)) {
        Write-Host "✗ Failed to install Chocolatey. Cannot continue." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Install Python
    if (-not (Install-Python)) {
        Write-Host "✗ Failed to install Python. Cannot continue." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Install FFmpeg
    if (-not (Install-FFmpeg)) {
        Write-Host "✗ Failed to install FFmpeg. Cannot continue." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Install espeak-ng
    $espeakInstalled = Install-ESpeak
    
    # Ask about CUDA
    $cudaInstalled = $false
    if (Test-NvidiaGPU) {
        $cudaInstalled = Install-CUDA
    }
    
    # Create virtual environment
    if (-not (New-VirtualEnvironment)) {
        Write-Host "✗ Failed to create virtual environment. Cannot continue." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Upgrade pip
    Update-Pip
    
    # Install base requirements
    if (-not (Install-BaseRequirements)) {
        Write-Host "✗ Failed to install base requirements." -ForegroundColor Red
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 1
        }
    }
    
    # Install NeuTTS (optional)
    $neuttsInstalled = Install-NeuTTS
    
    # Setup configuration
    $configResult = Initialize-Configuration -NeuTTSInstalled $neuttsInstalled
    
    # Show next steps
    Show-NextSteps -NeuTTSInstalled $neuttsInstalled -CudaInstalled $cudaInstalled
    
    Write-Host ""
    Read-Host "Press Enter to exit"
}

# Run the installation
try {
    Start-Installation
} catch {
    Write-Host "`n✗ An error occurred during installation: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
