# NeuTTS Air Reference Samples

This directory should contain your reference audio and text files for NeuTTS Air voice cloning.

## File Format Requirements

### Reference Audio (`reference.wav`)
- **Format**: WAV file
- **Channels**: Mono (1 channel)
- **Sample Rate**: 16-44 kHz
- **Duration**: 3-15 seconds
- **Quality**: Clean audio with minimal background noise
- **Content**: Natural, continuous speech (like a monologue or conversation)

### Reference Text (`reference.txt`)
- Plain text file containing the exact transcription of your reference audio
- Should match the audio content word-for-word
- Include natural speech patterns (ums, ahs, etc.) if present in the audio

## Example

If your reference audio says:
> "My name is Dave, and um, I'm from London."

Your `reference.txt` should contain:
```
My name is Dave, and um, I'm from London.
```

## Getting Started

1. Record or obtain a short audio sample (3-15 seconds) of the voice you want to clone
2. Save it as `reference.wav` in this directory
3. Transcribe the audio and save the text as `reference.txt`
4. Update your `.env` file to point to these files:
   ```
   NEUTTS_REF_AUDIO=samples/reference.wav
   NEUTTS_REF_TEXT=samples/reference.txt
   ```

## Sample Files

You can also download sample reference files from the NeuTTS Air repository:
- https://github.com/neuphonic/neutts-air/tree/main/samples

The repository includes samples like:
- `dave.wav` / `dave.txt`
- `jo.wav` / `jo.txt`
