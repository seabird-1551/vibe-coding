import unittest
import pandas as pd
import numpy as np
from app.backend.services.data_cleaner import DataCleaner
from app.backend.services.data_validator import DataValidator

class TestDataCleaner(unittest.TestCase):
    """Test cases for DataCleaner class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cleaner = DataCleaner()
        
        # Create test data with various issues
        self.test_df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, None, 35, 40],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'email': ['alice@test.com', 'bob@test.com', 'invalid-email', 'david@test.com', 'eve@test.com'],
            'phone': ['123-456-7890', 'invalid-phone', '987-654-3210', '555-123-4567', '999-888-7777'],
            'mixed_col': [1, 'text', 3.14, True, 'data']
        })
    
    def test_clean_dataset_basic(self):
        """Test basic data cleaning"""
        recommendations = [
            {
                'category': 'data_cleaning',
                'title': 'Address Missing Values'
            }
        ]
        
        cleaned_df, cleaning_log = self.cleaner.clean_dataset(self.test_df, recommendations)
        
        # Check that cleaning was performed
        self.assertIsInstance(cleaned_df, pd.DataFrame)
        self.assertIsInstance(cleaning_log, list)
        self.assertGreater(len(cleaning_log), 0)
    
    def test_handle_missing_values(self):
        """Test missing value handling"""
        # Create DataFrame with missing values
        df_with_missing = pd.DataFrame({
            'col1': [1, 2, None, 4, None],
            'col2': ['a', None, 'c', 'd', None],
            'col3': [1.1, 2.2, None, 4.4, 5.5]
        })
        
        recommendation = {'category': 'data_cleaning', 'title': 'Address Missing Values'}
        cleaned_df = self.cleaner._handle_missing_values(df_with_missing, recommendation)
        
        # Check that missing values were handled
        self.assertEqual(cleaned_df['col1'].isna().sum(), 0)
        self.assertEqual(cleaned_df['col2'].isna().sum(), 0)
        self.assertEqual(cleaned_df['col3'].isna().sum(), 0)
    
    def test_remove_duplicates(self):
        """Test duplicate removal"""
        df_with_duplicates = pd.DataFrame({
            'col1': [1, 2, 1, 3, 2],
            'col2': ['a', 'b', 'a', 'c', 'b']
        })
        
        recommendation = {'category': 'data_cleaning', 'title': 'Remove Duplicate Data'}
        cleaned_df = self.cleaner._remove_duplicates(df_with_duplicates, recommendation)
        
        # Check that duplicates were removed
        self.assertLess(len(cleaned_df), len(df_with_duplicates))
    
    def test_standardize_data_types(self):
        """Test data type standardization"""
        df_with_mixed_types = pd.DataFrame({
            'mixed_col': [1, 'text', 3.14, True, 'data']
        })
        
        recommendation = {'category': 'data_cleaning', 'title': 'Standardize Data Types'}
        cleaned_df = self.cleaner._standardize_data_types(df_with_mixed_types, recommendation)
        
        # Check that data types were standardized
        self.assertIsInstance(cleaned_df['mixed_col'].iloc[0], str)
    
    def test_handle_outliers(self):
        """Test outlier handling"""
        df_with_outliers = pd.DataFrame({
            'numeric_col': [1, 2, 3, 1000, 4, 5, -100]
        })
        
        recommendation = {'category': 'data_cleaning', 'title': 'Handle Outliers'}
        cleaned_df = self.cleaner._handle_outliers(df_with_outliers, recommendation)
        
        # Check that outliers were handled
        self.assertLess(cleaned_df['numeric_col'].max(), 1000)
        self.assertGreater(cleaned_df['numeric_col'].min(), -100)
    
    def test_standardize_formats(self):
        """Test format standardization"""
        df_with_formats = pd.DataFrame({
            'email': ['ALICE@TEST.COM', 'bob@test.com', 'CHARLIE@TEST.COM'],
            'phone': ['1234567890', '(555) 123-4567', '987.654.3210']
        })
        
        recommendation = {'category': 'data_cleaning', 'title': 'Standardize Formats'}
        cleaned_df = self.cleaner._standardize_formats(df_with_formats, recommendation)
        
        # Check that formats were standardized
        self.assertEqual(cleaned_df['email'].iloc[0], 'alice@test.com')
    
    def test_get_cleaning_summary(self):
        """Test cleaning summary generation"""
        # Perform some cleaning operations
        recommendations = [{'category': 'data_cleaning', 'title': 'Address Missing Values'}]
        self.cleaner.clean_dataset(self.test_df, recommendations)
        
        summary = self.cleaner.get_cleaning_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('total_operations', summary)


class TestDataValidator(unittest.TestCase):
    """Test cases for DataValidator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = DataValidator()
        
        # Create test data with various validation issues
        self.test_df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 150],  # Invalid age
            'salary': [50000, 60000, -1000, 80000, 2000000],  # Invalid salaries
            'email': ['alice@test.com', 'bob@test.com', 'invalid-email', 'david@test.com', 'eve@test.com'],
            'phone': ['123-456-7890', 'invalid-phone', '987-654-3210', '555-123-4567', '999-888-7777'],
            'join_date': ['2020-01-15', '2019-03-20', '2025-11-10', '2020-06-05', '2021-02-14']  # Future date
        })
    
    def test_validate_dataset_basic(self):
        """Test basic data validation"""
        validation_results = self.validator.validate_dataset(self.test_df)
        
        self.assertIsInstance(validation_results, dict)
        self.assertIn('total_violations', validation_results)
        self.assertIn('validation_results', validation_results)
    
    def test_validate_emails(self):
        """Test email validation"""
        self.validator._validate_emails(self.test_df, 'email')
        
        # Check that email validation results were added
        email_results = [r for r in self.validator.validation_results if r['rule_name'] == 'email_format']
        self.assertGreater(len(email_results), 0)
    
    def test_validate_phone_numbers(self):
        """Test phone number validation"""
        self.validator._validate_phone_numbers(self.test_df, 'phone')
        
        # Check that phone validation results were added
        phone_results = [r for r in self.validator.validation_results if r['rule_name'] == 'phone_format']
        self.assertGreater(len(phone_results), 0)
    
    def test_validate_dates(self):
        """Test date validation"""
        self.validator._validate_dates(self.test_df, 'join_date')
        
        # Check that date validation results were added
        date_results = [r for r in self.validator.validation_results if 'date' in r['rule_name']]
        self.assertGreater(len(date_results), 0)
    
    def test_validate_age(self):
        """Test age validation"""
        self.validator._validate_age(self.test_df, 'age')
        
        # Check that age validation results were added
        age_results = [r for r in self.validator.validation_results if r['rule_name'] == 'age_range']
        self.assertGreater(len(age_results), 0)
    
    def test_validate_salary(self):
        """Test salary validation"""
        self.validator._validate_salary(self.test_df, 'salary')
        
        # Check that salary validation results were added
        salary_results = [r for r in self.validator.validation_results if 'salary' in r['rule_name']]
        self.assertGreater(len(salary_results), 0)
    
    def test_validate_ids(self):
        """Test ID validation"""
        # Create DataFrame with duplicate IDs
        df_with_duplicate_ids = pd.DataFrame({
            'id': [1, 2, 1, 3, 2]  # Duplicate IDs
        })
        
        self.validator._validate_ids(df_with_duplicate_ids, 'id')
        
        # Check that ID validation results were added
        id_results = [r for r in self.validator.validation_results if r['rule_name'] == 'duplicate_ids']
        self.assertGreater(len(id_results), 0)
    
    def test_custom_validation_rules(self):
        """Test custom validation rules"""
        custom_rules = {
            'age_range': {
                'column': 'age',
                'type': 'range',
                'parameters': {
                    'min': 18,
                    'max': 65,
                    'severity': 'error'
                }
            },
            'salary_positive': {
                'column': 'salary',
                'type': 'range',
                'parameters': {
                    'min': 0,
                    'severity': 'error'
                }
            }
        }
        
        validation_results = self.validator.validate_dataset(self.test_df, custom_rules)
        
        self.assertIsInstance(validation_results, dict)
        self.assertIn('total_violations', validation_results)
    
    def test_generate_validation_summary(self):
        """Test validation summary generation"""
        # Perform some validations
        self.validator._validate_emails(self.test_df, 'email')
        self.validator._validate_age(self.test_df, 'age')
        
        summary = self.validator._generate_validation_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('total_violations', summary)
        self.assertIn('error_count', summary)
        self.assertIn('warning_count', summary)
        self.assertIn('overall_status', summary)


if __name__ == '__main__':
    unittest.main() 
