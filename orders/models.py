from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from clients.models import Client


class OrderStatus(models.Model):
    name = models.CharField('Статус', max_length=50)
    color = models.CharField('Цвет', max_length=20, default='secondary')
    sort_order = models.IntegerField('Порядок сортировки', default=0)

    class Meta:
        verbose_name = 'Статус заказа'
        verbose_name_plural = 'Статусы заказов'
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class Order(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT,
        verbose_name='Клиент', related_name='orders'
    )
    received_by = models.ForeignKey(
        User, on_delete=models.PROTECT,
        verbose_name='Принял', related_name='received_orders'
    )
    assigned_master = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Мастер', related_name='assigned_orders'
    )
    device_brand = models.CharField('Марка устройства', max_length=100)
    device_model = models.CharField('Модель устройства', max_length=100)
    imei = models.CharField('IMEI', max_length=20, blank=True)
    defect_description = models.TextField('Описание дефекта')
    estimated_cost = models.DecimalField(
        'Предварительная стоимость',
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    final_cost = models.DecimalField(
        'Итоговая стоимость',
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    status = models.ForeignKey(
        OrderStatus, on_delete=models.PROTECT,
        verbose_name='Статус'
    )
    received_at = models.DateTimeField('Дата приёма', default=timezone.now)
    deadline = models.DateField('Срок ремонта', null=True, blank=True)
    closed_at = models.DateTimeField('Дата выдачи', null=True, blank=True)
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-received_at']

    def __str__(self):
        return f'Заказ №{self.id} — {self.client.full_name}'

    @property
    def is_overdue(self):
        """Просрочен ли заказ (более 3 дней и не выдан)"""
        if self.status.name in ('Выдан', 'Отказ'):
            return False
        delta = timezone.now().date() - self.received_at.date()
        return delta.days > 3

    @property
    def total_paid(self):
        result = self.payments.aggregate(total=models.Sum('amount'))
        return result['total'] or 0

    @property
    def debt(self):
        if self.final_cost:
            return self.final_cost - self.total_paid
        return 0


class OrderWork(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        verbose_name='Заказ', related_name='works'
    )
    master = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, verbose_name='Мастер'
    )
    description = models.TextField('Описание работы')
    cost = models.DecimalField(
        'Стоимость', max_digits=10,
        decimal_places=2, default=0
    )
    performed_at = models.DateTimeField('Дата', default=timezone.now)

    class Meta:
        verbose_name = 'Выполненная работа'
        verbose_name_plural = 'Выполненные работы'

    def __str__(self):
        return f'{self.description[:50]} — Заказ №{self.order_id}'


class OrderHistory(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        verbose_name='Заказ', related_name='history'
    )
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, verbose_name='Изменил'
    )
    field_name = models.CharField('Поле', max_length=100, blank=True)
    old_value = models.TextField('Было', blank=True)
    new_value = models.TextField('Стало', blank=True)
    changed_at = models.DateTimeField('Дата изменения', auto_now_add=True)