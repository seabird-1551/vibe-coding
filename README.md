# AI-Powered Data Quality Checker

A comprehensive data quality analysis tool that combines automated data profiling with AI-powered recommendations for data quality improvements.

## Features

- **File Upload**: Support for CSV and Excel files
- **Data Profiling**: 
  - Row and column counts
  - Missing values analysis
  - Duplicate detection
  - Data type analysis
  - Mixed type detection
- **AI Recommendations**: OpenAI GPT-powered suggestions for data quality improvements
- **PDF Report Export**: Generate detailed PDF reports
- **Modern UI**: Streamlit-based frontend with interactive visualizations

## Architecture

- **Backend**: FastAPI with async file handling
- **Frontend**: Streamlit for user interface
- **AI Integration**: OpenAI GPT API for intelligent recommendations
- **Data Processing**: Pandas for data manipulation and analysis

## Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-data-quality-checker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**

   **Option 1: Run backend and frontend separately**
   ```bash
   # Terminal 1: Start FastAPI backend
   uvicorn app.backend.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Start Streamlit frontend
   streamlit run app/frontend/streamlit_app.py --server.port 8501
   ```

   **Option 2: Use Docker**
   ```bash
   docker build -t ai-data-quality-checker .
   docker run -p 8000:8000 -p 8501:8501 ai-data-quality-checker
   ```

## Usage

1. **Access the application**: Open your browser and go to `http://localhost:8501`

2. **Upload a file**: 
   - Click "Browse files" to select a CSV or Excel file
   - Supported formats: `.csv`, `.xlsx`, `.xls`

3. **Analyze data**: 
   - Click "Analyze Data Quality" to start the analysis
   - View profiling results and AI recommendations

4. **Export report**: 
   - Click "Export PDF Report" to download a detailed report

## API Endpoints

### Backend API (FastAPI)

- `POST /upload`: Upload CSV or Excel files
- `POST /analyze`: Analyze uploaded data and generate AI recommendations
- `GET /health`: Health check endpoint

### Frontend (Streamlit)

- File upload interface
- Interactive data quality dashboard
- AI recommendations display
- PDF report generation

## Project Structure

```
ai-data-quality-checker/
├── app/
│   ├── backend/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Pydantic models
│   │   ├── services/
│   │   │   ├── data_profiler.py # Data profiling logic
│   │   │   ├── ai_service.py    # OpenAI integration
│   │   │   └── report_generator.py # PDF report generation
│   │   └── utils/
│   │       └── file_handler.py  # File processing utilities
│   └── frontend/
│       └── streamlit_app.py     # Streamlit frontend
├── tests/                       # Unit tests
├── requirements.txt             # Python dependencies
├── Dockerfile                  # Docker configuration
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI recommendations
- `UPLOAD_DIR`: Directory for temporary file uploads (default: `./uploads`)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: `10MB`)

### API Configuration

- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:8501`
- API documentation available at `http://localhost:8000/docs`

## Features in Detail

### Data Profiling

- **Basic Statistics**: Row count, column count, memory usage
- **Missing Values**: Percentage and count of missing values per column
- **Data Types**: Automatic detection and validation
- **Duplicates**: Identification of duplicate rows
- **Mixed Types**: Detection of columns with inconsistent data types

### AI Recommendations

- **Data Quality Issues**: Identification of common data quality problems
- **Cleaning Suggestions**: Specific recommendations for data cleaning
- **Best Practices**: Suggestions for data governance and quality standards
- **Formatting Issues**: Detection of inconsistent formatting

### PDF Reports

- **Executive Summary**: High-level data quality overview
- **Detailed Analysis**: Comprehensive profiling results
- **AI Recommendations**: Prioritized improvement suggestions
- **Visualizations**: Charts and graphs for better understanding

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on the GitHub repository. 