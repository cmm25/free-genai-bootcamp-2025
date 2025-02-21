from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view

from .models import (
    Word_Review,
    WordGroup,
    Words,
    Study_Activities,
    Study_Sessions)
from .serializers import(
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
    def get(self,request):
        group_id = request.query_params.get('group_id')
        try:
            if group_id:
                current_group = WordGroup.objects.get(id = group_id)
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
            total_words_studied = Word_Review.objects.values('word_id').distinct().count()
            
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

