from django.urls import path
from transcribe_app import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = []

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
