import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
import re
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)


class DataValidator:
    """Data validation service for business rules and constraints"""
    
    def __init__(self):
        self.validation_rules = {}
        self.validation_results = []
    
    def validate_dataset(self, df: pd.DataFrame, custom_rules: Optional[Dict] = None) -> Dict[str, Any]:
        """Validate dataset against built-in and custom rules"""
        try:
            logger.info("Starting data validation")
            self.validation_results = []
            
            # Apply built-in validation rules
            self._apply_builtin_rules(df)
            
            # Apply custom rules if provided
            if custom_rules:
                self._apply_custom_rules(df, custom_rules)
            
            # Generate validation summary
            summary = self._generate_validation_summary()
            
            logger.info(f"Data validation completed. Found {summary['total_violations']} violations")
            return summary
            
        except Exception as e:
            logger.error(f"Error during data validation: {str(e)}")
            raise Exception(f"Data validation failed: {str(e)}")
    
    def _apply_builtin_rules(self, df: pd.DataFrame):
        """Apply built-in validation rules"""
        # Email validation
        email_columns = [col for col in df.columns if 'email' in col.lower()]
        for col in email_columns:
            self._validate_emails(df, col)
        
        # Phone number validation
        phone_columns = [col for col in df.columns if 'phone' in col.lower() or 'tel' in col.lower()]
        for col in phone_columns:
            self._validate_phone_numbers(df, col)
        
        # Date validation
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        for col in date_columns:
            self._validate_dates(df, col)
        
        # Age validation
        age_columns = [col for col in df.columns if 'age' in col.lower()]
        for col in age_columns:
            self._validate_age(df, col)
        
        # Salary validation
        salary_columns = [col for col in df.columns if 'salary' in col.lower() or 'income' in col.lower()]
        for col in salary_columns:
            self._validate_salary(df, col)
        
        # ID validation
        id_columns = [col for col in df.columns if 'id' in col.lower() and col.lower() != 'id']
        for col in id_columns:
            self._validate_ids(df, col)
    
    def _apply_custom_rules(self, df: pd.DataFrame, custom_rules: Dict):
        """Apply custom validation rules"""
        for rule_name, rule_config in custom_rules.items():
            try:
                column = rule_config.get('column')
                rule_type = rule_config.get('type')
                parameters = rule_config.get('parameters', {})
                
                if column not in df.columns:
                    self.validation_results.append({
                        'rule_name': rule_name,
                        'column': column,
                        'severity': 'error',
                        'message': f'Column {column} not found in dataset',
                        'violations': 0
                    })
                    continue
                
                if rule_type == 'range':
                    self._validate_range(df, column, rule_name, parameters)
                elif rule_type == 'pattern':
                    self._validate_pattern(df, column, rule_name, parameters)
                elif rule_type == 'unique':
                    self._validate_unique(df, column, rule_name, parameters)
                elif rule_type == 'not_null':
                    self._validate_not_null(df, column, rule_name, parameters)
                elif rule_type == 'custom':
                    self._validate_custom(df, column, rule_name, parameters)
                
            except Exception as e:
                logger.error(f"Error applying custom rule {rule_name}: {str(e)}")
    
    def _validate_emails(self, df: pd.DataFrame, column: str):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_emails = df[column].dropna().apply(lambda x: not re.match(email_pattern, str(x)))
        invalid_count = invalid_emails.sum()
        
        if invalid_count > 0:
            self.validation_results.append({
                'rule_name': 'email_format',
                'column': column,
                'severity': 'warning',
                'message': f'Found {invalid_count} invalid email formats',
                'violations': int(invalid_count),
                'invalid_values': df[column][invalid_emails].tolist()
            })
    
    def _validate_phone_numbers(self, df: pd.DataFrame, column: str):
        """Validate phone number format"""
        # Remove all non-digit characters and check length
        def is_valid_phone(phone):
            if pd.isna(phone):
                return True
            digits = re.sub(r'\D', '', str(phone))
            return len(digits) in [10, 11]
        
        invalid_phones = df[column].dropna().apply(lambda x: not is_valid_phone(x))
        invalid_count = invalid_phones.sum()
        
        if invalid_count > 0:
            self.validation_results.append({
                'rule_name': 'phone_format',
                'column': column,
                'severity': 'warning',
                'message': f'Found {invalid_count} invalid phone number formats',
                'violations': int(invalid_count),
                'invalid_values': df[column][invalid_phones].tolist()
            })
    
    def _validate_dates(self, df: pd.DataFrame, column: str):
        """Validate date format and range"""
        try:
            # Try to convert to datetime
            date_series = pd.to_datetime(df[column], errors='coerce')
            invalid_dates = date_series.isna() & df[column].notna()
            invalid_count = invalid_dates.sum()
            
            if invalid_count > 0:
                self.validation_results.append({
                    'rule_name': 'date_format',
                    'column': column,
                    'severity': 'warning',
                    'message': f'Found {invalid_count} invalid date formats',
                    'violations': int(invalid_count),
                    'invalid_values': df[column][invalid_dates].tolist()
                })
            
            # Check for future dates (if it's a join date or similar)
            if 'join' in column.lower() or 'hire' in column.lower():
                future_dates = date_series > pd.Timestamp.now()
                future_count = future_dates.sum()
                
                if future_count > 0:
                    self.validation_results.append({
                        'rule_name': 'future_date',
                        'column': column,
                        'severity': 'error',
                        'message': f'Found {future_count} future dates',
                        'violations': int(future_count),
                        'invalid_values': df[column][future_dates].tolist()
                    })
                    
        except Exception as e:
            logger.error(f"Error validating dates in column {column}: {str(e)}")
    
    def _validate_age(self, df: pd.DataFrame, column: str):
        """Validate age values"""
        age_series = pd.to_numeric(df[column], errors='coerce')
        
        # Check for reasonable age range (0-120)
        invalid_ages = (age_series < 0) | (age_series > 120)
        invalid_count = invalid_ages.sum()
        
        if invalid_count > 0:
            self.validation_results.append({
                'rule_name': 'age_range',
                'column': column,
                'severity': 'error',
                'message': f'Found {invalid_count} ages outside reasonable range (0-120)',
                'violations': int(invalid_count),
                'invalid_values': df[column][invalid_ages].tolist()
            })
    
    def _validate_salary(self, df: pd.DataFrame, column: str):
        """Validate salary values"""
        salary_series = pd.to_numeric(df[column], errors='coerce')
        
        # Check for negative salaries
        negative_salaries = salary_series < 0
        negative_count = negative_salaries.sum()
        
        if negative_count > 0:
            self.validation_results.append({
                'rule_name': 'negative_salary',
                'column': column,
                'severity': 'error',
                'message': f'Found {negative_count} negative salary values',
                'violations': int(negative_count),
                'invalid_values': df[column][negative_salaries].tolist()
            })
        
        # Check for unreasonably high salaries (>$1M)
        high_salaries = salary_series > 1000000
        high_count = high_salaries.sum()
        
        if high_count > 0:
            self.validation_results.append({
                'rule_name': 'high_salary',
                'column': column,
                'severity': 'warning',
                'message': f'Found {high_count} salaries above $1M',
                'violations': int(high_count),
                'invalid_values': df[column][high_salaries].tolist()
            })
    
    def _validate_ids(self, df: pd.DataFrame, column: str):
        """Validate ID uniqueness and format"""
        # Check for uniqueness
        duplicate_ids = df[column].duplicated()
        duplicate_count = duplicate_ids.sum()
        
        if duplicate_count > 0:
            self.validation_results.append({
                'rule_name': 'duplicate_ids',
                'column': column,
                'severity': 'error',
                'message': f'Found {duplicate_count} duplicate ID values',
                'violations': int(duplicate_count),
                'invalid_values': df[column][duplicate_ids].tolist()
            })
    
    def _validate_range(self, df: pd.DataFrame, column: str, rule_name: str, parameters: Dict):
        """Validate numeric range"""
        min_val = parameters.get('min')
        max_val = parameters.get('max')
        
        if min_val is not None or max_val is not None:
            numeric_series = pd.to_numeric(df[column], errors='coerce')
            
            if min_val is not None and max_val is not None:
                out_of_range = (numeric_series < min_val) | (numeric_series > max_val)
            elif min_val is not None:
                out_of_range = numeric_series < min_val
            else:
                out_of_range = numeric_series > max_val
            
            violation_count = out_of_range.sum()
            
            if violation_count > 0:
                self.validation_results.append({
                    'rule_name': rule_name,
                    'column': column,
                    'severity': parameters.get('severity', 'error'),
                    'message': f'Found {violation_count} values outside range [{min_val}, {max_val}]',
                    'violations': int(violation_count),
                    'invalid_values': df[column][out_of_range].tolist()
                })
    
    def _validate_pattern(self, df: pd.DataFrame, column: str, rule_name: str, parameters: Dict):
        """Validate pattern matching"""
        pattern = parameters.get('pattern')
        if pattern:
            invalid_values = df[column].dropna().apply(lambda x: not re.match(pattern, str(x)))
            violation_count = invalid_values.sum()
            
            if violation_count > 0:
                self.validation_results.append({
                    'rule_name': rule_name,
                    'column': column,
                    'severity': parameters.get('severity', 'error'),
                    'message': f'Found {violation_count} values not matching pattern {pattern}',
                    'violations': int(violation_count),
                    'invalid_values': df[column][invalid_values].tolist()
                })
    
    def _validate_unique(self, df: pd.DataFrame, column: str, rule_name: str, parameters: Dict):
        """Validate uniqueness"""
        duplicate_values = df[column].duplicated()
        violation_count = duplicate_values.sum()
        
        if violation_count > 0:
            self.validation_results.append({
                'rule_name': rule_name,
                'column': column,
                'severity': parameters.get('severity', 'error'),
                'message': f'Found {violation_count} duplicate values',
                'violations': int(violation_count),
                'invalid_values': df[column][duplicate_values].tolist()
            })
    
    def _validate_not_null(self, df: pd.DataFrame, column: str, rule_name: str, parameters: Dict):
        """Validate non-null values"""
        null_values = df[column].isna()
        violation_count = null_values.sum()
        
        if violation_count > 0:
            self.validation_results.append({
                'rule_name': rule_name,
                'column': column,
                'severity': parameters.get('severity', 'error'),
                'message': f'Found {violation_count} null values',
                'violations': int(violation_count)
            })
    
    def _validate_custom(self, df: pd.DataFrame, column: str, rule_name: str, parameters: Dict):
        """Validate custom function"""
        custom_func = parameters.get('function')
        if callable(custom_func):
            invalid_values = df[column].apply(lambda x: not custom_func(x))
            violation_count = invalid_values.sum()
            
            if violation_count > 0:
                self.validation_results.append({
                    'rule_name': rule_name,
                    'column': column,
                    'severity': parameters.get('severity', 'error'),
                    'message': f'Found {violation_count} values failing custom validation',
                    'violations': int(violation_count),
                    'invalid_values': df[column][invalid_values].tolist()
                })
    
    def _generate_validation_summary(self) -> Dict[str, Any]:
        """Generate validation summary"""
        total_violations = sum(result['violations'] for result in self.validation_results)
        error_count = len([r for r in self.validation_results if r['severity'] == 'error'])
        warning_count = len([r for r in self.validation_results if r['severity'] == 'warning'])
        
        # Group violations by column
        violations_by_column = {}
        for result in self.validation_results:
            column = result['column']
            if column not in violations_by_column:
                violations_by_column[column] = []
            violations_by_column[column].append(result)
        
        return {
            'total_violations': total_violations,
            'error_count': error_count,
            'warning_count': warning_count,
            'validation_results': self.validation_results,
            'violations_by_column': violations_by_column,
            'overall_status': 'error' if error_count > 0 else 'warning' if warning_count > 0 else 'pass'
        } 
