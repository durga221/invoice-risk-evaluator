import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..models.risk_models import RiskAssessment, RiskLevel, RiskFactor, InvoiceData
from ..integrations.xdc_blockchain import XDCBlockchain
import google.generativeai as genai
import numpy as np
from config.settings import settings

logger = logging.getLogger(__name__)

class RiskScoringAgent:
    """
    Risk Scoring Agent - Master Risk Calculator
    
    Responsibilities:
    - Synthesize data from all agents
    - Apply advanced ML models
    - Update XDC blockchain with assessments
    - Maintain decision transparency
    """
    
    def __init__(self):
        self.xdc_blockchain = XDCBlockchain()
        genai.configure(api_key=settings.GEMINI_AI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.name = "Risk Scoring Agent"
        
    async def synthesize_risk(
        self,
        invoice_data: InvoiceData,
        credit_analysis: Dict[str, Any],
        identity_verification: Dict[str, Any],
        market_intelligence: Dict[str, Any]
    ) -> RiskAssessment:
        """
        Synthesize all agent data into comprehensive risk assessment
        
        Args:
            invoice_data: Invoice information
            credit_analysis: Results from Credit Analysis Agent
            identity_verification: Results from Identity Verification Agent
            market_intelligence: Results from Market Intelligence Agent
            
        Returns:
            Complete risk assessment with blockchain record
        """
        try:
            logger.info(f"Synthesizing risk assessment for invoice {invoice_data.id}")
            
            # Calculate individual risk scores
            credit_score = self._calculate_credit_risk_score(credit_analysis)
            identity_score = self._calculate_identity_risk_score(identity_verification)
            market_score = self._calculate_market_risk_score(market_intelligence)
            invoice_score = self._calculate_invoice_risk_score(invoice_data)
            
            # Calculate weighted overall score
            weights = {
                'credit': 0.40,    # 40% weight - most important
                'identity': 0.25,  # 25% weight
                'market': 0.20,    # 20% weight
                'invoice': 0.15    # 15% weight
            }
            
            overall_score = (
                credit_score * weights['credit'] +
                identity_score * weights['identity'] +
                market_score * weights['market'] +
                invoice_score * weights['invoice']
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_score)
            
            # Build risk factors
            risk_factors = self._build_risk_factors(
                credit_analysis, identity_verification, 
                market_intelligence, invoice_data, weights
            )
            
            # Get AI reasoning
            ai_reasoning = await self._get_ai_reasoning(
                invoice_data, overall_score, risk_factors
            )
            
            # Generate recommendations
            recommendation = self._generate_recommendation(overall_score, risk_level)
            
            # Suggest terms
            suggested_terms = self._suggest_terms(overall_score, invoice_data)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                credit_analysis, identity_verification, market_intelligence
            )
            
            # Store on blockchain
            blockchain_record = await self._store_on_blockchain(
                invoice_data.id, overall_score, risk_factors
            )
            
            # Create risk assessment
            risk_assessment = RiskAssessment(
                invoice_id=invoice_data.id,
                overall_score=int(overall_score),
                risk_level=risk_level,
                confidence=confidence,
                recommendation=recommendation,
                factors=risk_factors,
                ai_reasoning=ai_reasoning,
                suggested_terms=suggested_terms,
                blockchain_record=blockchain_record
            )
            
            logger.info(f"Risk assessment completed - Score: {int(overall_score)}, Level: {risk_level}")
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error in risk synthesis: {str(e)}")
            return self._get_default_risk_assessment(invoice_data)
    
    def _calculate_credit_risk_score(self, credit_analysis: Dict[str, Any]) -> float:
        """Convert credit analysis to risk score (0-100, lower is better)"""
        credit_profile = credit_analysis.get('credit_profile')
        if not credit_profile:
            return 70.0  # High risk if no data
            
        credit_score = credit_profile.credit_score
        
        # Convert credit score (300-850) to risk score (0-100)
        # Higher credit score = lower risk
        if credit_score >= 750:
            return 10.0  # Very low risk
        elif credit_score >= 700:
            return 20.0  # Low risk
        elif credit_score >= 650:
            return 35.0  # Medium risk
        elif credit_score >= 600:
            return 50.0  # Medium-high risk
        elif credit_score >= 550:
            return 70.0  # High risk
        else:
            return 85.0  # Very high risk
    
    def _calculate_identity_risk_score(self, identity_verification: Dict[str, Any]) -> float:
        """Convert identity verification to risk score"""
        identity_data = identity_verification.get('identity_verification')
        if not identity_data:
            return 80.0  # High risk if no verification
            
        trust_score = identity_data.trust_score  # 0-100
        risk_flags_count = len(identity_data.risk_flags)
        
        # Convert trust score to risk score (inverse relationship)
        base_risk = 100 - trust_score
        
        # Add penalties for risk flags
        flag_penalty = min(risk_flags_count * 10, 30)
        
        return min(100, base_risk + flag_penalty)
    
    def _calculate_market_risk_score(self, market_intelligence: Dict[str, Any]) -> float:
        """Convert market intelligence to risk score"""
        market_data = market_intelligence.get('market_intelligence')
        if not market_data:
            return 60.0  # Medium risk if no data
            
        risk_score = 50.0  # Base score
        
        # Adjust for industry growth
        growth_rate = market_data.industry_growth_rate
        if growth_rate > 10:
            risk_score -= 15
        elif growth_rate > 5:
            risk_score -= 10
        elif growth_rate < 0:
            risk_score += 20
            
        # Adjust for market volatility
        volatility = market_data.market_volatility
        if volatility == 'Low':
            risk_score -= 10
        elif volatility == 'High':
            risk_score += 15
            
        # Adjust for economic outlook
        outlook = market_data.economic_outlook
        if outlook == 'Positive':
            risk_score -= 10
        elif outlook == 'Negative':
            risk_score += 15
            
        # Adjust for geographic risk
        geo_risk = market_data.geographic_risk_score
        risk_score += (geo_risk - 50) * 0.3  # Scale geographic risk
        
        return max(0, min(100, risk_score))
    
    def _calculate_invoice_risk_score(self, invoice_data: InvoiceData) -> float:
        """Calculate risk score based on invoice characteristics"""
        risk_score = 30.0  # Base score
        
        # Amount-based risk
        if invoice_data.amount > 500000:  # $500K+
            risk_score += 15
        elif invoice_data.amount > 100000:  # $100K+
            risk_score += 10
        elif invoice_data.amount < 10000:  # Less than $10K
            risk_score += 5
            
        # Payment terms risk
        if "60" in invoice_data.payment_terms or "90" in invoice_data.payment_terms:
            risk_score += 10
        elif "Net 30" in invoice_data.payment_terms:
            risk_score += 0  # Standard terms
        elif "15" in invoice_data.payment_terms:
            risk_score -= 5  # Shorter terms, lower risk
            
        # Due date risk (how far in future)
        days_to_due = (invoice_data.due_date - datetime.now()).days
        if days_to_due > 90:
            risk_score += 15
        elif days_to_due > 60:
            risk_score += 10
        elif days_to_due < 15:
            risk_score += 5  # Too short might indicate distress
            
        return max(0, min(100, risk_score))
    
    def _determine_risk_level(self, overall_score: float) -> RiskLevel:
        """Determine risk level from overall score"""
        if overall_score <= 20:
            return RiskLevel.VERY_LOW
        elif overall_score <= 35:
            return RiskLevel.LOW
        elif overall_score <= 55:
            return RiskLevel.MEDIUM
        elif overall_score <= 75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _build_risk_factors(
        self,
        credit_analysis: Dict[str, Any],
        identity_verification: Dict[str, Any],
        market_intelligence: Dict[str, Any],
        invoice_data: InvoiceData,
        weights: Dict[str, float]
    ) -> List[RiskFactor]:
        """Build detailed risk factors"""
        factors = []
        
        # Credit factor
        credit_profile = credit_analysis.get('credit_profile')
        if credit_profile:
            credit_score = self._calculate_credit_risk_score(credit_analysis)
            factors.append(RiskFactor(
                name="Credit Worthiness",
                score=credit_score,
                weight=weights['credit'],
                impact="POSITIVE" if credit_score < 35 else "NEGATIVE" if credit_score > 55 else "NEUTRAL",
                description=f"Credit score: {credit_profile.credit_score}, Payment history: {credit_profile.on_time_payment_rate}%"
            ))
        
        # Identity factor
        identity_data = identity_verification.get('identity_verification')
        if identity_data:
            identity_score = self._calculate_identity_risk_score(identity_verification)
            factors.append(RiskFactor(
                name="Identity Verification",
                score=identity_score,
                weight=weights['identity'],
                impact="POSITIVE" if identity_score < 35 else "NEGATIVE" if identity_score > 55 else "NEUTRAL",
                description=f"Trust score: {identity_data.trust_score}, KYC level: {identity_data.kyc_level}"
            ))
        
        # Market factor
        market_data = market_intelligence.get('market_intelligence')
        if market_data:
            market_score = self._calculate_market_risk_score(market_intelligence)
            factors.append(RiskFactor(
                name="Market Conditions",
                score=market_score,
                weight=weights['market'],
                impact="POSITIVE" if market_score < 35 else "NEGATIVE" if market_score > 55 else "NEUTRAL",
                description=f"Industry growth: {market_data.industry_growth_rate}%, Outlook: {market_data.economic_outlook}"
            ))
        
        # Invoice factor
        invoice_score = self._calculate_invoice_risk_score(invoice_data)
        factors.append(RiskFactor(
            name="Invoice Characteristics",
            score=invoice_score,
            weight=weights['invoice'],
            impact="POSITIVE" if invoice_score < 35 else "NEGATIVE" if invoice_score > 55 else "NEUTRAL",
            description=f"Amount: ${invoice_data.amount:,}, Terms: {invoice_data.payment_terms}"
        ))
        
        return factors
    
    async def _get_ai_reasoning(
        self,
        invoice_data: InvoiceData,
        overall_score: float,
        risk_factors: List[RiskFactor]
    ) -> str:
        """Get AI-powered reasoning for the risk assessment"""
        try:
            factor_summary = "\n".join([
                f"- {factor.name}: {factor.score:.1f} ({factor.impact})"
                for factor in risk_factors
            ])
            
            prompt = f"""
            Explain the risk assessment decision for this invoice:
            
            Invoice Details:
            - Company: {invoice_data.buyer_info.name}
            - Amount: ${invoice_data.amount:,}
            - Industry: {invoice_data.buyer_info.industry}
            - Payment Terms: {invoice_data.payment_terms}
            
            Risk Factors:
            {factor_summary}
            
            Overall Risk Score: {overall_score:.1f}/100
            
            Provide a clear, concise explanation of why this risk score was assigned,
            highlighting the key factors that influenced the decision.
            """
            
            response = await self.model.generate_content_async(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting AI reasoning: {str(e)}")
            return f"Risk score of {overall_score:.1f} based on weighted analysis of credit, identity, market, and invoice factors."
    
    def _generate_recommendation(self, overall_score: float, risk_level: RiskLevel) -> str:
        """Generate recommendation based on risk score"""
        if risk_level == RiskLevel.VERY_LOW:
            return "APPROVE - Excellent risk profile, standard terms recommended"
        elif risk_level == RiskLevel.LOW:
            return "APPROVE - Good risk profile, standard terms acceptable"
        elif risk_level == RiskLevel.MEDIUM:
            return "APPROVE WITH CONDITIONS - Moderate risk, consider enhanced terms"
        elif risk_level == RiskLevel.HIGH:
            return "REVIEW REQUIRED - High risk, manual assessment recommended"
        else:
            return "DECLINE - Very high risk, recommend rejection"
    
    def _suggest_terms(self, overall_score: float, invoice_data: InvoiceData) -> Dict[str, Any]:
        """Suggest financing terms based on risk score"""
        base_rate = 8.0  # Base interest rate
        
        # Adjust rate based on risk
        if overall_score <= 20:
            interest_rate = base_rate + 0.5
            collateral_required = False
        elif overall_score <= 35:
            interest_rate = base_rate + 1.0
            collateral_required = False
        elif overall_score <= 55:
            interest_rate = base_rate + 2.0
            collateral_required = False
        elif overall_score <= 75:
            interest_rate = base_rate + 4.0
            collateral_required = True
        else:
            interest_rate = base_rate + 8.0
            collateral_required = True
        
        # Calculate credit limit (based on amount and risk)
        base_limit = invoice_data.amount * 2
        if overall_score > 55:
            credit_limit = int(base_limit * 0.5)
        elif overall_score > 35:
            credit_limit = int(base_limit * 0.75)
        else:
            credit_limit = int(base_limit)
        
        return {
            "interest_rate": round(interest_rate, 2),
            "collateral_required": collateral_required,
            "credit_limit": credit_limit,
            "payment_terms": invoice_data.payment_terms,
            "advance_rate": min(90, max(70, 100 - overall_score)) # % of invoice value to advance
        }
    
    def _calculate_confidence(
        self,
        credit_analysis: Dict[str, Any],
        identity_verification: Dict[str, Any],
        market_intelligence: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence in the assessment"""
        confidences = []
        
        if credit_analysis.get('confidence'):
            confidences.append(credit_analysis['confidence'])
        if identity_verification.get('confidence'):
            confidences.append(identity_verification['confidence'])
        if market_intelligence.get('confidence'):
            confidences.append(market_intelligence['confidence'])
            
        if confidences:
            return sum(confidences) / len(confidences)
        else:
            return 0.60  # Default confidence
    
    async def _store_on_blockchain(
        self,
        invoice_id: str,
        risk_score: float,
        risk_factors: List[RiskFactor]
    ) -> Optional[str]:
        """Store risk assessment on XDC blockchain"""
        try:
            tx_hash = await self.xdc_blockchain.store_risk_assessment({
                'invoice_id': invoice_id,
                'risk_score': int(risk_score),
                'timestamp': int(datetime.now().timestamp()),
                'factors_count': len(risk_factors)
            })
            return tx_hash
        except Exception as e:
            logger.error(f"Error storing on blockchain: {str(e)}")
            return None
    
    def _get_default_risk_assessment(self, invoice_data: InvoiceData) -> RiskAssessment:
        """Return default risk assessment when synthesis fails"""
        default_factors = [
            RiskFactor(
                name="System Error",
                score=60.0,
                weight=1.0,
                impact="NEUTRAL",
                description="Unable to complete full risk analysis"
            )
        ]
        
        return RiskAssessment(
            invoice_id=invoice_data.id,
            overall_score=60,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.40,
            recommendation="MANUAL REVIEW REQUIRED - System analysis incomplete",
            factors=default_factors,
            ai_reasoning="Automated risk assessment unavailable, manual review recommended",
            suggested_terms={
                "interest_rate": 12.0,
                "collateral_required": True,
                "credit_limit": int(invoice_data.amount),
                "payment_terms": invoice_data.payment_terms,
                "advance_rate": 70
            },
            blockchain_record=None
        )
