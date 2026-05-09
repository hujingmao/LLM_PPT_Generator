"""Recharge package and mock payment logic.

当前版本是“模拟支付”：点击套餐后立即创建订单、标记已支付、给用户加积分。
真实接入微信/支付宝时，可保留订单创建逻辑，把 paid 状态更新放到支付回调里。
"""

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
    """返回前端展示用的套餐列表。

    字典内部使用 package_id 作为 key，接口输出时把它展开成 id 字段，前端点击时再传回来。
    """

    return [{"id": package_id, **payload} for package_id, payload in RECHARGE_PACKAGES.items()]


def create_mock_paid_order(db: Session, user: User, package_id: str) -> RechargeOrder:
    """创建一笔模拟支付订单，并同步更新用户积分。

    db.flush() 用于先拿到订单主键，但事务还没有提交；后面把订单改为 paid、更新用户余额后
    一次性 commit，保证订单和积分变化要么同时成功，要么同时失败。
    """

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
    # flush 只把 SQL 发送到数据库，不结束事务；适合在同一事务内继续更新关联数据。
    db.flush()

    # 模拟支付直接成功：真实支付场景中，这几行应放在支付平台异步回调处理函数里。
    order.status = "paid"
    order.paid_at = now
    user.points_balance = (user.points_balance or 0) + int(package["points"])
    user.account_balance = (user.account_balance or Decimal("0.00")) + package["amount"]
    db.commit()
    db.refresh(order)
    db.refresh(user)
    return order
