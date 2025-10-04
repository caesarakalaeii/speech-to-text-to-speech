#!/usr/bin/env python3
"""
Speech-to-Text-to-Speech Application
Captures audio from microphone, transcribes using Whisper, and sends to Speakerbot via WebSocket
"""
import os
import sys
import time
import queue
import json
import asyncio
import logging
from threading import Thread
from dotenv import load_dotenv
import numpy as np
import pyaudio
import whisper
import websockets

# Load environment variables
load_dotenv()

# Configuration
WEBSOCKET_URL = os.getenv("SPEAKERBOT_WEBSOCKET_URL", "ws://localhost:8080")
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


class AudioRecorder:
    """Records audio from microphone in chunks"""
    
    def __init__(self, sample_rate=SAMPLE_RATE, chunk_duration=CHUNK_DURATION):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.audio_queue = queue.Queue()
        self.running = False
        
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
                frames_per_buffer=1024
            )
            
            logger.info(f"Listening on microphone at {self.sample_rate}Hz...")
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
                message = json.dumps({
                    "type": "transcription",
                    "text": text,
                    "timestamp": time.time()
                })
                await self.websocket.send(message)
                logger.info(f"Sent: {text}")
            except Exception as e:
                logger.error(f"Error sending transcription: {e}")
                self.connected = False
                
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from Speakerbot")


class SpeechToTextApp:
    """Main application class"""
    
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber()
        self.client = SpeakerbotClient()
        self.running = False
        
    async def run(self):
        """Run the main application loop"""
        logger.info("Starting Speech-to-Text application...")
        
        # Connect to Speakerbot
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
                        # Send to Speakerbot
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
