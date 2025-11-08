# blog/models.py
from django.db import models
from django.utils.text import slugify
from urllib.parse import urlparse, parse_qs


def _extract_youtube_id(url: str) -> str:
    """
    Extracts the YouTube video ID from various URL formats:
    - https://youtu.be/VIDEOID
    - https://www.youtube.com/watch?v=VIDEOID
    - https://www.youtube.com/shorts/VIDEOID
    """
    if not url:
        return ""
    u = urlparse(url)
    host = (u.netloc or "").lower().replace("www.", "")

    # Short URL: youtu.be/VIDEOID
    if host == "youtu.be":
        return u.path.lstrip("/").split("/")[0]

    # Shorts: youtube.com/shorts/VIDEOID
    if "youtube.com" in host and "/shorts/" in u.path:
        return u.path.split("/shorts/")[-1].split("/")[0]

    # Watch URL: youtube.com/watch?v=VIDEOID
    if "youtube.com" in host and "/watch" in u.path:
        return parse_qs(u.query).get("v", [""])[0]

    return ""


class Post(models.Model):
    title        = models.CharField(max_length=200)
    slug         = models.SlugField(max_length=230, unique=True, blank=True)
    excerpt      = models.TextField(blank=True)
    content      = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    # YouTube
    youtube_url        = models.URLField(
        blank=True,
        help_text="Paste any YouTube link (watch / youtu.be / shorts)."
    )
    youtube_id         = models.CharField(max_length=32, blank=True, editable=False)
    youtube_embed_url  = models.URLField(blank=True, editable=False)

    # Choose embed vs thumbnail; default = thumbnail (safer)
    show_embed_player  = models.BooleanField(
        default=False,
        help_text="If ON, try to show the embedded YouTube player. If OFF, show a clickable thumbnail."
    )

    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not given
        if not self.slug:
            self.slug = slugify(self.title)[:230]

        # Compute YouTube ID + embed URL
        vid = _extract_youtube_id(self.youtube_url)
        self.youtube_id = vid or ""
        self.youtube_embed_url = f"https://www.youtube.com/embed/{vid}" if vid else ""

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
