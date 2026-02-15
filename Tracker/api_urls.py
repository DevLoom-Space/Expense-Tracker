from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Transaction, Category, Wallet, Budget
from .serializers import TransactionSerializer, CategorySerializer, WalletSerializer, BudgetSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from .analytics_api import MonthlySummaryAPIView
from .services import wallet_balance_for_user




class OwnedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class WalletViewSet(OwnedModelViewSet):
    serializer_class = WalletSerializer

    def get_queryset(self):
        return Wallet.objects.filter(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        wallet = self.get_object()
        income, expense, balance = wallet_balance_for_user(request.user, wallet)

        return Response({
            "wallet": wallet.name,
            "currency": wallet.currency,
            "income": income,
            "expense": expense,
            "balance": balance,
        })



class CategoryViewSet(OwnedModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)




class TransactionViewSet(OwnedModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.for_user(self.request.user).select_related("category", "wallet")

        t_type = self.request.query_params.get("t_type")
        category = self.request.query_params.get("category")
        wallet = self.request.query_params.get("wallet")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        search = self.request.query_params.get("search")
        ordering = self.request.query_params.get("ordering")

        if t_type:
            qs = qs.filter(t_type=t_type)

        if category:
            qs = qs.filter(category__id=category)

        if wallet:
            qs = qs.filter(wallet__id=wallet)

        if date_from:
            qs = qs.filter(date__gte=date_from)

        if date_to:
            qs = qs.filter(date__lte=date_to)

        if search:
            qs = qs.filter(Q(note__icontains=search))

        if ordering in ["date", "-date", "amount", "-amount", "created_at", "-created_at"]:
            qs = qs.order_by(ordering)

        return qs



class BudgetViewSet(OwnedModelViewSet):
    serializer_class = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user).select_related("category")


router = DefaultRouter()
router.register("wallets", WalletViewSet, basename="wallet")
router.register("categories", CategoryViewSet, basename="category")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("budgets", BudgetViewSet, basename="budget")

urlpatterns = [
    path("", include(router.urls)),
]

urlpatterns += [
    path("analytics/monthly-summary/", MonthlySummaryAPIView.as_view(), name="monthly_summary"),
]
