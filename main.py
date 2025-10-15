#!/usr/bin/env python3
"""
Speech-to-Text-to-Speech Application
Captures audio from microphone, transcribes using Whisper, and sends to TTS service (Speakerbot or NeuTTS Air)
"""
import os
import sys
import time
import queue
import json
import asyncio
import logging
import random
from threading import Thread
from dotenv import load_dotenv
import numpy as np
import pyaudio
import whisper
import websockets
import tkinter as tk
from tkinter import ttk, messagebox

# Load environment variables
load_dotenv()

# Configuration
TTS_SERVICE = os.getenv("TTS_SERVICE", "speakerbot").lower()

# Speakerbot settings
WEBSOCKET_URL = os.getenv("SPEAKERBOT_WEBSOCKET_URL", "ws://localhost:7585/speak")
VOICE_NAME = os.getenv("VOICE_NAME", "Sally")

# NeuTTS Air settings
NEUTTS_BACKBONE = os.getenv("NEUTTS_BACKBONE", "neuphonic/neutts-air-q4-gguf")
NEUTTS_BACKBONE_DEVICE = os.getenv("NEUTTS_BACKBONE_DEVICE", "cpu")
NEUTTS_CODEC = os.getenv("NEUTTS_CODEC", "neuphonic/neucodec")
NEUTTS_CODEC_DEVICE = os.getenv("NEUTTS_CODEC_DEVICE", "cpu")
NEUTTS_REF_AUDIO = os.getenv("NEUTTS_REF_AUDIO", "")
NEUTTS_REF_TEXT = os.getenv("NEUTTS_REF_TEXT", "")

# Piper TTS settings
PIPER_VOICE_PATH = os.getenv("PIPER_VOICE_PATH", "")

# StyleTTS2 settings
STYLETTS2_REF_AUDIO = os.getenv("STYLETTS2_REF_AUDIO", "")

# Whisper and audio settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
CHUNK_DURATION = float(os.getenv("CHUNK_DURATION", "3.0"))
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "0.01"))
MIN_SPEECH_DURATION = float(os.getenv("MIN_SPEECH_DURATION", "0.5"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_microphones():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            devices.append((i, info['name']))
    p.terminate()
    return devices


def list_output_devices():
    """List all available audio output devices"""
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxOutputChannels', 0) > 0:
            devices.append((i, info['name']))
    p.terminate()
    return devices


class AudioDeviceSelector:
    """Unified GUI for selecting both input and output audio devices"""

    def __init__(self, need_output=False):
        self.input_device_index = None
        self.output_device_index = None
        self.need_output = need_output

        self.root = tk.Tk()
        self.root.title('Audio Device Setup - Speech-to-Text-to-Speech')
        self.root.geometry('500x250')
        self.root.resizable(False, False)

        # Get devices
        self.input_devices = list_microphones()
        self.output_devices = list_output_devices() if need_output else []

        # Check for errors
        if not self.input_devices:
            messagebox.showerror('Error', 'No microphone devices found!')
            self.root.destroy()
            return

        if need_output and not self.output_devices:
            messagebox.showerror('Error', 'No output devices found!')
            self.root.destroy()
            return

        # Create UI
        self._create_ui()

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f'+{x}+{y}')

    def _create_ui(self):
        """Create the UI elements"""
        # Main frame with padding
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input device section
        input_label = tk.Label(main_frame, text='Microphone (Input):', font=('Arial', 10, 'bold'))
        input_label.pack(anchor=tk.W, pady=(0, 5))

        self.input_combo = ttk.Combobox(
            main_frame,
            values=[name for idx, name in self.input_devices],
            state='readonly',
            width=60
        )
        self.input_combo.pack(fill=tk.X, pady=(0, 15))
        self.input_combo.current(0)

        # Output device section (if needed)
        if self.need_output:
            output_label = tk.Label(main_frame, text='Speaker (Output):', font=('Arial', 10, 'bold'))
            output_label.pack(anchor=tk.W, pady=(0, 5))

            self.output_combo = ttk.Combobox(
                main_frame,
                values=[name for idx, name in self.output_devices],
                state='readonly',
                width=60
            )
            self.output_combo.pack(fill=tk.X, pady=(0, 15))
            self.output_combo.current(0)

        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))

        # Start button
        start_btn = tk.Button(
            button_frame,
            text='Start',
            command=self._on_start,
            width=15,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2'
        )
        start_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text='Cancel',
            command=self._on_cancel,
            width=15,
            font=('Arial', 10),
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Set protocol for window close
        self.root.protocol('WM_DELETE_WINDOW', self._on_cancel)

    def _on_start(self):
        """Handle start button click"""
        idx = self.input_combo.current()
        self.input_device_index = self.input_devices[idx][0]

        if self.need_output:
            idx = self.output_combo.current()
            self.output_device_index = self.output_devices[idx][0]

        self.root.quit()
        self.root.destroy()

    def _on_cancel(self):
        """Handle cancel button click"""
        self.input_device_index = None
        self.output_device_index = None
        self.root.quit()
        self.root.destroy()

    def show(self):
        """Show the dialog and return selected devices"""
        self.root.mainloop()
        return self.input_device_index, self.output_device_index


class AudioPlayer:
    """Plays audio through output device with queue"""
    
    def __init__(self, device_index=None):
        self.device_index = device_index
        self.playback_queue = queue.Queue()
        self.running = False
        
    def start(self):
        """Start audio playback thread"""
        self.running = True
        self.thread = Thread(target=self._playback_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Audio playback started")
        
    def stop(self):
        """Stop audio playback thread"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        logger.info("Audio playback stopped")
        
    def play(self, audio_data, sample_rate=24000):
        """Queue audio data for playback"""
        self.playback_queue.put((audio_data, sample_rate))
        
    def _playback_loop(self):
        """Playback loop running in separate thread"""
        p = pyaudio.PyAudio()
        
        try:
            while self.running:
                try:
                    audio_data, sample_rate = self.playback_queue.get(timeout=0.1)
                    
                    # Open stream for this audio
                    stream = p.open(
                        format=pyaudio.paFloat32,
                        channels=1,
                        rate=sample_rate,
                        output=True,
                        output_device_index=self.device_index
                    )
                    
                    # Convert to float32 if needed
                    if audio_data.dtype != np.float32:
                        audio_data = audio_data.astype(np.float32)
                    
                    # Play audio
                    stream.write(audio_data.tobytes())
                    stream.stop_stream()
                    stream.close()
                    
                    logger.info("Audio playback completed")
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error during audio playback: {e}")
                    
        finally:
            p.terminate()


class AudioRecorder:
    """Records audio from microphone in chunks"""
    
    def __init__(self, sample_rate=SAMPLE_RATE, chunk_duration=CHUNK_DURATION, device_index=None):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.audio_queue = queue.Queue()
        self.running = False
        self.device_index = device_index

    def start(self):
        """Start recording audio"""
        self.running = True
        self.thread = Thread(target=self._record_audio)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Audio recording started")
        
    def stop(self):
        """Stop recording audio"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        logger.info("Audio recording stopped")
        
    def _record_audio(self):
        """Record audio in a separate thread"""
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
                input_device_index=self.device_index
            )
            
            logger.info(f"Listening on microphone at {self.sample_rate}Hz (device {self.device_index})...")
            audio_buffer = []
            
            while self.running:
                # Read audio data
                data = stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_buffer.extend(audio_data)
                
                # Check if we have enough audio
                if len(audio_buffer) >= self.chunk_size:
                    chunk = np.array(audio_buffer[:self.chunk_size])
                    audio_buffer = audio_buffer[self.chunk_size:]
                    
                    # Check if chunk has speech (simple energy-based detection)
                    audio_float = chunk.astype(np.float32) / 32768.0
                    energy = np.sqrt(np.mean(audio_float ** 2))
                    
                    if energy > SILENCE_THRESHOLD:
                        self.audio_queue.put(audio_float)
                        
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            
    def get_audio_chunk(self, timeout=0.1):
        """Get next audio chunk from queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None


class WhisperTranscriber:
    """Transcribes audio using Whisper"""

    # Common Whisper hallucinations on silence/noise
    HALLUCINATION_PHRASES = {
        "thank you.", "thank you", "thanks for watching", "thanks for watching!",
        "bye.", "bye", "goodbye", "you", ".", ""
    }

    def __init__(self, model_name=WHISPER_MODEL):
        logger.info(f"Loading Whisper model '{model_name}'...")
        self.model = whisper.load_model(model_name)
        logger.info("Whisper model loaded successfully")

    def transcribe(self, audio_data):
        """Transcribe audio data"""
        try:
            # Whisper expects audio in float32 format
            result = self.model.transcribe(
                audio_data,
                language="en",
                fp16=False
            )
            text = result["text"].strip()

            # Filter out empty transcriptions
            if not text:
                return None

            # Filter out common hallucinations
            if text.lower() in self.HALLUCINATION_PHRASES:
                logger.debug(f"Filtered hallucination: '{text}'")
                return None

            # Check no_speech_prob to detect silence
            # Higher values (>0.6) indicate likely silence/hallucination
            avg_no_speech_prob = sum(
                segment.get("no_speech_prob", 0)
                for segment in result.get("segments", [])
            ) / max(len(result.get("segments", [])), 1)

            if avg_no_speech_prob > 0.6:
                logger.debug(f"Filtered low-confidence transcription (no_speech_prob={avg_no_speech_prob:.2f}): '{text}'")
                return None

            return text

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None


class SpeakerbotClient:
    """WebSocket client for Speakerbot"""
    
    def __init__(self, url=WEBSOCKET_URL):
        self.url = url
        self.websocket = None
        self.connected = False
        
    async def connect(self):
        """Connect to Speakerbot WebSocket"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            logger.info(f"Connected to Speakerbot at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Speakerbot: {e}")
            self.connected = False
            
    async def send_transcription(self, text):
        """Send transcription to Speakerbot"""
        if not self.connected:
            logger.warning("Not connected to Speakerbot, attempting to reconnect...")
            await self.connect()
            
        if self.connected:
            try:
                id = random.randrange(10000, 99999)
                message = json.dumps({
                    "request": "Speak",
                    "id": f"{id}",
                    "voice": f"{VOICE_NAME}",
                    "message": f"{text}"
                })
                await self.websocket.send(message)
                logger.info(f"Sent (ID {id}): {text}")
            except Exception as e:
                logger.error(f"Error sending transcription: {e}")
                self.connected = False
                
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from Speakerbot")


class NeuTTSClient:
    """Local NeuTTS Air TTS client"""
    
    def __init__(self, backbone=NEUTTS_BACKBONE, backbone_device=NEUTTS_BACKBONE_DEVICE,
                 codec=NEUTTS_CODEC, codec_device=NEUTTS_CODEC_DEVICE,
                 ref_audio=NEUTTS_REF_AUDIO, ref_text=NEUTTS_REF_TEXT, audio_player=None):
        self.backbone = backbone
        self.backbone_device = backbone_device
        self.codec = codec
        self.codec_device = codec_device
        self.ref_audio = ref_audio
        self.ref_text = ref_text
        self.tts = None
        self.ref_codes = None
        self.connected = False
        self.audio_player = audio_player
        
    async def connect(self):
        """Initialize NeuTTS model"""
        try:
            # Import here to avoid requiring it if not used
            from neuttsair.neutts import NeuTTSAir
            import soundfile as sf

            if not self.ref_audio or not os.path.exists(self.ref_audio):
                logger.error(f"Reference audio file not found: {self.ref_audio}")
                self.connected = False
                return

            if not self.ref_text or not os.path.exists(self.ref_text):
                logger.error(f"Reference text file not found: {self.ref_text}")
                self.connected = False
                return

            logger.info(f"Loading NeuTTS Air model (backbone: {self.backbone})...")
            logger.info("Note: On first run, NeuTTS will automatically download model files from HuggingFace")
            logger.info("This is a one-time download (~1-2GB) and may take several minutes")

            self.tts = NeuTTSAir(
                backbone_repo=self.backbone,
                backbone_device=self.backbone_device,
                codec_repo=self.codec,
                codec_device=self.codec_device
            )

            # Load and encode reference audio
            logger.info(f"Encoding reference audio from {self.ref_audio}...")
            self.ref_codes = self.tts.encode_reference(self.ref_audio)

            # Load reference text
            with open(self.ref_text, 'r') as f:
                self.ref_text_content = f.read().strip()

            self.connected = True
            logger.info("NeuTTS Air model loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import NeuTTS Air. Install with: pip install -r requirements-neutts.txt")
            logger.error(f"Error: {e}")
            self.connected = False
        except Exception as e:
            logger.error(f"Failed to initialize NeuTTS client: {e}")
            self.connected = False
            
    async def send_transcription(self, text):
        """Generate speech from transcription using NeuTTS"""
        if not self.connected:
            logger.warning("NeuTTS client not initialized, attempting to connect...")
            await self.connect()
            
        if self.connected and self.tts:
            try:
                # Generate speech
                wav = self.tts.infer(text, self.ref_codes, self.ref_text_content)
                
                logger.info(f"Generated speech for: {text}")
                
                # Play audio if audio player is available
                if self.audio_player:
                    self.audio_player.play(wav, sample_rate=24000)
                    logger.info("Audio queued for playback")
                else:
                    logger.warning("No audio player available, audio not played")
                
            except Exception as e:
                logger.error(f"Error generating speech with NeuTTS: {e}")
                
    async def close(self):
        """Close NeuTTS client"""
        self.tts = None
        self.ref_codes = None
        self.connected = False
        logger.info("Closed NeuTTS client")


class PiperClient:
    """Local Piper TTS client"""

    def __init__(self, voice_path=PIPER_VOICE_PATH, audio_player=None):
        self.voice_path = voice_path
        self.tts = None
        self.connected = False
        self.audio_player = audio_player
        self.default_voice = "en_US-amy-medium"

    async def _download_voice_model(self, voice_name):
        """Download a Piper voice model from HuggingFace"""
        try:
            import urllib.request
            import json

            # Create voices directory if it doesn't exist
            voices_dir = os.path.join(os.path.dirname(__file__), "voices")
            os.makedirs(voices_dir, exist_ok=True)

            # Parse voice name (format: en_US-amy-medium)
            # HuggingFace structure: en/en_US/amy/medium/en_US-amy-medium.onnx
            parts = voice_name.split('-')
            if len(parts) < 2:
                logger.error(f"Invalid voice name format: {voice_name}")
                return None

            # Extract language_country (e.g., en_US)
            lang_country = parts[0]
            # Extract language (e.g., en)
            lang = lang_country.split('_')[0]

            # Rest is voice name and quality (e.g., amy-medium)
            voice_parts = parts[1:]
            if len(voice_parts) < 2:
                logger.error(f"Invalid voice name format: {voice_name} (need name and quality)")
                return None

            voice_speaker = voice_parts[0]  # amy
            voice_quality = voice_parts[1]  # medium

            # Construct HuggingFace URL path
            # Format: en/en_US/amy/medium/en_US-amy-medium.onnx
            hf_path = f"{lang}/{lang_country}/{voice_speaker}/{voice_quality}/{voice_name}"

            base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{hf_path}"
            onnx_url = f"{base_url}.onnx"
            json_url = f"{base_url}.onnx.json"

            onnx_path = os.path.join(voices_dir, f"{voice_name}.onnx")
            json_path = os.path.join(voices_dir, f"{voice_name}.onnx.json")

            logger.info(f"Downloading Piper voice model '{voice_name}'...")
            logger.info("This is a one-time download (~20-50MB)")

            # Download .onnx file
            logger.info(f"Downloading {onnx_url}...")
            urllib.request.urlretrieve(onnx_url, onnx_path)
            logger.info(f"Downloaded {onnx_path}")

            # Download .onnx.json file
            logger.info(f"Downloading {json_url}...")
            urllib.request.urlretrieve(json_url, json_path)
            logger.info(f"Downloaded {json_path}")

            logger.info(f"Voice model '{voice_name}' downloaded successfully")
            return onnx_path

        except Exception as e:
            logger.error(f"Failed to download voice model: {e}")
            return None

    async def connect(self):
        """Initialize Piper model"""
        try:
            # Import here to avoid requiring it if not used
            from piper.voice import PiperVoice

            # If no voice path specified, try to download default voice
            if not self.voice_path:
                logger.info(f"No voice model specified, downloading default voice '{self.default_voice}'...")
                self.voice_path = await self._download_voice_model(self.default_voice)

                if not self.voice_path:
                    logger.error("Failed to download default voice model")
                    logger.error("You can manually download voices from: https://huggingface.co/rhasspy/piper-voices")
                    logger.error("Or set PIPER_VOICE_PATH in .env to a valid voice model path")
                    self.connected = False
                    raise RuntimeError("Piper voice model not available. Cannot initialize TTS.")

            # If voice path specified but doesn't exist, try to extract voice name and download
            elif not os.path.exists(self.voice_path):
                logger.warning(f"Voice model file not found: {self.voice_path}")

                # Try to extract voice name from path
                voice_name = os.path.basename(self.voice_path).replace('.onnx', '')
                logger.info(f"Attempting to download voice model '{voice_name}'...")

                downloaded_path = await self._download_voice_model(voice_name)
                if downloaded_path:
                    self.voice_path = downloaded_path
                else:
                    logger.error("Failed to download voice model")
                    logger.error("Download voice models from: https://huggingface.co/rhasspy/piper-voices")
                    logger.error("Or set PIPER_VOICE_PATH in .env to a valid voice model path")
                    self.connected = False
                    raise RuntimeError("Piper voice model not available. Cannot initialize TTS.")

            logger.info(f"Loading Piper voice model from {self.voice_path}...")
            self.tts = PiperVoice.load(self.voice_path)

            self.connected = True
            logger.info("Piper TTS model loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import Piper TTS. Install with: pip install -r requirements-piper.txt")
            logger.error(f"Error: {e}")
            self.connected = False
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Piper client: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.connected = False
            raise

    async def send_transcription(self, text):
        """Generate speech from transcription using Piper"""
        if not self.connected:
            logger.warning("Piper client not initialized, attempting to connect...")
            await self.connect()

        if self.connected and self.tts:
            try:
                # Use synthesize() which yields AudioChunk objects
                audio_chunks = []
                sample_rate = None

                # Collect audio chunks from generator
                for audio_chunk in self.tts.synthesize(text):
                    # AudioChunk has audio_float_array property with numpy array
                    audio_chunks.append(audio_chunk.audio_float_array)
                    # Get sample rate from first chunk
                    if sample_rate is None:
                        sample_rate = audio_chunk.sample_rate

                # Combine all chunks into single array
                if audio_chunks:
                    wav = np.concatenate(audio_chunks)

                    # Use default sample rate if not set
                    if sample_rate is None:
                        sample_rate = 22050

                    logger.info(f"Generated speech for: {text}")

                    # Play audio if audio player is available
                    if self.audio_player:
                        self.audio_player.play(wav, sample_rate=sample_rate)
                        logger.info("Audio queued for playback")
                    else:
                        logger.warning("No audio player available, audio not played")
                else:
                    logger.warning("No audio generated by Piper")

            except Exception as e:
                logger.error(f"Error generating speech with Piper: {e}")
                import traceback
                logger.error(traceback.format_exc())

    async def close(self):
        """Close Piper client"""
        self.tts = None
        self.connected = False
        logger.info("Closed Piper client")


class StyleTTS2Client:
    """Local StyleTTS2 TTS client with voice cloning"""

    def __init__(self, ref_audio=STYLETTS2_REF_AUDIO, audio_player=None):
        self.ref_audio = ref_audio
        self.tts = None
        self.connected = False
        self.audio_player = audio_player

    async def connect(self):
        """Initialize StyleTTS2 model"""
        try:
            # Import here to avoid requiring it if not used
            from styletts2 import tts

            logger.info("Loading StyleTTS2 model...")
            logger.info("Note: On first run, StyleTTS2 will automatically download model files from HuggingFace")
            logger.info("This is a one-time download (~500MB-1GB) and may take several minutes")

            self.tts = tts.StyleTTS2()

            # Validate reference audio if voice cloning is desired
            if self.ref_audio and not os.path.exists(self.ref_audio):
                logger.warning(f"Reference audio file not found: {self.ref_audio}")
                logger.warning("Will use default voice. Provide reference audio for voice cloning.")

            self.connected = True
            logger.info("StyleTTS2 model loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import StyleTTS2. Install with: pip install -r requirements-styletts2.txt")
            logger.error(f"Error: {e}")
            self.connected = False
        except Exception as e:
            logger.error(f"Failed to initialize StyleTTS2 client: {e}")
            self.connected = False

    async def send_transcription(self, text):
        """Generate speech from transcription using StyleTTS2"""
        if not self.connected:
            logger.warning("StyleTTS2 client not initialized, attempting to connect...")
            await self.connect()

        if self.connected and self.tts:
            try:
                # Generate speech with optional voice cloning
                if self.ref_audio and os.path.exists(self.ref_audio):
                    # Use voice cloning
                    wav = self.tts.inference(
                        text,
                        target_voice_path=self.ref_audio,
                        output_wav_file=None,  # Return audio instead of saving
                        output_sample_rate=24000
                    )
                else:
                    # Use default voice
                    wav = self.tts.inference(
                        text,
                        output_wav_file=None,
                        output_sample_rate=24000
                    )

                logger.info(f"Generated speech for: {text}")

                # Play audio if audio player is available
                if self.audio_player:
                    # StyleTTS2 returns tuple (audio, sample_rate)
                    if isinstance(wav, tuple):
                        audio_data, sample_rate = wav
                    else:
                        audio_data = wav
                        sample_rate = 24000

                    # Convert to numpy array if needed
                    if not isinstance(audio_data, np.ndarray):
                        audio_data = np.array(audio_data, dtype=np.float32)

                    self.audio_player.play(audio_data, sample_rate=sample_rate)
                    logger.info("Audio queued for playback")
                else:
                    logger.warning("No audio player available, audio not played")

            except Exception as e:
                logger.error(f"Error generating speech with StyleTTS2: {e}")

    async def close(self):
        """Close StyleTTS2 client"""
        self.tts = None
        self.connected = False
        logger.info("Closed StyleTTS2 client")


def create_tts_client(audio_player=None):
    """Factory function to create appropriate TTS client based on configuration"""
    if TTS_SERVICE == "neutts":
        logger.info("Using NeuTTS Air local TTS service")
        return NeuTTSClient(audio_player=audio_player)
    elif TTS_SERVICE == "piper":
        logger.info("Using Piper TTS service")
        return PiperClient(audio_player=audio_player)
    elif TTS_SERVICE == "styletts2":
        logger.info("Using StyleTTS2 TTS service")
        return StyleTTS2Client(audio_player=audio_player)
    else:
        logger.info("Using Speakerbot TTS service")
        return SpeakerbotClient()


class SpeechToTextApp:
    """Main application class"""
    
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber()
        self.audio_player = None
        self.client = None
        self.running = False
        
    async def run(self):
        """Run the main application loop"""
        logger.info("Starting Speech-to-Text application...")

        try:
            # Determine if we need output device selection
            need_output = TTS_SERVICE in ["neutts", "piper", "styletts2"]

            # Show unified device selector
            selector = AudioDeviceSelector(need_output=need_output)
            input_device_index, output_device_index = selector.show()

            # Check if user cancelled
            if input_device_index is None:
                logger.info("Device selection cancelled, exiting...")
                return

            # Initialize audio recorder with selected input device
            self.recorder = AudioRecorder(device_index=input_device_index)
            logger.info(f"Using microphone device: {input_device_index}")

            # Initialize audio player if output device was selected
            if need_output:
                if output_device_index is not None:
                    self.audio_player = AudioPlayer(device_index=output_device_index)
                    self.audio_player.start()
                    logger.info(f"Using output device: {output_device_index}")
                else:
                    logger.error("No output device selected, exiting...")
                    return

            # Create TTS client with audio player
            self.client = create_tts_client(audio_player=self.audio_player)

            # Connect to TTS service
            logger.info("Connecting to TTS service...")
            await self.client.connect()

            # Check if connection was successful
            if not self.client.connected:
                logger.error("Failed to connect to TTS service. Exiting...")
                await self.shutdown()
                return

            # Start audio recording
            self.recorder.start()
            self.running = True

            logger.info("Application is running. Press Ctrl+C to stop.")

            while self.running:
                # Get audio chunk
                audio_chunk = self.recorder.get_audio_chunk(timeout=0.1)

                if audio_chunk is not None:
                    # Transcribe audio
                    text = self.transcriber.transcribe(audio_chunk)

                    if text:
                        # Send to TTS service
                        await self.client.send_transcription(text)

                # Small delay to prevent tight loop
                await asyncio.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Shutdown the application"""
        logger.info("Shutting down...")
        self.running = False
        self.recorder.stop()
        if self.audio_player:
            self.audio_player.stop()
        if self.client:
            await self.client.close()
        logger.info("Application stopped")


def main():
    """Main entry point"""
    try:
        app = SpeechToTextApp()
        asyncio.run(app.run())
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
