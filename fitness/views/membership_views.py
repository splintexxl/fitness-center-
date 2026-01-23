from django.shortcuts import render
from ..models import Membership


def membership_list(request):
    """Список абонементов"""
    memberships = Membership.objects.select_related('user', 'tariff_type').all()
    return render(request, 'fitness/membership_list.html', {'memberships': memberships})
