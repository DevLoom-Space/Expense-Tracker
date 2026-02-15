from django.contrib import admin
from .models import Wallet, Category, Transaction, Budget


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("name", "currency", "owner")
    search_fields = ("name", "owner__username")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    search_fields = ("name", "owner__username")


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("owner", "category", "month", "limit_amount")
    list_filter = ("month", "category")
    search_fields = ("owner__username", "category__name")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("t_type", "amount", "date", "owner", "wallet", "category", "is_deleted")
    list_filter = ("t_type", "date", "category", "wallet", "is_deleted")
    search_fields = ("note", "owner__username")
