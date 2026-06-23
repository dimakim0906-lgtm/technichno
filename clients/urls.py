from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('clients/', views.client_list, name='list'),
    path('clients/new/', views.client_create, name='create'),
    path('clients/<int:pk>/', views.client_detail, name='detail'),
]