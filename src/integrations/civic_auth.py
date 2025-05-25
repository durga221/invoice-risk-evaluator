
import httpx
import asyncio
import jwt
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

logger = logging.getLogger(__name__)

@dataclass
class IdentityVerification:
    """Identity verification result"""
    status: str
    confidence: int
    kyc_level: str
    document_verification: Dict[str, str]
    embedded_wallet: Dict[str, Any]
    risk_flags: List[str]
    compliance_score: int

@dataclass
class EmbeddedWallet:
    """Embedded wallet information"""
    address: str
    created: str
    multi_sig_enabled: bool
    permissions: List[str]

class CivicAuth:
    """
    Civic Auth integration for identity verification and embedded wallets
    Provides KYC, authentication, and wallet management
    """
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://api.civic.com/v1"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            headers={
                "X-API-Key": self.api_key,
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
    
    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Generate HMAC signature for request authentication"""
        message = f"{timestamp}{payload}"
        signature = hashlib.sha256(
            f"{self.api_secret}{message}".encode()
        ).hexdigest()
        return signature
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Civic API"""
        if not self.session:
            raise RuntimeError("CivicAuth session not initialized. Use async context manager.")
        
        timestamp = str(int(datetime.now().timestamp()))
        payload = json.dumps(data) if data else ""
        signature = self._generate_signature(payload, timestamp)
        
        headers = {
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }
        
        try:
            if method.upper() == "GET":
                response = await self.session.get(
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    params=data
                )
            else:
                response = await self.session.request(
                    method.upper(),
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    json=data
                )
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Civic API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Civic API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Civic Auth request error: {str(e)}")
            raise
    
    async def verify_identity(self, user_data: Dict[str, Any]) -> IdentityVerification:
        """Perform comprehensive identity verification"""
        verification_data = {
            "user_id": user_data.get("user_id"),
            "documents": user_data.get("documents", {}),
            "business_info": user_data.get("business_info", {}),
            "verification_level": "FULL_KYC"
        }
        
        try:
            result = await self._make_request("POST", "identity/verify", verification_data)
            
            return IdentityVerification(
                status=result.get("status", "PENDING"),
                confidence=result.get("confidence_score", 0),
                kyc_level=result.get("kyc_level", "BASIC"),
                document_verification={
                    "business_registration": result.get("documents", {}).get("business_reg", "UNVERIFIED"),
                    "tax_id": result.get("documents", {}).get("tax_id", "UNVERIFIED"),
                    "director_ids": result.get("documents", {}).get("director_ids", "UNVERIFIED")
                },
                embedded_wallet=result.get("embedded_wallet", {}),
                risk_flags=result.get("risk_flags", []),
                compliance_score=result.get("compliance_score", 0)
            )
        except Exception as e:
            logger.error(f"Identity verification failed: {str(e)}")
            raise
    
    async def create_embedded_wallet(self, user_id: str, permissions: List[str]) -> EmbeddedWallet:
        """Create embedded wallet for user"""
        wallet_data = {
            "user_id": user_id,
            "wallet_type": "EMBEDDED",
            "permissions": permissions,
            "multi_sig": True,
            "network": "XDC"
        }
        
        try:
            result = await self._make_request("POST", "wallets/create", wallet_data)
            
            return EmbeddedWallet(
                address=result.get("wallet_address", ""),
                created=result.get("created_at", datetime.now().isoformat()),
                multi_sig_enabled=result.get("multi_sig_enabled", False),
                permissions=result.get("permissions", [])
            )
        except Exception as e:
            logger.error(f"Embedded wallet creation failed: {str(e)}")
            raise
    
    async def verify_business_registration(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify business registration documents"""
        verification_data = {
            "business_name": business_data.get("name"),
            "registration_number": business_data.get("registration_number"),
            "tax_id": business_data.get("tax_id"),
            "jurisdiction": business_data.get("jurisdiction", "US"),
            "documents": business_data.get("documents", [])
        }
        
        try:
            result = await self._make_request("POST", "business/verify", verification_data)
            return {
                "verification_status": result.get("status", "PENDING"),
                "registration_valid": result.get("registration_valid", False),
                "tax_id_valid": result.get("tax_id_valid", False),
                "business_active": result.get("business_active", False),
                "directors_verified": result.get("directors_verified", False),
                "risk_score": result.get("risk_score", 50),
                "verification_details": result.get("details", {})
            }
        except Exception as e:
            logger.error(f"Business verification failed: {str(e)}")
            raise
    
    async def check_sanctions_and_pep(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check against sanctions lists and PEP databases"""
        screening_data = {
            "entity_type": entity_data.get("type", "BUSINESS"),
            "name": entity_data.get("name"),
            "aliases": entity_data.get("aliases", []),
            "directors": entity_data.get("directors", []),
            "jurisdiction": entity_data.get("jurisdiction")
        }
        
        try:
            result = await self._make_request("POST", "screening/check", screening_data)
            return {
                "sanctions_hit": result.get("sanctions_match", False),
                "pep_hit": result.get("pep_match", False),
                "risk_level": result.get("risk_level", "LOW"),
                "matches": result.get("matches", []),
                "screening_date": result.get("screening_date", datetime.now().isoformat())
            }
        except Exception as e:
            logger.error(f"Sanctions/PEP screening failed: {str(e)}")
            raise
    
    async def get_wallet_status(self, wallet_address: str) -> Dict[str, Any]:
        """Get embedded wallet status and permissions"""
        try:
            result = await self._make_request("GET", f"wallets/{wallet_address}/status")
            return {
                "status": result.get("status", "UNKNOWN"),
                "balance": result.get("balance", "0"),
                "permissions": result.get("permissions", []),
                "last_activity": result.get("last_activity"),
                "multi_sig_threshold": result.get("multi_sig_threshold", 1)
            }
        except Exception as e:
            logger.error(f"Wallet status check failed: {str(e)}")
            raise
    
    async def update_compliance_score(self, user_id: str, new_data: Dict[str, Any]) -> int:
        """Update compliance score based on new information"""
        update_data = {
            "user_id": user_id,
            "data_updates": new_data,
            "recalculate_score": True
        }
        
        try:
            result = await self._make_request("PUT", f"compliance/{user_id}/update", update_data)
            return result.get("compliance_score", 0)
        except Exception as e:
            logger.error(f"Compliance score update failed: {str(e)}")
            raise
