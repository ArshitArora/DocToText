from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import os
from docx import Document
from PyPDF2 import PdfReader
import os
from pytube import YouTube
from moviepy.editor import AudioFileClip
from docx import Document
from PyPDF2 import PdfReader

@csrf_exempt
def doc_to_text(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        if file.name.endswith('.docx') or file.name.endswith('.doc'):
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            try:
                doc = Document(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                os.remove(file_path)  # Clean up uploaded file
                return JsonResponse({"text": text}, status=200)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
        else:
            return JsonResponse({"error": "Invalid file format. Only .doc/.docx allowed."}, status=400)
    return JsonResponse({"error": "Invalid request method or missing file."}, status=400)

@csrf_exempt
def txt_to_text(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        if file.name.endswith('.txt'):
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            try:
                with open(file_path, 'r') as f:
                    text = f.read()
                os.remove(file_path)  # Clean up uploaded file
                return JsonResponse({"text": text}, status=200)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
        else:
            return JsonResponse({"error": "Invalid file format. Only .txt allowed."}, status=400)
    return JsonResponse({"error": "Invalid request method or missing file."}, status=400)

@csrf_exempt
def pdf_to_text(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        if file.name.endswith('.pdf'):
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_path = fs.path(filename)
            try:
                reader = PdfReader(file_path)
                text = ''.join([page.extract_text() for page in reader.pages])
                os.remove(file_path)  # Clean up uploaded file
                return JsonResponse({"text": text}, status=200)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
        else:
            return JsonResponse({"error": "Invalid file format. Only .pdf allowed."}, status=400)
    return JsonResponse({"error": "Invalid request method or missing file."}, status=400)