import os
import io
from datetime import datetime
from typing import List, Dict, Any
import logging
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from app.backend.models import DataProfile, AIRecommendation, DataQualityIssue

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate PDF reports for data quality analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.darkblue
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkgreen
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        self.highlight_style = ParagraphStyle(
            'CustomHighlight',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            textColor=colors.red
        )
    
    def generate_report(self, profile: DataProfile, output_path: str = None) -> bytes:
        """Generate comprehensive PDF report"""
        try:
            if output_path is None:
                output_path = f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Add report sections
            story.extend(self._create_header(profile))
            story.append(PageBreak())
            
            story.extend(self._create_executive_summary(profile))
            story.append(PageBreak())
            
            story.extend(self._create_data_overview(profile))
            story.append(PageBreak())
            
            story.extend(self._create_column_analysis(profile))
            story.append(PageBreak())
            
            story.extend(self._create_quality_issues(profile))
            story.append(PageBreak())
            
            story.extend(self._create_ai_recommendations(profile))
            story.append(PageBreak())
            
            story.extend(self._create_visualizations(profile))
            
            # Build PDF
            doc.build(story)
            
            # Read the generated PDF
            with open(output_path, 'rb') as f:
                pdf_content = f.read()
            
            # Clean up temporary file
            if os.path.exists(output_path):
                os.remove(output_path)
            
            logger.info(f"PDF report generated successfully")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise Exception(f"Failed to generate PDF report: {str(e)}")
    
    def _create_header(self, profile: DataProfile) -> List:
        """Create report header"""
        elements = []
        
        # Title
        title = Paragraph("Data Quality Analysis Report", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Report metadata
        metadata_data = [
            ["File Name:", profile.file_name],
            ["Analysis Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["File Size:", f"{profile.file_size:,} bytes"],
            ["Total Rows:", f"{profile.row_count:,}"],
            ["Total Columns:", f"{profile.column_count}"],
            ["Memory Usage:", profile.memory_usage]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(metadata_table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_executive_summary(self, profile: DataProfile) -> List:
        """Create executive summary section"""
        elements = []
        
        # Section title
        title = Paragraph("Executive Summary", self.heading_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Summary statistics
        summary_text = f"""
        This data quality analysis report provides a comprehensive assessment of the dataset '{profile.file_name}'. 
        The analysis reveals {len(profile.quality_issues)} quality issues and provides {len(profile.ai_recommendations)} 
        AI-powered recommendations for improvement.
        
        Key Findings:
        • Dataset contains {profile.row_count:,} rows and {profile.column_count} columns
        • {profile.duplicate_percentage:.1f}% of rows are duplicates ({profile.duplicate_rows:,} duplicate rows)
        • {len([col for col in profile.columns if col.missing_percentage > 0])} columns contain missing values
        • {len([col for col in profile.columns if col.data_type.value == "mixed"])} columns have mixed data types
        
        Overall Data Quality Score: {self._calculate_quality_score(profile):.1f}/100
        """
        
        summary_para = Paragraph(summary_text, self.body_style)
        elements.append(summary_para)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_data_overview(self, profile: DataProfile) -> List:
        """Create data overview section"""
        elements = []
        
        # Section title
        title = Paragraph("Data Overview", self.heading_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Overview table
        overview_data = [
            ["Metric", "Value", "Status"],
            ["Total Rows", f"{profile.row_count:,}", "✓" if profile.row_count > 0 else "⚠"],
            ["Total Columns", f"{profile.column_count}", "✓" if profile.column_count > 0 else "⚠"],
            ["Duplicate Rows", f"{profile.duplicate_rows:,} ({profile.duplicate_percentage:.1f}%)", 
             "⚠" if profile.duplicate_percentage > 10 else "✓"],
            ["Memory Usage", profile.memory_usage, "✓"],
            ["Quality Issues", f"{len(profile.quality_issues)}", 
             "⚠" if len(profile.quality_issues) > 0 else "✓"]
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 2*inch, 1*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(overview_table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_column_analysis(self, profile: DataProfile) -> List:
        """Create column analysis section"""
        elements = []
        
        # Section title
        title = Paragraph("Column Analysis", self.heading_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Column details table
        column_headers = ["Column Name", "Data Type", "Missing %", "Unique %", "Sample Values"]
        column_data = [column_headers]
        
        for col in profile.columns:
            sample_values = ', '.join(col.sample_values[:3]) if col.sample_values else "N/A"
            column_data.append([
                col.name,
                col.data_type.value,
                f"{col.missing_percentage:.1f}%",
                f"{col.unique_percentage:.1f}%",
                sample_values
            ])
        
        column_table = Table(column_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 2*inch])
        column_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(column_table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_quality_issues(self, profile: DataProfile) -> List:
        """Create quality issues section"""
        elements = []
        
        # Section title
        title = Paragraph("Data Quality Issues", self.heading_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        if not profile.quality_issues:
            no_issues = Paragraph("No quality issues detected in the dataset.", self.body_style)
            elements.append(no_issues)
            return elements
        
        # Issues table
        for i, issue in enumerate(profile.quality_issues, 1):
            # Issue header
            issue_title = Paragraph(f"{i}. {issue.issue_type.replace('_', ' ').title()} (Severity: {issue.severity})", 
                                  self.subheading_style)
            elements.append(issue_title)
            
            # Issue details
            issue_text = f"""
            Description: {issue.description}
            Affected Columns: {', '.join(issue.affected_columns) if issue.affected_columns else 'All columns'}
            Recommendation: {issue.recommendation}
            """
            
            issue_para = Paragraph(issue_text, self.body_style)
            elements.append(issue_para)
            elements.append(Spacer(1, 8))
        
        return elements
    
    def _create_ai_recommendations(self, profile: DataProfile) -> List:
        """Create AI recommendations section"""
        elements = []
        
        # Section title
        title = Paragraph("AI-Powered Recommendations", self.heading_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        if not profile.ai_recommendations:
            no_recs = Paragraph("No AI recommendations available.", self.body_style)
            elements.append(no_recs)
            return elements
        
        # Recommendations table
        for i, rec in enumerate(profile.ai_recommendations, 1):
            # Recommendation header
            rec_title = Paragraph(f"{i}. {rec.title} (Priority: {rec.priority})", self.subheading_style)
            elements.append(rec_title)
            
            # Recommendation details
            rec_text = f"""
            Category: {rec.category}
            Description: {rec.description}
            Estimated Impact: {rec.estimated_impact}
            
            Action Items:
            """
            
            for j, action in enumerate(rec.action_items, 1):
                rec_text += f"• {action}\n"
            
            rec_para = Paragraph(rec_text, self.body_style)
            elements.append(rec_para)
            elements.append(Spacer(1, 8))
        
        return elements
    
    def _create_visualizations(self, profile: DataProfile) -> List:
        """Create visualizations section"""
        elements = []
        
        # Section title
        title = Paragraph("Data Visualizations", self.heading_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Create visualizations
        try:
            # Missing values chart
            missing_chart = self._create_missing_values_chart(profile)
            if missing_chart:
                elements.append(missing_chart)
                elements.append(Spacer(1, 12))
            
            # Data types chart
            types_chart = self._create_data_types_chart(profile)
            if types_chart:
                elements.append(types_chart)
                elements.append(Spacer(1, 12))
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
            error_msg = Paragraph("Visualizations could not be generated due to an error.", self.body_style)
            elements.append(error_msg)
        
        return elements
    
    def _create_missing_values_chart(self, profile: DataProfile):
        """Create missing values visualization"""
        try:
            # Prepare data
            columns = [col.name for col in profile.columns]
            missing_percentages = [col.missing_percentage for col in profile.columns]
            
            # Create matplotlib figure
            plt.figure(figsize=(10, 6))
            bars = plt.bar(range(len(columns)), missing_percentages)
            plt.xlabel('Columns')
            plt.ylabel('Missing Values (%)')
            plt.title('Missing Values by Column')
            plt.xticks(range(len(columns)), columns, rotation=45, ha='right')
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Convert to reportlab image
            from reportlab.platypus import Image
            img = Image(img_buffer)
            img.drawHeight = 4*inch
            img.drawWidth = 6*inch
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating missing values chart: {str(e)}")
            return None
    
    def _create_data_types_chart(self, profile: DataProfile):
        """Create data types visualization"""
        try:
            # Prepare data
            type_counts = {}
            for col in profile.columns:
                data_type = col.data_type.value
                type_counts[data_type] = type_counts.get(data_type, 0) + 1
            
            # Create matplotlib figure
            plt.figure(figsize=(8, 6))
            plt.pie(type_counts.values(), labels=type_counts.keys(), autopct='%1.1f%%')
            plt.title('Data Types Distribution')
            plt.axis('equal')
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Convert to reportlab image
            from reportlab.platypus import Image
            img = Image(img_buffer)
            img.drawHeight = 4*inch
            img.drawWidth = 4*inch
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating data types chart: {str(e)}")
            return None
    
    def _calculate_quality_score(self, profile: DataProfile) -> float:
        """Calculate overall data quality score (0-100)"""
        score = 100.0
        
        # Deduct points for issues
        score -= profile.duplicate_percentage * 0.5  # Duplicates
        score -= sum(col.missing_percentage for col in profile.columns) / len(profile.columns) * 0.3  # Missing values
        score -= len(profile.quality_issues) * 5  # Quality issues
        score -= len([col for col in profile.columns if col.data_type.value == "mixed"]) * 3  # Mixed types
        
        return max(0.0, score) 
