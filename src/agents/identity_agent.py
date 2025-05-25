import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.risk_models import IdentityVerification, CompanyInfo
from ..integrations.civic_auth import CivicAuth
from config.settings import settings

logger = logging.getLogger(__name__)

class IdentityVerificationAgent:
    """
    Identity Verification Agent - Digital Identity Specialist
    
    Responsibilities:
    - Authenticate users via Civic Auth
    - Create and manage embedded wallets
    - Ensure regulatory compliance
    - Monitor for suspicious activities
    """
    
    def __init__(self):
        self.civic_auth = CivicAuth()
        self.name = "Identity Verification Agent"
        
    async def verify_identity(self, company_info: CompanyInfo) -> Dict[str, Any]:
        """
        Perform comprehensive identity verification for a company
        
        Args:
            company_info: Company information to verify
            
        Returns:
            Identity verification results with trust score
        """
        try:
            logger.info(f"Starting identity verification for {company_info.name}")
            
            # Perform Civic Auth verification
            civic_result = await self.civic_auth.verify_business(
                company_name=company_info.name,
                tax_id=company_info.tax_id,
                registration_location=company_info.location
            )
            
            # Calculate trust score
            trust_score = self._calculate_trust_score(civic_result)
            
            # Create embedded wallet if verification successful
            wallet_address = None
            if civic_result.get('verified', False):
                wallet_address = await self.civic_auth.create_embedded_wallet(
                    company_id=company_info.tax_id
                )
            
            # Check for risk flags
            risk_flags = self._assess_risk_flags(civic_result, company_info)
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(civic_result)
            
            # Build identity verification result
            identity_verification = IdentityVerification(
                verified=civic_result.get('verified', False),
                kyc_level=civic_result.get('kyc_level', 'BASIC'),
                trust_score=trust_score,
                compliance_score=compliance_score,
                document_verification=civic_result.get('document_verification', {}),
                wallet_address=wallet_address,
                risk_flags=risk_flags
            )
            
            result = {
                'identity_verification': identity_verification,
                'confidence': civic_result.get('confidence', 0.85),
                'verification_details': civic_result,
                'fraud_assessment': self._assess_fraud_risk(civic_result)
            }
            
            logger.info(f"Identity verification completed for {company_info.name} - Trust Score: {trust_score}")
            return result
            
        except Exception as e:
            logger.error(f"Error in identity verification: {str(e)}")
            return self._get_default_identity_result()
    
    def _calculate_trust_score(self, civic_result: Dict[str, Any]) -> int:
        """Calculate trust score based on Civic Auth results"""
        base_score = 0
        
        # Document verification (40% weight)
        doc_verification = civic_result.get('document_verification', {})
        verified_docs = sum(1 for verified in doc_verification.values() if verified)
        total_docs = len(doc_verification) or 1
        doc_score = (verified_docs / total_docs) * 40
        base_score += doc_score
        
        # KYC level (30% weight)
        kyc_level = civic_result.get('kyc_level', 'NONE')
        kyc_scores = {'FULL': 30, 'ENHANCED': 25, 'BASIC': 15, 'NONE': 0}
        base_score += kyc_scores.get(kyc_level, 0)
        
        # Verification confidence (20% weight)
        confidence = civic_result.get('confidence', 0.5)
        base_score += confidence * 20
        
        # Historical performance (10% weight)
        history_score = civic_result.get('history_score', 50)
        base_score += (history_score / 100) * 10
        
        return min(100, max(0, int(base_score)))
    
    def _calculate_compliance_score(self, civic_result: Dict[str, Any]) -> int:
        """Calculate compliance score based on regulatory requirements"""
        base_score = 0
        
        # AML compliance
        if civic_result.get('aml_compliant', False):
            base_score += 25
            
        # KYC compliance
        if civic_result.get('kyc_compliant', False):
            base_score += 25
            
        # Document authenticity
        if civic_result.get('documents_authentic', False):
            base_score += 25
            
        # Sanctions check
        if civic_result.get('sanctions_clear', False):
            base_score += 25
            
        return min(100, max(0, base_score))
    
    def _assess_risk_flags(self, civic_result: Dict[str, Any], company_info: CompanyInfo) -> List[str]:
        """Assess and return risk flags"""
        flags = []
        
        # Document-related flags
        if not civic_result.get('documents_authentic', True):
            flags.append("Document authenticity concerns")
            
        # Sanctions-related flags
        if civic_result.get('sanctions_hit', False):
            flags.append("Sanctions list match found")
            
        # Age-related flags
        if company_info.registration_date:
            days_since_registration = (datetime.now() - company_info.registration_date).days
            if days_since_registration < 90:
                flags.append("Recently registered company")
                
        # Location-related flags
        high_risk_locations = ['afghanistan', 'north korea', 'iran', 'syria']
        if any(location in company_info.location.lower() for location in high_risk_locations):
            flags.append("High-risk geographic location")
            
        # Verification flags
        if civic_result.get('confidence', 1.0) < 0.70:
            flags.append("Low verification confidence")
            
        return flags
    
    def _assess_fraud_risk(self, civic_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess fraud risk based on verification results"""
        risk_score = 0
        risk_factors = []
        
        # Document inconsistencies
        if civic_result.get('document_inconsistencies', 0) > 0:
            risk_score += 20
            risk_factors.append("Document inconsistencies detected")
            
        # Verification mismatches
        if civic_result.get('verification_mismatches', 0) > 0:
            risk_score += 15
            risk_factors.append("Verification data mismatches")
            
        # Suspicious patterns
        if civic_result.get('suspicious_patterns', False):
            risk_score += 25
            risk_factors.append("Suspicious activity patterns")
            
        # Determine risk level
        if risk_score >= 50:
            risk_level = "High"
        elif risk_score >= 25:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        return {
            'fraud_risk_score': risk_score,
            'fraud_risk_level': risk_level,
            'fraud_risk_factors': risk_factors
        }
    
    def _get_default_identity_result(self) -> Dict[str, Any]:
        """Return default result when verification fails"""
        default_verification = IdentityVerification(
            verified=False,
            kyc_level="NONE",
            trust_score=30,
            compliance_score=0,
            document_verification={},
            wallet_address=None,
            risk_flags=["Verification failed"]
        )
        
        return {
            'identity_verification': default_verification,
            'confidence': 0.20,
            'verification_details': {},
            'fraud_assessment': {
                'fraud_risk_score': 50,
                'fraud_risk_level': 'Medium',
                'fraud_risk_factors': ['Verification unavailable']
            }
        }