from django.urls import path
from .views import index, api_test, login_view, logout_view, database_schema

app_name = 'fitness'

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('api-test/', api_test, name='api_test'),
    path('database-schema/', database_schema, name='database_schema'),
]
