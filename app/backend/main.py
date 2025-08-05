import os
import logging
import time
from typing import Optional, Dict
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import tempfile

from app.backend.models import (
    UploadResponse, AnalyzeResponse, HealthResponse, 
    ErrorResponse, DataProfile
)
from app.backend.utils.file_handler import FileHandler
from app.backend.services.data_profiler import DataProfiler
from app.backend.services.ai_service import AIService
from app.backend.services.report_generator import ReportGenerator
from app.backend.services.data_cleaner import DataCleaner
from app.backend.services.data_validator import DataValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Data Quality Checker",
    description="A comprehensive data quality analysis tool with AI-powered recommendations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_handler = FileHandler()
data_profiler = DataProfiler()
ai_service = AIService()
report_generator = ReportGenerator()
data_cleaner = DataCleaner()
data_validator = DataValidator()

# In-memory storage for uploaded files (use database in production)
uploaded_files = {}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload CSV or Excel file for analysis"""
    try:
        logger.info(f"File upload request: {file.filename}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file
        is_valid, validation_message = file_handler.validate_file(file.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_message)
        
        # Save file
        file_path, file_id = file_handler.save_uploaded_file(file_content, file.filename)
        
        # Store file info
        uploaded_files[file_id] = {
            "file_path": file_path,
            "file_name": file.filename,
            "file_size": file_size,
            "upload_time": datetime.now().isoformat()
        }
        
        logger.info(f"File uploaded successfully: {file_id}")
        
        return UploadResponse(
            message="File uploaded successfully",
            file_id=file_id,
            file_name=file.filename,
            file_size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_data(file_id: str):
    """Analyze uploaded data and generate AI recommendations"""
    try:
        start_time = time.time()
        logger.info(f"Data analysis request for file: {file_id}")
        
        # Check if file exists
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[file_id]
        file_path = file_info["file_path"]
        
        # Load data
        df = file_handler.load_dataframe(file_path)
        logger.info(f"Data loaded successfully: {df.shape}")
        
        # Profile data
        profile = data_profiler.profile_data(
            df=df,
            file_name=file_info["file_name"],
            file_size=file_info["file_size"]
        )
        
        # Generate AI recommendations
        ai_recommendations = ai_service.generate_recommendations(profile)
        profile.ai_recommendations = ai_recommendations
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(f"Analysis completed in {processing_time:.2f} seconds")
        
        return AnalyzeResponse(
            success=True,
            message="Data analysis completed successfully",
            profile=profile,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/analyze-with-file", response_model=AnalyzeResponse)
async def analyze_data_with_file(file: UploadFile = File(...)):
    """Upload and analyze file in one request"""
    try:
        start_time = time.time()
        logger.info(f"Combined upload and analysis request: {file.filename}")
        
        # Upload file
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file
        is_valid, validation_message = file_handler.validate_file(file.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_message)
        
        # Save file temporarily
        file_path, file_id = file_handler.save_uploaded_file(file_content, file.filename)
        
        try:
            # Load and analyze data
            df = file_handler.load_dataframe(file_path)
            profile = data_profiler.profile_data(
                df=df,
                file_name=file.filename,
                file_size=file_size
            )
            
            # Generate AI recommendations
            ai_recommendations = ai_service.generate_recommendations(profile)
            profile.ai_recommendations = ai_recommendations
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(f"Combined analysis completed in {processing_time:.2f} seconds")
            
            return AnalyzeResponse(
                success=True,
                message="Data analysis completed successfully",
                profile=profile,
                processing_time=processing_time
            )
            
        finally:
            # Clean up temporary file
            file_handler.delete_file(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in combined upload and analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/generate-report")
async def generate_pdf_report(file_id: str):
    """Generate PDF report for analyzed data"""
    try:
        logger.info(f"PDF report generation request for file: {file_id}")
        
        # Check if file exists
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[file_id]
        file_path = file_info["file_path"]
        
        # Load and analyze data if not already done
        df = file_handler.load_dataframe(file_path)
        profile = data_profiler.profile_data(
            df=df,
            file_name=file_info["file_name"],
            file_size=file_info["file_size"]
        )
        
        # Generate AI recommendations
        ai_recommendations = ai_service.generate_recommendations(profile)
        profile.ai_recommendations = ai_recommendations
        
        # Generate PDF report
        pdf_content = report_generator.generate_report(profile)
        
        # Create temporary file for response
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
        
        # Return PDF file
        return FileResponse(
            path=tmp_file_path,
            filename=f"data_quality_report_{file_info['file_name']}.pdf",
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete uploaded file"""
    try:
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[file_id]
        file_path = file_info["file_path"]
        
        # Delete file
        if file_handler.delete_file(file_path):
            del uploaded_files[file_id]
            logger.info(f"File deleted successfully: {file_id}")
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/files")
async def list_files():
    """List all uploaded files"""
    try:
        files = []
        for file_id, file_info in uploaded_files.items():
            files.append({
                "file_id": file_id,
                "file_name": file_info["file_name"],
                "file_size": file_info["file_size"],
                "upload_time": file_info["upload_time"]
            })
        
        return {"files": files}
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.post("/clean-data")
async def clean_data(file_id: str):
    """Clean data based on AI recommendations"""
    try:
        logger.info(f"Data cleaning request for file: {file_id}")
        
        # Check if file exists
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[file_id]
        file_path = file_info["file_path"]
        
        # Load data
        df = file_handler.load_dataframe(file_path)
        
        # Get AI recommendations
        profile = data_profiler.profile_data(
            df=df,
            file_name=file_info["file_name"],
            file_size=file_info["file_size"]
        )
        
        ai_recommendations = ai_service.generate_recommendations(profile)
        
        # Clean data
        cleaned_df, cleaning_log = data_cleaner.clean_dataset(df, ai_recommendations)
        
        # Save cleaned data
        cleaned_file_path = file_path.replace('.csv', '_cleaned.csv').replace('.xlsx', '_cleaned.xlsx')
        if cleaned_file_path.endswith('.csv'):
            cleaned_df.to_csv(cleaned_file_path, index=False)
        else:
            cleaned_df.to_excel(cleaned_file_path, index=False)
        
        # Get cleaning summary
        cleaning_summary = data_cleaner.get_cleaning_summary()
        
        return {
            "success": True,
            "message": "Data cleaning completed successfully",
            "original_shape": df.shape,
            "cleaned_shape": cleaned_df.shape,
            "cleaning_summary": cleaning_summary,
            "cleaned_file_path": cleaned_file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data cleaning failed: {str(e)}")


@app.post("/validate-data")
async def validate_data(file_id: str, custom_rules: Optional[Dict] = None):
    """Validate data against business rules"""
    try:
        logger.info(f"Data validation request for file: {file_id}")
        
        # Check if file exists
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[file_id]
        file_path = file_info["file_path"]
        
        # Load data
        df = file_handler.load_dataframe(file_path)
        
        # Validate data
        validation_results = data_validator.validate_dataset(df, custom_rules)
        
        return {
            "success": True,
            "message": "Data validation completed",
            "validation_results": validation_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data validation failed: {str(e)}")


@app.post("/comprehensive-analysis")
async def comprehensive_analysis(file_id: str):
    """Perform comprehensive analysis including profiling, cleaning, and validation"""
    try:
        start_time = time.time()
        logger.info(f"Comprehensive analysis request for file: {file_id}")
        
        # Check if file exists
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[file_id]
        file_path = file_info["file_path"]
        
        # Load data
        df = file_handler.load_dataframe(file_path)
        
        # Step 1: Profile data
        profile = data_profiler.profile_data(
            df=df,
            file_name=file_info["file_name"],
            file_size=file_info["file_size"]
        )
        
        # Step 2: Generate AI recommendations
        ai_recommendations = ai_service.generate_recommendations(profile)
        
        # Step 3: Clean data
        cleaned_df, cleaning_log = data_cleaner.clean_dataset(df, ai_recommendations)
        
        # Step 4: Validate cleaned data
        validation_results = data_validator.validate_dataset(cleaned_df)
        
        # Step 5: Generate final recommendations
        final_recommendations = ai_service.enhance_recommendations_with_ai(
            ai_recommendations, profile
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "message": "Comprehensive analysis completed successfully",
            "processing_time": processing_time,
            "original_profile": profile,
            "cleaning_log": cleaning_log,
            "validation_results": validation_results,
            "final_recommendations": final_recommendations,
            "original_shape": df.shape,
            "cleaned_shape": cleaned_df.shape
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comprehensive analysis failed: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            status_code=exc.status_code
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            status_code=500
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
