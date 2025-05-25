
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CreditProfile:
    """Credit profile data structure"""
    overall_score: int
    rating_agency: str
    financial_health: Dict[str, Any]
    payment_history: Dict[str, Any]
    market_data: Dict[str, Any]
    banking_relationships: Dict[str, Any]

@dataclass
class MarketIntelligence:
    """Market intelligence data structure"""
    sector_health: Dict[str, Any]
    geographic_risk: Dict[str, Any]
    supply_chain_factors: Dict[str, Any]

class QUEXOracle:
    """
    QUEX Oracle integration for real-time financial data
    Provides credit analysis and market intelligence
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.quex.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self._rate_limit_delay = 0.1  # 100ms between requests
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "InvoiceRiskEvaluator/1.0"
            },
            timeout=30.0
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to QUEX API"""
        if not self.session:
            raise RuntimeError("QUEXOracle session not initialized. Use async context manager.")
        
        try:
            await asyncio.sleep(self._rate_limit_delay)  # Rate limiting
            response = await self.session.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"QUEX API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"QUEX API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"QUEX Oracle request error: {str(e)}")
            raise
    
    async def get_credit_profile(self, company_id: str, tax_id: Optional[str] = None) -> CreditProfile:
        """Get comprehensive credit profile for a company"""
        params = {"company_id": company_id}
        if tax_id:
            params["tax_id"] = tax_id
            
        try:
            data = await self._make_request("credit/profile", params)
            
            return CreditProfile(
                overall_score=data.get("overall_score", 0),
                rating_agency=data.get("rating_agency", "N/A"),
                financial_health={
                    "revenue": {
                        "current": data.get("revenue", {}).get("current", 0),
                        "growth": data.get("revenue", {}).get("growth_rate", 0),
                        "consistency": data.get("revenue", {}).get("consistency", "UNKNOWN")
                    },
                    "profitability": {
                        "net_margin": data.get("profitability", {}).get("net_margin", 0),
                        "gross_margin": data.get("profitability", {}).get("gross_margin", 0),
                        "trend": data.get("profitability", {}).get("trend", "STABLE")
                    },
                    "liquidity": {
                        "current_ratio": data.get("liquidity", {}).get("current_ratio", 0),
                        "quick_ratio": data.get("liquidity", {}).get("quick_ratio", 0),
                        "cash_reserves": data.get("liquidity", {}).get("cash_reserves", 0)
                    }
                },
                payment_history={
                    "on_time_rate": data.get("payment_history", {}).get("on_time_rate", 0),
                    "average_payment_days": data.get("payment_history", {}).get("avg_days", 0),
                    "late_payments": data.get("payment_history", {}).get("late_count", 0),
                    "default_history": data.get("payment_history", {}).get("defaults", [])
                },
                market_data={
                    "industry_growth": data.get("market_data", {}).get("industry_growth", 0),
                    "competitive_position": data.get("market_data", {}).get("position", "UNKNOWN"),
                    "market_volatility": data.get("market_data", {}).get("volatility", "UNKNOWN")
                },
                banking_relationships={
                    "primary_bank": data.get("banking", {}).get("primary_bank", "Unknown"),
                    "credit_lines": data.get("banking", {}).get("credit_lines", 0),
                    "utilization": data.get("banking", {}).get("utilization_rate", 0)
                }
            )
        except Exception as e:
            logger.error(f"Failed to get credit profile for {company_id}: {str(e)}")
            raise
    
    async def get_market_intelligence(self, industry: str, location: str) -> MarketIntelligence:
        """Get market intelligence for specific industry and location"""
        params = {
            "industry": industry,
            "location": location,
            "include_forecasts": True
        }
        
        try:
            data = await self._make_request("market/intelligence", params)
            
            return MarketIntelligence(
                sector_health={
                    industry: {
                        "growth_rate": data.get("sector", {}).get("growth_rate", 0),
                        "outlook": data.get("sector", {}).get("outlook", "NEUTRAL"),
                        "key_trends": data.get("sector", {}).get("trends", [])
                    }
                },
                geographic_risk={
                    location.lower(): {
                        "political_stability": data.get("geographic", {}).get("political_score", 50),
                        "economic_growth": data.get("geographic", {}).get("gdp_growth", 0),
                        "currency_stability": data.get("geographic", {}).get("currency_risk", "MEDIUM")
                    }
                },
                supply_chain_factors={
                    "disruption": data.get("supply_chain", {}).get("disruption_level", "MEDIUM"),
                    "cost_pressures": data.get("supply_chain", {}).get("cost_pressure", "MEDIUM"),
                    "availability": data.get("supply_chain", {}).get("availability", "GOOD")
                }
            )
        except Exception as e:
            logger.error(f"Failed to get market intelligence for {industry}/{location}: {str(e)}")
            raise
    
    async def get_payment_prediction(self, company_id: str, amount: float, terms: int) -> Dict[str, Any]:
        """Get payment probability prediction"""
        params = {
            "company_id": company_id,
            "amount": amount,
            "payment_terms": terms
        }
        
        try:
            data = await self._make_request("predict/payment", params)
            return {
                "probability_on_time": data.get("on_time_probability", 0.5),
                "probability_30_days": data.get("late_30_probability", 0.3),
                "probability_60_days": data.get("late_60_probability", 0.15),
                "probability_default": data.get("default_probability", 0.05),
                "confidence_score": data.get("confidence", 0.7),
                "risk_factors": data.get("risk_factors", [])
            }
        except Exception as e:
            logger.error(f"Failed to get payment prediction for {company_id}: {str(e)}")
            raise
    
    async def get_real_time_updates(self, company_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get real-time updates for multiple companies"""
        params = {"company_ids": ",".join(company_ids)}
        
        try:
            data = await self._make_request("realtime/updates", params)
            return data.get("updates", {})
        except Exception as e:
            logger.error(f"Failed to get real-time updates: {str(e)}")
            raise