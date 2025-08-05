import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime
from app.backend.models import (
    DataProfile, ColumnProfile, DataQualityIssue, 
    DataType, AIRecommendation
)

logger = logging.getLogger(__name__)


class DataProfiler:
    """Comprehensive data profiling and quality analysis"""
    
    def __init__(self):
        self.quality_issues = []
        self.ai_recommendations = []
    
    def profile_data(self, df: pd.DataFrame, file_name: str, file_size: int) -> DataProfile:
        """Generate comprehensive data profile"""
        try:
            logger.info(f"Starting data profiling for {file_name}")
            
            # Basic statistics
            row_count = len(df)
            column_count = len(df.columns)
            memory_usage = self._get_memory_usage(df)
            
            # Duplicate analysis
            duplicate_rows, duplicate_percentage = self._analyze_duplicates(df)
            
            # Column profiling
            columns = self._profile_columns(df)
            
            # Quality issues detection
            quality_issues = self._detect_quality_issues(df, columns)
            
            # AI recommendations
            ai_recommendations = self._generate_ai_recommendations(df, columns, quality_issues)
            
            profile = DataProfile(
                file_name=file_name,
                file_size=file_size,
                row_count=row_count,
                column_count=column_count,
                memory_usage=memory_usage,
                duplicate_rows=duplicate_rows,
                duplicate_percentage=duplicate_percentage,
                columns=columns,
                quality_issues=quality_issues,
                ai_recommendations=ai_recommendations
            )
            
            logger.info(f"Data profiling completed for {file_name}")
            return profile
            
        except Exception as e:
            logger.error(f"Error during data profiling: {str(e)}")
            raise Exception(f"Data profiling failed: {str(e)}")
    
    def _get_memory_usage(self, df: pd.DataFrame) -> str:
        """Calculate memory usage of DataFrame"""
        memory_bytes = df.memory_usage(deep=True).sum()
        if memory_bytes < 1024:
            return f"{memory_bytes} B"
        elif memory_bytes < 1024 * 1024:
            return f"{memory_bytes / 1024:.1f} KB"
        else:
            return f"{memory_bytes / (1024 * 1024):.1f} MB"
    
    def _analyze_duplicates(self, df: pd.DataFrame) -> Tuple[int, float]:
        """Analyze duplicate rows"""
        duplicate_count = df.duplicated().sum()
        total_rows = len(df)
        duplicate_percentage = (duplicate_count / total_rows * 100) if total_rows > 0 else 0
        return duplicate_count, duplicate_percentage
    
    def _profile_columns(self, df: pd.DataFrame) -> List[ColumnProfile]:
        """Profile individual columns"""
        columns = []
        
        for col_name in df.columns:
            try:
                col_data = df[col_name]
                
                # Missing values
                missing_count = col_data.isna().sum()
                missing_percentage = (missing_count / len(col_data) * 100) if len(col_data) > 0 else 0
                
                # Unique values
                unique_count = col_data.nunique()
                unique_percentage = (unique_count / len(col_data) * 100) if len(col_data) > 0 else 0
                
                # Data type detection
                data_type = self._detect_data_type(col_data)
                
                # Sample values
                sample_values = self._get_sample_values(col_data)
                
                # Statistical values
                min_value, max_value, mean_value, std_value = self._get_statistical_values(col_data, data_type)
                
                column_profile = ColumnProfile(
                    name=col_name,
                    data_type=data_type,
                    missing_count=missing_count,
                    missing_percentage=missing_percentage,
                    unique_count=unique_count,
                    unique_percentage=unique_percentage,
                    sample_values=sample_values,
                    min_value=min_value,
                    max_value=max_value,
                    mean_value=mean_value,
                    std_value=std_value
                )
                
                columns.append(column_profile)
                
            except Exception as e:
                logger.error(f"Error profiling column {col_name}: {str(e)}")
                # Create basic profile for failed column
                columns.append(ColumnProfile(
                    name=col_name,
                    data_type=DataType.STRING,
                    missing_count=0,
                    missing_percentage=0.0,
                    unique_count=0,
                    unique_percentage=0.0
                ))
        
        return columns
    
    def _detect_data_type(self, col_data: pd.Series) -> DataType:
        """Detect the data type of a column"""
        try:
            # Remove missing values for type detection
            clean_data = col_data.dropna()
            
            if len(clean_data) == 0:
                return DataType.STRING
            
            # Check for mixed types
            type_counts = clean_data.apply(type).value_counts()
            if len(type_counts) > 1:
                return DataType.MIXED
            
            # Try to convert to different types
            sample_values = clean_data.head(100)
            
            # Check for datetime
            try:
                pd.to_datetime(sample_values, errors='raise')
                return DataType.DATETIME
            except:
                pass
            
            # Check for boolean
            if clean_data.dtype == bool or clean_data.dtype == 'object':
                bool_values = ['true', 'false', 'yes', 'no', '1', '0']
                if all(str(val).lower() in bool_values for val in sample_values):
                    return DataType.BOOLEAN
            
            # Check for numeric types
            try:
                numeric_data = pd.to_numeric(clean_data, errors='raise')
                if numeric_data.dtype in ['int64', 'int32']:
                    return DataType.INTEGER
                elif numeric_data.dtype in ['float64', 'float32']:
                    return DataType.FLOAT
            except:
                pass
            
            # Default to string
            return DataType.STRING
            
        except Exception as e:
            logger.error(f"Error detecting data type: {str(e)}")
            return DataType.STRING
    
    def _get_sample_values(self, col_data: pd.Series) -> List[str]:
        """Get sample values from column"""
        try:
            # Get non-null unique values
            unique_values = col_data.dropna().unique()
            sample_size = min(5, len(unique_values))
            
            if sample_size == 0:
                return []
            
            # Convert to strings and take sample
            sample_values = [str(val) for val in unique_values[:sample_size]]
            return sample_values
            
        except Exception as e:
            logger.error(f"Error getting sample values: {str(e)}")
            return []
    
    def _get_statistical_values(self, col_data: pd.Series, data_type: DataType) -> Tuple[str, str, float, float]:
        """Get statistical values for numeric columns"""
        try:
            if data_type in [DataType.INTEGER, DataType.FLOAT]:
                numeric_data = pd.to_numeric(col_data, errors='coerce')
                clean_numeric = numeric_data.dropna()
                
                if len(clean_numeric) > 0:
                    min_val = str(clean_numeric.min())
                    max_val = str(clean_numeric.max())
                    mean_val = float(clean_numeric.mean())
                    std_val = float(clean_numeric.std())
                    return min_val, max_val, mean_val, std_val
            
            return None, None, None, None
            
        except Exception as e:
            logger.error(f"Error getting statistical values: {str(e)}")
            return None, None, None, None
    
    def _detect_quality_issues(self, df: pd.DataFrame, columns: List[ColumnProfile]) -> List[DataQualityIssue]:
        """Detect data quality issues"""
        issues = []
        
        # Missing values issues
        high_missing_cols = [col for col in columns if col.missing_percentage > 50]
        if high_missing_cols:
            issues.append(DataQualityIssue(
                issue_type="high_missing_values",
                severity="high" if len(high_missing_cols) > len(columns) * 0.3 else "medium",
                description=f"{len(high_missing_cols)} columns have more than 50% missing values",
                affected_columns=[col.name for col in high_missing_cols],
                recommendation="Consider removing columns with high missing values or implementing data imputation strategies"
            ))
        
        # Duplicate rows issue
        if df.duplicated().sum() > 0:
            issues.append(DataQualityIssue(
                issue_type="duplicate_rows",
                severity="medium",
                description=f"Found {df.duplicated().sum()} duplicate rows",
                affected_columns=[],
                recommendation="Remove duplicate rows to improve data quality"
            ))
        
        # Mixed data types issue
        mixed_type_cols = [col for col in columns if col.data_type == DataType.MIXED]
        if mixed_type_cols:
            issues.append(DataQualityIssue(
                issue_type="mixed_data_types",
                severity="high",
                description=f"{len(mixed_type_cols)} columns have mixed data types",
                affected_columns=[col.name for col in mixed_type_cols],
                recommendation="Standardize data types in affected columns"
            ))
        
        # Low cardinality issue
        low_cardinality_cols = [col for col in columns if col.unique_percentage < 5 and col.missing_percentage < 50]
        if low_cardinality_cols:
            issues.append(DataQualityIssue(
                issue_type="low_cardinality",
                severity="low",
                description=f"{len(low_cardinality_cols)} columns have very low cardinality",
                affected_columns=[col.name for col in low_cardinality_cols],
                recommendation="Consider if low cardinality columns provide value or can be removed"
            ))
        
        return issues
    
    def _generate_ai_recommendations(self, df: pd.DataFrame, columns: List[ColumnProfile], issues: List[DataQualityIssue]) -> List[AIRecommendation]:
        """Generate AI-powered recommendations"""
        recommendations = []
        
        # Data cleaning recommendations
        if any(issue.issue_type == "high_missing_values" for issue in issues):
            recommendations.append(AIRecommendation(
                category="data_cleaning",
                priority="high",
                title="Address Missing Values",
                description="High percentage of missing values detected in multiple columns",
                action_items=[
                    "Implement data imputation strategies",
                    "Investigate root cause of missing data",
                    "Consider removing columns with >80% missing values"
                ],
                estimated_impact="High - Will improve data completeness and analysis accuracy"
            ))
        
        # Data type standardization
        if any(issue.issue_type == "mixed_data_types" for issue in issues):
            recommendations.append(AIRecommendation(
                category="data_standardization",
                priority="high",
                title="Standardize Data Types",
                description="Mixed data types detected in columns",
                action_items=[
                    "Convert mixed-type columns to consistent formats",
                    "Implement data validation rules",
                    "Create data type conversion pipelines"
                ],
                estimated_impact="High - Will prevent analysis errors and improve performance"
            ))
        
        # Data quality monitoring
        recommendations.append(AIRecommendation(
            category="monitoring",
            priority="medium",
            title="Implement Data Quality Monitoring",
            description="Set up automated data quality checks",
            action_items=[
                "Create data quality dashboards",
                "Set up automated alerts for quality issues",
                "Implement data quality scoring"
            ],
            estimated_impact="Medium - Will help maintain data quality over time"
        ))
        
        return recommendations 
