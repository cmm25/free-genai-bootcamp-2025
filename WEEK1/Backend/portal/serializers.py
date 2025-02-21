from .models import (
    Word_Review,
    WordGroup,
    Words,
    Study_Activities,
    Study_Sessions,
    WordCategory)
from rest_framework import serializers


class WordCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WordCategory
        fields = ['id', 'name', 'description']


class WordsSerializer(serializers.ModelSerializer):
    correct_count = serializers.SerializerMethodField()
    wrong_count = serializers.SerializerMethodField()
    categories = WordCategorySerializer(many=True, read_only=True)
    groups = serializers.SerializerMethodField()

    class Meta:
        model = Words
        fields = [
            'id', 'Swahili', 'Pronounciation', 'English',
            'correct_count', 'wrong_count', 'categories', 'groups'
        ]
        extra_kwargs = {
            'Swahili': {'help_text': 'Enter the word in Swahili'},
            'Pronounciation': {'help_text': 'Provide phonetic guidance'},
            'English': {'help_text': 'English translation'}
        }

    def get_correct_count(self, obj):
        return obj.review_stats['correct_count']

    def get_wrong_count(self, obj):
        return obj.review_stats['wrong_count']

    def get_groups(self, obj):
        return [{
            'id': group.id,
            'name': group.name,
            'stats': obj.review_stats['by_group'].get(group.id, {
                'correct_count': 0,
                'wrong_count': 0
            })
        } for group in obj.word_groups.all()]

    def validate_Swahili(self, value):
        if not value.strip():
            raise serializers.ValidationError("Swahili word cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError(
                "Swahili word exceeds maximum length of 200 characters")
        return value.strip()

    def validate_English(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "English translation cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError(
                "English translation exceeds maximum length of 200 characters")
        return value.strip()

    def validate_Pronounciation(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Pronunciation guide cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError(
                "Pronunciation guide exceeds maximum length of 200 characters")
        return value.strip()


class WordGroupSerializer(serializers.ModelSerializer):
    word_count = serializers.IntegerField(source='total_word_count', read_only=True)
    stats = serializers.SerializerMethodField()
    categories = WordCategorySerializer(many=True, read_only=True)

    class Meta:
        model = WordGroup
        fields = ['id', 'name', 'description', 'word_count', 'stats',
                    'categories', 'created_at']

    def get_stats(self, obj):
        base_stats = {
            'total_word_count': obj.total_word_count,
            'sessions_count': obj.study_sessions_count,
            'progress': obj.get_progress_stats()
        }

        # Add category distribution
        category_counts = {}
        for word in obj.words.all():
            for category in word.categories.all():
                category_counts[category.name] = category_counts.get(
                    category.name, 0) + 1

        base_stats['category_distribution'] = category_counts
        return base_stats

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Group name cannot be empty")
        return value.strip()


class WordReviewSerializer(serializers.ModelSerializer):
    word_details = WordsSerializer(source='word_id', read_only=True)

    class Meta:
        model = Word_Review
        fields = ['id', 'word_id', 'word_details',
                    'study_session_id', 'correct', 'creation_time']
        read_only_fields = ['creation_time']

    def validate_correct(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError(
                "'correct' must be a boolean value")
        return value


class SessionsSerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(
        source='study_activity_id', read_only=True)
    group_name = serializers.CharField(source='Group.name', read_only=True)
    review_items_count = serializers.IntegerField(read_only=True)
    duration = serializers.IntegerField(read_only=True)

    class Meta:
        model = Study_Sessions
        fields = [
            'id', 'activity_name', 'group_name', 'creation_time',
            'end_time', 'review_items_count', 'duration'
        ]
        read_only_fields = ['creation_time', 'end_time']

    def validate_study_activity_id(self, value):
        if value < 0:
            raise serializers.ValidationError("Activity ID cannot be negative")
        return value


class StudyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Study_Activities
        fields = ['id', 'study_session_id', 'Group', 'creation_time']
        read_only_fields = ['creation_time']
