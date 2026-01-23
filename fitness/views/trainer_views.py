from django.shortcuts import render
from ..models import Trainer


def trainer_list(request):
    """Список тренеров"""
    trainers = Trainer.objects.select_related('user', 'club').all()
    return render(request, 'fitness/trainer_list.html', {'trainers': trainers})
