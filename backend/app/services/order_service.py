from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select

from backend.app.models.record import Product, PurchaseOrder, DailySale
from backend.app.schemas.record import PurchaseOrderCreate, PurchaseOrderResponse
from backend.app.services.inventory import evaluate_inventory_health


def list_purchase_orders(session: Session) -> List[PurchaseOrderResponse]:
    """Retrieve all purchase orders ordered by creation date descending."""
    statement = select(PurchaseOrder).order_by(PurchaseOrder.id.desc())
    orders = session.exec(statement).all()
    
    # Map product names
    products = {p.sku: p.name for p in session.exec(select(Product)).all()}
    
    return [
        PurchaseOrderResponse(
            id=po.id,
            po_number=po.po_number,
            sku=po.sku,
            product_name=products.get(po.sku, po.sku),
            order_qty=po.order_qty,
            unit_cost=po.unit_cost,
            total_cost=po.total_cost,
            status=po.status,
            priority=po.priority,
            created_at=po.created_at,
            expected_delivery=po.expected_delivery,
        )
        for po in orders
    ]


def create_purchase_order(session: Session, order_in: PurchaseOrderCreate) -> PurchaseOrderResponse:
    """Create a new purchase order and register on_order units."""
    product = session.exec(select(Product).where(Product.sku == order_in.sku)).first()
    if not product:
        raise ValueError(f"Product SKU {order_in.sku} not found")
        
    # Generate unique PO number
    now = datetime.now(timezone.utc)
    count = len(session.exec(select(PurchaseOrder)).all()) + 1
    po_num = f"PO-{now.year}-{count:04d}"
    
    lead_time = product.lead_time_days
    delivery_date = (now + timedelta(days=lead_time)).strftime("%Y-%m-%d")
    
    unit_cost = product.unit_cost
    total_cost = round(order_in.order_qty * unit_cost, 2)
    
    po = PurchaseOrder(
        po_number=po_num,
        sku=order_in.sku,
        order_qty=order_in.order_qty,
        unit_cost=unit_cost,
        total_cost=total_cost,
        status="DRAFT",
        priority=order_in.priority,
        created_at=now.strftime("%Y-%m-%d"),
        expected_delivery=delivery_date,
    )
    session.add(po)
    
    # Update product on_order counter
    product.on_order += order_in.order_qty
    session.add(product)
    
    session.commit()
    session.refresh(po)
    
    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        sku=po.sku,
        product_name=product.name,
        order_qty=po.order_qty,
        unit_cost=po.unit_cost,
        total_cost=po.total_cost,
        status=po.status,
        priority=po.priority,
        created_at=po.created_at,
        expected_delivery=po.expected_delivery,
    )


def update_purchase_order_status(session: Session, po_id: int, new_status: str) -> PurchaseOrderResponse:
    """Advance PO status (DRAFT -> APPROVED -> ORDERED -> RECEIVED) and adjust inventory on receipt."""
    valid_statuses = ["DRAFT", "APPROVED", "ORDERED", "RECEIVED", "CANCELLED"]
    status_upper = new_status.upper()
    if status_upper not in valid_statuses:
        raise ValueError(f"Invalid status {new_status}. Must be one of {valid_statuses}")
        
    po = session.get(PurchaseOrder, po_id)
    if not po:
        raise ValueError(f"Purchase Order ID {po_id} not found")
        
    product = session.exec(select(Product).where(Product.sku == po.sku)).first()
    
    # If order is received, increment stock and decrement on_order
    if status_upper == "RECEIVED" and po.status != "RECEIVED":
        if product:
            product.current_stock += po.order_qty
            product.on_order = max(0, product.on_order - po.order_qty)
            session.add(product)
    elif status_upper == "CANCELLED" and po.status != "CANCELLED":
        if product:
            product.on_order = max(0, product.on_order - po.order_qty)
            session.add(product)
            
    po.status = status_upper
    session.add(po)
    session.commit()
    session.refresh(po)
    
    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        sku=po.sku,
        product_name=product.name if product else po.sku,
        order_qty=po.order_qty,
        unit_cost=po.unit_cost,
        total_cost=po.total_cost,
        status=po.status,
        priority=po.priority,
        created_at=po.created_at,
        expected_delivery=po.expected_delivery,
    )


def generate_replenishment_suggestions(session: Session) -> List[Dict[str, Any]]:
    """Generate automatic reorder suggestions for all SKUs where Stock + OnOrder <= ROP."""
    products = session.exec(select(Product)).all()
    if not products:
        return []
        
    sales_by_sku = {}
    for p in products:
        sales = session.exec(
            select(DailySale).where(DailySale.sku == p.sku).order_by(DailySale.date)
        ).all()
        if sales:
            sales_by_sku[p.sku] = pd.DataFrame([s.model_dump() for s in sales])
            
    health_items = evaluate_inventory_health(products, sales_by_sku, service_level=0.95)
    
    suggestions = []
    for item in health_items:
        if item.status in ["CRITICAL", "REORDER NOW"] and item.recommended_reorder_qty > 0:
            priority = "CRITICAL" if item.status == "CRITICAL" else "HIGH"
            suggestions.append({
                "sku": item.sku,
                "name": item.name,
                "category": item.category,
                "current_stock": item.stock_level,
                "on_order": item.on_order,
                "reorder_point": item.reorder_point,
                "safety_stock": item.safety_stock,
                "recommended_order_qty": item.recommended_reorder_qty,
                "estimated_cost": item.estimated_reorder_cost,
                "priority": priority,
                "lead_time_days": item.lead_time_days,
            })
            
    return suggestions
