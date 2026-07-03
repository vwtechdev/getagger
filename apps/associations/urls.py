from django.urls import path

from apps.associations import views

app_name = 'associations'

urlpatterns = [
    path('invoices/<uuid:pk>/associate/', views.association, name='association'),
    path('invoices/<uuid:pk>/associate/create', views.association_create, name='association_create'),
    path('invoices/<uuid:pk>/associate/undo', views.association_undo, name='association_undo'),
]
