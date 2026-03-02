from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, BigInteger, Enum
from database import Base
from datetime import datetime

class MasterOrder(Base):
    __tablename__ = "master_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    txn_id = Column(String(255))
    payment_status = Column(String(255))
    order_count = Column(Integer)
    payment_method = Column(String(255))
    delivery_info = Column(Text)
    order_total = Column(Numeric(10, 2))
    delivery_charge = Column(Numeric(10, 2))
    discount = Column(Numeric(10, 2))
    before_discount = Column(Numeric(10, 2))
    status = Column(Enum('1', '0'))
    created_at = Column(DateTime)

class Order(Base):
    __tablename__ = "orders"
    
    order_id = Column(BigInteger, primary_key=True, index=True)
    bill_number = Column(Integer)
    master_order_id = Column(Integer)
    txn_id = Column(String(250))
    buyer_userid = Column(BigInteger)
    start_time = Column(Integer)
    last_update_time = Column(Integer)
    short_datetime = Column(Text)
    order_state = Column(String(250))
    payment_method = Column(String(250))
    ctype_id = Column(String(250))
    items_count = Column(Integer)
    delivery_charge = Column(Numeric(10, 0))
    order_total = Column(Numeric(12, 2))
    bill_amount = Column(Integer)
    delivery_info = Column(Text)
    area_name = Column(Text)
    feedback = Column(String(100))
    admin_id = Column(BigInteger)
    payment_status = Column(String(250))
    amountReceivedInfo = Column(Text)
    trip_id = Column(Integer)
    discount = Column(Numeric(10, 2))
    before_discount = Column(Numeric(10, 2))
    time_slot = Column(String(250))
    delivered_time = Column(Integer)
    deli_id = Column(Integer)

class OrderItem(Base):
    __tablename__ = "orders_item"
    
    order_id = Column(BigInteger, primary_key=True)
    item_id = Column(BigInteger, primary_key=True)
    product_id = Column(BigInteger)
    vendor_product_id = Column(Integer)
    pinfo = Column(Text)
    offers = Column(Text)
    quantity = Column(Integer)
    qty_loaded = Column(Integer)
    qty_delivered = Column(Integer)
    qty_returned = Column(Integer)
    item_price = Column(Numeric(12, 2))
    item_total = Column(Numeric(12, 2))
    op_id = Column(BigInteger)
    commission = Column(Numeric(10, 2))
