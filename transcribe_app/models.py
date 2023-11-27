from django.db import models
class Meta:
    app_label = "transcribe_app"
class AudioFile(models.Model):
    audio = models.FileField(upload_to="audio_files/")