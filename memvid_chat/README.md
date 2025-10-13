# Memvid Chat System

## Overview
The Memvid Chat system is a Telegram bot that allows users to interact with documents that have been processed with Memvid technology. Users can ask questions about documents, and the system will retrieve relevant information and generate responses using a combination of Memvid retrieval and Claude 3.7 Sonnet via OpenRouter.

## Features
- 📄 Document selection and management
- 💬 Natural language conversation with documents
- 🔍 Context-aware responses with semantic search
- ⚙️ Customizable retrieval and generation parameters
- 🧪 Beta mode with advanced features
- 📱 Telegram interface for convenient access
- 🔄 Persistent conversation history

## Installation

### Prerequisites
- Python 3.8 or higher
- Memvid library
- Telegram Bot Token
- OpenRouter API Key

### Setup
1. Clone the repository
2. Create and configure `.env` file in the `config` directory based on `.env.example`
3. Run the initialization script:
   - Windows: `initialize.bat`
   - Linux/Mac: `initialize.sh`

### Running the Bot
1. Run the bot:
   - Windows: `start_bot.bat`
   - Linux/Mac: `start_bot.sh`
2. Open the Telegram bot and start chatting

## Usage
1. Start the bot with `/start`
2. Select a document with `/select`
3. Ask questions about the document
4. Adjust settings with `/settings`
5. Reset the conversation with `/reset` if needed
6. Get help with `/help`

## Configuration
The system can be configured by editing the `.env` file or by using the `/settings` command in the Telegram bot.

### Available Settings
- `top_k`: Number of document chunks to retrieve
- `temperature`: Temperature for response generation
- `max_tokens`: Maximum number of tokens in the response
- `beta_mode`: Enable advanced features

## Project Structure
```
memvid_chat/
├── config/               # Configuration and settings management
├── core/                 # Core RAG functionality
│   ├── memvid_retriever.py  # Document retrieval with Memvid
│   ├── llm_client.py     # OpenRouter API integration
│   └── rag_pipeline.py   # RAG pipeline implementation
├── database/             # Database models and operations
├── telegram/             # Telegram bot interface
├── utils/                # Utility functions
├── main.py               # Main application entry point
├── initialize.bat/.sh    # Initialization scripts
├── start_bot.bat/.sh     # Launch scripts
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Development
The system is designed to be modular and extensible. New features can be added by extending the existing modules or creating new ones.

### Adding New Features
1. Create a new module in the appropriate directory
2. Import the module in `main.py` or the relevant module
3. Update the bot interface to expose the new functionality
4. Add any necessary database models or operations
5. Update the documentation

## Deployment
The system can be deployed on any server that supports Python. It can also be deployed on Railway using the provided Procfile.

### Railway Deployment
1. Connect your repository to Railway
2. Set the environment variables in Railway
3. Deploy using the Procfile configuration

## License
This project is licensed under the MIT License - see the LICENSE file for details.
