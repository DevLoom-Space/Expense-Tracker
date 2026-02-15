from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Transaction, Wallet


User = get_user_model()


class TrackerCoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="erick", password="pass12345")
        self.client.login(username="erick", password="pass12345")
        self.wallet = Wallet.objects.get(owner=self.user)  # created by signal

    def test_create_category(self):
        c = Category.objects.create(owner=self.user, name="Food")
        self.assertEqual(str(c), "Food")

    def test_transaction_owner_is_enforced(self):
        cat = Category.objects.create(owner=self.user, name="Food")
        t = Transaction.objects.create(
            owner=self.user,
            wallet=self.wallet,
            t_type="EXPENSE",
            amount="100.00",
            category=cat,
            date=date.today(),
            note="Lunch",
        )
        self.assertEqual(t.owner, self.user)

    def test_dashboard_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 302)

    def test_soft_delete(self):
        cat = Category.objects.create(owner=self.user, name="Food")
        t = Transaction.objects.create(
            owner=self.user,
            wallet=self.wallet,
            t_type="EXPENSE",
            amount="50.00",
            category=cat,
            date=date.today(),
            note="Test",
        )

        # soft delete via view
        resp = self.client.post(reverse("transaction_delete", args=[t.pk]))
        self.assertEqual(resp.status_code, 302)

        t.refresh_from_db()
        self.assertTrue(t.is_deleted)

        # should not appear in active manager results
        self.assertEqual(Transaction.objects.for_user(self.user).count(), 0)
