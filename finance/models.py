from django.db import models
from django.contrib.auth.models import User
from orders.models import Order


class Payment(models.Model):
    PAYMENT_TYPES = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
    ]

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        verbose_name='Заказ', related_name='payments'
    )
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    payment_type = models.CharField(
        'Способ оплаты', max_length=10,
        choices=PAYMENT_TYPES, default='cash'
    )
    is_prepayment = models.BooleanField('Предоплата', default=False)
    paid_at = models.DateTimeField('Дата оплаты', auto_now_add=True)
    received_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, verbose_name='Принял оплату'
    )
    notes = models.CharField('Примечание', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.amount} руб. — Заказ №{self.order_id}'
