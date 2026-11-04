from django.urls import path

from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('pillar/<slug:slug>/', views.PillarDetailView.as_view(), name='pillar-detail'),
]
