from fastapi import FastAPI
from app.api.transactions import router as transactions_router
from app.api.customers import (
    router as customers_router,
)
from app.api.accounts import (
    router as accounts_router,
)

from app.api.merchants import (
    router as merchants_router,
)

app = FastAPI(
    title="TransactionShield API",
    description=(
        "Bank transaction processing "
        "with fraud detection"
    ),
    version="1.0.0",
    
)
##customers
app.include_router(transactions_router)
app.include_router(customers_router)
app.include_router(transactions_router)

##accounts
app.include_router(accounts_router)
app.include_router(customers_router)
app.include_router(transactions_router)

##merchants
app.include_router(accounts_router)
app.include_router(customers_router)
app.include_router(merchants_router)
app.include_router(transactions_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TransactionShield",
    }