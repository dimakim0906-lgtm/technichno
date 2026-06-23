from django.db import models


class Client(models.Model):
    full_name = models.CharField('ФИО', max_length=200)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email', blank=True)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.phone})'