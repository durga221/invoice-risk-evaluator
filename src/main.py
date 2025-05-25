from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agents.identity_agent import verify_identity
from src.agents.credit_agent import analyze_credit
from src.agents.market_agent import analyze_market
from src.agents.risk_agent import score_risk
from src.models.risk_models import InvoiceData, RiskAssessmentResult

app = FastAPI(
    title="Invoice Risk Evaluator",
    description="AI-powered invoice risk evaluation system using multi-agent architecture",
    version="1.0.0"
)


@app.post("/assess-risk", response_model=RiskAssessmentResult)
async def assess_invoice_risk(invoice: InvoiceData):
    try:
        # Step 1: Verify Identity
        identity_verified = await verify_identity(invoice.company_id)
        if not identity_verified:
            raise HTTPException(status_code=400, detail="Identity verification failed.")

        # Step 2: Analyze Credit
        credit_score = await analyze_credit(invoice.company_id)

        # Step 3: Analyze Market
        market_risk = await analyze_market(invoice.industry, invoice.region)

        # Step 4: Score Final Risk
        final_score, risk_level = await score_risk(
            identity_verified,
            credit_score,
            market_risk
        )

        return RiskAssessmentResult(
            company_id=invoice.company_id,
            credit_score=credit_score,
            market_risk=market_risk,
            risk_score=final_score,
            risk_level=risk_level
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Welcome to Invoice Risk Evaluator API"}
