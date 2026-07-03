from django.urls import path

from apps.labels import views

app_name = 'labels'

urlpatterns = [
    path('invoices/<uuid:pk>/part-labels.pdf', views.part_labels_pdf, name='part_labels_pdf'),
    path('reprint/', views.reprint, name='reprint'),
]
