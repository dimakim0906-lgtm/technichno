from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.order_list, name='list'),
    path('orders/new/', views.order_create, name='create'),
    path('orders/<int:pk>/', views.order_detail, name='detail'),
    path('orders/<int:pk>/edit/', views.order_edit, name='edit'),
    path('orders/<int:pk>/status/', views.order_change_status, name='change_status'),
    path('orders/<int:pk>/work/', views.order_add_work, name='add_work'),
    path('orders/<int:pk>/payment/', views.order_add_payment, name='add_payment'),
]