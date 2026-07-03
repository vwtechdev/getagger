from django.urls import path

from apps.services import views

app_name = 'services'

urlpatterns = [
    path('service-calls/', views.service_call_list, name='service_call_list'),
    path('service-calls/new/', views.service_call_new, name='service_call_new'),
    path('service-calls/<uuid:pk>/edit/', views.service_call_edit, name='service_call_edit'),
    path('service-calls/<uuid:pk>/', views.service_call_detail, name='service_call_detail'),
]
