from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import date, timedelta
from .models import Order, OrderStatus, OrderWork, OrderHistory
from clients.models import Client
from finance.models import Payment


@login_required
def dashboard(request):
    """Главная страница — дашборд"""
    today = date.today()

    # Счётчики
    orders_today = Order.objects.filter(received_at__date=today).count()
    orders_in_work = Order.objects.exclude(
        status__name__in=['Выдан', 'Отказ']
    ).count()
    orders_ready = Order.objects.filter(status__name='Готов к выдаче').count()

    # Просроченные (более 3 дней, не выданы)
    overdue_date = today - timedelta(days=3)
    orders_overdue = Order.objects.filter(
        received_at__date__lte=overdue_date
    ).exclude(status__name__in=['Выдан', 'Отказ']).count()

    # Выручка сегодня
    revenue_today = Payment.objects.filter(
        paid_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Последние 10 заказов
    recent_orders = Order.objects.select_related(
        'client', 'status', 'assigned_master'
    )[:10]

    return render(request, 'orders/dashboard.html', {
        'orders_today': orders_today,
        'orders_in_work': orders_in_work,
        'orders_ready': orders_ready,
        'orders_overdue': orders_overdue,
        'revenue_today': revenue_today,
        'recent_orders': recent_orders,
    })


@login_required
def order_list(request):
    """Список заказов с фильтрацией"""
    orders = Order.objects.select_related(
        'client', 'status', 'received_by', 'assigned_master'
    )

    # Мастер видит только свои заказы
    if request.user.groups.filter(name='Мастер').exists():
        orders = orders.filter(assigned_master=request.user)

    # Фильтры
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')

    if status_filter:
        orders = orders.filter(status_id=status_filter)
    if date_from:
        orders = orders.filter(received_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(received_at__date__lte=date_to)
    if search:
        orders = orders.filter(
            Q(client__full_name__icontains=search) |
            Q(client__phone__icontains=search) |
            Q(device_model__icontains=search) |
            Q(device_brand__icontains=search) |
            Q(id__icontains=search)
        )

    statuses = OrderStatus.objects.all()

    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'statuses': statuses,
        'current_status': status_filter,
        'search': search or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
    })


@login_required
def order_create(request):
    """Создание нового заказа"""
    if request.method == 'POST':
        # Получаем или создаём клиента
        client_id = request.POST.get('client_id')
        if client_id:
            client = get_object_or_404(Client, pk=client_id)
        else:
            # Создаём нового клиента
            client = Client.objects.create(
                full_name=request.POST.get('client_name'),
                phone=request.POST.get('client_phone'),
                email=request.POST.get('client_email', '')
            )

        first_status = OrderStatus.objects.order_by('sort_order').first()

        order = Order.objects.create(
            client=client,
            received_by=request.user,
            device_brand=request.POST.get('device_brand'),
            device_model=request.POST.get('device_model'),
            imei=request.POST.get('imei', ''),
            defect_description=request.POST.get('defect_description'),
            estimated_cost=request.POST.get('estimated_cost') or None,
            status=first_status,
            notes=request.POST.get('notes', '')
        )

        # Записываем в историю
        OrderHistory.objects.create(
            order=order,
            changed_by=request.user,
            field_name='Создание заказа',
            new_value=f'Заказ создан. Статус: {first_status.name}'
        )

        messages.success(request, f'Заказ №{order.id} успешно создан!')
        return redirect('orders:detail', pk=order.id)

    # GET — показываем форму
    clients = Client.objects.all().order_by('full_name')
    return render(request, 'orders/order_form.html', {
        'clients': clients,
        'title': 'Новый заказ'
    })


@login_required
def order_detail(request, pk):
    """Карточка заказа"""
    order = get_object_or_404(
        Order.objects.select_related('client', 'status', 'received_by', 'assigned_master'),
        pk=pk
    )
    history = order.history.select_related('changed_by').order_by('changed_at')
    works = order.works.select_related('master').order_by('performed_at')
    payments = order.payments.select_related('received_by').order_by('paid_at')
    statuses = OrderStatus.objects.all()

    return render(request, 'orders/order_detail.html', {
        'order': order,
        'history': history,
        'works': works,
        'payments': payments,
        'statuses': statuses,
    })


@login_required
def order_edit(request, pk):
    """Редактирование заказа"""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        order.device_brand = request.POST.get('device_brand')
        order.device_model = request.POST.get('device_model')
        order.imei = request.POST.get('imei', '')
        order.defect_description = request.POST.get('defect_description')
        order.estimated_cost = request.POST.get('estimated_cost') or None
        order.final_cost = request.POST.get('final_cost') or None
        order.notes = request.POST.get('notes', '')
        order.save()

        OrderHistory.objects.create(
            order=order,
            changed_by=request.user,
            field_name='Редактирование',
            new_value='Данные заказа обновлены'
        )

        messages.success(request, 'Заказ обновлён!')
        return redirect('orders:detail', pk=pk)

    clients = Client.objects.all().order_by('full_name')
    return render(request, 'orders/order_form.html', {
        'order': order,
        'clients': clients,
        'title': f'Редактировать заказ №{pk}'
    })


@login_required
def order_change_status(request, pk):
    """Смена статуса заказа"""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        new_status_id = request.POST.get('status_id')
        new_status = get_object_or_404(OrderStatus, pk=new_status_id)
        old_status_name = order.status.name

        order.status = new_status
        if new_status.name == 'Выдан':
            order.closed_at = timezone.now()
        order.save()

        OrderHistory.objects.create(
            order=order,
            changed_by=request.user,
            field_name='Статус',
            old_value=old_status_name,
            new_value=new_status.name
        )

        messages.success(request, f'Статус изменён на «{new_status.name}»')

    return redirect('orders:detail', pk=pk)


@login_required
def order_add_work(request, pk):
    """Добавление выполненной работы"""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        OrderWork.objects.create(
            order=order,
            master=request.user,
            description=request.POST.get('description'),
            cost=request.POST.get('cost') or 0
        )

        OrderHistory.objects.create(
            order=order,
            changed_by=request.user,
            field_name='Работа',
            new_value=request.POST.get('description')
        )

        messages.success(request, 'Работа добавлена!')

    return redirect('orders:detail', pk=pk)


@login_required
def order_add_payment(request, pk):
    """Добавление оплаты"""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        Payment.objects.create(
            order=order,
            amount=request.POST.get('amount'),
            payment_type=request.POST.get('payment_type'),
            is_prepayment=request.POST.get('is_prepayment') == 'on',
            received_by=request.user,
            notes=request.POST.get('notes', '')
        )

        OrderHistory.objects.create(
            order=order,
            changed_by=request.user,
            field_name='Оплата',
            new_value=f'{request.POST.get("amount")} руб.'
        )

        messages.success(request, 'Оплата добавлена!')

    return redirect('orders:detail', pk=pk)
