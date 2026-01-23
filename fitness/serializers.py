from rest_framework import serializers
from .models import FitnessClass, Membership, Trainer, User, ClassBooking, WorkoutType


class FitnessClassSerializer(serializers.ModelSerializer):
    workout_type_name = serializers.CharField(source='workout_type.name', read_only=True)
    trainer_name = serializers.CharField(source='trainer.user.full_name', read_only=True)
    bookings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FitnessClass
        fields = ('id', 'workout_type', 'workout_type_name', 'trainer', 'trainer_name', 
                 'capacity', 'bookings_count', 'created_at')
        read_only_fields = ('created_at',)
    
    def get_bookings_count(self, obj):
        return obj.classbooking_set.count()
    
    def validate_capacity(self, value):
        """Валидация: вместимость должна быть от 1 до 50"""
        if value < 1 or value > 50:
            raise serializers.ValidationError("Вместимость должна быть от 1 до 50 человек")
        return value


class MembershipSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    tariff_type_name = serializers.CharField(source='tariff_type.name', read_only=True)
    visits_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Membership
        fields = ('id', 'user', 'user_name', 'tariff_type', 'tariff_type_name',
                 'start_date', 'end_date', 'status', 'visits_count', 'created_at')
        read_only_fields = ('created_at',)
    
    def get_visits_count(self, obj):
        """Подсчет посещений по записям на занятия"""
        from datetime import date
        return ClassBooking.objects.filter(
            user=obj.user,
            status='attended',
            start_time__isnull=False,
            start_time__date__gte=obj.start_date,
            start_time__date__lte=obj.end_date
        ).count()
    
    def validate(self, data):
        """Валидация: дата окончания должна быть позже даты начала"""
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError({
                    'end_date': 'Дата окончания должна быть позже даты начала'
                })
        return data


class TrainerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    classes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Trainer
        fields = ('id', 'user', 'user_name', 'specialization', 'classes_count', 'created_at')
        read_only_fields = ('created_at',)
    
    def get_classes_count(self, obj):
        return obj.fitnessclass_set.count()
    
    def validate_specialization(self, value):
        """Валидация: специализация не должна быть пустой"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Специализация должна содержать минимум 2 символа")
        return value.strip()
