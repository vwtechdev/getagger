from django.urls import path

from apps.invoices import views

app_name = 'invoices'

urlpatterns = [
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/import/', views.invoice_import, name='invoice_import'),
    path('invoices/<uuid:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:pk>/invoice-labels.pdf', views.invoice_labels_pdf, name='invoice_labels_pdf'),
    path('invoices/<uuid:pk>/combined-labels.pdf', views.combined_labels_pdf, name='combined_labels_pdf'),
    path('invoices/<uuid:pk>/reassociate/', views.invoice_reassociate, name='invoice_reassociate'),
    path('invoices/<uuid:pk>/delete/', views.invoice_delete, name='invoice_delete'),
]
