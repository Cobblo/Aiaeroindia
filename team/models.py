from django.db import models

class TeamMember(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=160, help_text="e.g. DevOps Engineer")
    # Multiline skills (2–5 lines allowed)
    skills = models.TextField(
        blank=True,
        help_text="Enter 2–5 lines describing skills/expertise. Use line breaks."
    )
    quote = models.CharField(max_length=300, blank=True, help_text="Short one-liner shown in the card")
    photo = models.ImageField(upload_to="team/", blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name
