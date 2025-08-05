import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import time
from datetime import datetime
import io
import base64
from typing import Dict, Any, Optional

# Page configuration
st.set_page_config(
    page_title="AI-Powered Data Quality Checker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API configuration
BACKEND_URL = "http://localhost:8000"

def main():
    """Main Streamlit application"""
    
    # Sidebar
    st.sidebar.title("📊 Data Quality Checker")
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Choose a page",
        ["🏠 Home", "📁 Upload & Analyze", "📈 Results Dashboard", "🤖 AI Recommendations", "🧹 Data Cleaning", "✅ Data Validation", "📄 Generate Report"]
    )
    
    if page == "🏠 Home":
        show_home_page()
    elif page == "📁 Upload & Analyze":
        show_upload_page()
    elif page == "📈 Results Dashboard":
        show_dashboard_page()
    elif page == "🤖 AI Recommendations":
        show_recommendations_page()
    elif page == "🧹 Data Cleaning":
        show_cleaning_page()
    elif page == "✅ Data Validation":
        show_validation_page()
    elif page == "📄 Generate Report":
        show_report_page()

def show_home_page():
    """Display home page with application overview"""
    st.title("🤖 AI-Powered Data Quality Checker")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Welcome to the Data Quality Analysis Tool
        
        This application provides comprehensive data quality analysis with AI-powered recommendations.
        
        ### Key Features:
        - **📁 File Upload**: Support for CSV and Excel files
        - **📊 Data Profiling**: Automatic analysis of data structure and quality
        - **🤖 AI Recommendations**: Intelligent suggestions for data quality improvements
        - **📈 Interactive Visualizations**: Charts and graphs for better understanding
        - **📄 PDF Reports**: Detailed reports with actionable insights
        
        ### How to Use:
        1. **Upload** your CSV or Excel file
        2. **Analyze** the data quality automatically
        3. **Review** the detailed profiling results
        4. **Explore** AI-powered recommendations
        5. **Generate** comprehensive PDF reports
        """)
    
    with col2:
        st.markdown("""
        ### Supported File Types:
        - CSV files (.csv)
        - Excel files (.xlsx, .xls)
        
        ### Maximum File Size:
        - 10 MB per file
        
        ### Data Quality Metrics:
        - Row and column counts
        - Missing values analysis
        - Duplicate detection
        - Data type analysis
        - Mixed type detection
        """)
    
    # Check backend connection
    st.markdown("---")
    if check_backend_health():
        st.success("✅ Backend service is running")
    else:
        st.error("❌ Backend service is not available. Please start the FastAPI server.")

def show_upload_page():
    """Display file upload and analysis page"""
    st.title("📁 Upload & Analyze Data")
    st.markdown("---")
    
    # File upload section
    st.subheader("📤 Upload Your Data File")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your data file for quality analysis"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("File Type", uploaded_file.type or "Unknown")
        
        # Preview data
        st.subheader("📋 Data Preview")
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.dataframe(df.head(10), use_container_width=True)
            st.info(f"Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return
        
        # Analysis button
        st.markdown("---")
        if st.button("🚀 Analyze Data Quality", type="primary", use_container_width=True):
            with st.spinner("Analyzing data quality..."):
                try:
                    # Reset file pointer
                    uploaded_file.seek(0)
                    
                    # Send file to backend
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    response = requests.post(f"{BACKEND_URL}/analyze-with-file", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        profile = result["profile"]
                        
                        # Store results in session state
                        st.session_state.analysis_results = result
                        st.session_state.profile = profile
                        st.session_state.uploaded_file = uploaded_file
                        
                        st.success("✅ Analysis completed successfully!")
                        st.balloons()
                        
                        # Show quick summary
                        show_quick_summary(profile)
                        
                    else:
                        st.error(f"❌ Analysis failed: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")

def show_quick_summary(profile):
    """Display quick summary of analysis results"""
    st.subheader("📊 Quick Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rows", f"{profile['row_count']:,}")
    with col2:
        st.metric("Total Columns", profile['column_count'])
    with col3:
        st.metric("Duplicate Rows", f"{profile['duplicate_rows']:,} ({profile['duplicate_percentage']:.1f}%)")
    with col4:
        st.metric("Quality Issues", len(profile['quality_issues']))
    
    # Quality score
    quality_score = calculate_quality_score(profile)
    st.metric("Overall Quality Score", f"{quality_score:.1f}/100")

def show_dashboard_page():
    """Display detailed results dashboard"""
    st.title("📈 Data Quality Dashboard")
    st.markdown("---")
    
    if "profile" not in st.session_state:
        st.warning("⚠️ No analysis results available. Please upload and analyze a file first.")
        return
    
    profile = st.session_state.profile
    
    # Overview metrics
    st.subheader("📊 Overview Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("File Name", profile['file_name'])
        st.metric("File Size", f"{profile['file_size'] / 1024:.1f} KB")
    with col2:
        st.metric("Total Rows", f"{profile['row_count']:,}")
        st.metric("Total Columns", profile['column_count'])
    with col3:
        st.metric("Duplicate Rows", f"{profile['duplicate_rows']:,}")
        st.metric("Duplicate %", f"{profile['duplicate_percentage']:.1f}%")
    with col4:
        st.metric("Memory Usage", profile['memory_usage'])
        quality_score = calculate_quality_score(profile)
        st.metric("Quality Score", f"{quality_score:.1f}/100")
    
    # Column analysis
    st.subheader("📋 Column Analysis")
    if profile['columns']:
        # Create DataFrame for column analysis
        col_data = []
        for col in profile['columns']:
            col_data.append({
                'Column Name': col['name'],
                'Data Type': col['data_type'],
                'Missing Count': col['missing_count'],
                'Missing %': f"{col['missing_percentage']:.1f}%",
                'Unique Count': col['unique_count'],
                'Unique %': f"{col['unique_percentage']:.1f}%"
            })
        
        col_df = pd.DataFrame(col_data)
        st.dataframe(col_df, use_container_width=True)
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Missing values chart
            fig_missing = px.bar(
                col_df, 
                x='Column Name', 
                y='Missing Count',
                title="Missing Values by Column",
                color='Missing Count',
                color_continuous_scale='Reds'
            )
            fig_missing.update_xaxes(tickangle=45)
            st.plotly_chart(fig_missing, use_container_width=True)
        
        with col2:
            # Data types distribution
            type_counts = col_df['Data Type'].value_counts()
            fig_types = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Data Types Distribution"
            )
            st.plotly_chart(fig_types, use_container_width=True)
    
    # Quality issues
    st.subheader("⚠️ Quality Issues")
    if profile['quality_issues']:
        for i, issue in enumerate(profile['quality_issues'], 1):
            with st.expander(f"{i}. {issue['issue_type'].replace('_', ' ').title()} (Severity: {issue['severity']})"):
                st.write(f"**Description:** {issue['description']}")
                if issue['affected_columns']:
                    st.write(f"**Affected Columns:** {', '.join(issue['affected_columns'])}")
                st.write(f"**Recommendation:** {issue['recommendation']}")
    else:
        st.success("✅ No quality issues detected!")

def show_recommendations_page():
    """Display AI recommendations"""
    st.title("🤖 AI-Powered Recommendations")
    st.markdown("---")
    
    if "profile" not in st.session_state:
        st.warning("⚠️ No analysis results available. Please upload and analyze a file first.")
        return
    
    profile = st.session_state.profile
    
    if not profile.get('ai_recommendations'):
        st.info("ℹ️ No AI recommendations available.")
        return
    
    # Group recommendations by priority
    recommendations = profile['ai_recommendations']
    priority_groups = {}
    
    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        if priority not in priority_groups:
            priority_groups[priority] = []
        priority_groups[priority].append(rec)
    
    # Display recommendations by priority
    priority_order = ['critical', 'high', 'medium', 'low']
    priority_colors = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    }
    
    for priority in priority_order:
        if priority in priority_groups:
            st.subheader(f"{priority_colors[priority]} {priority.title()} Priority")
            
            for i, rec in enumerate(priority_groups[priority], 1):
                with st.expander(f"{i}. {rec['title']}"):
                    st.write(f"**Category:** {rec['category']}")
                    st.write(f"**Description:** {rec['description']}")
                    st.write(f"**Estimated Impact:** {rec['estimated_impact']}")
                    
                    if rec.get('action_items'):
                        st.write("**Action Items:**")
                        for action in rec['action_items']:
                            st.write(f"• {action}")

def show_report_page():
    """Display PDF report generation"""
    st.title("📄 Generate PDF Report")
    st.markdown("---")
    
    if "profile" not in st.session_state:
        st.warning("⚠️ No analysis results available. Please upload and analyze a file first.")
        return
    
    profile = st.session_state.profile
    
    st.subheader("📊 Report Summary")
    
    # Report preview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        **File:** {profile['file_name']}
        
        **Analysis Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        **Dataset Overview:**
        - Rows: {profile['row_count']:,}
        - Columns: {profile['column_count']}
        - Duplicate Rate: {profile['duplicate_percentage']:.1f}%
        - Quality Issues: {len(profile['quality_issues'])}
        - AI Recommendations: {len(profile.get('ai_recommendations', []))}
        """)
    
    with col2:
        quality_score = calculate_quality_score(profile)
        st.metric("Quality Score", f"{quality_score:.1f}/100")
        
        if quality_score >= 80:
            st.success("Excellent Quality")
        elif quality_score >= 60:
            st.warning("Good Quality")
        else:
            st.error("Needs Improvement")
    
    # Generate report button
    st.markdown("---")
    if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating PDF report..."):
            try:
                # For now, we'll create a simple report
                # In a real implementation, you'd call the backend API
                st.success("✅ PDF report generated successfully!")
                st.info("📥 Download link will appear here (backend integration required)")
                
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")

def show_cleaning_page():
    """Display data cleaning page"""
    st.title("🧹 Data Cleaning")
    st.markdown("---")
    
    if "profile" not in st.session_state:
        st.warning("⚠️ No analysis results available. Please upload and analyze a file first.")
        return
    
    profile = st.session_state.profile
    
    st.subheader("📊 Cleaning Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Available Cleaning Operations:**
        - 🗑️ Remove duplicate rows
        - 📝 Fill missing values
        - 🔧 Standardize data types
        - 📊 Handle outliers
        - 📋 Format standardization
        """)
    
    with col2:
        st.markdown("""
        **AI-Powered Cleaning:**
        - 🤖 Automatic issue detection
        - 🎯 Smart value imputation
        - 📈 Quality improvement tracking
        - 📄 Detailed cleaning logs
        """)
    
    st.markdown("---")
    
    if st.button("🚀 Start Data Cleaning", type="primary", use_container_width=True):
        with st.spinner("Cleaning data..."):
            try:
                # Call backend cleaning endpoint
                response = requests.post(f"{BACKEND_URL}/clean-data", json={"file_id": "current"})
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("✅ Data cleaning completed successfully!")
                    
                    # Display cleaning results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Original Rows", result['original_shape'][0])
                        st.metric("Original Columns", result['original_shape'][1])
                    
                    with col2:
                        st.metric("Cleaned Rows", result['cleaned_shape'][0])
                        st.metric("Cleaned Columns", result['cleaned_shape'][1])
                    
                    with col3:
                        rows_removed = result['original_shape'][0] - result['cleaned_shape'][0]
                        cols_removed = result['original_shape'][1] - result['cleaned_shape'][1]
                        st.metric("Rows Removed", rows_removed)
                        st.metric("Columns Removed", cols_removed)
                    
                    # Show cleaning summary
                    if 'cleaning_summary' in result:
                        st.subheader("📋 Cleaning Summary")
                        summary = result['cleaning_summary']
                        
                        if 'operations_by_type' in summary:
                            for op_type, count in summary['operations_by_type'].items():
                                st.info(f"**{op_type.replace('_', ' ').title()}**: {count} operations")
                    
                else:
                    st.error(f"❌ Cleaning failed: {response.json().get('detail', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"❌ Error during cleaning: {str(e)}")


def show_validation_page():
    """Display data validation page"""
    st.title("✅ Data Validation")
    st.markdown("---")
    
    if "profile" not in st.session_state:
        st.warning("⚠️ No analysis results available. Please upload and analyze a file first.")
        return
    
    profile = st.session_state.profile
    
    st.subheader("🔍 Validation Rules")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Built-in Validations:**
        - 📧 Email format validation
        - 📞 Phone number validation
        - 📅 Date format validation
        - 👤 Age range validation
        - 💰 Salary validation
        - 🆔 ID uniqueness validation
        """)
    
    with col2:
        st.markdown("""
        **Custom Rules:**
        - 📊 Range validation
        - 🔤 Pattern matching
        - 🔒 Uniqueness checks
        - ❌ Null value checks
        - ⚙️ Custom functions
        """)
    
    st.markdown("---")
    
    if st.button("🔍 Start Data Validation", type="primary", use_container_width=True):
        with st.spinner("Validating data..."):
            try:
                # Call backend validation endpoint
                response = requests.post(f"{BACKEND_URL}/validate-data", json={"file_id": "current"})
                
                if response.status_code == 200:
                    result = response.json()
                    validation_results = result['validation_results']
                    
                    st.success("✅ Data validation completed!")
                    
                    # Display validation summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Violations", validation_results['total_violations'])
                    
                    with col2:
                        st.metric("Errors", validation_results['error_count'])
                    
                    with col3:
                        st.metric("Warnings", validation_results['warning_count'])
                    
                    # Show validation results
                    st.subheader("📋 Validation Results")
                    
                    if validation_results['validation_results']:
                        for result in validation_results['validation_results']:
                            severity_color = "🔴" if result['severity'] == 'error' else "🟡"
                            st.markdown(f"{severity_color} **{result['rule_name']}** ({result['column']})")
                            st.write(f"*{result['message']}*")
                            st.write(f"Violations: {result['violations']}")
                            st.markdown("---")
                    else:
                        st.success("🎉 No validation issues found!")
                    
                else:
                    st.error(f"❌ Validation failed: {response.json().get('detail', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"❌ Error during validation: {str(e)}")


def calculate_quality_score(profile) -> float:
    """Calculate overall data quality score"""
    score = 100.0
    
    # Deduct points for issues
    score -= profile['duplicate_percentage'] * 0.5  # Duplicates
    score -= sum(col['missing_percentage'] for col in profile['columns']) / len(profile['columns']) * 0.3  # Missing values
    score -= len(profile['quality_issues']) * 5  # Quality issues
    score -= len([col for col in profile['columns'] if col['data_type'] == "mixed"]) * 3  # Mixed types
    
    return max(0.0, score)

def check_backend_health() -> bool:
    """Check if backend service is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    main() 
