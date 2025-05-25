
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Settings:
    # XDC Network
    XDC_NETWORK_URL: str = os.getenv("XDC_NETWORK_URL", "https://rpc.xinfin.network")
    XDC_PRIVATE_KEY: str = os.getenv("XDC_PRIVATE_KEY", "")
    XDC_CONTRACT_ADDRESS: str = os.getenv("XDC_CONTRACT_ADDRESS", "")
    
    # API Keys
    CIVIC_AUTH_API_KEY: str = os.getenv("CIVIC_AUTH_API_KEY", "")
    QUEX_ORACLE_API_KEY: str = os.getenv("QUEX_ORACLE_API_KEY", "")
    GEMINI_AI_API_KEY: str = os.getenv("GEMINI_AI_API_KEY", "")
    
    # System Configuration
    RISK_THRESHOLD: int = int(os.getenv("RISK_THRESHOLD", "50"))
    MAX_INVOICE_AMOUNT: int = int(os.getenv("MAX_INVOICE_AMOUNT", "1000000"))
    DEFAULT_CONFIDENCE_THRESHOLD: float = float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.85"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./invoice_risk.db")

settings = Settings()