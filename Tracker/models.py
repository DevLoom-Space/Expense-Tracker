from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from .managers import TransactionManager


class Wallet(models.Model):
    """
    Wallet/Account model (Phase 5)
    A user can have multiple wallets: Cash, M-Pesa, Bank, etc.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallets")
    name = models.CharField(max_length=50, default="Main Wallet")
    currency = models.CharField(max_length=10, default="KES")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("owner", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.currency})"


class Category(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ("owner", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Budget(models.Model):
    """
    Budget per category per month (Phase 5)
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    month = models.DateField(help_text="Use the 1st day of the month, e.g. 2026-02-01")
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])

    class Meta:
        unique_together = ("owner", "category", "month")
        ordering = ["-month", "category__name"]

    def __str__(self):
        return f"{self.category} - {self.month} - {self.limit_amount}"


class Transaction(models.Model):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

    TYPE_CHOICES = [
        (EXPENSE, "Expense"),
        (INCOME, "Income"),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")

    t_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=EXPENSE)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True)

    # Phase 3: Soft delete
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager
    objects = TransactionManager()

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["owner", "date"]),
            models.Index(fields=["owner", "t_type", "date"]),
            models.Index(fields=["owner", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.t_type} - {self.amount} on {self.date}"
