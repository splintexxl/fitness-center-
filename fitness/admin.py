from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Count
from .models import (
    User, Trainer, FitnessClass,
    TariffType, Membership, ClassBooking
)
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export.formats import base_formats


# Отключаем встроенную модель Group
admin.site.unregister(Group)


# Встроенные таблицы для пользователя
class MembershipInline(admin.TabularInline):
    model = Membership
    fk_name = 'user'
    extra = 0
    exclude = ('tariff_type', 'updated_by')
    readonly_fields = ('created_at', 'updated_at')


class ClassBookingInline(admin.TabularInline):
    model = ClassBooking
    fk_name = 'user'
    extra = 0
    exclude = ('updated_by', 'start_time', 'end_time')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('fitness_class',)


# Админка для пользователей
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'role', 'birth_date', 'get_memberships_count')
    list_display_links = ('full_name', 'email')
    list_filter = ('role', 'birth_date', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MembershipInline, ClassBookingInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'email', 'phone', 'role')
        }),
        ('Дополнительно', {
            'fields': ('birth_date', 'password_hash')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_memberships_count(self, obj):
        return obj.memberships.count()
    get_memberships_count.short_description = 'Количество абонементов'


# Встроенная таблица для занятий в админке тренера
class TrainerClassInline(admin.TabularInline):
    model = FitnessClass
    extra = 0
    raw_id_fields = ('workout_type', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('club', 'capacity', 'image', 'updated_by')


# Админка для тренеров
@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'specialization', 'get_classes_count')
    list_display_links = ('get_user_name',)
    list_filter = ('specialization', 'created_at')
    search_fields = ('user__full_name', 'specialization')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('club', 'bio', 'photo', 'updated_by')
    inlines = [TrainerClassInline]
    
    def get_user_name(self, obj):
        return obj.user.full_name
    get_user_name.short_description = 'Тренер'
    
    def get_classes_count(self, obj):
        return obj.fitnessclass_set.count()
    get_classes_count.short_description = 'Количество занятий'
    
    def save_model(self, request, obj, form, change):
        from .models import Club
        if not obj.club_id:
            club = Club.objects.first()
            if not club:
                club = Club.objects.create(
                    name='Основной клуб',
                    city='Москва',
                    address='',
                    phone='',
                    work_hours='',
                    created_by=request.user
                )
            obj.club = club
        super().save_model(request, obj, form, change)


# Ресурс для экспорта занятий в Excel
class FitnessClassResource(resources.ModelResource):
    bookings_count = resources.Field()
    capacity_info = resources.Field()
    created_at_formatted = resources.Field()
    
    class Meta:
        model = FitnessClass
        fields = ('id', 'workout_type__name', 'trainer__user__full_name', 'bookings_count', 'capacity_info', 'created_at_formatted')
        export_order = ('id', 'workout_type__name', 'trainer__user__full_name', 'bookings_count', 'capacity_info', 'created_at_formatted')
    
    def get_export_queryset(self):
        """Кастомизация: экспорт только занятий с записями"""
        return FitnessClass.objects.select_related('workout_type', 'trainer__user').annotate(
            bookings_count=Count('classbooking')
        ).filter(bookings_count__gt=0)
    
    def dehydrate_bookings_count(self, fitness_class):
        """Количество записей на занятие"""
        return fitness_class.classbooking_set.count()
    
    def dehydrate_capacity_info(self, fitness_class):
        """Информация о заполненности"""
        bookings_count = fitness_class.classbooking_set.count()
        return f'{bookings_count}/{fitness_class.capacity}'
    
    def dehydrate_created_at_formatted(self, fitness_class):
        """Форматированная дата создания"""
        if fitness_class.created_at:
            return fitness_class.created_at.strftime('%d.%m.%Y %H:%M')
        return ''
    
    def get_workout_type_name(self, fitness_class):
        """Получить название типа занятия"""
        return fitness_class.workout_type.name if fitness_class.workout_type else 'Не указано'
    


# Встроенная таблица для записей в админке занятия
class ClassBookingInlineForClass(admin.TabularInline):
    model = ClassBooking
    extra = 0
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('updated_by',)


# Админка для занятий
@admin.register(FitnessClass)
class FitnessClassAdmin(ImportExportModelAdmin):
    resource_class = FitnessClassResource
    formats = [base_formats.XLSX, base_formats.CSV]
    list_display = ('get_workout_name', 'get_trainer_name', 'get_bookings_count')
    list_display_links = ('get_workout_name',)
    list_filter = ('trainer', 'workout_type', 'created_at')
    search_fields = ('workout_type__name', 'trainer__user__full_name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('created_by',)
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('club', 'capacity', 'image', 'updated_by')
    inlines = [ClassBookingInlineForClass]
    fieldsets = (
        ('Основная информация', {
            'fields': ('trainer', 'workout_type')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_workout_name(self, obj):
        return obj.workout_type.name if obj.workout_type else '-'
    get_workout_name.short_description = 'Занятие'
    
    def get_trainer_name(self, obj):
        return obj.trainer.user.full_name if obj.trainer and obj.trainer.user else '-'
    get_trainer_name.short_description = 'Тренер'
    
    def get_bookings_count(self, obj):
        return obj.classbooking_set.count()
    get_bookings_count.short_description = 'Записей'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'trainer':
            kwargs['queryset'] = Trainer.objects.select_related('user').all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        from .models import Club
        if not obj.club_id:
            club = Club.objects.first()
            if not club:
                club = Club.objects.create(
                    name='Основной клуб',
                    city='Москва',
                    address='',
                    phone='',
                    work_hours='',
                    created_by=request.user
                )
            obj.club = club
        if not obj.capacity:
            obj.capacity = 20
        super().save_model(request, obj, form, change)


# Админка для типов абонементов
@admin.register(TariffType)
class TariffTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_days', 'price', 'is_active')
    list_display_links = ('name',)
    list_filter = ('is_active', 'duration_days')
    search_fields = ('name',)


# Админка для абонементов
@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'start_date', 'end_date', 'status')
    list_display_links = ('get_user_name',)
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('user__full_name',)
    date_hierarchy = 'start_date'
    raw_id_fields = ('user', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('updated_by',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'tariff_type', 'status')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_name(self, obj):
        return obj.user.full_name
    get_user_name.short_description = 'Пользователь'


# Админка для записей на занятия
@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ('get_user_name', 'get_class_name', 'status')
    list_display_links = ('get_user_name',)
    list_filter = ('status', 'created_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    exclude = ('updated_by',)
    
    def get_user_name(self, obj):
        return obj.user.full_name
    get_user_name.short_description = 'Пользователь'
    
    def get_class_name(self, obj):
        if obj.fitness_class and obj.fitness_class.workout_type:
            return obj.fitness_class.workout_type.name
        return '-'
    get_class_name.short_description = 'Занятие'
