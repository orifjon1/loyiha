from django.db import models
from datetime import datetime
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


class Task(models.Model):
    STATUS_CHOICES = (
        ('missed', 'Missed'),
        ('doing', 'Doing'),
        ('finished', 'Finished'),
        ('canceled', 'Canceled'),
        ('changed', 'Changed'),
    )

    reason = models.CharField(max_length=200, blank=True)
    event = models.CharField(max_length=200, blank=True)
    problem = models.TextField()
    deadline = models.DateTimeField()
    boss = models.ForeignKey("user.CustomUser", on_delete=models.CASCADE, related_name='given_tasks')
    employee = models.ForeignKey("user.CustomUser", on_delete=models.CASCADE, related_name='accepted_tasks')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='doing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    financial_help = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_changed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.boss} gave a task to {self.employee}"

    @property
    def all_days(self):
        days = (self.deadline.date() - self.created_at.date()).days
        return days

    @property
    def remain_days(self):
        remain = (self.deadline.date() - datetime.now().date()).days
        return remain


class TaskUpdateTimes(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='updated_times')
    updated_by = models.ForeignKey('user.CustomUser', on_delete=models.CASCADE, related_name='updated_tasks')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.task.employee.first_name} - {self.created.date()}'


@receiver(post_save, sender=Task)
def create_update_time(sender, instance, created, **kwargs):
    if not created:
        TaskUpdateTimes.objects.create(
            task=instance, updated_by=instance.boss
        )
        # instance.is_changed = True
        # instance.save()


class TaskReview(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_reviews')
    user = models.ForeignKey("user.CustomUser", on_delete=models.CASCADE, related_name='user_reviews')
    content = models.TextField(help_text='write your comment')
    reply = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.content[:10]
