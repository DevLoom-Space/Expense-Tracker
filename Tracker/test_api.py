from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from django.urls import reverse

from Tracker.models import Wallet, Category, Transaction

User = get_user_model()

class APICoreTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="devloom2", password="pass12345")
        self.client.login(username="devloom2", password="pass12345")
        self.wallet = Wallet.objects.get(owner=self.user)
        self.category = Category.objects.create(owner=self.user, name="Food")

    def test_wallets_list(self):
        resp = self.client.get("/api/wallets/")
        self.assertEqual(resp.status_code, 200)

    def test_create_transaction(self):
        payload = {
            "wallet": self.wallet.id,
            "t_type": "EXPENSE",
            "amount": "100.00",
            "category": self.category.id,
            "date": str(date.today()),
            "note": "Lunch"
        }
        resp = self.client.post("/api/transactions/", payload, format="json")
        self.assertEqual(resp.status_code, 201)
