import csv
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)

from .forms import TransactionForm, CategoryForm, BudgetForm
from .models import Transaction, Category, Budget, Wallet
from .services import (
    get_month_window,
    monthly_totals_for_user,
    category_breakdown_for_user,
    budget_alerts_for_user,
    monthly_history_for_user,
)



class OwnerQuerysetMixin:
    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


# ----------------------------
# DASHBOARD (Phase 1 + 2 + 5 analytics)
# ----------------------------

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()

        # 1️⃣ Get month window from service
        month_start, month_end = get_month_window(today)

        # 2️⃣ Monthly totals
        month_income_total, month_expense_total = monthly_totals_for_user(
            self.request.user, month_start, month_end
        )

        # 3️⃣ Category breakdown
        category_breakdown = category_breakdown_for_user(
            self.request.user, month_start, month_end
        )

        # 4️⃣ ✅ Budget alerts (THIS is where your line goes)
        budget_alerts = budget_alerts_for_user(
            self.request.user, month_start, month_end
        )

        # 5️⃣ Monthly history (last 6 months)
        last_6_months_start = (month_start - timezone.timedelta(days=180)).replace(day=1)
        monthly_history = monthly_history_for_user(
            self.request.user, last_6_months_start, month_end
        )

        # 6️⃣ Recent transactions
        recent_transactions = (
            Transaction.objects.for_user(self.request.user)
            .select_related("category", "wallet")
            .filter(date__gte=month_start, date__lte=month_end)[:8]
        )

        # 7️⃣ Add everything to context
        context["month_expense_total"] = month_expense_total
        context["month_income_total"] = month_income_total
        context["net_balance"] = month_income_total - month_expense_total
        context["category_breakdown"] = category_breakdown
        context["budget_alerts"] = budget_alerts
        context["monthly_history"] = monthly_history
        context["recent_transactions"] = recent_transactions

        return context


# ----------------------------
# TRANSACTIONS CRUD + Filters + Soft Delete + CSV Export
# ----------------------------

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 10

    def get_queryset(self):
        qs = Transaction.objects.for_user(self.request.user).select_related("category", "wallet")

        t_type = self.request.GET.get("type")
        category = self.request.GET.get("category")
        wallet = self.request.GET.get("wallet")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        search = self.request.GET.get("search")

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

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(owner=self.request.user)
        context["wallets"] = Wallet.objects.filter(owner=self.request.user)
        # Keep existing filter values in template
        context["current"] = {
            "type": self.request.GET.get("type", ""),
            "category": self.request.GET.get("category", ""),
            "wallet": self.request.GET.get("wallet", ""),
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "search": self.request.GET.get("search", ""),
        }
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = "transaction_detail.html"
    context_object_name = "t"

    def get_queryset(self):
        return Transaction.objects.for_user(self.request.user).select_related("category", "wallet")


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transaction_form.html"
    success_url = reverse_lazy("transaction_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transaction_form.html"
    success_url = reverse_lazy("transaction_list")

    def get_queryset(self):
        return Transaction.objects.for_user(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = "transaction_confirm_delete.html"
    success_url = reverse_lazy("transaction_list")

    def get_queryset(self):
        return Transaction.objects.for_user(self.request.user)

    # Phase 3: Soft delete override
    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.is_deleted = True
        obj.save(update_fields=["is_deleted"])
        return redirect(self.success_url)


class TransactionExportCSVView(LoginRequiredMixin, ListView):
    model = Transaction

    def get(self, request, *args, **kwargs):
        qs = Transaction.objects.for_user(request.user).select_related("category", "wallet")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(["Date", "Wallet", "Type", "Amount", "Category", "Note"])

        for t in qs:
            writer.writerow([t.date, t.wallet.name, t.t_type, t.amount, t.category.name if t.category else "", t.note])

        return response


# ----------------------------
# CATEGORIES CRUD
# ----------------------------

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "category_form.html"
    success_url = reverse_lazy("category_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "category_form.html"
    success_url = reverse_lazy("category_list")

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = "category_confirm_delete.html"
    success_url = reverse_lazy("category_list")

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)


# ----------------------------
# BUDGETS CRUD (Phase 5)
# ----------------------------

class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = "budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user).select_related("category")


class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = "budget_form.html"
    success_url = reverse_lazy("budget_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = "budget_form.html"
    success_url = reverse_lazy("budget_list")

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = "budget_confirm_delete.html"
    success_url = reverse_lazy("budget_list")

    def get_queryset(self):
        return Budget.objects.filter(owner=self.request.user)
