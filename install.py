#!/usr/bin/env python3
"""
Automated Installation Script for speech-to-text-to-speech
Handles dependency installation and TTS service setup across platforms

This script will:
1. Check system dependencies (Python, FFmpeg, PortAudio)
2. Create a virtual environment
3. Install base requirements (Whisper, PyAudio, etc.)
4. Let you choose TTS service: Speakerbot, Piper, StyleTTS2, or NeuTTS Air
5. Install TTS-specific dependencies
6. Set up environment configuration
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(text):
    """Print a formatted step"""
    print(f"\n>>> {text}")


def run_command(cmd, shell=True, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except Exception as e:
        return False, "", str(e)


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    print_step("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print(f"✗ Python 3.8+ required, but {version.major}.{version.minor}.{version.micro} found")
        return False


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print_step("Checking for FFmpeg...")
    success, _, _ = run_command("ffmpeg -version", check=False)
    if success:
        print("✓ FFmpeg is installed")
        return True
    else:
        print("✗ FFmpeg not found")
        return False


def install_ffmpeg():
    """Provide instructions for installing FFmpeg"""
    system = platform.system()
    print_step("FFmpeg Installation Required")
    
    if system == "Windows":
        print("\n⚠ FFmpeg is required but not found!")
        print("\nFor automatic installation, please run setup.bat instead of install.bat")
        print("(setup.bat will install all system dependencies automatically)")
        print("\nOr install FFmpeg manually using one of these methods:")
        print("1. Using Chocolatey: choco install ffmpeg")
        print("2. Using Scoop: scoop install ffmpeg")
        print("3. Download from: https://www.gyan.dev/ffmpeg/builds/")
        print("   Then add to PATH manually")
    elif system == "Darwin":  # macOS
        print("\nPlease install FFmpeg using Homebrew:")
        print("   brew install ffmpeg")
    else:  # Linux
        print("\nPlease install FFmpeg using your package manager:")
        print("   sudo apt-get install ffmpeg  # Ubuntu/Debian")
        print("   sudo yum install ffmpeg      # CentOS/RHEL")
        print("   sudo pacman -S ffmpeg        # Arch")
    
    input("\nPress Enter after installing FFmpeg to continue...")
    return check_ffmpeg()


def check_portaudio():
    """Check if PortAudio is installed (Linux/macOS)"""
    system = platform.system()
    if system == "Windows":
        return True  # PortAudio comes with PyAudio wheel on Windows
    
    print_step("Checking for PortAudio...")
    
    # Check for common PortAudio locations
    if system == "Darwin":
        success, _, _ = run_command("brew list portaudio", check=False)
    else:  # Linux
        success, _, _ = run_command("dpkg -l | grep portaudio", check=False)
    
    if success:
        print("✓ PortAudio is installed")
        return True
    else:
        print("✗ PortAudio not found")
        return False


def install_portaudio():
    """Install PortAudio on Linux/macOS"""
    system = platform.system()
    print_step("Installing PortAudio...")
    
    if system == "Darwin":
        print("Installing PortAudio via Homebrew...")
        success, _, _ = run_command("brew install portaudio")
        return success
    else:  # Linux
        print("Please install PortAudio using your package manager:")
        print("   sudo apt-get install portaudio19-dev  # Ubuntu/Debian")
        print("   sudo yum install portaudio-devel      # CentOS/RHEL")
        input("\nPress Enter after installing PortAudio to continue...")
        return check_portaudio()


def create_venv():
    """Create virtual environment"""
    print_step("Creating virtual environment...")
    
    if os.path.exists("venv"):
        print("Virtual environment already exists")
        return True
    
    success, _, stderr = run_command(f"{sys.executable} -m venv venv")
    if success:
        print("✓ Virtual environment created")
        return True
    else:
        print(f"✗ Failed to create virtual environment: {stderr}")
        return False


def get_venv_python():
    """Get the path to the virtual environment Python executable"""
    system = platform.system()
    if system == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")


def get_venv_pip():
    """Get the path to the virtual environment pip executable"""
    system = platform.system()
    if system == "Windows":
        return os.path.join("venv", "Scripts", "pip.exe")
    else:
        return os.path.join("venv", "bin", "pip")


def upgrade_pip():
    """Upgrade pip in virtual environment"""
    print_step("Upgrading pip...")
    pip_path = get_venv_pip()
    success, _, _ = run_command(f'"{pip_path}" install --upgrade pip')
    if success:
        print("✓ pip upgraded")
        return True
    else:
        print("✗ Failed to upgrade pip (continuing anyway...)")
        return True  # Non-critical


def install_base_requirements():
    """Install base requirements"""
    print_step("Installing base requirements...")
    pip_path = get_venv_pip()
    
    print("This will install:")
    print("  - openai-whisper (speech recognition)")
    print("  - numpy (numerical computations)")
    print("  - pyaudio (audio input/output)")
    print("  - python-dotenv (configuration management)")
    print("  - websockets (WebSocket client)")
    print("")
    
    # Try to install requirements
    success, stdout, stderr = run_command(f'"{pip_path}" install -r requirements.txt')
    
    if success:
        print("✓ Base requirements installed successfully")
        return True
    else:
        print("⚠ Some packages may have failed to install")
        print(f"\nError details:\n{stderr[:500]}")
        
        # Check if PyAudio failed on Windows
        if platform.system() == "Windows" and ("pyaudio" in stderr.lower() or "portaudio" in stderr.lower()):
            print("\n⚠ PyAudio installation failed. This is common on Windows.")
            print("\nOptions to fix:")
            print("1. Install Microsoft C++ Build Tools from:")
            print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            print("   Select 'Desktop development with C++' during installation")
            print("\n2. Or use pipwin to install PyAudio:")
            print(f'   "{pip_path}" install pipwin')
            print(f'   "{pip_path}" install pyaudio --only-binary :all:')
            print("\n3. Or download pre-built PyAudio wheel from:")
            print("   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
            print(f'   Then install with: "{pip_path}" install PyAudio-X.X.X-cpXX-cpXX-win_amd64.whl')
            
            response = input("\nContinue anyway? (y/n): ").strip().lower()
            return response == 'y'
        
        response = input("\nContinue anyway? (y/n): ").strip().lower()
        return response == 'y'


def ask_stt_service():
    """Ask user which STT (Speech-to-Text) service they want to install"""
    print_header("STT (Speech-to-Text) Service Selection")

    print("This project supports multiple speech-to-text options:")
    print("")
    print("1. Whisper (default, well-established):")
    print("   • OpenAI's Whisper model")
    print("   • Well-tested and reliable")
    print("   • Multiple model sizes (tiny to large)")
    print("   • Good accuracy")
    print("   • ~1-10GB depending on model size")
    print("")
    print("2. Parakeet (NVIDIA, ultra-fast):")
    print("   • NVIDIA Parakeet-TDT model")
    print("   • Ultra-fast transcription (60min audio/sec)")
    print("   • Multilingual (25 European languages)")
    print("   • Automatic language detection")
    print("   • Requires PyTorch + NeMo (~2-3GB)")
    print("   • Best with GPU but works on CPU")
    print("")

    while True:
        print("Which STT service would you like to install?")
        response = input("Enter 1 (Whisper) or 2 (Parakeet): ").strip()
        if response in ['1', '2']:
            return response
        print("Please enter 1 or 2")


def ask_tts_service():
    """Ask user which TTS service they want to install"""
    print_header("TTS (Text-to-Speech) Service Selection")

    print("This project supports multiple TTS options:")
    print("")
    print("1. Speakerbot (default - no installation needed):")
    print("   • External WebSocket TTS service")
    print("   • Requires Speakerbot running separately")
    print("   • Zero local dependencies")
    print("   • Network dependent")
    print("")
    print("2. Piper (simplest local option):")
    print("   • Fast local TTS with ONNX")
    print("   • Pre-trained voices only (no voice cloning)")
    print("   • Very lightweight (~100MB)")
    print("   • Runs fast on CPU")
    print("   • MIT licensed")
    print("")
    print("3. StyleTTS2 (modern voice cloning):")
    print("   • Local neural TTS with voice cloning")
    print("   • Clone voice from 3-15 second samples")
    print("   • Simpler than NeuTTS (no espeak-ng needed)")
    print("   • Requires PyTorch (~1-2GB)")
    print("   • MIT licensed")
    print("")
    print("4. NeuTTS Air (advanced voice cloning):")
    print("   • High-quality voice cloning")
    print("   • Most features, most complex")
    print("   • Requires PyTorch + espeak-ng (~2-4GB)")
    print("   • Best with GPU")
    print("")

    while True:
        print("Which TTS service would you like to install?")
        response = input("Enter 1 (Speakerbot), 2 (Piper), 3 (StyleTTS2), or 4 (NeuTTS): ").strip()
        if response in ['1', '2', '3', '4']:
            return response
        print("Please enter 1, 2, 3, or 4")


def install_neutts_requirements():
    """Install NeuTTS requirements"""
    print_step("Installing NeuTTS Air requirements...")
    pip_path = get_venv_pip()
    python_path = get_venv_python()
    
    print("This will install:")
    print("  - PyTorch (deep learning framework)")
    print("  - Transformers (NLP models)")
    print("  - Phonemizer (text-to-phoneme conversion)")
    print("  - NeuCodec (audio codec)")
    print("  - And other dependencies...")
    print("\nThis may take several minutes and download ~1-2GB of packages.")
    print("")
    
    # Check if CUDA is available
    system = platform.system()
    cuda_available = False
    
    if system == "Windows":
        cuda_available = os.path.exists("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA") or \
                        os.path.exists("C:\\ProgramData\\chocolatey\\lib\\cuda")
    
    # Install PyTorch first with proper error handling
    torch_installed = False
    
    if cuda_available:
        print("✓ CUDA detected - installing PyTorch 2.4.1 with GPU support")
        print("  Using CUDA 12.1 index: https://download.pytorch.org/whl/cu121")
        print("")

        success, stdout, stderr = run_command(
            f'"{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cu121',
            check=False
        )

        if success:
            print("✓ PyTorch with CUDA support installed successfully")
            torch_installed = True
        else:
            print("⚠ Failed to install PyTorch with CUDA support")
            print(f"  Error: {stderr[:200]}")
            print("  Falling back to CPU version...")

    if not torch_installed:
        print("ℹ Installing PyTorch 2.4.1 (CPU version)")
        print("  Using CPU index: https://download.pytorch.org/whl/cpu")
        print("")

        success, stdout, stderr = run_command(
            f'"{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cpu',
            check=False
        )
        
        if not success:
            print("✗ Failed to install PyTorch (CPU version)")
            print(f"  Error: {stderr[:200]}")
            print("\nYou may need to install PyTorch manually:")
            print("Visit: https://pytorch.org/get-started/locally/")
            print("\nFor CPU-only (no GPU):")
            print(f'  "{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cpu')
            print("\nFor NVIDIA GPU (CUDA 12.1):")
            print(f'  "{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cu121')
            print("\nAlternatively, try without version constraint:")
            print(f'  "{pip_path}" install torch torchaudio')
            response = input("\nContinue with remaining packages? (y/n): ").strip().lower()
            if response != 'y':
                return False
        else:
            print("✓ PyTorch (CPU version) installed successfully")
            torch_installed = True
    
    # Verify PyTorch installation
    if torch_installed:
        print("\nℹ Verifying PyTorch installation...")
        success, stdout, stderr = run_command(
            f'"{python_path}" -c "import torch; print(f\'PyTorch {{torch.__version__}}\'); print(f\'CUDA available: {{torch.cuda.is_available()}}\')"',
            check=False
        )
        if success:
            print("✓ PyTorch verification:")
            for line in stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("⚠ Could not verify PyTorch installation")
    
    # Install remaining NeuTTS dependencies
    print("\nℹ Installing remaining NeuTTS dependencies...")
    success, stdout, stderr = run_command(f'"{pip_path}" install -r requirements-neutts.txt', check=False)
    
    if success:
        print("✓ NeuTTS requirements installed successfully")
    else:
        print("⚠ Some NeuTTS packages may have failed to install")
        print(f"\nError details:\n{stderr[:500]}")
    
    # Check for espeak-ng
    print_step("Checking for espeak-ng (required for NeuTTS)...")
    espeak_success, stdout, _ = run_command("espeak-ng --version", check=False)
    
    if espeak_success:
        print("✓ espeak-ng is installed")
        version_line = stdout.split('\n')[0] if stdout else ""
        print(f"  {version_line}")
    else:
        print("✗ espeak-ng not found - THIS IS REQUIRED FOR NEUTTS!")
        
        if system == "Windows":
            print("\n⚠ espeak-ng is required but not installed!")
            print("\nFor automatic installation, please run setup.bat instead of install.bat")
            print("(setup.bat will install all system dependencies automatically)")
            print("\n📥 Or install espeak-ng manually:")
            print("1. Download from: https://github.com/espeak-ng/espeak-ng/releases")
            print("2. Look for espeak-ng-X.XX-x64.msi (e.g., espeak-ng-1.51-x64.msi)")
            print("3. Run the installer")
            print("4. Make sure to check 'Add to PATH' during installation")
            print("\nDirect link: https://github.com/espeak-ng/espeak-ng/releases/latest")
        elif system == "Darwin":
            print("\n📥 Installing espeak-ng via Homebrew...")
            brew_success, _, _ = run_command("brew install espeak-ng", check=False)
            if brew_success:
                print("✓ espeak-ng installed successfully")
                return True
        else:
            print("\n📥 Please install espeak-ng:")
            print("   sudo apt-get install espeak-ng  # Ubuntu/Debian")
            print("   sudo yum install espeak-ng      # CentOS/RHEL")
            print("   sudo pacman -S espeak-ng        # Arch")
        
        input("\nPress Enter after installing espeak-ng to continue...")
        
        # Verify installation
        espeak_success, _, _ = run_command("espeak-ng --version", check=False)
        if not espeak_success:
            print("⚠ espeak-ng still not found. NeuTTS may not work correctly.")
            print("Please ensure espeak-ng is installed and in your system PATH.")
    
    return True


def install_parakeet_requirements():
    """Install Parakeet TDT requirements"""
    print_step("Installing Parakeet TDT requirements...")
    pip_path = get_venv_pip()
    python_path = get_venv_python()

    print("This will install:")
    print("  - PyTorch (deep learning framework)")
    print("  - NeMo toolkit with ASR support")
    print("  - And other dependencies...")
    print("\nThis may take several minutes and download ~2-3GB of packages.")
    print("")

    # Check if CUDA is available (reuse logic from NeuTTS)
    system = platform.system()
    cuda_available = False

    if system == "Windows":
        cuda_available = os.path.exists("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA") or \
                        os.path.exists("C:\\ProgramData\\chocolatey\\lib\\cuda")

    # Install PyTorch first with proper error handling
    torch_installed = False

    if cuda_available:
        print("✓ CUDA detected - installing PyTorch 2.4.1 with GPU support")
        print("  Using CUDA 12.1 index: https://download.pytorch.org/whl/cu121")
        print("")

        success, stdout, stderr = run_command(
            f'"{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cu121',
            check=False
        )

        if success:
            print("✓ PyTorch with CUDA support installed successfully")
            torch_installed = True
        else:
            print("⚠ Failed to install PyTorch with CUDA support")
            print(f"  Error: {stderr[:200]}")
            print("  Falling back to CPU version...")

    if not torch_installed:
        print("ℹ Installing PyTorch 2.4.1 (CPU version)")
        print("  Using CPU index: https://download.pytorch.org/whl/cpu")
        print("")

        success, stdout, stderr = run_command(
            f'"{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cpu',
            check=False
        )

        if not success:
            print("✗ Failed to install PyTorch (CPU version)")
            print(f"  Error: {stderr[:200]}")
            print("\nYou may need to install PyTorch manually:")
            print("Visit: https://pytorch.org/get-started/locally/")
            print("\nFor CPU-only (no GPU):")
            print(f'  "{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cpu')
            print("\nFor NVIDIA GPU (CUDA 12.1):")
            print(f'  "{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cu121')
            response = input("\nContinue with remaining packages? (y/n): ").strip().lower()
            if response != 'y':
                return False
        else:
            print("✓ PyTorch (CPU version) installed successfully")
            torch_installed = True

    # Verify PyTorch installation
    if torch_installed:
        print("\nℹ Verifying PyTorch installation...")
        success, stdout, stderr = run_command(
            f'"{python_path}" -c "import torch; print(f\'PyTorch {{torch.__version__}}\'); print(f\'CUDA available: {{torch.cuda.is_available()}}\')"',
            check=False
        )
        if success:
            print("✓ PyTorch verification:")
            for line in stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("⚠ Could not verify PyTorch installation")

    # Install Parakeet/NeMo dependencies
    print("\nℹ Installing NeMo toolkit with ASR support...")
    success, stdout, stderr = run_command(f'"{pip_path}" install -r requirements-parakeet.txt', check=False)

    if success:
        print("✓ Parakeet requirements installed successfully")
        print("\n📝 NOTE: The Parakeet model (~600MB) will be downloaded automatically on first use")
        print("   It will be cached in ~/.cache/huggingface/hub/")
        return True
    else:
        print("⚠ Some Parakeet packages may have failed to install")
        print(f"\nError details:\n{stderr[:500]}")
        response = input("\nContinue anyway? (y/n): ").strip().lower()
        return response == 'y'


def install_piper_requirements():
    """Install Piper TTS requirements"""
    print_step("Installing Piper TTS requirements...")
    pip_path = get_venv_pip()

    print("This will install:")
    print("  - piper-tts (fast local TTS)")
    print("\nThis is very lightweight, only ~20MB")
    print("")

    success, stdout, stderr = run_command(f'"{pip_path}" install -r requirements-piper.txt', check=False)

    if success:
        print("✓ Piper TTS requirements installed successfully")
        print("\n📝 NOTE: You need to download voice models separately:")
        print("   Download from: https://huggingface.co/rhasspy/piper-voices")
        print("   Set PIPER_VOICE_PATH in .env to the .onnx file path")
        return True
    else:
        print("⚠ Piper TTS installation failed")
        print(f"\nError details:\n{stderr[:500]}")
        response = input("\nContinue anyway? (y/n): ").strip().lower()
        return response == 'y'


def install_styletts2_requirements():
    """Install StyleTTS2 requirements"""
    print_step("Installing StyleTTS2 requirements...")
    pip_path = get_venv_pip()
    python_path = get_venv_python()

    print("This will install:")
    print("  - PyTorch (deep learning framework)")
    print("  - StyleTTS2 (neural TTS with voice cloning)")
    print("\nThis may take several minutes and download ~1-2GB of packages.")
    print("")

    # Check if CUDA is available
    system = platform.system()
    cuda_available = False

    if system == "Windows":
        cuda_available = os.path.exists("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA") or \
                        os.path.exists("C:\\ProgramData\\chocolatey\\lib\\cuda")

    # Install PyTorch first
    torch_installed = False

    if cuda_available:
        print("✓ CUDA detected - installing PyTorch 2.4.1 with GPU support")
        print("  Using CUDA 12.1 index: https://download.pytorch.org/whl/cu121")
        print("")

        success, stdout, stderr = run_command(
            f'"{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cu121',
            check=False
        )

        if success:
            print("✓ PyTorch with CUDA support installed successfully")
            torch_installed = True
        else:
            print("⚠ Failed to install PyTorch with CUDA support")
            print(f"  Error: {stderr[:200]}")
            print("  Falling back to CPU version...")

    if not torch_installed:
        print("ℹ Installing PyTorch 2.4.1 (CPU version)")
        print("  Using CPU index: https://download.pytorch.org/whl/cpu")
        print("")

        success, stdout, stderr = run_command(
            f'"{pip_path}" install torch==2.4.1 torchaudio==2.4.1 --extra-index-url https://download.pytorch.org/whl/cpu',
            check=False
        )

        if not success:
            print("✗ Failed to install PyTorch (CPU version)")
            print(f"  Error: {stderr[:200]}")
            response = input("\nContinue with remaining packages? (y/n): ").strip().lower()
            if response != 'y':
                return False
        else:
            print("✓ PyTorch 2.4.1 (CPU version) installed successfully")
            torch_installed = True

    # Verify PyTorch installation
    if torch_installed:
        print("\nℹ Verifying PyTorch installation...")
        success, stdout, stderr = run_command(
            f'"{python_path}" -c "import torch; print(f\'PyTorch {{torch.__version__}}\'); print(f\'CUDA available: {{torch.cuda.is_available()}}\')"',
            check=False
        )
        if success:
            print("✓ PyTorch verification:")
            for line in stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("⚠ Could not verify PyTorch installation")

    # Install StyleTTS2
    print("\nℹ Installing StyleTTS2...")
    success, stdout, stderr = run_command(f'"{pip_path}" install -r requirements-styletts2.txt', check=False)

    if success:
        # Download required NLTK data
        print("ℹ Downloading NLTK punkt_tab tokenizer...")
        run_command(f'"{python_path}" -c "import nltk; nltk.download(\'punkt_tab\', quiet=True)"', check=False)

        print("✓ StyleTTS2 requirements installed successfully")
        print("\n📝 NOTE: On first run, StyleTTS2 will download model files (~500MB-1GB)")
        print("   This is a one-time download from HuggingFace")
        return True
    else:
        print("⚠ Some StyleTTS2 packages may have failed to install")
        print(f"\nError details:\n{stderr[:500]}")
        response = input("\nContinue anyway? (y/n): ").strip().lower()
        return response == 'y'


def setup_env_file(stt_choice, tts_choice):
    """Set up .env file from .env.example"""
    print_step("Setting up environment configuration...")

    env_exists = os.path.exists(".env")

    # Map choice to service name
    stt_service_map = {
        '1': 'whisper',
        '2': 'parakeet'
    }
    stt_service = stt_service_map.get(stt_choice, 'whisper')

    tts_service_map = {
        '1': 'speakerbot',
        '2': 'piper',
        '3': 'styletts2',
        '4': 'neutts'
    }
    tts_service = tts_service_map.get(tts_choice, 'speakerbot')

    if env_exists:
        print("✓ .env file already exists")
        overwrite = input("Overwrite existing .env file with defaults? (y/n): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("Keeping existing .env file")
            return True

    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("✓ .env file created from .env.example")

        # Update STT_SERVICE and TTS_SERVICE based on installation choices
        try:
            with open(".env", "r") as f:
                content = f.read()
            content = content.replace("STT_SERVICE=whisper", f"STT_SERVICE={stt_service}")
            content = content.replace("TTS_SERVICE=speakerbot", f"TTS_SERVICE={tts_service}")
            with open(".env", "w") as f:
                f.write(content)
            print(f"✓ Set STT_SERVICE={stt_service} in .env")
            print(f"✓ Set TTS_SERVICE={tts_service} in .env")
        except Exception as e:
            print(f"⚠ Could not update .env automatically: {e}")

        print("\n📝 Configuration file created!")
        print("   Location: .env")
        print("\n⚠ You may need to edit .env for your setup:")

        # STT configuration hints
        if stt_service == 'parakeet':
            print("\n   STT (Speech-to-Text) Settings:")
            print("   - PARAKEET_MODEL: model name (default: nvidia/parakeet-tdt-0.6b-v3)")
        else:  # whisper
            print("\n   STT (Speech-to-Text) Settings:")
            print("   - WHISPER_MODEL: tiny/base/small/medium/large (larger = more accurate but slower)")

        # TTS configuration hints
        print("\n   TTS (Text-to-Speech) Settings:")
        if tts_service == 'neutts':
            print("   - NEUTTS_REF_AUDIO: path to your reference audio (3-15 sec, .wav)")
            print("   - NEUTTS_REF_TEXT: path to transcription of reference audio")
            print("   - NEUTTS_BACKBONE_DEVICE: 'cuda' for GPU or 'cpu' for CPU")
        elif tts_service == 'piper':
            print("   - PIPER_VOICE_PATH: path to .onnx voice model file")
            print("   - Download voices from: https://huggingface.co/rhasspy/piper-voices")
        elif tts_service == 'styletts2':
            print("   - STYLETTS2_REF_AUDIO: path to reference audio for voice cloning")
            print("   - Leave empty to use default voice")
        else:  # speakerbot
            print("   - SPEAKERBOT_WEBSOCKET_URL: your Speakerbot WebSocket URL")
            print("   - VOICE_NAME: the voice to use in Speakerbot")

        return True
    else:
        print("⚠ .env.example not found, creating basic .env...")
        try:
            with open(".env", "w") as f:
                f.write(f"STT_SERVICE={stt_service}\n")
                if stt_service == 'whisper':
                    f.write("WHISPER_MODEL=base\n")
                else:
                    f.write("PARAKEET_MODEL=nvidia/parakeet-tdt-0.6b-v3\n")
                f.write(f"TTS_SERVICE={tts_service}\n")
                if tts_service == 'neutts':
                    f.write("NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf\n")
                    f.write("NEUTTS_BACKBONE_DEVICE=cpu\n")
                elif tts_service == 'piper':
                    f.write("PIPER_VOICE_PATH=\n")
                elif tts_service == 'styletts2':
                    f.write("STYLETTS2_REF_AUDIO=\n")
                else:
                    f.write("SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080\n")
            print("✓ Basic .env file created")
            return True
        except Exception as e:
            print(f"⚠ Could not create .env file: {e}")
            return False


def print_next_steps(tts_choice):
    """Print next steps for the user"""
    print_header("Installation Complete!")

    system = platform.system()
    tts_service_map = {
        '1': 'speakerbot',
        '2': 'piper',
        '3': 'styletts2',
        '4': 'neutts'
    }
    tts_service = tts_service_map.get(tts_choice, 'speakerbot')

    print("🎉 Installation finished successfully!")
    print("\n" + "─" * 70)
    print("NEXT STEPS:")
    print("─" * 70)

    print("\n1️⃣  Activate the virtual environment:")
    if system == "Windows":
        print("   venv\\Scripts\\activate")
        print("   (or venv\\Scripts\\activate.bat in Command Prompt)")
    else:
        print("   source venv/bin/activate")

    print("\n2️⃣  Review and edit configuration file:")
    print("   Edit the .env file to configure:")

    if tts_service == 'neutts':
        print("\n   For NeuTTS Air:")
        print(f"   - TTS_SERVICE={tts_service} (already set)")
        print("   - NEUTTS_REF_AUDIO=path to reference audio (3-15 sec .wav file)")
        print("   - NEUTTS_REF_TEXT=path to transcription text file")
        print("   - NEUTTS_BACKBONE_DEVICE=cuda (if you have GPU) or cpu")
        print("\n   Sample files are available in the 'samples/' directory")
    elif tts_service == 'piper':
        print("\n   For Piper TTS:")
        print(f"   - TTS_SERVICE={tts_service} (already set)")
        print("   - PIPER_VOICE_PATH=path/to/voice.onnx")
        print("   - Download voices from: https://huggingface.co/rhasspy/piper-voices")
        print("   - You need both .onnx and .onnx.json files")
    elif tts_service == 'styletts2':
        print("\n   For StyleTTS2:")
        print(f"   - TTS_SERVICE={tts_service} (already set)")
        print("   - STYLETTS2_REF_AUDIO=path to reference audio (for voice cloning)")
        print("   - Leave empty to use default voice")
    else:  # speakerbot
        print("\n   For Speakerbot:")
        print(f"   - TTS_SERVICE={tts_service} (already set)")
        print("   - SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080")
        print("   - VOICE_NAME=your preferred voice")

    print("\n   For Whisper (speech recognition):")
    print("   - WHISPER_MODEL=base (or tiny/small/medium/large)")
    print("     • tiny:   fastest, least accurate (~1GB RAM)")
    print("     • base:   balanced (default, ~1GB RAM)")
    print("     • small:  good quality (~2GB RAM)")
    print("     • medium: better quality (~5GB RAM)")
    print("     • large:  best quality, slowest (~10GB RAM)")

    print("\n3️⃣  Run the application:")
    if system == "Windows":
        print("   run.bat")
    else:
        print("   ./run.sh")
        print("   (or: python main.py)")

    if tts_service in ['neutts', 'styletts2']:
        print(f"\n📝 NOTE: On first run, {tts_service.upper()} will download model files.")
        print("   This is a one-time download and may take several minutes.")

    print("\n" + "─" * 70)
    print("📚 For more information:")
    print("   - README.md - General documentation")
    print("   - .env.example - Configuration options")
    print("   - CLAUDE.md - TTS comparison and troubleshooting")
    print("─" * 70 + "\n")

    print("Need help? Check the README or open an issue on GitHub!")
    print("")


def main():
    """Main installation function"""
    print_header("Speech-to-Text-to-Speech Installer")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check Python version
    if not check_python_version():
        print("\n✗ Please install Python 3.8 or higher and try again")
        sys.exit(1)
    
    # Check FFmpeg
    if not check_ffmpeg():
        if not install_ffmpeg():
            print("\n✗ FFmpeg is required. Please install it and run this script again.")
            sys.exit(1)
    
    # Check PortAudio (Linux/macOS only)
    if not check_portaudio():
        if not install_portaudio():
            print("\n✗ PortAudio is required. Please install it and run this script again.")
            sys.exit(1)
    
    # Create virtual environment
    if not create_venv():
        print("\n✗ Failed to create virtual environment")
        sys.exit(1)
    
    # Upgrade pip
    upgrade_pip()
    
    # Install base requirements
    base_requirements_successful = install_base_requirements()
    if not base_requirements_successful:
        print("\n✗ Failed to install base requirements")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(1)

    # Ask about STT service
    stt_choice = ask_stt_service()

    # Install STT-specific dependencies
    stt_setup_successful = True
    if stt_choice == '1':
        print("\n✓ Whisper selected - no additional dependencies needed (already in base requirements)")
        # Use base requirements status since Whisper depends on them
        stt_setup_successful = base_requirements_successful
    elif stt_choice == '2':
        print("\n✓ Installing Parakeet TDT...")
        stt_setup_successful = install_parakeet_requirements()

    if not stt_setup_successful:
        print("\n⚠ STT setup encountered issues.")
        print("You can reconfigure later by editing .env")

    # Ask about TTS service
    tts_choice = ask_tts_service()

    # Install TTS-specific dependencies
    tts_installed = True
    if tts_choice == '1':
        print("\n✓ Speakerbot selected - no additional dependencies needed")
    elif tts_choice == '2':
        print("\n✓ Installing Piper TTS...")
        tts_installed = install_piper_requirements()
    elif tts_choice == '3':
        print("\n✓ Installing StyleTTS2...")
        tts_installed = install_styletts2_requirements()
    elif tts_choice == '4':
        print("\n✓ Installing NeuTTS Air...")
        tts_installed = install_neutts_requirements()

    if not tts_installed:
        print("\n⚠ TTS installation encountered issues.")
        print("You can reconfigure later by editing .env")

    # Setup .env file
    setup_env_file(stt_choice, tts_choice)

    # Print next steps
    print_next_steps(tts_choice)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
