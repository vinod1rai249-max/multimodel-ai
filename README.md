# ✨ Premium Multimodal AI Studio

A professional-grade, high-performance Streamlit application for multimodal AI generation. Features an elegant "Premium Aura" theme, robust fallback mechanisms, and high-fidelity Indian vocal personas.

## 🚀 Key Features

- **Text Generation:** High-speed responses powered by Groq (Llama 3.3) and Gemini 1.5.
- **Image Generation:** Stunning 4K visuals using Flux Schnell (via OpenRouter and Pollinations).
- **Audio Synthesis:** Ultra-premium North Indian voices (Sarah & Marcus) with energetic, professional tuning via ElevenLabs and Edge-TTS.
- **Video Retrieval:** Instant cinematic 4K stock videos matching your prompt via Pexels API.
- **Intelligent Routing:** Smart Vision Bridge that analyzes uploaded images to find matching videos.
- **Enterprise UI:** Colorful, high-contrast "Premium Aura" aesthetic with 100% readability.

## 🛠 Tech Stack

- **Frontend:** Streamlit + Custom CSS + Shadcn UI
- **Orchestrator:** Asynchronous Python with robust fallback logic
- **AI Providers:** ElevenLabs, Groq, Google Gemini, OpenRouter, Pollinations, Pexels

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vinod1rai249-max/multimodel-ai.git
   cd multimodel-ai
   ```

2. **Setup Virtual Environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   Create a `.env` file and add your API keys:
   ```env
   GEMINI_API_KEY=...
   GROQ_API_KEY=...
   OPENROUTER_API_KEY=...
   PEXELS_API_KEY=...
   ELEVENLABS_API_KEY=...
   ```

5. **Run the Studio:**
   ```bash
   streamlit run app.py
   ```

## 🎯 Pro-Prompting Guide

- **Video:** Describe cinematic motion (e.g., 'Golden hour mountain pan').
- **Image:** Use artistic styles and lighting (e.g., 'Oil painting, bokeh').
- **Audio:** Use clear, conversational sentences for best cadence.

---
Developed by **Vinod Rai**
