import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DataCleaner:
    """Automated data cleaning service based on AI recommendations"""
    
    def __init__(self):
        self.cleaning_log = []
    
    def clean_dataset(self, df: pd.DataFrame, recommendations: List[Dict]) -> Tuple[pd.DataFrame, List[Dict]]:
        """Apply cleaning operations based on AI recommendations"""
        try:
            logger.info("Starting automated data cleaning")
            original_shape = df.shape
            cleaned_df = df.copy()
            
            for recommendation in recommendations:
                if recommendation.get('category') == 'data_cleaning':
                    cleaned_df = self._apply_cleaning_operation(cleaned_df, recommendation)
            
            # Log cleaning results
            final_shape = cleaned_df.shape
            rows_removed = original_shape[0] - final_shape[0]
            cols_removed = original_shape[1] - final_shape[1]
            
            self.cleaning_log.append({
                'timestamp': datetime.now().isoformat(),
                'original_shape': original_shape,
                'final_shape': final_shape,
                'rows_removed': rows_removed,
                'columns_removed': cols_removed,
                'operations_applied': len(self.cleaning_log)
            })
            
            logger.info(f"Data cleaning completed. Removed {rows_removed} rows and {cols_removed} columns")
            return cleaned_df, self.cleaning_log
            
        except Exception as e:
            logger.error(f"Error during data cleaning: {str(e)}")
            raise Exception(f"Data cleaning failed: {str(e)}")
    
    def _apply_cleaning_operation(self, df: pd.DataFrame, recommendation: Dict) -> pd.DataFrame:
        """Apply specific cleaning operation based on recommendation"""
        operation_type = recommendation.get('title', '').lower()
        
        if 'missing values' in operation_type:
            return self._handle_missing_values(df, recommendation)
        elif 'duplicate' in operation_type:
            return self._remove_duplicates(df, recommendation)
        elif 'data type' in operation_type:
            return self._standardize_data_types(df, recommendation)
        elif 'outlier' in operation_type:
            return self._handle_outliers(df, recommendation)
        elif 'format' in operation_type:
            return self._standardize_formats(df, recommendation)
        else:
            logger.warning(f"Unknown cleaning operation: {operation_type}")
            return df
    
    def _handle_missing_values(self, df: pd.DataFrame, recommendation: Dict) -> pd.DataFrame:
        """Handle missing values based on data type and context"""
        cleaned_df = df.copy()
        
        for column in df.columns:
            missing_pct = df[column].isna().sum() / len(df) * 100
            
            if missing_pct > 80:
                # Remove columns with >80% missing values
                cleaned_df = cleaned_df.drop(columns=[column])
                self.cleaning_log.append({
                    'operation': 'remove_column',
                    'column': column,
                    'reason': f'High missing values ({missing_pct:.1f}%)'
                })
            elif missing_pct > 0:
                # Fill missing values based on data type
                if df[column].dtype in ['int64', 'float64']:
                    # Numeric columns: fill with median
                    median_val = df[column].median()
                    cleaned_df[column] = cleaned_df[column].fillna(median_val)
                    self.cleaning_log.append({
                        'operation': 'fill_missing',
                        'column': column,
                        'method': 'median',
                        'value': median_val
                    })
                elif df[column].dtype == 'object':
                    # String columns: fill with mode
                    mode_val = df[column].mode().iloc[0] if not df[column].mode().empty else 'Unknown'
                    cleaned_df[column] = cleaned_df[column].fillna(mode_val)
                    self.cleaning_log.append({
                        'operation': 'fill_missing',
                        'column': column,
                        'method': 'mode',
                        'value': mode_val
                    })
        
        return cleaned_df
    
    def _remove_duplicates(self, df: pd.DataFrame, recommendation: Dict) -> pd.DataFrame:
        """Remove duplicate rows"""
        original_count = len(df)
        cleaned_df = df.drop_duplicates()
        removed_count = original_count - len(cleaned_df)
        
        if removed_count > 0:
            self.cleaning_log.append({
                'operation': 'remove_duplicates',
                'rows_removed': removed_count,
                'percentage': (removed_count / original_count) * 100
            })
        
        return cleaned_df
    
    def _standardize_data_types(self, df: pd.DataFrame, recommendation: Dict) -> pd.DataFrame:
        """Standardize data types in mixed-type columns"""
        cleaned_df = df.copy()
        
        for column in df.columns:
            # Detect mixed types
            sample_values = df[column].dropna().head(100)
            if len(sample_values) == 0:
                continue
            
            # Check if column has mixed types
            type_counts = sample_values.apply(type).value_counts()
            if len(type_counts) > 1:
                # Try to convert to consistent type
                cleaned_df[column] = self._convert_to_consistent_type(df[column])
                self.cleaning_log.append({
                    'operation': 'standardize_data_type',
                    'column': column,
                    'original_types': type_counts.to_dict()
                })
        
        return cleaned_df
    
    def _convert_to_consistent_type(self, series: pd.Series) -> pd.Series:
        """Convert series to consistent data type"""
        # Try numeric conversion first
        try:
            numeric_series = pd.to_numeric(series, errors='coerce')
            if numeric_series.notna().sum() > len(series) * 0.8:  # 80% numeric
                return numeric_series
        except:
            pass
        
        # Try datetime conversion
        try:
            datetime_series = pd.to_datetime(series, errors='coerce')
            if datetime_series.notna().sum() > len(series) * 0.8:  # 80% datetime
                return datetime_series
        except:
            pass
        
        # Default to string
        return series.astype(str)
    
    def _handle_outliers(self, df: pd.DataFrame, recommendation: Dict) -> pd.DataFrame:
        """Handle outliers in numeric columns using IQR method"""
        cleaned_df = df.copy()
        
        for column in df.columns:
            if df[column].dtype in ['int64', 'float64']:
                Q1 = df[column].quantile(0.25)
                Q3 = df[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[column][(df[column] < lower_bound) | (df[column] > upper_bound)]
                
                if len(outliers) > 0:
                    # Replace outliers with bounds
                    cleaned_df[column] = cleaned_df[column].clip(lower=lower_bound, upper=upper_bound)
                    self.cleaning_log.append({
                        'operation': 'handle_outliers',
                        'column': column,
                        'outliers_found': len(outliers),
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound
                    })
        
        return cleaned_df
    
    def _standardize_formats(self, df: pd.DataFrame, recommendation: Dict) -> pd.DataFrame:
        """Standardize formats for common data types"""
        cleaned_df = df.copy()
        
        for column in df.columns:
            if df[column].dtype == 'object':
                # Standardize email formats
                if 'email' in column.lower():
                    cleaned_df[column] = cleaned_df[column].str.lower().str.strip()
                
                # Standardize phone numbers
                elif 'phone' in column.lower() or 'tel' in column.lower():
                    cleaned_df[column] = cleaned_df[column].apply(self._standardize_phone)
                
                # Standardize dates
                elif 'date' in column.lower():
                    cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors='coerce')
                
                # Remove extra whitespace
                cleaned_df[column] = cleaned_df[column].astype(str).str.strip()
        
        return cleaned_df
    
    def _standardize_phone(self, phone: str) -> str:
        """Standardize phone number format"""
        if pd.isna(phone):
            return phone
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', str(phone))
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return str(phone)
    
    def get_cleaning_summary(self) -> Dict[str, Any]:
        """Get summary of cleaning operations performed"""
        if not self.cleaning_log:
            return {"message": "No cleaning operations performed"}
        
        total_operations = len(self.cleaning_log)
        operations_by_type = {}
        
        for log in self.cleaning_log:
            if 'operation' in log:
                op_type = log['operation']
                if op_type not in operations_by_type:
                    operations_by_type[op_type] = 0
                operations_by_type[op_type] += 1
        
        return {
            "total_operations": total_operations,
            "operations_by_type": operations_by_type,
            "cleaning_log": self.cleaning_log
        } 
