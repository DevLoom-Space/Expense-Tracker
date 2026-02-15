from django.utils import timezone
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Transaction


class MonthlySummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = request.query_params.get("month")
        today = timezone.localdate()

        if month:
            # expects YYYY-MM-01
            month_start = timezone.datetime.fromisoformat(month).date()
        else:
            month_start = today.replace(day=1)

        month_end = today if (today.year == month_start.year and today.month == month_start.month) else month_start.replace(day=28)

        txns = Transaction.objects.for_user(request.user).filter(date__gte=month_start)

        income = txns.filter(t_type=Transaction.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        expense = txns.filter(t_type=Transaction.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "month_start": str(month_start),
            "income": income,
            "expense": expense,
            "net": income - expense,
        })
