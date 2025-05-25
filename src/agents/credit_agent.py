
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.risk_models import CreditProfile, CompanyInfo, FinancialMetrics
from ..integrations.quex_oracle import QUEXOracle
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)

class CreditAnalysisAgent:
    """
    Credit Analysis Agent - Primary Financial Data Analyst
    
    Responsibilities:
    - Monitor financial markets through QUEX Oracle
    - Analyze creditworthiness using multiple data sources
    - Generate comprehensive financial health reports
    - Provide confidence intervals for assessments
    """
    
    def __init__(self):
        self.quex_oracle = QUEXOracle()
        genai.configure(api_key=settings.GEMINI_AI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.name = "Credit Analysis Agent"
        
    async def analyze_credit(self, company_info: CompanyInfo) -> Dict[str, Any]:
        """
        Perform comprehensive credit analysis for a company
        
        Args:
            company_info: Company information to analyze
            
        Returns:
            Credit analysis results with score and insights
        """
        try:
            logger.info(f"Starting credit analysis for {company_info.name}")
            
            # Get real-time financial data from QUEX Oracle
            quex_data = await self.quex_oracle.get_company_profile(company_info.tax_id)
            
            # Calculate base credit score
            credit_score = self._calculate_credit_score(quex_data)
            
            # Get AI-powered insights
            ai_insights = await self._get_ai_insights(company_info, quex_data)
            
            # Build financial metrics
            financial_metrics = FinancialMetrics(
                revenue=quex_data.get('revenue', 0),
                growth_rate=quex_data.get('growth_rate', 0),
                net_margin=quex_data.get('net_margin', 0),
                current_ratio=quex_data.get('current_ratio', 1.0),
                debt_to_equity=quex_data.get('debt_to_equity', 0),
                cash_reserves=quex_data.get('cash_reserves', 0)
            )
            
            # Create credit profile
            credit_profile = CreditProfile(
                credit_score=credit_score,
                rating=self._get_rating_from_score(credit_score),
                financial_metrics=financial_metrics,
                payment_history_score=quex_data.get('payment_history_score', 0),
                on_time_payment_rate=quex_data.get('on_time_rate', 0),
                late_payments_count=quex_data.get('late_payments', 0),
                default_history=quex_data.get('default_history', []),
                banking_relationships=quex_data.get('banking_relationships', {})
            )
            
            result = {
                'credit_profile': credit_profile,
                'confidence': ai_insights.get('confidence', 0.85),
                'insights': ai_insights.get('insights', ''),
                'risk_factors': ai_insights.get('risk_factors', []),
                'recommendations': ai_insights.get('recommendations', [])
            }
            
            logger.info(f"Credit analysis completed for {company_info.name} - Score: {credit_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error in credit analysis: {str(e)}")
            # Return default low-confidence result
            return self._get_default_credit_result()
    
    def _calculate_credit_score(self, quex_data: Dict[str, Any]) -> int:
        """Calculate credit score based on QUEX Oracle data"""
        base_score = 300
        
        # Payment history (35% weight)
        payment_score = quex_data.get('payment_history_score', 50)
        base_score += int(payment_score * 0.35 * 7)  # Scale to contribute ~245 points max
        
        # Financial health (30% weight)
        revenue = quex_data.get('revenue', 0)
        growth_rate = quex_data.get('growth_rate', 0)
        if revenue > 1000000:  # $1M+ revenue
            base_score += 50
        if growth_rate > 10:  # 10%+ growth
            base_score += 40
            
        # Credit utilization (20% weight)
        utilization = quex_data.get('credit_utilization', 50)
        if utilization < 30:
            base_score += 100
        elif utilization < 60:
            base_score += 50
            
        # Credit history length (10% weight)
        history_length = quex_data.get('credit_history_months', 12)
        if history_length > 60:  # 5+ years
            base_score += 50
            
        # Credit mix (5% weight)
        credit_types = quex_data.get('credit_types', 1)
        if credit_types >= 3:
            base_score += 25
            
        return min(850, max(300, base_score))
    
    def _get_rating_from_score(self, score: int) -> str:
        """Convert numeric score to letter rating"""
        if score >= 800:
            return "AAA"
        elif score >= 750:
            return "AA"
        elif score >= 700:
            return "A"
        elif score >= 650:
            return "BBB"
        elif score >= 600:
            return "BB"
        elif score >= 550:
            return "B"
        else:
            return "CCC"
    
    async def _get_ai_insights(self, company_info: CompanyInfo, quex_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered insights using Gemini"""
        try:
            prompt = f"""
            Analyze the following company financial data and provide insights:
            
            Company: {company_info.name}
            Industry: {company_info.industry}
            Location: {company_info.location}
            
            Financial Data:
            - Revenue: ${quex_data.get('revenue', 0):,}
            - Growth Rate: {quex_data.get('growth_rate', 0)}%
            - Payment History Score: {quex_data.get('payment_history_score', 0)}
            - On-time Payment Rate: {quex_data.get('on_time_rate', 0)}%
            - Late Payments: {quex_data.get('late_payments', 0)}
            
            Provide analysis in JSON format with:
            1. confidence (0-1 scale)
            2. insights (detailed analysis)
            3. risk_factors (list of concerns)
            4. recommendations (list of suggestions)
            """
            
            response = await self.model.generate_content_async(prompt)
            
            # Parse AI response (simplified - in production, use better JSON parsing)
            insights = {
                'confidence': 0.85,
                'insights': response.text,
                'risk_factors': self._extract_risk_factors(response.text),
                'recommendations': self._extract_recommendations(response.text)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting AI insights: {str(e)}")
            return {
                'confidence': 0.60,
                'insights': "AI analysis unavailable - using default assessment",
                'risk_factors': ["AI analysis unavailable"],
                'recommendations': ["Manual review recommended"]
            }
    
    def _extract_risk_factors(self, ai_response: str) -> List[str]:
        """Extract risk factors from AI response"""
        # Simplified extraction - in production, use better NLP
        risk_keywords = ['risk', 'concern', 'negative', 'decline', 'poor', 'low']
        factors = []
        
        for line in ai_response.split('\n'):
            if any(keyword in line.lower() for keyword in risk_keywords):
                factors.append(line.strip())
                
        return factors[:5]  # Limit to top 5
    
    def _extract_recommendations(self, ai_response: str) -> List[str]:
        """Extract recommendations from AI response"""
        # Simplified extraction - in production, use better NLP
        rec_keywords = ['recommend', 'suggest', 'should', 'consider', 'improve']
        recommendations = []
        
        for line in ai_response.split('\n'):
            if any(keyword in line.lower() for keyword in rec_keywords):
                recommendations.append(line.strip())
                
        return recommendations[:5]  # Limit to top 5
    
    def _get_default_credit_result(self) -> Dict[str, Any]:
        """Return default result when analysis fails"""
        default_metrics = FinancialMetrics(
            revenue=0,
            growth_rate=0,
            net_margin=0,
            current_ratio=1.0,
            debt_to_equity=0,
            cash_reserves=0
        )
        
        default_profile = CreditProfile(
            credit_score=500,
            rating="BBB",
            financial_metrics=default_metrics,
            payment_history_score=50,
            on_time_payment_rate=75,
            late_payments_count=0,
            default_history=[],
            banking_relationships={}
        )
        
        return {
            'credit_profile': default_profile,
            'confidence': 0.40,
            'insights': 'Limited data available for analysis',
            'risk_factors': ['Insufficient data'],
            'recommendations': ['Manual review required']
        }