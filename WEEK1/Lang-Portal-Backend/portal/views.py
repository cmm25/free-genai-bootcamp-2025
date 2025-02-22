from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework import generics, filters
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import (
    Word_Review,
    WordGroup,
    Words,
    Study_Activities,
    Study_Sessions)
from .serializers import (
    WordGroupSerializer,
    WordReviewSerializer,
    WordsSerializer,
    SessionsSerializer,
    ActivitiesSerializer
)

# Create your views here.


class ResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'items_per_page'
    max_page_size = 500


class StudyProgressView(APIView):
    def get(self, request):
        group_id = request.query_params.get('group_id')
        try:
            if group_id:
                current_group = WordGroup.objects.get(id=group_id)
            else:
                current_group = WordGroup.objects.earliest('id')

            current_group_stats = current_group.get_progress_stats()

            all_groups = WordGroup.objects.all()
            groups_progress = []

            for group in all_groups:
                stats = group.get_progress_stats()
                groups_progress.append({
                    'group_id': group.id,
                    'group_name': group.name,
                    'total_words': stats['total_words'],
                    'words_studied': stats['words_studied'],
                    'progress_percentage': round(stats['progress_percentage'], 2),
                    'accuracy': round(stats['accuracy'], 2)
                })
            total_available_words = Words.objects.count()
            total_words_studied = Word_Review.objects.values(
                'word_id').distinct().count()

            data = {
                "current_group": {
                    "id": current_group.id,
                    "name": current_group.name,
                    "total_words": current_group_stats['total_words'],
                    "words_studied": current_group_stats['words_studied'],
                    "progress_percentage": round(current_group_stats['progress_percentage'], 2),
                    "total_reviews": current_group_stats['total_reviews'],
                    "correct_reviews": current_group_stats['correct_reviews'],
                    "accuracy": round(current_group_stats['accuracy'], 2)
                },
                "all_groups_progress": groups_progress,
                "overall_progress": {
                    "total_words_studied": total_words_studied,
                    "total_available_words": total_available_words,
                    "overall_progress_percentage": round((total_words_studied / total_available_words * 100) if total_available_words > 0 else 0, 2)
                }
            }
            return Response(data, status=status.HTTP_200_OK)
        except WordGroup.DoesNotExist:
            return Response(
                {"error": "Word group not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardLastSessionView(APIView):
    """
    Returns information about the most recent study session
    """

    def get(self, request):
        try:
            last_session = Study_Sessions.objects.select_related(
                'Group').latest('creation_time')

            return Response({
                "id": last_session.id,
                "group_id": last_session.Group.id,
                "created_at": last_session.creation_time,
                "study_activity_id": last_session.study_activity_id,
                "group_name": last_session.Group.name
            })
        except Study_Sessions.DoesNotExist:
            return Response({
                "error": "No study sessions found"
            }, status=status.HTTP_404_NOT_FOUND)


class DashboardQuickStatsView(APIView):
    def get(self, request):
        # Get total reviews and correct reviews
        total_reviews = Word_Review.objects.count()
        correct_reviews = Word_Review.objects.filter(correct=True).count()
        success_rate = (correct_reviews / total_reviews *
                        100) if total_reviews > 0 else 0
        total_sessions = Study_Sessions.objects.count()
        active_groups = WordGroup.objects.filter(
            student_study_groups__isnull=False
        ).distinct().count()
        today = timezone.now().date()
        sessions_by_date = Study_Sessions.objects.values(
            'creation_time__date').distinct()
        streak_days = 0

        for i in range(7):
            check_date = today - timezone.timedelta(days=i)
            if not sessions_by_date.filter(creation_time__date=check_date).exists():
                break
            streak_days += 1

        return Response({
            "success_rate": round(success_rate, 1),
            "total_study_sessions": total_sessions,
            "total_active_groups": active_groups,
            "study_streak_days": streak_days
        })


class StudyActivityDetailView(generics.RetrieveAPIView):
    queryset = Study_Activities.objects.all()
    serializer_class = ActivitiesSerializer
    lookup_field = 'id'


class StudyActivitySessionsView(generics.ListAPIView):
    serializer_class = SessionsSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        activity_id = self.kwargs['id']
        return Study_Sessions.objects.filter(
            study_activity_id=activity_id
        ).order_by('-creation_time')


class StudyActivityCreateView(APIView):
    def post(self, request):
        group_id = request.data.get('group_id')
        study_activity_id = request.data.get('study_activity_id')

        try:
            group = WordGroup.objects.get(id=group_id)
            session = Study_Sessions.objects.create(
                Group=group,
                study_activity_id=study_activity_id
            )

            return Response({
                "id": session.id,
                "group_id": group_id
            }, status=status.HTTP_201_CREATED)

        except WordGroup.DoesNotExist:
            return Response({
                "error": "Group not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class WordListView(generics.ListCreateAPIView):
    queryset = Words.objects.all()
    serializer_class = WordsSerializer
    pagination_class = ResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['Swahili', 'English']


class WordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a word
    """
    queryset = Words.objects.all()
    serializer_class = WordsSerializer
    lookup_field = 'id'


class GroupWordsView(generics.ListAPIView):
    """
    List words in a specific group
    """
    serializer_class = WordsSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        group_id = self.kwargs['id']
        return Words.objects.filter(word_groups__id=group_id)


class WordGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a word group
    """
    queryset = WordGroup.objects.all()
    serializer_class = WordGroupSerializer
    lookup_field = 'id'


class GroupStudySessionsView(generics.ListAPIView):
    """
    List study sessions for a specific group
    """
    serializer_class = SessionsSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        group_id = self.kwargs['id']
        return Study_Sessions.objects.filter(Group_id=group_id).order_by('-creation_time')


class StudySessionListView(generics.ListCreateAPIView):
    """
    List all study sessions or create a new one
    """
    queryset = Study_Sessions.objects.all().order_by('-creation_time')
    serializer_class = SessionsSerializer
    pagination_class = ResultsSetPagination


class StudySessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a study session
    """
    queryset = Study_Sessions.objects.all()
    serializer_class = SessionsSerializer
    lookup_field = 'id'


class SessionWordsView(generics.ListAPIView):
    """
    List words reviewed in a specific study session
    """
    serializer_class = WordsSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        session_id = self.kwargs['id']
        return Words.objects.filter(word_review__study_session_id=session_id).distinct()


class ResetHistoryView(APIView):
    """
    Reset study history
    """

    def post(self, request):
        try:
            Word_Review.objects.all().delete()
            Study_Sessions.objects.all().delete()
            Study_Activities.objects.all().delete()
            return Response({
                "success": True,
                "message": "Study history has been reset"
            })
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FullResetView(APIView):
    """
    Full system reset
    """

    def post(self, request):
        try:
            Word_Review.objects.all().delete()
            Study_Sessions.objects.all().delete()
            Study_Activities.objects.all().delete()
            WordGroup.objects.all().delete()
            Words.objects.all().delete()
            return Response({
                "success": True,
                "message": "System has been fully reset"
            })
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WordReviewStatsView(APIView):

    def get(self, request, word_id):
        try:
            word = get_object_or_404(Words, id=word_id)
            reviews = Word_Review.objects.filter(word_id=word)

            total_reviews = reviews.count()
            correct_reviews = reviews.filter(correct=True).count()
            accuracy = (correct_reviews / total_reviews *
                        100) if total_reviews > 0 else 0

            return Response({
                "word": {
                    "id": word.id,
                    "swahili": word.Swahili,
                    "english": word.English
                },
                "stats": {
                    "total_reviews": total_reviews,
                    "correct_reviews": correct_reviews,
                    "accuracy": round(accuracy, 2)
                }
            })
        except Words.DoesNotExist:
            return Response({
                "error": "Word not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WordGroupListView(generics.ListCreateAPIView):
    queryset = WordGroup.objects.all()
    serializer_class = WordGroupSerializer
    pagination_class = ResultsSetPagination

    def get_queryset(self):
        queryset = WordGroup.objects.all()
        # Add category filter if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(categories__name=category)
        return queryset.annotate(
            total_words=Count('words'),
            studied_words=Count(
                'student_study_groups__word_review__word_id', distinct=True)
        )

    def perform_create(self, serializer):
        group = serializer.save()
        # Handle categories if provided in request
        categories = self.request.data.get('categories', [])
        if categories:
            group.categories.set(categories)
