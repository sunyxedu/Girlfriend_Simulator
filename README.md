# Girlfriend Simulator

An AI-powered chatbot that simulates a girlfriend experience with advanced features like daily experiences, news integration, and contextual memory.

## Features

- 🤖 AI-powered conversations using OpenAI's GPT models
- 📅 Daily experience tracking and memory
- 📰 Real-time news integration and discussion
- 💾 Persistent chat history using SQLite
- 🔍 Context-aware responses using RAG (Retrieval-Augmented Generation)
- 🎨 Beautiful terminal UI with color-coded messages
- 💭 Smart response filtering to maintain natural conversation flow
- 🎯 Fine-tuned model for more personalized responses

## Prerequisites

- Python 3.8 or higher
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Girlfriend_Simulator.git
cd Girlfriend_Simulator
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the chatbot:
```bash
python chatbot.py
```

### Available Commands

- Type your messages to chat with the AI
- Type 'exit' to quit the chat
- Type 'clear' to clear the chat history
- Type 'history' to view chat history
- Type 'experiences' to view daily experiences

## Project Structure

- `chatbot.py` - Main chatbot implementation
- `utils.py` - Utility functions and constants
- `database_related.py` - Database operations
- `rag_utils.py` - RAG implementation for context-aware responses
- `new_related.py` - News fetching and relevance checking
- `chat_history.db` - SQLite database for storing chat history
- `chat_embeddings.index` - FAISS index for vector search
- `message_mapping.json` - Message mapping configurations
- `finetune/` - Directory containing fine-tuning related files:
  - `main.py` - Script for fine-tuning the model
  - `test.ipynb` - Jupyter notebook for testing fine-tuned model
  - `girlfriend_simulator.jsonl` - Training data for fine-tuning
  - `girlfriend question answer.json` - Q&A dataset for fine-tuning
