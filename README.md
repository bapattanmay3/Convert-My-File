# Convert My File ⚓

"Convert My File" is a premium, high-fidelity file conversion and translation suite designed for professionals. It features a sophisticated "Royal Enfield Racing Green" dark theme and prioritizes user privacy.

## Features
- **High-Fidelity Converter**: Advanced conversion between PDF, DOCX, and TXT with perfect structure preservation using the Aspose engine.
- **Universal Translator**: Document and text translation across **100+ languages** with layout maintenance.
- **Smart Merger**: Combine multiple PDF documents into a single professional file.
- **Precision Compressor**: Compress or expand files to exact target sizes (5KB - 50MB).
- **Privacy-First**: Automatic file deletion after 5 minutes and strict no-storage policy.
- **Admin Dashboard**: Secure analytics dashboard to monitor visitors, usage, and global demographics.

## Tech Stack
- **Backend**: Flask (Python 3.11)
- **Engine**: Aspose.Words, WeasyPrint, pdf2docx
- **UI/UX**: HTML5, Vanilla CSS3 (Custom Premium Dark Theme)
- **Deployment**: Docker-ready (supports Google Cloud Run, Render, etc.)

## Quick Start
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Set secret key in `app.py`.
4. Run: `python app.py`.

## Deployment

### Google Cloud Run (Recommended)
1. Build & Push: `gcloud builds submit --tag gcr.io/[PROJECT-ID]/convertmyfile`
2. Deploy: `gcloud run deploy --image gcr.io/[PROJECT-ID]/convertmyfile --platform managed --allow-unauthenticated`

### Render.com
Connect your GitHub repository to Render. Use the included `render.yaml` or `Dockerfile` for automatic, one-click deployment.

---
© 2026 Convert My File - T⚓B Branding
