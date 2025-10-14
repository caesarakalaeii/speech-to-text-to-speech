#!/usr/bin/env python3
"""
Automated Installation Script for speech-to-text-to-speech
Handles dependency installation and NeuTTS setup across platforms

This script will:
1. Check system dependencies (Python, FFmpeg, PortAudio)
2. Create a virtual environment
3. Install base requirements (Whisper, PyAudio, etc.)
4. Optionally install NeuTTS Air dependencies for local TTS
5. Set up environment configuration
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


def ask_neutts():
    """Ask user if they want to install NeuTTS"""
    print_header("NeuTTS Air - Local Neural TTS with Voice Cloning")
    
    print("This project supports two TTS (Text-to-Speech) options:")
    print("")
    print("1. Speakerbot (default):")
    print("   • Uses external WebSocket TTS service")
    print("   • Requires Speakerbot or compatible service running separately")
    print("   • Lightweight, no additional dependencies")
    print("")
    print("2. NeuTTS Air (optional):")
    print("   • Completely offline, local neural TTS engine")
    print("   • Instant voice cloning from short audio samples (3-15 seconds)")
    print("   • High-quality speech synthesis")
    print("   • No API calls, subscription fees, or usage limits")
    print("   • Requires ~2-4GB additional disk space")
    print("   • Requires espeak-ng system dependency")
    print("   • May require GPU for best performance (CPU works but slower)")
    print("")
    
    while True:
        response = input("Do you want to install NeuTTS Air dependencies? (y/n): ").strip().lower()
        if response in ['y', 'n', 'yes', 'no']:
            return response in ['y', 'yes']
        print("Please enter 'y' or 'n'")


def install_neutts_requirements():
    """Install NeuTTS requirements"""
    print_step("Installing NeuTTS Air requirements...")
    pip_path = get_venv_pip()
    
    print("This will install:")
    print("  - PyTorch (deep learning framework)")
    print("  - Transformers (NLP models)")
    print("  - Phonemizer (text-to-phoneme conversion)")
    print("  - NeuCodec (audio codec)")
    print("  - And other dependencies...")
    print("\nThis may take several minutes and download ~1-2GB of packages.")
    print("")
    
    # On Windows, suggest PyTorch installation first
    system = platform.system()
    if system == "Windows":
        print("⚠ For Windows users:")
        print("If you have an NVIDIA GPU and want to use CUDA acceleration,")
        print("PyTorch with CUDA support will be installed.")
        print("\nIf you ran setup.bat and CUDA was installed, we'll use GPU support.")
        print("Otherwise, we'll install CPU-only PyTorch.")
        print("")
        
        # Check if CUDA is available
        cuda_available = os.path.exists("C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA")
        
        if cuda_available:
            print("✓ CUDA detected - will install PyTorch with GPU support")
            # Install PyTorch with CUDA support first
            print("\nInstalling PyTorch with CUDA 12.1 support...")
            success, _, stderr = run_command(
                f'"{pip_path}" install torch torchaudio --index-url https://download.pytorch.org/whl/cu121',
                check=False
            )
            if not success:
                print("⚠ Failed to install PyTorch with CUDA, trying CPU version...")
                run_command(
                    f'"{pip_path}" install torch torchaudio --index-url https://download.pytorch.org/whl/cpu',
                    check=False
                )
        else:
            print("ℹ No CUDA detected - will install CPU-only PyTorch")
            print("\nInstalling PyTorch (CPU version)...")
            run_command(
                f'"{pip_path}" install torch torchaudio --index-url https://download.pytorch.org/whl/cpu',
                check=False
            )
    
    success, stdout, stderr = run_command(f'"{pip_path}" install -r requirements-neutts.txt', check=False)
    
    if success:
        print("✓ NeuTTS requirements installed successfully")
    else:
        print("⚠ Some NeuTTS packages may have failed to install")
        print(f"\nError details:\n{stderr[:500]}")
        print("\nYou may need to install PyTorch separately for your system:")
        print("Visit: https://pytorch.org/get-started/locally/")
        print("\nFor CPU-only (no GPU):")
        print(f'  "{pip_path}" install torch torchaudio --index-url https://download.pytorch.org/whl/cpu')
        print("\nFor NVIDIA GPU (CUDA 12.1):")
        print(f'  "{pip_path}" install torch torchaudio --index-url https://download.pytorch.org/whl/cu121')
    
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


def setup_env_file(neutts_installed):
    """Set up .env file from .env.example"""
    print_step("Setting up environment configuration...")
    
    env_exists = os.path.exists(".env")
    
    if env_exists:
        print("✓ .env file already exists")
        overwrite = input("Overwrite existing .env file with defaults? (y/n): ").strip().lower()
        if overwrite not in ['y', 'yes']:
            print("Keeping existing .env file")
            return True
    
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("✓ .env file created from .env.example")
        
        # Update TTS_SERVICE based on installation choice
        if neutts_installed:
            try:
                with open(".env", "r") as f:
                    content = f.read()
                content = content.replace("TTS_SERVICE=speakerbot", "TTS_SERVICE=neutts")
                with open(".env", "w") as f:
                    f.write(content)
                print("✓ Set TTS_SERVICE=neutts in .env")
            except Exception as e:
                print(f"⚠ Could not update .env automatically: {e}")
        
        print("\n📝 Configuration file created!")
        print("   Location: .env")
        print("\n⚠ You may need to edit .env for your setup:")
        
        if neutts_installed:
            print("   - NEUTTS_REF_AUDIO: path to your reference audio (3-15 sec, .wav)")
            print("   - NEUTTS_REF_TEXT: path to transcription of reference audio")
            print("   - NEUTTS_BACKBONE_DEVICE: 'cuda' for GPU or 'cpu' for CPU")
        else:
            print("   - SPEAKERBOT_WEBSOCKET_URL: your Speakerbot WebSocket URL")
            print("   - VOICE_NAME: the voice to use in Speakerbot")
        
        print("   - WHISPER_MODEL: tiny/base/small/medium/large (larger = more accurate but slower)")
        
        return True
    else:
        print("⚠ .env.example not found, creating basic .env...")
        try:
            with open(".env", "w") as f:
                tts_service = "neutts" if neutts_installed else "speakerbot"
                f.write(f"TTS_SERVICE={tts_service}\n")
                f.write("WHISPER_MODEL=base\n")
                if neutts_installed:
                    f.write("NEUTTS_BACKBONE=neuphonic/neutts-air-q4-gguf\n")
                    f.write("NEUTTS_BACKBONE_DEVICE=cpu\n")
                else:
                    f.write("SPEAKERBOT_WEBSOCKET_URL=ws://localhost:8080\n")
            print("✓ Basic .env file created")
            return True
        except Exception as e:
            print(f"⚠ Could not create .env file: {e}")
            return False


def print_next_steps(neutts_installed):
    """Print next steps for the user"""
    print_header("Installation Complete!")
    
    system = platform.system()
    
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
    
    if neutts_installed:
        print("\n   For NeuTTS Air:")
        print("   - TTS_SERVICE=neutts (already set)")
        print("   - NEUTTS_REF_AUDIO=path to reference audio (3-15 sec .wav file)")
        print("   - NEUTTS_REF_TEXT=path to transcription text file")
        print("   - NEUTTS_BACKBONE_DEVICE=cuda (if you have GPU) or cpu")
        print("\n   Sample files are available in the 'samples/' directory")
    else:
        print("\n   For Speakerbot:")
        print("   - TTS_SERVICE=speakerbot (already set)")
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
    
    if neutts_installed:
        print("\n📝 NOTE: On first run, NeuTTS will download model files (~1-2GB).")
        print("   This is a one-time download and may take several minutes.")
    
    print("\n" + "─" * 70)
    print("📚 For more information:")
    print("   - README.md - General documentation")
    print("   - .env.example - Configuration options")
    if neutts_installed:
        print("   - neuttsair/ - NeuTTS Air module")
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
    if not install_base_requirements():
        print("\n✗ Failed to install base requirements")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    
    # Ask about NeuTTS
    neutts_installed = False
    if ask_neutts():
        if install_neutts_requirements():
            neutts_installed = True
        else:
            print("\n⚠ NeuTTS installation encountered issues.")
            print("You can still use Speakerbot for TTS.")
    else:
        print("\n✓ Skipping NeuTTS installation - will use Speakerbot")
    
    # Setup .env file
    setup_env_file(neutts_installed)
    
    # Print next steps
    print_next_steps(neutts_installed)


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
