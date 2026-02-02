from django.db import models
from django.contrib.auth.models import User

class Play(models.Model):
    story_id = models.IntegerField()
    ending_page_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null = True, blank=True,
                             related_name='plays')
    created_at = models.DateTimeField(auto_now_add=True)

    #decide whether to add meta class or not.
    def __str__(self):
        user_info = f"User {self.user.username}" if self.user else 'Anonymous'
        return f"Play #{self.id} - Story{self.story_id} by {user_info}"
    
class PlaySession(models.Model):
    session_key = models.CharField(max_length=100, db_index=True)
    story_id = models.IntegerField()
    current_page_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                             blank=True, related_name='play_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_key} - Story {self.story_id} at Page {self.current_page_id}"
    
class UserProfile(models.Model):
    role_choices = [('reader', 'Reader'),
                    ('author', 'Author'),
                    ('admin', 'Admin')]
    
    #relating with the built-in django user
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=role_choices, default='reader')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_author(self):
        return self.role == 'author' or self.user.is_staff
    
    def is_admin(self):
        return self.user.is_staff
    
#class for ratings

#class for report

#class for path tracking