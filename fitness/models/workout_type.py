from django.db import models


class WorkoutType(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название типа занятия')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['name']

    def __str__(self):
        return self.name
