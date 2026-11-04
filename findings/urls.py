from django.urls import path

from . import views

urlpatterns = [
    path('', views.FindingListView.as_view(), name='finding-list'),
    path('new/', views.FindingCreateView.as_view(), name='finding-create'),
    path('export/', views.FindingExportView.as_view(), name='findings-export'),
    path('<int:pk>/', views.FindingDetailView.as_view(), name='finding-detail'),
    path('<int:pk>/edit/', views.FindingUpdateView.as_view(), name='finding-edit'),
    path('<int:pk>/tasks/new/', views.TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/status/', views.TaskStatusView.as_view(), name='task-status'),
]
