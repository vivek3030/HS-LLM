# 🧠 AI-Powered Document Chat Platform

This project enables local document-based question-answering by combining ChromaDB, Ollama (LLM runtime), and a React-based frontend. The system allows you to query your own documents using locally hosted LLMs such as Mistral and LLaMA.

## 🛠️ Features

- Document ingestion and preprocessing
- Vector database powered by ChromaDB
- Local LLMs with Ollama
- React frontend for interactive chat
- Fully local – No cloud dependencies

---

## 📦 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

### 2. Install Python Requirements

```bash
pip install -r requirements.txt
```

### 3. Configure Document Paths

Edit `doc_helpers.py` and update the following variables with correct paths:

```python
DOCUMENT_DIR = "path/to/your/documents"
PROCESSED_DIR = "path/to/processed/documents"
```

---

## 🧬 Backend Setup

### 4. Setup and Activate Python Virtual Environment (Optional but Recommended)

```bash
python3 -m venv chromadb-env
source chromadb-env/bin/activate
```

### 5. Install ChromaDB

```bash
pip install chromadb
```

### 6. Run ChromaDB

```bash
chroma run --host 0.0.0.0 --port 8002
```

### 7. Install Ollama (Linux)

```bash
curl -fsSL https://ollama.com/download/Ollama.deb -o ollama.deb
sudo apt install ./ollama.deb
sudo systemctl start ollama       # Optional
sudo systemctl enable ollama      # Optional
```

Verify installation:

```bash
curl http://localhost:11434
```

### 8. Download Required LLM Models

```bash
ollama run mistral-small3.1:24b
ollama run llama2:7b
```

Check available models:

```bash
ollama list
```

---

## 📄 Document Ingestion

Place your documents inside the `documents` directory:

```bash
mkdir documents
# Copy your files into the documents folder
```

Then run the document processing script:

```bash
python doc_helpers.py
```

---

## 🚀 Start the Backend API

Navigate to the backend server directory:

```bash
cd src/api
python server.py
```

---

## 🌐 Frontend Setup

In a new terminal tab:

### 1. Install Node.js Dependencies

```bash
npm install
```

### 2. Start the Frontend

```bash
npm run dev
```

The app should now be available at:

```
http://localhost:5173/
```

---

## 🧩 Directory Structure

```bash
your-repo-name/
├── documents/              # Place your documents here
├── src/
│   └── api/                # Backend API (FastAPI or Flask)
├── doc_helpers.py          # Document processing script
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
```

---

## 🧠 Powered By

- Hochschule Albstadt Sigmaringen.


---

## 📬 Contact

For questions or contributions, feel free to open an issue or reach out via GitHub.
