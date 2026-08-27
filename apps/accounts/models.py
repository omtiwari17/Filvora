from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=50)
    avatar = models.CharField(max_length=255, default='https://ui-avatars.com/api/?name=User&background=111827&color=fff&bold=true')
    is_kids = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'accounts'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({'Kids' if self.is_kids else 'Standard'})"
