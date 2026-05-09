"""Recharge package and mock payment logic."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models import RechargeOrder, User


RECHARGE_PACKAGES = {
    "points_100": {"name": "100积分包", "amount": Decimal("10.00"), "points": 100},
    "points_600": {"name": "600积分包", "amount": Decimal("50.00"), "points": 600},
    "points_1300": {"name": "1300积分包", "amount": Decimal("100.00"), "points": 1300},
}


def list_packages() -> list[dict]:
    return [{"id": package_id, **payload} for package_id, payload in RECHARGE_PACKAGES.items()]


def create_mock_paid_order(db: Session, user: User, package_id: str) -> RechargeOrder:
    package = RECHARGE_PACKAGES.get(package_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="充值套餐不存在")

    now = datetime.now()
    order = RechargeOrder(
        order_no=f"MOCK{now.strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}",
        user_id=user.id,
        amount=package["amount"],
        points=package["points"],
        status="pending",
        pay_channel="mock",
    )
    db.add(order)
    db.flush()

    order.status = "paid"
    order.paid_at = now
    user.points_balance = (user.points_balance or 0) + int(package["points"])
    user.account_balance = (user.account_balance or Decimal("0.00")) + package["amount"]
    db.commit()
    db.refresh(order)
    db.refresh(user)
    return order
