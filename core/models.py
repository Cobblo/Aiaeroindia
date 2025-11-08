# core/models.py
from django.db import models
from urllib.parse import urlparse, parse_qs

class PromoVideo(models.Model):
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=250, blank=True)
    youtube_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to="videos/", blank=True)
    thumbnail = models.ImageField(upload_to="videos/thumbs/", blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "-created_at")

    def __str__(self):
        return self.title

    def youtube_id(self):
        if not self.youtube_url: return None
        u = urlparse(self.youtube_url)
        if u.netloc in ("youtu.be", "www.youtu.be"):
            return u.path.lstrip("/")
        if "youtube" in u.netloc:
            if u.path.startswith("/watch"):
                return (parse_qs(u.query).get("v") or [None])[0]
            if u.path.startswith("/shorts/"):
                return u.path.split("/shorts/")[1].split("/")[0]
        return None

    def youtube_embed_url(self):
        vid = self.youtube_id()
        return f"https://www.youtube.com/embed/{vid}" if vid else None
