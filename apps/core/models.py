from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)
    entity_type = models.CharField(max_length=40)
    entity_id = models.BigIntegerField()
    offering = models.ForeignKey("catalog.CourseOffering", null=True, on_delete=models.SET_NULL)
    before = models.JSONField(null=True)
    after = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["offering", "-created_at"], name="audit_offering_time_idx"),
            models.Index(fields=["entity_type", "entity_id"], name="audit_entity_idx"),
        ]

    def __str__(self):
        return f"{self.action} {self.entity_type}#{self.entity_id}"