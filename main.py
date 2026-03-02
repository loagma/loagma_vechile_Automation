from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Order, MasterOrder, OrderItem
from dotenv import load_dotenv
import sys
import os

# Add algo_generated_trips to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'algo_generated_trips'))

from algo_generated_trips.api.routes import vehicles, zone_vehicles, pincodes, trips

load_dotenv()

app = FastAPI(title="Loagma API")

# Include API routers
app.include_router(vehicles.router)
app.include_router(zone_vehicles.router)
app.include_router(pincodes.router)
app.include_router(trips.router)

@app.get("/")
def read_root():
    return {"message": "Loagma API", "status": "connected"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/orders")
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = db.query(Order).offset(skip).limit(limit).all()
    return {"total": len(orders), "orders": orders}

@app.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        return {"error": "Order not found"}
    return order

@app.get("/master-orders")
def get_master_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = db.query(MasterOrder).offset(skip).limit(limit).all()
    return {"total": len(orders), "orders": orders}

@app.get("/master-orders/{order_id}")
def get_master_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(MasterOrder).filter(MasterOrder.id == order_id).first()
    if not order:
        return {"error": "Master order not found"}
    return order
