from django.urls import path
from . import views

urlpatterns = [
     # Dashboard endpoints
     path('dashboard/last_study_session/',
          views.DashboardLastSessionView.as_view(),
          name='last-session'),
     path('dashboard/study_progress/',
          views.StudyProgressView.as_view(),
          name='study-progress'),
     path('dashboard/quick-stats/',
          views.DashboardQuickStatsView.as_view(),
          name='quick-stats'),

     # Word endpoints
     path('words/',
          views.WordListView.as_view(),
          name='word-list'),
     path('words/<int:id>/',
          views.WordDetailView.as_view(),
          name='word-detail'),
     path('words/<int:word_id>/stats/',
          views.WordReviewStatsView.as_view(),
          name='word-stats'),

     # Group endpoints
     path('groups/',
          views.WordGroupListView.as_view(),
          name='group-list'),
     path('groups/<int:id>/',
          views.WordGroupDetailView.as_view(),
          name='group-detail'),
     path('groups/<int:id>/words/',
          views.GroupWordsView.as_view(),
          name='group-words'),
     path('groups/<int:id>/study_sessions/',
          views.GroupStudySessionsView.as_view(),
          name='group-sessions'),

     # Study activities endpoints
     path('study_activities/',
          views.StudyActivityCreateView.as_view(),
          name='activity-create'),
     path('study_activities/<int:id>/',
          views.StudyActivityDetailView.as_view(),
          name='activity-detail'),
     path('study_activities/<int:id>/study_sessions/',
          views.StudyActivitySessionsView.as_view(),
          name='activity-sessions'),

     # Study sessions endpoints
     path('study_sessions/',
          views.StudySessionListView.as_view(),
          name='session-list'),
     path('study_sessions/<int:id>/',
          views.StudySessionDetailView.as_view(),
          name='session-detail'),
     path('study_sessions/<int:id>/words/',
          views.SessionWordsView.as_view(),
          name='session-words'),

     # System reset endpoints
     path('reset_history/',
          views.ResetHistoryView.as_view(),
          name='reset-history'),
     path('full_reset/',
          views.FullResetView.as_view(),
          name='full-reset'),
]
