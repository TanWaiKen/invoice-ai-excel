# Invoice AI Excel Generator

🚀 **Automate invoice image processing and Excel report generation using AI OCR.**

Transform invoice images into structured Excel reports with AI-powered OCR, customer matching, and automated calculations.

## 📋 Features

- **🤖 AI-Powered OCR**: Extract invoice data from images using advanced AI
- **📊 Excel Generation**: Create structured Excel reports with formulas (like VLookup)
- **👥 Customer Matching**: Fuzzy matching for customer name consistency using vector database
- **📁 File Management**: Track and manage generated Excel files
- **🎨 Modern UI**: Built with Wails for native desktop experience
- **⚡ Fast Processing**: Efficient batch processing of multiple invoices

## 🏗️ Project Structure

```
excel-ai-updater/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── api/
│   │   │   ├── main.py        # FastAPI server
│   │   │   └── .env           # Environment variables
│   │   ├── excel/             # Excel generation logic
│   │   ├── knowledge_base/    # Customer database
│   │   └── models/            # Data models
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Wails frontend
│   ├── src/
│   │   ├── components/        # JavaScript modules
│   │   ├── styles/           # CSS styles
│   │   └── data/             # JSON data storage
│   ├── index.html
│   └── package.json          # Node dependencies
├── app.go                     # Go application logic
├── main.go                    # Go main entry point
├── wails.json                 # Wails configuration
└── README.md
```

## 🛠️ Prerequisites

### 1. **Install Go (Golang)**
- **Download**: https://golang.org/dl/
- **Windows**: Download `.msi` installer and run
- **Verify installation**:
  ```bash
  go version
  ```

### 2. **Install Node.js**
- **Download**: https://nodejs.org/
- **Recommended**: LTS version (18.x or 20.x)
- **Verify installation**:
  ```bash
  node --version
  npm --version
  ```

### 3. **Install Python**
- **Download**: https://python.org/downloads/
- **Recommended**: Python 3.9+
- **Verify installation**:
  ```bash
  python --version
  # or
  python3 --version
  ```

### 4. **Install Wails**
```bash
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

## 🚀 Installation & Setup

### **1. Clone the Repository**
```bash
git clone https://github.com/TanWaiKen/invoice-ai-excel.git
cd invoice-ai-excel
```

### **2. Backend Setup (Python)**
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install Python dependencies
pip install -r src/requirements.txt
```

### **3. Frontend Setup (Node.js)**
```bash
# Navigate to frontend (from project root)
cd frontend

# Install Node dependencies
npm install
```

### **4. Go Dependencies**
```bash
# From project root
go mod tidy
```

## 🏃‍♂️ Running the Application - Create 2 terminal

### **Method 1: Development Mode (Recommended)**

**Terminal 1 - Backend:**
```bash
cd backend
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
cd src/api
python main.py
# Server will run on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
# From project root
wails dev
# App will open in development mode with hot reload
```

### **Method 2: Production Build**
```bash
# Build the application
wails build

# Run the built executable
# Windows: .\build\bin\excel-ai-updater.exe
# Linux: ./build/bin/excel-ai-updater
# Mac: ./build/bin/excel-ai-updater.app
```

## 📖 Usage

1. **Start the Backend**: Run Python FastAPI server
2. **Launch Frontend**: Use `wails dev` or built executable
3. **Select Files**:
   - Choose image folder containing invoice images
   - Select Excel with a specific template and a formula sheet
   - <img width="1132" height="64" alt="image" src="https://github.com/user-attachments/assets/2488d2a0-c058-4d87-a902-b100aa46aa91" />
   - <img width="1415" height="98" alt="image" src="https://github.com/user-attachments/assets/a9e93522-d04b-4ca4-b511-5f48258540a8" />
4. **Process**: Click "Process Files" to generate Excel report
5. **View Results**: Check "Generated Files" tab for outputs

## 🔧 Configuration

### **Environment Variables (.env)**
Create `backend/src/api/.env`:
```env
# AI Service API Keys
GEMINI_API_KEY=your_api_key_here
```

### **Supported File Types**
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`
- **Excel**: `.xlsx`, `.xls` and need folow below format


## 🛠️ Development Commands

```bash
# Backend development
cd backend && python src/api/main.py

# Frontend development
wails dev

# Build for production
wails build

# Generate Go bindings
wails generate module

# Install dependencies
go mod tidy
npm install  # in frontend folder
pip install -r requirements.txt  # in backend folder
```

## 📝 API Endpoints

- **POST** `/process-invoices` - Process invoice images
- **GET** `/health` - Health check
- **GET** `/` - API information

## 🐛 Troubleshooting

### **Common Issues:**

1. **CORS Errors**:
   - Ensure backend is running on `localhost:8000`
   - Check CORS settings in `backend/src/api/main.py`

2. **Python Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Node Modules**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Go Modules**:
   ```bash
   go clean -modcache
   go mod download
   ```

## 📦 Building for Distribution .exe file

```bash
# Build for current platform
wails build

# Build for specific platform
wails build -platform windows/amd64
wails build -platform darwin/amd64
wails build -platform linux/amd64
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Wails** - Desktop app framework
- **FastAPI** - Python web framework
- **Go** - Backend language

---

**Good Luck for coding...! 🎉**
