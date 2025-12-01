from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('contacts/', views.contacts, name='contacts'),
    path('import-entreprises/', views.import_companies, name='import_companies'),
    path('appels/acces/', views.call_access, name='call_access'),
    path('appels/', views.call_list, name='call_list'),
    path('appels/<int:company_id>/remplir/', views.call_form, name='call_form'),
    path('api/companies/status/', views.company_statuses, name='company_statuses'),
    path('api/companies/<int:company_id>/reset/', views.reset_company_status, name='reset_company_status'),
    path('api/users/stats/', views.user_stats, name='user_stats'),
    path('export/', views.export_calls, name='export_calls'),
]
