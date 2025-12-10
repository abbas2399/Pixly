from django.db import models
import uuid


class Job(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Input data
    s3_key = models.CharField(max_length=500)
    rules_text = models.TextField()

    # Processing data
    original_metadata = models.JSONField(null=True, blank=True)
    constraints = models.JSONField(null=True, blank=True)
    commands = models.JSONField(null=True, blank=True)

    # Output data
    output_s3_key = models.CharField(max_length=500, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} - {self.status}"