from django.db import models
from .user import User


class News(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Текст')
    image = models.ImageField(upload_to='news/', blank=True, null=True, verbose_name='Изображение')
    start_date = models.DateField(blank=True, null=True, verbose_name='Дата начала (для акции)')
    end_date = models.DateField(blank=True, null=True, verbose_name='Дата окончания (для акции)')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='created_news', verbose_name='Кто создал')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='updated_news', verbose_name='Кто изменил')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Изменено')

    class Meta:
        verbose_name = 'Новость / Акция'
        verbose_name_plural = 'Новости и акции'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
