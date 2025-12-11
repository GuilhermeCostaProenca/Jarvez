# Vision (v0.5)

## Components
- `vision/multimodal.py`: multimodal client with OpenAI hook and stub fallback.
- `vision/capture_screen.py`: screen capture (PIL.ImageGrab) with config-gated enablement.
- `vision/capture_camera.py`: webcam frame capture (OpenCV if available) with config gating.
- `vision/capture_file.py` + `vision/ocr.py`: file ingestion and OCR stub for PDFs/images.
- `vision/pipelines.py`: high-level flows (screen summary/errors, camera snapshot, PDF ingestion, study plan from PDF).

## Config
- Enable globally: `JARVEZ_VISION_ENABLED=1`
- Gate by source: `JARVEZ_VISION_ALLOW_SCREEN=1`, `JARVEZ_VISION_ALLOW_CAMERA=1`
- Provider hints: `JARVEZ_VISION_PROVIDER`, `JARVEZ_VISION_MODEL`
- Capture dir: `JARVEZ_CAPTURE_DIR` (default `data/captures`)

## Flows
1) Command triggers (e.g., “vision screen summarize”, “olha minha tela”).
2) Capture (screen/camera/file) -> multimodal/ocr.
3) Outputs: note creation, memory dynamic fact, RAG index entry, optional plan.
4) Response returned to user; debug shows vision usage.

## Stubs
- If vision is disabled or provider unavailable, pipelines return a stub message; no crashes.
- OCR for PDFs/images is stubbed until a real backend is configured.

## Extensibility
- Swap multimodal client to Gemini/Claude/OpenAI Vision.
- Replace OCR stub with pytesseract/pdf parsing.
- Add continuous capture and batching; add posture/gesture detection pipelines.
