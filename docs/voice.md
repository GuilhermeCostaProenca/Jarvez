# Voice (v0.4)

## Files
- `voice/audio_input.py`: STT via OpenAI Whisper when available; text stub otherwise.
- `voice/audio_output.py`: TTS via OpenAI when available; stub logging otherwise.
- `voice/microphone_loop.py`: microphone loop stub (uses text input fallback) with optional TTS playback.
- `interface/voice_cli.py`: entrypoint for voice-mode chat (`jarvez-voice` script).

## Flow
1. Voice CLI starts Agent (with optional mode).
2. MicrophoneLoop requests input (text fallback), transcribes via audio_input.
3. Agent/Orchestrator responds; audio_output optionally speaks via TTS.
4. Debug flag shows when memory/notes/RAG are used.

## Configuration
- `OPENAI_API_KEY`: enables Whisper + OpenAI TTS.
- `JARVEZ_VOICE`: select voice id for TTS (default alloy).
- `JARVEZ_AUDIO_OUT`: folder for generated audio files (default `data/audio`).

## Extensibility
- Swap microphone_loop to use Vosk/whisper.cpp capture.
- Add wake-word and continuous streaming.
- Add caching for frequent TTS phrases.
