from django.db import models
import uuid

class Transcript(models.Model):
    """
    Model to store the uploaded transcript text and its generated summary.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_text = models.TextField()
    summary_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transcript {self.id}"