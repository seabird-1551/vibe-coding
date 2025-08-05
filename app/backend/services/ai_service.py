import os
import openai
from typing import List, Dict, Any
import logging
from app.backend.models import DataProfile, AIRecommendation, DataQualityIssue
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """AI-powered data quality recommendations using OpenAI GPT"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not found. AI recommendations will be limited.")
        
        # Configure OpenAI client
        if self.api_key:
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_recommendations(self, profile: DataProfile) -> List[AIRecommendation]:
        """Generate AI-powered recommendations based on data profile"""
        try:
            if not self.client:
                logger.warning("OpenAI client not available. Using fallback recommendations.")
                return self._generate_fallback_recommendations(profile)
            
            # Prepare context for AI
            context = self._prepare_ai_context(profile)
            
            # Generate AI recommendations
            ai_recommendations = self._call_openai_api(context)
            
            # Parse and validate recommendations
            parsed_recommendations = self._parse_ai_recommendations(ai_recommendations)
            
            logger.info(f"Generated {len(parsed_recommendations)} AI recommendations")
            return parsed_recommendations
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}")
            return self._generate_fallback_recommendations(profile)
    
    def _prepare_ai_context(self, profile: DataProfile) -> str:
        """Prepare context for AI analysis"""
        context = f"""
        Data Quality Analysis Report:
        
        File: {profile.file_name}
        Size: {profile.file_size} bytes
        Rows: {profile.row_count}
        Columns: {profile.column_count}
        Memory Usage: {profile.memory_usage}
        Duplicate Rows: {profile.duplicate_rows} ({profile.duplicate_percentage:.1f}%)
        
        Column Analysis:
        """
        
        for col in profile.columns:
            context += f"""
        - {col.name}:
          - Data Type: {col.data_type}
          - Missing Values: {col.missing_count} ({col.missing_percentage:.1f}%)
          - Unique Values: {col.unique_count} ({col.unique_percentage:.1f}%)
          - Sample Values: {', '.join(col.sample_values[:3])}
          """
        
        context += f"""
        
        Quality Issues Found:
        """
        
        for issue in profile.quality_issues:
            context += f"""
        - {issue.issue_type} (Severity: {issue.severity}):
          - Description: {issue.description}
          - Affected Columns: {', '.join(issue.affected_columns)}
          - Recommendation: {issue.recommendation}
          """
        
        context += """
        
        Please provide specific, actionable recommendations for improving data quality. 
        Focus on:
        1. Data cleaning strategies
        2. Data type standardization
        3. Missing value handling
        4. Performance optimization
        5. Best practices for data governance
        
        Format your response as a JSON array of recommendation objects with:
        - category: string (data_cleaning, data_standardization, monitoring, etc.)
        - priority: string (low, medium, high, critical)
        - title: string
        - description: string
        - action_items: array of strings
        - estimated_impact: string
        """
        
        return context
    
    def _call_openai_api(self, context: str) -> str:
        """Call OpenAI API for recommendations"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data quality expert. Analyze the provided data profile and generate specific, actionable recommendations for improving data quality. Return your response as a valid JSON array."
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise Exception(f"Failed to get AI recommendations: {str(e)}")
    
    def _parse_ai_recommendations(self, ai_response: str) -> List[AIRecommendation]:
        """Parse AI response into structured recommendations"""
        try:
            import json
            
            # Clean the response and extract JSON
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            recommendations_data = json.loads(cleaned_response)
            
            recommendations = []
            for rec_data in recommendations_data:
                try:
                    recommendation = AIRecommendation(
                        category=rec_data.get("category", "general"),
                        priority=rec_data.get("priority", "medium"),
                        title=rec_data.get("title", "Data Quality Improvement"),
                        description=rec_data.get("description", ""),
                        action_items=rec_data.get("action_items", []),
                        estimated_impact=rec_data.get("estimated_impact", "Medium")
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.error(f"Error parsing recommendation: {str(e)}")
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error parsing AI recommendations: {str(e)}")
            return []
    
    def _generate_fallback_recommendations(self, profile: DataProfile) -> List[AIRecommendation]:
        """Generate fallback recommendations when AI is not available"""
        recommendations = []
        
        # Basic recommendations based on profile analysis
        if profile.duplicate_percentage > 10:
            recommendations.append(AIRecommendation(
                category="data_cleaning",
                priority="high",
                title="Remove Duplicate Data",
                description=f"High duplicate rate ({profile.duplicate_percentage:.1f}%) detected",
                action_items=[
                    "Implement duplicate detection and removal processes",
                    "Set up data validation rules to prevent future duplicates",
                    "Consider using unique identifiers for data deduplication"
                ],
                estimated_impact="High - Will improve data accuracy and reduce storage costs"
            ))
        
        high_missing_cols = [col for col in profile.columns if col.missing_percentage > 30]
        if high_missing_cols:
            recommendations.append(AIRecommendation(
                category="data_cleaning",
                priority="medium",
                title="Address Missing Values",
                description=f"{len(high_missing_cols)} columns have significant missing values",
                action_items=[
                    "Investigate root causes of missing data",
                    "Implement data imputation strategies",
                    "Set up data quality monitoring for missing values"
                ],
                estimated_impact="Medium - Will improve data completeness"
            ))
        
        mixed_type_cols = [col for col in profile.columns if col.data_type.value == "mixed"]
        if mixed_type_cols:
            recommendations.append(AIRecommendation(
                category="data_standardization",
                priority="high",
                title="Standardize Data Types",
                description=f"{len(mixed_type_cols)} columns have mixed data types",
                action_items=[
                    "Implement data type validation rules",
                    "Create data transformation pipelines",
                    "Set up automated data type detection"
                ],
                estimated_impact="High - Will prevent analysis errors"
            ))
        
        # Always include monitoring recommendation
        recommendations.append(AIRecommendation(
            category="monitoring",
            priority="medium",
            title="Implement Data Quality Monitoring",
            description="Set up comprehensive data quality monitoring",
            action_items=[
                "Create data quality dashboards",
                "Set up automated alerts for quality issues",
                "Implement regular data quality assessments"
            ],
            estimated_impact="Medium - Will help maintain data quality over time"
        ))
        
        return recommendations
    
    def enhance_recommendations_with_ai(self, base_recommendations: List[AIRecommendation], profile: DataProfile) -> List[AIRecommendation]:
        """Enhance existing recommendations with AI insights"""
        try:
            if not self.client:
                return base_recommendations
            
            # Create context for enhancement
            context = f"""
            Current recommendations for data quality improvement:
            """
            
            for i, rec in enumerate(base_recommendations, 1):
                context += f"""
            {i}. {rec.title} (Priority: {rec.priority})
               Category: {rec.category}
               Description: {rec.description}
               Action Items: {', '.join(rec.action_items)}
               Estimated Impact: {rec.estimated_impact}
            """
            
            context += f"""
            
            Data Profile Summary:
            - File: {profile.file_name}
            - Rows: {profile.row_count}, Columns: {profile.column_count}
            - Duplicate Rate: {profile.duplicate_percentage:.1f}%
            - Quality Issues: {len(profile.quality_issues)}
            
            Please enhance these recommendations with additional insights, specific action items, and priority adjustments based on the data profile.
            """
            
            enhanced_response = self._call_openai_api(context)
            enhanced_recommendations = self._parse_ai_recommendations(enhanced_response)
            
            # Combine base and enhanced recommendations
            all_recommendations = base_recommendations + enhanced_recommendations
            
            # Remove duplicates and sort by priority
            unique_recommendations = self._deduplicate_recommendations(all_recommendations)
            
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"Error enhancing recommendations: {str(e)}")
            return base_recommendations
    
    def _deduplicate_recommendations(self, recommendations: List[AIRecommendation]) -> List[AIRecommendation]:
        """Remove duplicate recommendations and sort by priority"""
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        
        # Create unique recommendations based on title
        unique_recs = {}
        for rec in recommendations:
            if rec.title not in unique_recs:
                unique_recs[rec.title] = rec
            else:
                # Keep the one with higher priority
                existing_priority = priority_order.get(unique_recs[rec.title].priority, 0)
                new_priority = priority_order.get(rec.priority, 0)
                if new_priority > existing_priority:
                    unique_recs[rec.title] = rec
        
        # Sort by priority
        sorted_recs = sorted(
            unique_recs.values(),
            key=lambda x: priority_order.get(x.priority, 0),
            reverse=True
        )
        
        return sorted_recs 
