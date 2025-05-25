import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.risk_models import MarketIntelligence, CompanyInfo
from ..integrations.quex_oracle import QUEXOracle
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)

class MarketIntelligenceAgent:
    """
    Market Intelligence Agent - Economic Trend Analyst
    
    Responsibilities:
    - Monitor global economic indicators
    - Identify risks and opportunities
    - Provide contextual market intelligence
    - Adapt models to market conditions
    """
    
    def __init__(self):
        self.quex_oracle = QUEXOracle()
        genai.configure(api_key=settings.GEMINI_AI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.name = "Market Intelligence Agent"
        
    async def assess_market_conditions(self, company_info: CompanyInfo, invoice_amount: float) -> Dict[str, Any]:
        """
        Assess market conditions affecting invoice risk
        
        Args:
            company_info: Company information
            invoice_amount: Invoice amount for context
            
        Returns:
            Market intelligence analysis
        """
        try:
            logger.info(f"Analyzing market conditions for {company_info.industry} sector")
            
            # Get market data from QUEX Oracle
            market_data = await self.quex_oracle.get_market_intelligence(
                industry=company_info.industry,
                location=company_info.location
            )
            
            # Get AI-powered market insights
            ai_insights = await self._get_market_ai_insights(company_info, market_data, invoice_amount)
            
            # Calculate sector health score
            sector_health = self._calculate_sector_health(market_data)
            
            # Assess economic outlook
            economic_outlook = self._assess_economic_outlook(market_data)
            
            # Build market intelligence
            market_intelligence = MarketIntelligence(
                industry_growth_rate=market_data.get('industry_growth_rate', 0),
                market_volatility=market_data.get('volatility', 'Medium'),
                economic_outlook=economic_outlook,
                sector_health=sector_health,
                geographic_risk_score=market_data.get('geographic_risk_score', 50),
                supply_chain_status=market_data.get('supply_chain_status', 'Stable')
            )
            
            result = {
                'market_intelligence': market_intelligence,
                'confidence': ai_insights.get('confidence', 0.80),
                'market_trends': ai_insights.get('trends', []),
                'risk_factors': ai_insights.get('risk_factors', []),
                'opportunities': ai_insights.get('opportunities', []),
                'recommendations': ai_insights.get('recommendations', [])
            }
            
            logger.info(f"Market analysis completed - Sector Health: {sector_health}")
            return result
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return self._get_default_market_result()
    
    def _calculate_sector_health(self, market_data: Dict[str, Any]) -> str:
        """Calculate overall sector health score"""
        health_score = 0
        
        # Growth rate (40% weight)
        growth_rate = market_data.get('industry_growth_rate', 0)
        if growth_rate > 10:
            health_score += 40
        elif growth_rate > 5:
            health_score += 30
        elif growth_rate > 0:
            health_score += 20
        else:
            health_score += 0
            
        # Market stability (30% weight)
        volatility = market_data.get('volatility', 'High')
        if volatility == 'Low':
            health_score += 30
        elif volatility == 'Medium':
            health_score += 20
        else:
            health_score += 10
            
        # Employment trends (20% weight)
        employment_trend = market_data.get('employment_trend', 'Stable')
        if employment_trend == 'Growing':
            health_score += 20
        elif employment_trend == 'Stable':
            health_score += 15
        else:
            health_score += 5
            
        # Investment flows (10% weight)
        investment_flow = market_data.get('investment_flow', 'Neutral')
        if investment_flow == 'Positive':
            health_score += 10
        elif investment_flow == 'Neutral':
            health_score += 5
            
        # Convert to descriptive rating
        if health_score >= 80:
            return "Excellent"
        elif health_score >= 60:
            return "Good"
        elif health_score >= 40:
            return "Fair"
        else:
            return "Poor"
    
    def _assess_economic_outlook(self, market_data: Dict[str, Any]) -> str:
        """Assess overall economic outlook"""
        outlook_factors = []
        
        # GDP growth
        gdp_growth = market_data.get('gdp_growth', 0)
        if gdp_growth > 3:
            outlook_factors.append('positive')
        elif gdp_growth < 0:
            outlook_factors.append('negative')
        else:
            outlook_factors.append('neutral')
            
        # Determine overall outlook
        positive_count = outlook_factors.count('positive')
        negative_count = outlook_factors.count('negative')
        
        if positive_count > negative_count:
            return "Positive"
        elif negative_count > positive_count:
            return "Negative"
        else:
            return "Neutral"
    
    async def _get_market_ai_insights(self, company_info: CompanyInfo, market_data: Dict[str, Any], invoice_amount: float) -> Dict[str, Any]:
        """Get AI-powered market insights using Gemini"""
        try:
            prompt = f"""
            Analyze the following market conditions for invoice risk assessment:
            
            Company Industry: {company_info.industry}
            Location: {company_info.location}
            Invoice Amount: ${invoice_amount:,}
            
            Market Data:
            - Industry Growth Rate: {market_data.get('industry_growth_rate', 0)}%
            - Market Volatility: {market_data.get('volatility', 'Medium')}
            - GDP Growth: {market_data.get('gdp_growth', 0)}%
            - Inflation Rate: {market_data.get('inflation_rate', 3)}%
            - Employment Trend: {market_data.get('employment_trend', 'Stable')}
            
            Provide analysis focusing on:
            1. Key market trends affecting payment risk
            2. Industry-specific risk factors
            3. Economic opportunities
            4. Risk mitigation recommendations
            
            Format as structured insights.
            """
            
            response = await self.model.generate_content_async(prompt)
            
            insights = {
                'confidence': 0.80,
                'trends': self._extract_trends(response.text),
                'risk_factors': self._extract_market_risks(response.text),
                'opportunities': self._extract_opportunities(response.text),
                'recommendations': self._extract_market_recommendations(response.text)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting market AI insights: {str(e)}")
            return {
                'confidence': 0.60,
                'trends': ["Market analysis unavailable"],
                'risk_factors': ["AI analysis unavailable"],
                'opportunities': [],
                'recommendations': ["Manual market review recommended"]
            }
    
    def _extract_trends(self, ai_response: str) -> List[str]:
        """Extract market trends from AI response"""
        trend_keywords = ['trend', 'growing', 'declining', 'increasing', 'shift']
        trends = []
        
        for line in ai_response.split('\n'):
            if any(keyword in line.lower() for keyword in trend_keywords):
                trends.append(line.strip())
                
        return trends[:5]
    
    def _extract_market_risks(self, ai_response: str) -> List[str]:
        """Extract market risks from AI response"""
        risk_keywords = ['risk', 'threat', 'challenge', 'concern', 'volatility']
        risks = []
        
        for line in ai_response.split('\n'):
            if any(keyword in line.lower() for keyword in risk_keywords):
                risks.append(line.strip())
                
        return risks[:5]
    
    def _extract_opportunities(self, ai_response: str) -> List[str]:
        """Extract opportunities from AI response"""
        opp_keywords = ['opportunity', 'growth', 'potential', 'advantage', 'benefit']
        opportunities = []
        
        for line in ai_response.split('\n'):
            if any(keyword in line.lower() for keyword in opp_keywords):
                opportunities.append(line.strip())
                
        return opportunities[:3]
    
    def _extract_market_recommendations(self, ai_response: str) -> List[str]:
        """Extract market-specific recommendations from AI response"""
        rec_keywords = ['recommend', 'suggest', 'consider', 'monitor', 'hedge']
        recommendations = []
        
        for line in ai_response.split('\n'):
            if any(keyword in line.lower() for keyword in rec_keywords):
                recommendations.append(line.strip())
                
        return recommendations[:5]
    
    def _get_default_market_result(self) -> Dict[str, Any]:
        """Return default result when market analysis fails"""
        default_intelligence = MarketIntelligence(
            industry_growth_rate=2.0,
            market_volatility="Medium",
            economic_outlook="Neutral",
            sector_health="Fair",
            geographic_risk_score=50,
            supply_chain_status="Stable"
        )
        
        return {
            'market_intelligence': default_intelligence,
            'confidence': 0.50,
            'market_trends': ["Limited market data available"],
            'risk_factors': ["Market analysis unavailable"],
            'opportunities': [],
            'recommendations': ["Manual market assessment required"]
        }