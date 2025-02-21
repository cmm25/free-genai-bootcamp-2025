from django.urls import path
from . import views

urlpatterns = [
    path('words/', views.WordListView.as_view(), name='word-list'),
    path('groups/', views.WordGroupListView.as_view(), name='group-list'),
    path('sessions/', views.StudySessionView.as_view(), name='session-list'),
    path('reviews/', views.WordReviewCreateView.as_view(), name='review-create'),
    path('words/<int:word_id>/stats/', views.WordReviewStatsView.as_view(), name='word-stats'),
    path('progress/', views.StudyProgressView.as_view(), name='study-progress'),
    path('dashboard/last_study_session/', views.DashboardLastSessionView.as_view(), name='last-session'),
    path('dashboard/quick-stats/', views.DashboardQuickStatsView.as_view(), name='quick-stats'),
    path('study_activities/<int:id>/', views.StudyActivityDetailView.as_view(), name='activity-detail'),
    path('study_activities/<int:id>/study_sessions/', views.StudyActivitySessionsView.as_view(), name='activity-sessions'),
    path('study_activities/', views.StudyActivityCreateView.as_view(), name='activity-create'),
] 