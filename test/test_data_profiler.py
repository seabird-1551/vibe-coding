import unittest
import pandas as pd
import numpy as np
from app.backend.services.data_profiler import DataProfiler
from app.backend.models import DataType

class TestDataProfiler(unittest.TestCase):
    """Test cases for DataProfiler class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.profiler = DataProfiler()
        
        # Create test data
        self.test_df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, None, 40],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'is_active': [True, False, True, True, False],
            'mixed_col': [1, 'text', 3.14, True, 'data']
        })
    
    def test_profile_data_basic(self):
        """Test basic data profiling"""
        profile = self.profiler.profile_data(
            df=self.test_df,
            file_name="test.csv",
            file_size=1024
        )
        
        # Check basic metrics
        self.assertEqual(profile.row_count, 5)
        self.assertEqual(profile.column_count, 6)
        self.assertEqual(profile.file_name, "test.csv")
        self.assertEqual(profile.file_size, 1024)
    
    def test_memory_usage_calculation(self):
        """Test memory usage calculation"""
        memory_usage = self.profiler._get_memory_usage(self.test_df)
        self.assertIsInstance(memory_usage, str)
        self.assertIn("B", memory_usage)
    
    def test_duplicate_analysis(self):
        """Test duplicate analysis"""
        # Create DataFrame with duplicates
        df_with_duplicates = pd.DataFrame({
            'col1': [1, 2, 1, 3, 2],
            'col2': ['a', 'b', 'a', 'c', 'b']
        })
        
        duplicate_count, duplicate_percentage = self.profiler._analyze_duplicates(df_with_duplicates)
        self.assertEqual(duplicate_count, 2)  # Two duplicate rows
        self.assertEqual(duplicate_percentage, 40.0)  # 2/5 * 100
    
    def test_column_profiling(self):
        """Test column profiling"""
        columns = self.profiler._profile_columns(self.test_df)
        
        self.assertEqual(len(columns), 6)
        
        # Check specific column
        id_col = next(col for col in columns if col.name == 'id')
        self.assertEqual(id_col.data_type, DataType.INTEGER)
        self.assertEqual(id_col.missing_count, 0)
        self.assertEqual(id_col.unique_count, 5)
    
    def test_data_type_detection(self):
        """Test data type detection"""
        # Test integer column
        int_series = pd.Series([1, 2, 3, 4, 5])
        data_type = self.profiler._detect_data_type(int_series)
        self.assertEqual(data_type, DataType.INTEGER)
        
        # Test float column
        float_series = pd.Series([1.1, 2.2, 3.3])
        data_type = self.profiler._detect_data_type(float_series)
        self.assertEqual(data_type, DataType.FLOAT)
        
        # Test string column
        string_series = pd.Series(['a', 'b', 'c'])
        data_type = self.profiler._detect_data_type(string_series)
        self.assertEqual(data_type, DataType.STRING)
        
        # Test mixed column
        mixed_series = pd.Series([1, 'text', 3.14])
        data_type = self.profiler._detect_data_type(mixed_series)
        self.assertEqual(data_type, DataType.MIXED)
    
    def test_quality_issues_detection(self):
        """Test quality issues detection"""
        # Create DataFrame with quality issues
        df_with_issues = pd.DataFrame({
            'col1': [1, 2, 3, None, None],  # 40% missing
            'col2': [1, 1, 1, 1, 1],  # Low cardinality
            'col3': [1, 'text', 3, True, 5],  # Mixed types
            'col4': [1, 2, 3, 4, 5]  # Good column
        })
        
        columns = self.profiler._profile_columns(df_with_issues)
        issues = self.profiler._detect_quality_issues(df_with_issues, columns)
        
        # Should detect mixed data types
        mixed_type_issues = [issue for issue in issues if issue.issue_type == "mixed_data_types"]
        self.assertGreater(len(mixed_type_issues), 0)
    
    def test_ai_recommendations_generation(self):
        """Test AI recommendations generation"""
        profile = self.profiler.profile_data(
            df=self.test_df,
            file_name="test.csv",
            file_size=1024
        )
        
        recommendations = self.profiler._generate_ai_recommendations(
            self.test_df, 
            profile.columns, 
            profile.quality_issues
        )
        
        # Should generate at least monitoring recommendation
        self.assertGreater(len(recommendations), 0)
        
        # Check recommendation structure
        for rec in recommendations:
            self.assertIn('category', rec.__dict__)
            self.assertIn('priority', rec.__dict__)
            self.assertIn('title', rec.__dict__)
            self.assertIn('description', rec.__dict__)

if __name__ == '__main__':
    unittest.main() 
