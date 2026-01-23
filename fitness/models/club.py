from django.db import models
from simple_history.models import HistoricalRecords
from .user import User


class Club(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название клуба')
    city = models.CharField(max_length=100, verbose_name='Город')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    work_hours = models.CharField(max_length=100, blank=True, verbose_name='Режим работы')
    image = models.ImageField(upload_to='clubs/', blank=True, null=True, verbose_name='Фото клуба')
    description = models.TextField(blank=True, verbose_name='Описание фитнес-центра')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='created_clubs', verbose_name='Кто создал')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='updated_clubs', verbose_name='Кто изменил')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменено')
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Информация о фитнес-центре'
        verbose_name_plural = 'Информация о фитнес-центре'
        ordering = ['name']

    def __str__(self):
        return self.name
