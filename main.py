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
WEBSOCKET_URL = os.getenv("SPEAKERBOT_WEBSOCKET_URL", "ws://localhost:7585/speak")
VOICE_NAME = os.getenv("VOICE_NAME", "Sally")
NEUTTS_BACKBONE = os.getenv("NEUTTS_BACKBONE", "neuphonic/neutts-air-q4-gguf")
NEUTTS_BACKBONE_DEVICE = os.getenv("NEUTTS_BACKBONE_DEVICE", "cpu")
NEUTTS_CODEC = os.getenv("NEUTTS_CODEC", "neuphonic/neucodec")
NEUTTS_CODEC_DEVICE = os.getenv("NEUTTS_CODEC_DEVICE", "cpu")
NEUTTS_REF_AUDIO = os.getenv("NEUTTS_REF_AUDIO", "")
NEUTTS_REF_TEXT = os.getenv("NEUTTS_REF_TEXT", "")
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


class MicrophoneSelector:
    def __init__(self):
        self.selected_index = None
        self.root = tk.Tk()
        self.root.title('Select Microphone')
        self.devices = list_microphones()
        if not self.devices:
            messagebox.showerror('Error', 'No microphone devices found!')
            self.root.destroy()
            return
        tk.Label(self.root, text='Choose a microphone:').pack(padx=10, pady=10)
        self.combo = ttk.Combobox(self.root, values=[name for idx, name in self.devices], state='readonly')
        self.combo.pack(padx=10, pady=10)
        self.combo.current(0)
        tk.Button(self.root, text='Select', command=self.select).pack(pady=10)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def select(self):
        idx = self.combo.current()
        self.selected_index = self.devices[idx][0]
        self.root.quit()

    def on_close(self):
        self.selected_index = None
        self.root.quit()

    def show(self):
        self.root.mainloop()
        return self.selected_index


class OutputDeviceSelector:
    """GUI for selecting audio output device"""
    
    def __init__(self):
        self.selected_index = None
        self.root = tk.Tk()
        self.root.title('Select Output Device')
        self.devices = list_output_devices()
        if not self.devices:
            messagebox.showerror('Error', 'No output devices found!')
            self.root.destroy()
            return
        tk.Label(self.root, text='Choose an output device:').pack(padx=10, pady=10)
        self.combo = ttk.Combobox(self.root, values=[name for idx, name in self.devices], state='readonly')
        self.combo.pack(padx=10, pady=10)
        self.combo.current(0)
        tk.Button(self.root, text='Select', command=self.select).pack(pady=10)
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def select(self):
        idx = self.combo.current()
        self.selected_index = self.devices[idx][0]
        self.root.quit()

    def on_close(self):
        self.selected_index = None
        self.root.quit()

    def show(self):
        self.root.mainloop()
        return self.selected_index


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
            return text if text else None
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


def create_tts_client(audio_player=None):
    """Factory function to create appropriate TTS client based on configuration"""
    if TTS_SERVICE == "neutts":
        logger.info("Using NeuTTS Air local TTS service")
        return NeuTTSClient(audio_player=audio_player)
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
        
        # Select microphone
        mic_selector = MicrophoneSelector()
        device_index = mic_selector.show()
        if device_index is not None:
            self.recorder = AudioRecorder(device_index=device_index)
        else:
            logger.error("No microphone selected, exiting...")
            return
        
        # Select output device (only for NeuTTS)
        if TTS_SERVICE == "neutts":
            output_selector = OutputDeviceSelector()
            output_device_index = output_selector.show()
            if output_device_index is not None:
                self.audio_player = AudioPlayer(device_index=output_device_index)
                self.audio_player.start()
                logger.info(f"Audio player initialized with device {output_device_index}")
            else:
                logger.error("No output device selected, exiting...")
                return
        
        # Create TTS client with audio player
        self.client = create_tts_client(audio_player=self.audio_player)
        
        # Connect to TTS service
        await self.client.connect()

        # Start audio recording
        self.recorder.start()
        self.running = True
        
        try:
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
