
from web3 import Web3
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class RiskAssessment:
    """Risk assessment data structure for blockchain storage"""
    invoice_id: str
    risk_score: int
    risk_level: str
    confidence: int
    factors: Dict[str, Any]
    timestamp: int
    assessor_agents: List[str]
    
class XDCBlockchain:
    """
    XDC Network blockchain integration
    Handles smart contract interactions and risk assessment storage
    """
    
    def __init__(self, rpc_url: str, private_key: str, contract_address: str):
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.contract_address = contract_address
        self.w3 = None
        self.contract = None
        self.account = None
        
        # Smart contract ABI (simplified for risk assessment storage)
        self.contract_abi = [
            {
                "inputs": [
                    {"name": "invoiceId", "type": "string"},
                    {"name": "riskScore", "type": "uint256"},
                    {"name": "riskLevel", "type": "string"},
                    {"name": "confidence", "type": "uint256"},
                    {"name": "dataHash", "type": "bytes32"}
                ],
                "name": "storeRiskAssessment",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "inputs": [{"name": "invoiceId", "type": "string"}],
                "name": "getRiskAssessment",
                "outputs": [
                    {"name": "riskScore", "type": "uint256"},
                    {"name": "riskLevel", "type": "string"},
                    {"name": "confidence", "type": "uint256"},
                    {"name": "timestamp", "type": "uint256"},
                    {"name": "dataHash", "type": "bytes32"}
                ],
                "type": "function"
            },
            {
                "inputs": [{"name": "invoiceId", "type": "string"}],
                "name": "getAssessmentHistory",
                "outputs": [
                    {"name": "timestamps", "type": "uint256[]"},
                    {"name": "riskScores", "type": "uint256[]"},
                    {"name": "dataHashes", "type": "bytes32[]"}
                ],
                "type": "function"
            }
        ]
    
    async def initialize(self):
        """Initialize Web3 connection and contract"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Verify connection
            if not self.w3.is_connected():
                raise Exception("Failed to connect to XDC Network")
            
            # Setup account
            self.account = self.w3.eth.account.from_key(self.private_key)
            
            # Initialize contract
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.contract_abi
            )
            
            logger.info(f"Connected to XDC Network. Account: {self.account.address}")
            
        except Exception as e:
            logger.error(f"XDC blockchain initialization failed: {str(e)}")
            raise
    
    def _generate_data_hash(self, assessment_data: Dict[str, Any]) -> str:
        """Generate hash of assessment data for integrity verification"""
        data_string = json.dumps(assessment_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    async def store_risk_assessment(self, assessment: RiskAssessment) -> str:
        """Store risk assessment on XDC blockchain"""
        if not self.w3 or not self.contract:
            await self.initialize()
        
        try:
            # Generate data hash for integrity
            assessment_dict = asdict(assessment)
            data_hash = self._generate_data_hash(assessment_dict)
            data_hash_bytes = Web3.to_bytes(hexstr=data_hash)
            
            # Prepare transaction
            tx = self.contract.functions.storeRiskAssessment(
                assessment.invoice_id,
                assessment.risk_score,
                assessment.risk_level,
                assessment.confidence,
                data_hash_bytes
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 500000,
                'gasPrice': self.w3.to_wei('1', 'gwei')
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt.status == 1:
                logger.info(f"Risk assessment stored successfully. TX Hash: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                raise Exception("Transaction failed")
                
        except Exception as e:
            logger.error(f"Failed to store risk assessment: {str(e)}")
            raise
    
    async def get_risk_assessment(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve risk assessment from blockchain"""
        if not self.w3 or not self.contract:
            await self.initialize()
        
        try:
            result = self.contract.functions.getRiskAssessment(invoice_id).call()
            
            if result[0] == 0:  # No assessment found
                return None
            
            return {
                "risk_score": result[0],
                "risk_level": result[1],
                "confidence": result[2],
                "timestamp": result[3],
                "data_hash": result[4].hex()
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve risk assessment: {str(e)}")
            raise
    
    async def get_assessment_history(self, invoice_id: str) -> List[Dict[str, Any]]:
        """Get historical risk assessments for an invoice"""
        if not self.w3 or not self.contract:
            await self.initialize()
        
        try:
            result = self.contract.functions.getAssessmentHistory(invoice_id).call()
            
            timestamps, risk_scores, data_hashes = result
            
            history = []
            for i in range(len(timestamps)):
                history.append({
                    "timestamp": timestamps[i],
                    "risk_score": risk_scores[i],
                    "data_hash": data_hashes[i].hex(),
                    "date": datetime.fromtimestamp(timestamps[i]).isoformat()
                })
            
            return sorted(history, key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to retrieve assessment history: {str(e)}")
            raise
    
    async def verify_assessment_integrity(self, invoice_id: str, original_data: Dict[str, Any]) -> bool:
        """Verify the integrity of stored assessment data"""
        try:
            stored_assessment = await self.get_risk_assessment(invoice_id)
            if not stored_assessment:
                return False
            
            original_hash = self._generate_data_hash(original_data)
            stored_hash = stored_assessment["data_hash"]
            
            return original_hash == stored_hash
            
        except Exception as e:
            logger.error(f"Failed to verify assessment integrity: {str(e)}")
            return False
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Get XDC network statistics"""
        if not self.w3:
            await self.initialize()
        
        try:
            latest_block = self.w3.eth.get_block('latest')
            balance = self.w3.eth.get_balance(self.account.address)
            
            return {
                "connected": self.w3.is_connected(),
                "latest_block": latest_block.number,
                "account_address": self.account.address,
                "account_balance": self.w3.from_wei(balance, 'ether'),
                "network_id": self.w3.net.version,
                "gas_price": self.w3.from_wei(self.w3.eth.gas_price, 'gwei')
            }
            
        except Exception as e:
            logger.error(f"Failed to get network stats: {str(e)}")
            raise
    
    async def estimate_gas_cost(self, assessment: RiskAssessment) -> Dict[str, Any]:
        """Estimate gas cost for storing risk assessment"""
        if not self.w3 or not self.contract:
            await self.initialize()
        
        try:
            assessment_dict = asdict(assessment)
            data_hash = self._generate_data_hash(assessment_dict)
            data_hash_bytes = Web3.to_bytes(hexstr=data_hash)
            
            # Estimate gas
            gas_estimate = self.contract.functions.storeRiskAssessment(
                assessment.invoice_id,
                assessment.risk_score,
                assessment.risk_level,
                assessment.confidence,
                data_hash_bytes
            ).estimate_gas({'from': self.account.address})
            
            gas_price = self.w3.eth.gas_price
            total_cost = gas_estimate * gas_price
            
            return {
                "gas_estimate": gas_estimate,
                "gas_price_gwei": self.w3.from_wei(gas_price, 'gwei'),
                "total_cost_eth": self.w3.from_wei(total_cost, 'ether'),
                "total_cost_wei": total_cost
            }
            
        except Exception as e:
            logger.error(f"Failed to estimate gas cost: {str(e)}")
            raise
    
    async def batch_store_assessments(self, assessments: List[RiskAssessment]) -> List[str]:
        """Store multiple risk assessments in batch"""
        tx_hashes = []
        
        for assessment in assessments:
            try:
                tx_hash = await self.store_risk_assessment(assessment)
                tx_hashes.append(tx_hash)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to store assessment {assessment.invoice_id}: {str(e)}")
                tx_hashes.append(None)
        
        return tx_hashes