from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date, timedelta
from orders.models import Order
from finance.models import Payment


@login_required
def report_main(request):
    today = date.today()
    date_from = request.GET.get('date_from', today.replace(day=1).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', today.strftime('%Y-%m-%d'))

    revenue = Payment.objects.filter(
        paid_at__date__gte=date_from,
        paid_at__date__lte=date_to
    ).aggregate(total=Sum('amount'))['total'] or 0

    orders_count = Order.objects.filter(
        received_at__date__gte=date_from,
        received_at__date__lte=date_to
    ).count()

    overdue_date = today - timedelta(days=3)
    overdue_orders = Order.objects.filter(
        received_at__date__lte=overdue_date
    ).exclude(
        status__name__in=['Выдан', 'Отказ']
    ).select_related('client', 'status')

    active_orders = Order.objects.exclude(
        status__name__in=['Выдан', 'Отказ']
    ).select_related('client', 'status')

    return render(request, 'reports/report_main.html', {
        'revenue': revenue,
        'orders_count': orders_count,
        'overdue_orders': overdue_orders,
        'active_orders': active_orders,
        'date_from': date_from,
        'date_to': date_to,
    })
