# 🧠 LocalMind - LIVE-OFFLINE AI Assistant

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Offline First](https://img.shields.io/badge/Offline-First-green.svg)](https://github.com)

> **LIVE-OFFLINE AI**: Experience the full power of AI assistance without internet dependency

LocalMind is a comprehensive offline AI assistant with conversation memory, powered by GPT4All and designed for complete privacy and accessibility. It provides intelligent responses across education, healthcare, and general domains while operating entirely on your local machine.

## ✨ Features

🔒 **Complete Privacy** - All data stays on your device  
🌐 **100% Offline** - No internet required after setup  
🧠 **Conversation Memory** - Remembers context and learns from interactions  
🎯 **Domain Expertise** - Specialized in Education, Healthcare, and General assistance  
💻 **Dual Interface** - Both CLI and GUI available  
⚡ **GPT4All Powered** - Uses Llama-3.2-1B for intelligent responses  
🔍 **Vector Memory** - FAISS-powered semantic search for conversation history  

## 🚀 Quick Start

### One-Click Setup & Launch

1. **Download** the repository
2. **Double-click** `setup.bat` to install all dependencies
3. **Double-click** `LocalMind.bat` to launch with menu options

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/your-username/LocalMind.git
cd LocalMind

# Run setup
setup.bat

# Launch LocalMind
LocalMind.bat
```

## 🎮 Usage

### Launch Options

- **`LocalMind.bat`** - Interactive menu to choose CLI or GUI
- **`run_cli.bat`** - Direct CLI launch
- **`run_gui.bat`** - Direct GUI launch

### CLI Commands

```bash
# Switch domains
domain education    # Switch to education domain
domain healthcare   # Switch to healthcare domain
domain general      # Switch to general domain

# Memory management
memory stats        # View conversation statistics
memory search <query>  # Search conversation history
memory clear        # Clear conversation history

# System commands
status             # Check system status
help               # Show all commands
quit               # Exit LocalMind
```

### Sample Conversations

```
🧠 LocalMind - Education Domain
You: Explain photosynthesis
AI: [Detailed explanation with diagrams]

You: What about cellular respiration?
AI: [Continues with context from photosynthesis discussion]
```

## 🏗️ Architecture

```
LocalMind/
├── 🚀 LocalMind.bat           # Main launcher
├── 🔧 setup.bat               # One-click setup
├── 📱 run_cli.bat             # CLI launcher
├── 🖥️ run_gui.bat             # GUI launcher
├── 🐍 localmind.py            # Main application
├── 📂 src/                    # Source code
│   ├── 🧠 model/              # AI models & GPT4All
│   ├── 💾 knowledge/          # Vector DB & memory
│   ├── 🎯 domains/            # Specialized domains
│   └── 🖥️ interface/          # CLI & GUI
├── 📋 requirements.txt        # Dependencies
└── 📖 README.md               # This file
```

## 💡 Technical Details

- **AI Engine**: GPT4All with Llama-3.2-1B (773MB model)
- **Memory System**: FAISS vector database with sentence-transformers
- **Embeddings**: all-MiniLM-L6-v2 for semantic search
- **Interface**: Rich CLI formatting + Tkinter GUI
- **Domains**: Modular architecture for specialized responses

## 🔧 System Requirements

- **OS**: Windows 10/11 (with .bat files), Linux/macOS supported
- **Python**: 3.8+ 
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space (includes model downloads)
- **CPU**: Any modern processor (optimized for CPU inference)

## 📦 Dependencies

All dependencies are automatically installed via `setup.bat`:

- `torch` - PyTorch for model inference
- `transformers` - HuggingFace transformers
- `gpt4all` - Local LLM integration
- `faiss-cpu` - Vector database for memory
- `sentence-transformers` - Text embeddings
- `rich` - Beautiful CLI formatting
- `tkinter` - GUI framework (built-in)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [GPT4All](https://gpt4all.io/) for local LLM capabilities
- [FAISS](https://github.com/facebookresearch/faiss) for vector database
- [Sentence Transformers](https://www.sbert.net/) for embeddings
- [Rich](https://github.com/Textualize/rich) for beautiful CLI

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/LocalMind/issues) page
2. Create a new issue with detailed description
3. Include system specs and error logs

---

**⭐ Star this repository if you find LocalMind useful!**
