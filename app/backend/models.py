from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class DataType(str, Enum):
    """Data type enumeration"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    MIXED = "mixed"


class ColumnProfile(BaseModel):
    """Profile information for a single column"""
    name: str
    data_type: DataType
    missing_count: int
    missing_percentage: float
    unique_count: int
    unique_percentage: float
    sample_values: List[str] = Field(default_factory=list)
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None


class DataQualityIssue(BaseModel):
    """Represents a data quality issue"""
    issue_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_columns: List[str] = Field(default_factory=list)
    recommendation: str


class AIRecommendation(BaseModel):
    """AI-generated recommendation for data quality improvement"""
    category: str
    priority: str  # "low", "medium", "high", "critical"
    title: str
    description: str
    action_items: List[str] = Field(default_factory=list)
    estimated_impact: str


class DataProfile(BaseModel):
    """Complete data profile information"""
    file_name: str
    file_size: int
    row_count: int
    column_count: int
    memory_usage: str
    duplicate_rows: int
    duplicate_percentage: float
    columns: List[ColumnProfile]
    quality_issues: List[DataQualityIssue] = Field(default_factory=list)
    ai_recommendations: List[AIRecommendation] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Response for file upload"""
    message: str
    file_id: str
    file_name: str
    file_size: int


class AnalyzeResponse(BaseModel):
    """Response for data analysis"""
    success: bool
    message: str
    profile: Optional[DataProfile] = None
    processing_time: float


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int 
