from django.db import models

# Create your models here.
class Groups(models.Model):
    Name = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        return self.Name

class Words(models.Model):
    Swahili = models.CharField(max_length = 200)
    Pronounciation = models.CharField (max_length = 200)
    English = models.CharField( max_length= 200)
    

class WordGroup(models.Model):
    name = models.CharField(max_length=100)
    words = models.ManyToManyField(Words, related_name='word_groups')

    def __str__(self):
        return self.name
class Study_Sessions(models.Model):
    Group = models.ForeignKey(WordGroup , on_delete = models.CASCADE, related_name = 'student_study_groups')
    creation_time = models.DateTimeField(auto_now_add = True)
    study_activity_id = models.IntegerField()
    
    def __str__(self) -> str:
        return f"Session id {self.id} for {self.Group.Name}"
class Study_Activities(models.Model):
    study_session_id = models.ForeignKey(Study_Sessions, on_delete= models.CASCADE, related_name = 'parent_study_group' )
    Group = models.ForeignKey(WordGroup, on_delete = models.CASCADE, related_name = 'student_study_groups')
    creation_time = models.DateTimeField(auto_now_add = True)
    
    def __str__(self) -> str:
        return f"Study activitiy of Group{self.Group.Name} for session {self.study_session_id.study_activity_id}"

class Word_Review(models.Model):
    word_id = models.ForeignKey(Words, on_delete= models.CASCADE)
    study_session_id = models.ForeignKey(Study_Sessions, on_delete=models.CASCADE)
    correct = models.BooleanField()
    creation_time = models.DateTimeField(auto_now_add = True)

    def __str__(self) -> str:
        return f"word review for {self.word_id.Swahili} belonging to this word group {self.study_session_id.study_activity_id}"