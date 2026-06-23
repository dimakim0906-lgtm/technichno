from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Client


@login_required
def client_list(request):
    clients = Client.objects.all()
    search = request.GET.get('search')
    if search:
        clients = clients.filter(
            Q(full_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    return render(request, 'clients/client_list.html', {
        'clients': clients,
        'search': search or ''
    })


@login_required
def client_create(request):
    if request.method == 'POST':
        Client.objects.create(
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email', '')
        )
        messages.success(request, 'Клиент добавлен!')
        return redirect('clients:list')
    return render(request, 'clients/client_form.html')


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    orders = client.orders.select_related('status').order_by('-received_at')
    return render(request, 'clients/client_detail.html', {
        'client': client,
        'orders': orders
    })
