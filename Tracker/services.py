from django.db.models import Sum
from django.db.models.functions import TruncMonth

from .models import Transaction, Budget


def get_month_window(today):
    """
    Returns (month_start, today).
    Month start = first day of current month.
    """
    month_start = today.replace(day=1)
    return month_start, today


def monthly_totals_for_user(user, month_start, month_end):
    """
    Returns (income_total, expense_total) for a given month window.
    """
    month_txns = Transaction.objects.for_user(user).filter(date__gte=month_start, date__lte=month_end)

    income = (
        month_txns.filter(t_type=Transaction.INCOME)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    expense = (
        month_txns.filter(t_type=Transaction.EXPENSE)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )

    return income, expense


def category_breakdown_for_user(user, month_start, month_end):
    """
    Expense breakdown grouped by category for a month window.
    """
    month_txns = Transaction.objects.for_user(user).filter(date__gte=month_start, date__lte=month_end)

    return (
        month_txns.filter(t_type=Transaction.EXPENSE)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )


def wallet_balance_for_user(user, wallet):
    """
    Returns (income, expense, balance) for a specific wallet.
    """
    txns = Transaction.objects.for_user(user).filter(wallet=wallet)

    income = txns.filter(t_type=Transaction.INCOME).aggregate(total=Sum("amount"))["total"] or 0
    expense = txns.filter(t_type=Transaction.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0

    return income, expense, income - expense


def budget_alerts_for_user(user, month_start, month_end):
    """
    Returns a list of budget alerts for a given month_start (first day of month).
    Each item: {category, limit, spent, over, is_exceeded}
    """
    budgets = Budget.objects.filter(owner=user, month=month_start).select_related("category")

    # Calculate spend per category for that month (expenses only)
    spent_rows = (
        Transaction.objects.for_user(user)
        .filter(date__gte=month_start, date__lte=month_end, t_type=Transaction.EXPENSE)
        .values("category__name")
        .annotate(total=Sum("amount"))
    )

    spent_map = {row["category__name"]: row["total"] for row in spent_rows}

    alerts = []
    for b in budgets:
        spent = spent_map.get(b.category.name, 0)
        over = spent - b.limit_amount
        alerts.append({
            "category": b.category.name,
            "limit": b.limit_amount,
            "spent": spent,
            "over": over if over > 0 else 0,
            "is_exceeded": spent > b.limit_amount,
        })

    return alerts


def monthly_history_for_user(user, start_date, end_date):
    """
    Groups totals by month + type, returning rows like:
    {month, t_type, total}
    """
    return (
        Transaction.objects.for_user(user)
        .filter(date__gte=start_date, date__lte=end_date)
        .annotate(month=TruncMonth("date"))
        .values("month", "t_type")
        .annotate(total=Sum("amount"))
        .order_by("month", "t_type")
    )
