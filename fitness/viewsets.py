from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import FitnessClass, Membership, Trainer, User, ClassBooking
from .serializers import FitnessClassSerializer, MembershipSerializer, TrainerSerializer


class FitnessClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet для занятий с фильтрацией, поиском и сложными запросами
    """
    queryset = FitnessClass.objects.select_related('trainer__user', 'workout_type', 'club').all()
    serializer_class = FitnessClassSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['trainer', 'workout_type']
    search_fields = ['workout_type__name', 'trainer__user__full_name']
    ordering_fields = ['created_at', 'capacity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Сложные запросы с Q объектами"""
        queryset = super().get_queryset()
        
        # Запрос 1 с Q (OR + AND + NOT): занятия с записями (забронированные ИЛИ посещенные) 
        # И с вместимостью >= 10, НО не отмененные
        high_bookings = self.request.query_params.get('high_bookings', None)
        if high_bookings == 'true':
            queryset = queryset.annotate(
                bookings_count=Count('classbooking')
            ).filter(
                (Q(classbooking__status='booked') | Q(classbooking__status='attended')) &
                Q(capacity__gte=10) &
                ~Q(classbooking__status='canceled')
            ).distinct()
        
        # Запрос 2 с Q (OR + AND + NOT): популярные занятия с записями ИЛИ высокой вместимостью,
        # И созданные недавно, НО не старые занятия
        popular_recent = self.request.query_params.get('popular_recent', None)
        if popular_recent == 'true':
            from datetime import datetime, timedelta
            week_ago = datetime.now() - timedelta(days=7)
            queryset = queryset.annotate(
                bookings_count=Count('classbooking')
            ).filter(
                (Q(classbooking__status='booked') | Q(capacity__gte=15)) &
                Q(created_at__gte=week_ago) &
                ~Q(created_at__lt=datetime.now() - timedelta(days=30))
            ).distinct()
        
        return queryset
    
    @action(methods=['GET'], detail=False)
    def popular_classes(self, request):
        """Получить популярные занятия (с наибольшим количеством записей)"""
        classes = self.get_queryset().annotate(
            bookings_count=Count('classbooking')
        ).order_by('-bookings_count')[:10]
        
        serializer = self.get_serializer(classes, many=True)
        return Response(serializer.data)
    
    @action(methods=['POST'], detail=True)
    def cancel_booking(self, request, pk=None):
        """Отменить все записи на занятие"""
        fitness_class = self.get_object()
        ClassBooking.objects.filter(
            fitness_class=fitness_class,
            status='booked'
        ).update(status='canceled')
        
        return Response({
            'status': 'success',
            'message': f'Все записи на занятие {fitness_class.workout_type.name} отменены'
        }, status=status.HTTP_200_OK)
    
    @action(methods=['GET'], detail=True)
    def history(self, request, pk=None):
        """Получить историю изменений занятия"""
        fitness_class = self.get_object()
        history = fitness_class.history.all()[:10]
        
        history_data = []
        for record in history:
            history_data.append({
                'history_date': record.history_date,
                'workout_type': record.workout_type.name if record.workout_type else None,
                'capacity': record.capacity,
                'history_type': record.get_history_type_display(),
            })
        
        return Response(history_data)


class MembershipViewSet(viewsets.ModelViewSet):
    """
    ViewSet для абонементов с фильтрацией и сложными запросами
    """
    queryset = Membership.objects.select_related('user', 'tariff_type').all()
    serializer_class = MembershipSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'tariff_type']
    search_fields = ['user__full_name', 'tariff_type__name']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']
    
    def get_queryset(self):
        """Сложные запросы с Q объектами"""
        queryset = super().get_queryset()
        
        # Запрос 3 с Q (OR + AND + NOT): активные абонементы ИЛИ истекающие в ближайшие 7 дней,
        # И с датой начала в текущем году, НО не замороженные
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            from datetime import date, timedelta
            today = date.today()
            week_later = today + timedelta(days=7)
            year_start = date(today.year, 1, 1)
            
            queryset = queryset.filter(
                (Q(status='active') | Q(end_date__gte=today, end_date__lte=week_later)) &
                Q(start_date__gte=year_start) &
                ~Q(status='frozen')
            )
        
        # Запрос 4 с Q (OR + AND + NOT): активные ИЛИ истекающие абонементы,
        # И созданные администратором, НО не просроченные
        urgent_memberships = self.request.query_params.get('urgent', None)
        if urgent_memberships == 'true':
            from datetime import date
            today = date.today()
            queryset = queryset.filter(
                (Q(status='active') | Q(end_date__gte=today, end_date__lte=today + timedelta(days=3))) &
                Q(created_by__isnull=False) &
                ~Q(end_date__lt=today)
            )
        
        return queryset
    
    @action(methods=['GET'], detail=False)
    def active_memberships(self, request):
        """Получить все активные абонементы"""
        from datetime import date
        active = self.get_queryset().filter(
            status='active',
            start_date__lte=date.today(),
            end_date__gte=date.today()
        )
        serializer = self.get_serializer(active, many=True)
        return Response(serializer.data)
    
    @action(methods=['POST'], detail=True)
    def freeze_membership(self, request, pk=None):
        """Заморозить абонемент"""
        membership = self.get_object()
        if membership.status == 'active':
            membership.status = 'frozen'
            membership.save()
            return Response({
                'status': 'success',
                'message': 'Абонемент заморожен'
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': 'Можно заморозить только активный абонемент'
        }, status=status.HTTP_400_BAD_REQUEST)


class TrainerViewSet(viewsets.ModelViewSet):
    """
    ViewSet для тренеров
    """
    queryset = Trainer.objects.select_related('user', 'club').all()
    serializer_class = TrainerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['specialization', 'club']
    search_fields = ['user__full_name', 'specialization']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Сложные запросы с Q"""
        queryset = super().get_queryset()
        return queryset
    
    @action(methods=['GET'], detail=False)
    def workload_statistics(self, request):
        """Статистика загрузки тренеров"""
        trainers = self.get_queryset().annotate(
            classes_count=Count('fitnessclass'),
            bookings_count=Count('fitnessclass__classbooking')
        ).order_by('-classes_count')
        
        data = []
        for trainer in trainers:
            data.append({
                'trainer': trainer.user.full_name,
                'specialization': trainer.specialization,
                'classes_count': trainer.classes_count,
                'bookings_count': trainer.bookings_count,
            })
        
        return Response(data)
    
    @action(methods=['POST'], detail=True)
    def update_specialization(self, request, pk=None):
        """Обновить специализацию тренера"""
        trainer = self.get_object()
        new_specialization = request.data.get('specialization')
        
        if not new_specialization:
            return Response({
                'error': 'Поле specialization обязательно'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trainer.specialization = new_specialization
        trainer.save()
        
        serializer = self.get_serializer(trainer)
        return Response(serializer.data)
