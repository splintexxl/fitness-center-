from django.db import models
from simple_history.models import HistoricalRecords
from .trainer import Trainer
from .workout_type import WorkoutType
from .club import Club
from .user import User


class FitnessClass(models.Model):
    club = models.ForeignKey(Club, on_delete=models.PROTECT, verbose_name='Клуб')
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, verbose_name='Тренер')
    workout_type = models.ForeignKey(WorkoutType, on_delete=models.PROTECT, verbose_name='Занятие')
    capacity = models.PositiveIntegerField(default=20, verbose_name='Максимум участников')
    image = models.ImageField(upload_to='classes/', blank=True, null=True, verbose_name='Изображение занятия')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='created_classes', verbose_name='Кто создал')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='updated_classes', verbose_name='Кто изменил')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменено')
    
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['-created_at']

    def __str__(self):
        if self.workout_type:
            return f'{self.workout_type.name} - {self.trainer.user.full_name if self.trainer and self.trainer.user else ""}'
        return f'Занятие #{self.id}'
