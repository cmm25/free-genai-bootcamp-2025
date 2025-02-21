from .models import (
    Word_Review,
    WordGroup,
    Words,
    Study_Activities,
    Study_Sessions)
from rest_framework import serializers


class WordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Words
        fields = ['Swahili', 'Pronounciation', 'English']
        extra_kwargs = {
            'Swahili': {'help_text': 'Enter the word in Swahili.'},
            'Pronounciation': {'help_text': 'Provide phonetic guidance for correct pronunciation.'},
            'English': {'help_text': 'English translation of the Swahili word.'}
        }

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
    words = WordsSerializer(many=True, read_only=True)
    word_count = serializers.SerializerMethodField()

    class Meta:
        model = WordGroup
        fields = ['id', 'name', 'words', 'word_count']
        extra_kwargs = {
            'name': {
                'help_text': 'Name of the word group',
                'required': True,
                'min_length': 1,
                'max_length': 100
            }
        }

    def get_word_count(self, obj):
        return obj.words.count()

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Group name cannot be empty")
        return value.strip()


class WordReviewSerializer(serializers.ModelSerializer):
    word = serializers.SerializerMethodField()

    class Meta:
        model = Word_Review
        fields = ['id', 'word', 'correct', 'creation_time', 'study_session_id']
        read_only_fields = ['creation_time']

    def get_word(self, obj):
        return {
            'id': obj.word_id.id,
            'swahili': obj.word_id.Swahili,
            'english': obj.word_id.English
        }

    def validate_correct(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError(
                "'correct' must be a boolean value")
        return value


class SessionsSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='Group.name', read_only=True)
    reviews_count = serializers.SerializerMethodField()

    class Meta:
        model = Study_Sessions
        fields = ['id', 'Group', 'group_name', 'creation_time',
                  'study_activity_id', 'reviews_count']
        read_only_fields = ['creation_time']

    def get_reviews_count(self, obj):
        return obj.word_review_set.count()

    def validate_study_activity_id(self, value):
        if value < 0:
            raise serializers.ValidationError("Activity ID cannot be negative")
        return value


class ActivitiesSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='Group.name', read_only=True)
    session_info = serializers.SerializerMethodField()

    class Meta:
        model = Study_Activities
        fields = ['id', 'study_session_id', 'Group', 'group_name',
                        'creation_time', 'session_info']
        read_only_fields = ['creation_time']

    def get_session_info(self, obj):
        return {
            'session_id': obj.study_session_id.id,
            'activity_id': obj.study_session_id.study_activity_id
        }
