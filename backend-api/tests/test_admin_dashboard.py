from datetime import timedelta

from fastapi.testclient import TestClient

import models
from app import app
from core import accounts
from core.admin_dashboard import summary
from core.errors import RuleError
from database import get_db
from models import Payment
from security import create_token


def test_admin_dashboard_reports_paid_transactions_and_subscription_run_rate(world, db, clock):
    admin = world.user("Admin One", role="admin")
    admin.created_at = clock.now
    subscription = db.get(models.Subscription, "sub_t_free")
    subscription.plan_id = "pro"
    db.add(Payment(
        payment_id="payment_admin_test",
        subscription_id=subscription.subscription_id,
        payment_type="subscription",
        amount=299,
        method="card",
        status="paid",
        paid_at=clock.now + timedelta(minutes=1),
    ))
    db.commit()

    dashboard = summary(db, clock.now.date())

    assert dashboard["active_users"] == 4
    assert dashboard["total_shops"] == 1
    assert dashboard["transactions_this_month"] == 1
    assert dashboard["transaction_volume_this_month"] == 299
    assert dashboard["projected_mrr"] == 299
    assert dashboard["projected_arr"] == 3588
    current_month = dashboard["months"][-1]
    assert current_month["users"] == 1
    assert current_month["transactions"] == 1
    assert current_month["transaction_volume"] == 299


def test_admin_dashboard_is_only_available_to_admins(world, db):
    admin = world.user("Admin One", role="admin")
    customer_token = create_token(world.ploy)
    admin_token = create_token(admin)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        assert client.get("/admin/dashboard").status_code == 401
        assert client.get("/admin/dashboard", headers={"Authorization": f"Bearer {customer_token}"}).status_code == 403
        assert client.get("/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_public_registration_cannot_create_admin_accounts(db):
    try:
        accounts.register(
            db,
            full_name="Self-registered Admin",
            email="self-admin@test.nadd",
            phone="080",
            password="password1",
            role="admin",
            line=False,
        )
    except RuleError as error:
        assert error.message == "Choose whether you're booking or running a shop."
    else:
        raise AssertionError("Public registration unexpectedly created an Admin account")
