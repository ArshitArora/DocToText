from django.urls import path
from . import views

urlpatterns = [
    path('doc-to-text/', views.doc_to_text, name='doc_to_text'),
    path('txt-to-text/', views.txt_to_text, name='txt_to_text'),
    path('pdf-to-text/', views.pdf_to_text, name='pdf_to_text'),
]

