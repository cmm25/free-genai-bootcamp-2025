from django.db import models
from django.utils import timezone

# Create your models here.


class Groups(models.Model):
    Name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.Name


class WordCategory(models.Model):
    """
    Categories like 'Noun', 'Verb', 'Adjective', 'Basic Greetings', etc.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Word Categories"

    def __str__(self):
        return self.name


class Words(models.Model):
    Swahili = models.CharField(max_length=200)
    Pronounciation = models.CharField(max_length=200)
    English = models.CharField(max_length=200)
    categories = models.ManyToManyField(WordCategory, related_name='words')

    @property
    def review_stats(self):
        reviews = self.word_review_set.all()
        return {
            'correct_count': reviews.filter(correct=True).count(),
            'wrong_count': reviews.filter(correct=False).count(),
            'by_group': self._get_group_stats()
        }

    def _get_group_stats(self):
        """Get review statistics per group"""
        stats = {}
        for group in self.word_groups.all():
            group_reviews = self.word_review_set.filter(
                study_session_id__Group=group
            )
            if group_reviews.exists():
                stats[group.id] = {
                    'group_name': group.name,
                    'correct_count': group_reviews.filter(correct=True).count(),
                    'wrong_count': group_reviews.filter(correct=False).count()
                }
        return stats

    class Meta:
        verbose_name_plural = "Words"

    def __str__(self):
        return f"{self.Swahili} ({self.English})"


class WordGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    words = models.ManyToManyField(Words, related_name='word_groups')
    categories = models.ManyToManyField(
        WordCategory, related_name='word_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_word_count(self):
        return self.words.count()

    @property
    def study_sessions_count(self):
        return self.study_sessions.count()

    def get_progress_stats(self):
        total_words = self.words.count()
        sessions = self.study_sessions.all()
        reviews = Word_Review.objects.filter(study_session_id__in=sessions)
        unique_words_studied = reviews.values('word_id').distinct().count()
        total_reviews = reviews.count()
        correct_reviews = reviews.filter(correct=True).count()

        return {
            'total_words': total_words,
            'words_studied': unique_words_studied,
            'progress_percentage': (unique_words_studied / total_words * 100) if total_words > 0 else 0,
            'total_reviews': total_reviews,
            'correct_reviews': correct_reviews,
            'accuracy': (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0
        }


class Study_Sessions(models.Model):
    Group = models.ForeignKey(
        WordGroup,
        on_delete=models.CASCADE,
        related_name='study_sessions'  # Changed from 'student_study_groups'
    )
    creation_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    study_activity_id = models.IntegerField()

    @property
    def review_items_count(self):
        return self.word_review_set.count()

    @property
    def duration(self):
        if self.end_time:
            return (self.end_time - self.creation_time).total_seconds()
        return None

    def finish_session(self):
        self.end_time = timezone.now()
        self.save()

    def __str__(self) -> str:
        return f"Session id {self.id} for {self.Group.Name}"


class Study_Activities(models.Model):
    study_session_id = models.ForeignKey(
        Study_Sessions,
        on_delete=models.CASCADE,
        related_name='activities'  # Changed from 'parent_study_group'
    )
    Group = models.ForeignKey(
        WordGroup,
        on_delete=models.CASCADE,
        related_name='study_activities'  # Changed from 'student_study_groups'
    )
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Study activity of Group {self.Group.Name} for session {self.study_session_id.study_activity_id}"


class Word_Review(models.Model):
    word_id = models.ForeignKey(Words, on_delete=models.CASCADE)
    study_session_id = models.ForeignKey(
        Study_Sessions, on_delete=models.CASCADE)
    correct = models.BooleanField()
    creation_time = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"word review for {self.word_id.Swahili} belonging to this word group {self.study_session_id.study_activity_id}"
