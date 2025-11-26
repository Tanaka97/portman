"# Portman"
# Portfolio Manager

A comprehensive portfolio management application for tracking investments across multiple asset classes.

## 🚀 Features

- 📊 Track stocks, crypto, ETFs, bonds, and more
- 💰 Real-time portfolio valuation
- 📈 Asset allocation and position sizing
- 📉 Risk metrics and diversification analysis
- 📁 CSV import from multiple broker formats
- 🎯 Rebalancing recommendations
- 📱 Mobile-responsive PWA

## 🛠️ Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- Supabase (PostgreSQL)

**Frontend:**
- React 18
- Vite
- TailwindCSS
- Recharts

## 📋 Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for frontend)
- Git

## 🏃 Getting Started

### Backend Setup

1. Clone the repository:
```bash
   git clone https://github.com/Tanaka97/portfolio-manager.git
   cd portfolio-manager
```

2. Create virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
   cd backend
   pip install -r requirements.txt
```

4. Set up environment variables:
```bash
   cp .env.example .env
   # Edit .env with your credentials
```

5. Run the development server:
```bash
   uvicorn app.main:app --reload
```

   API will be available at: http://localhost:8000

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs) (when running)
- [Project Wiki](docs/)

## 🤝 Contributing

This is a personal learning project, but feedback is welcome!

## 📄 License

MIT License - feel free to use this for learning

## 👨‍💻 Author

Built by Tanaka97 as a portfolio project

---

**Status:** 🚧 Work in Progress