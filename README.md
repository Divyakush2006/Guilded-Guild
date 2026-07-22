<div align="center">

# 🎬 AI-Based Content Recommendation System
### Sequential Deep-Learning Recommendations for Movies & Music

<em>Self-attentive sequential modelling (SASRec) served end-to-end through a Flask REST API and a React + TypeScript interface.</em>

<br/>

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)

**[Overview](#-overview) • [Results](#-results) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API](#-api-reference)**

</div>

---

## 📖 Overview

A production-oriented recommendation engine that predicts what a user will engage with **next**, by modelling the *sequence* of their interactions rather than treating them as an unordered set. Built on the **MovieLens 20M** dataset (27,278 movies · 20M+ ratings · 138,493 users) and extended to music via live Spotify/iTunes catalog data.

Unlike classical collaborative filtering, this system uses a **Self-Attentive Sequential Recommendation (SASRec)** transformer to capture temporal preference patterns — directly addressing the **cold-start** and **sequential-understanding** limitations of matrix-factorisation approaches.

| | |
|---|---|
| 🧠 **Model** | SASRec (self-attention) + NCF baseline, implemented from scratch in PyTorch |
| 🎯 **Domain** | Cross-domain — movies (MovieLens 20M) **and** music (Spotify / iTunes) |
| 🖥️ **Serving** | Flask REST API with CORS + a React 18 / TypeScript / Vite SPA |
| 🖼️ **Enrichment** | TMDB posters & trailers (100% fetch-success rate), Spotify metadata |

---

## 📊 Results

Evaluated on a held-out temporal split of MovieLens 20M (leave-last-out protocol):

| Metric | Score |
|--------|-------|
| **AUC-ROC** | **98.47%** |
| **Hit-Rate @ 10** | **98.23%** |
| Model parameters | ~25M |
| Poster/trailer enrichment success (TMDB) | 100% |

> Metrics are reproducible via `flask_app/evaluate_sasrec.py` on the provided data split.

---

## 🏗️ Architecture

```
┌──────────────────────────┐        ┌───────────────────────────────┐
│  React + TS Frontend      │  REST  │  Flask API  (flask_app/app.py) │
│  (harmony-hub / Vite)     │ <────> │  /api/recommend/movies         │
│  shadcn-ui · Tailwind     │  JSON  │  /api/recommend/music          │
└──────────────────────────┘        └───────────────┬───────────────┘
                                                     │
                            ┌────────────────────────┼────────────────────────┐
                            ▼                        ▼                         ▼
                  ┌──────────────────┐   ┌────────────────────┐   ┌────────────────────┐
                  │  SASRec (PyTorch) │   │  Enrichment Layer  │   │  Music Pipeline     │
                  │  self-attention   │   │  TMDB posters/     │   │  Spotify + iTunes   │
                  │  + NCF baseline   │   │  trailers          │   │  fetch + sequence   │
                  └──────────────────┘   └────────────────────┘   └────────────────────┘
```

### 🔬 Model internals (`flask_app/sasrec_model.py`)
- **Item + positional embeddings** with padding-aware masking
- **Multi-head self-attention** blocks with pre-LayerNorm residual connections
- **Point-wise feed-forward** networks (`Conv1d`, kernel size 1) with dropout regularisation
- Trained with `train_sasrec.py`; evaluated with `evaluate_sasrec.py`; **NCF** (`train_ncf.py`) retained as a baseline for comparison

---

## 🧰 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Modelling** | PyTorch · SASRec · Neural Collaborative Filtering · NumPy · Pandas |
| **Backend** | Flask · Flask-CORS · REST · Python 3.13 |
| **Frontend** | React 18 · TypeScript · Vite · shadcn/ui · Radix UI · Tailwind CSS · Vitest |
| **Data & APIs** | MovieLens 20M · Spotify API · iTunes API · TMDB API |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ · Node.js 18+ · a TMDB API key (and optionally Spotify credentials)

### 1 — Backend (Flask + model)
```bash
git clone https://github.com/Divyakush2006/Guilded-Guild.git
cd Guilded-Guild/flask_app

python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r ../requirements.txt                # or: pip install torch flask flask-cors pandas numpy requests

cp ../.env.example .env        # add TMDB_API_KEY / Spotify keys
python app.py                  # serves the API + legacy HTML at http://localhost:5000
```

### 2 — Frontend (React + Vite)
```bash
cd ../harmony-hub-main
npm install
npm run dev                    # http://localhost:5173
```

### 3 — (Optional) Train / evaluate the model
```bash
python train_sasrec.py         # train SASRec on MovieLens 20M
python evaluate_sasrec.py      # reproduce AUC-ROC / Hit-Rate@10
```

---

## 📡 API Reference

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/api/recommend/movies` | `{ "current_watch": str, "history": [str] }` | Sequential movie recommendations with TMDB enrichment |
| `POST` | `/api/recommend/music`  | `{ "current_track": str, "history": [str] }` | Music recommendations via Spotify/iTunes pipeline |
| `GET`  | `/` · `/music` | — | Server-rendered legacy demo pages |

<details>
<summary><b>Example request</b></summary>

```bash
curl -X POST http://localhost:5000/api/recommend/movies \
  -H "Content-Type: application/json" \
  -d '{"current_watch": "Inception", "history": ["The Matrix", "Interstellar"]}'
```
</details>

---

## 📁 Project Structure

```
Guilded-Guild/
├── flask_app/
│   ├── app.py                 # Flask REST API + CORS
│   ├── sasrec_model.py        # SASRec transformer (PyTorch)
│   ├── train_sasrec.py        # training loop
│   ├── evaluate_sasrec.py     # metrics: AUC-ROC / Hit-Rate@10
│   ├── train_ncf.py           # NCF baseline
│   ├── inference*.py          # movie + music inference
│   ├── tmdb_fetcher.py        # poster/trailer enrichment
│   ├── spotify_fetcher.py     # music catalog integration
│   └── templates/             # legacy server-rendered UI
├── harmony-hub-main/          # React 18 + TS + Vite frontend
└── AI_Content_Recommendation_Submission.ipynb
```

---

## 🗺️ Roadmap
- [ ] Containerise backend + model with Docker for one-command deploy
- [ ] Add Redis caching layer for hot recommendations
- [ ] Expose model-explainability (attention weights) in the UI

---

## 👤 Author

**Divyakush Punjabi** — B.Tech CSE @ VIT Vellore · AI Major @ IIT Ropar
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/divyakush-punjabi)
[![Portfolio](https://img.shields.io/badge/Portfolio-FF5722?style=flat&logo=googlechrome&logoColor=white)](https://divyakush.is-a.dev)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white)](https://github.com/divyakush2006)

<div align="center"><sub>⭐ If this project helped or impressed you, consider starring the repo.</sub></div>
