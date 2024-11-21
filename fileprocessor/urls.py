from django.urls import path
from . import views

urlpatterns = [
    path('doc-to-text/', views.doc_to_text, name='doc_to_text'),
    path('txt-to-text/', views.txt_to_text, name='txt_to_text'),
    path('pdf-to-text/', views.pdf_to_text, name='pdf_to_text'),
    path('audio-to-text/',views.audio_to_text,name='audio_to_text'),
    path('image-to-text/',views.image_to_text,name='image_to_image'),
]

