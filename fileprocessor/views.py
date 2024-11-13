from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import os
from docx import Document
from PyPDF2 import PdfReader
import os
from pytube import YouTube
from moviepy.editor import AudioFileClip
import speech_recognition as sr
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

@csrf_exempt
def yt_to_text(request):
    if request.method == 'POST':
        video_url = request.POST.get('url')  # Accept YouTube URL as input
        print(video_url)
        if not video_url:
            return JsonResponse({"error": "No URL provided."}, status=400)
        
        try:
            # Step 1: Download the video
            yt = YouTube(video_url)
            stream = yt.streams.filter(only_audio=True).first()  # Get audio stream
            output_dir = os.path.join('media', 'temporary')
            os.makedirs(output_dir, exist_ok=True)
            audio_path = stream.download(output_path=output_dir, filename='yt_audio.mp4')

            # Step 2: Extract audio and save it as WAV
            wav_path = os.path.join(output_dir, 'yt_audio.wav')
            clip = AudioFileClip(audio_path)
            clip.write_audiofile(wav_path, codec='pcm_s16le')
            clip.close()

            # Step 3: Transcribe the audio
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)

            # Clean up temporary files
            os.remove(audio_path)
            os.remove(wav_path)

            return JsonResponse({"text": text}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)