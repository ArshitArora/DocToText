from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import os
from docx import Document
from PyPDF2 import PdfReader
import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import json
from pytube import YouTube
from moviepy.editor import AudioFileClip
from docx import Document
from PyPDF2 import PdfReader
import tempfile
import whisper
import base64
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import os
from . import services

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key='api_key')
os.environ['GOOGLE_API_KEY'] = api_key

EMBEDDING_MODEL = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en")
LLM = ChatGoogleGenerativeAI(model='gemini-1.5-flash',
                             temperature=0.4,
                             max_output_tokens=512)

def health_check():
    return JsonResponse({"message":"Everything is working fine"})
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
def audio_to_text(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        if file.name.endswith('.mp3'):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
                    for chunk in file.chunks():
                        temp_audio_file.write(chunk)
                    temp_audio_path = temp_audio_file.name

                model = whisper.load_model("base")
                result = model.transcribe(temp_audio_path)
                text = result['text']

                return JsonResponse({"text": text}, status=200)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        else:
            return JsonResponse({"error": "Invalid file format. Only .pdf allowed."}, status=400)

    return JsonResponse({"error": "Invalid request method or missing file."}, status=400)

@csrf_exempt
def image_to_text(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        print(file.name)
        if file.name[file.name.index("."):] in ['.jpg','.png','.jpeg']:
            try:
                image_data = file.read()
                b64_encoded_data = base64.b64encode(image_data)
                b64_encoded_string = b64_encoded_data.decode('utf-8')
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", "Describe all the details in the provided image, be verbose."),
                        (
                            "user", [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": "data:image/jpeg;base64,{image_data}"}
                                }
                            ]
                        ),
                        ("user", "Describe the given image. Explain everything in details, be very verbose")
                    ]
                )
                chain = prompt | LLM
                text = chain.invoke({"image_data": b64_encoded_string})

                return JsonResponse({"text": text.content}, status=200)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        else:
            return JsonResponse({"error": "Invalid file format. Only .pdf allowed."}, status=400)

    return JsonResponse({"error": "Invalid request method or missing file."}, status=400)

@csrf_exempt
def create_image_db(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        user = request.POST.get('text')
        print(file.name)
        if file.name[file.name.index("."):] in ['.jpg','.png','.jpeg']:
            try:
                image_data = file.read()
                b64_encoded_data = base64.b64encode(image_data)
                b64_encoded_string = b64_encoded_data.decode('utf-8')
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", "Describe all the details in the provided image, be verbose."),
                        (
                            "user", [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": "data:image/jpeg;base64,{image_data}"}
                                }
                            ]
                        ),
                        ("user", "Describe the given image. Explain everything in details, be very verbose")
                    ]
                )
                chain = prompt | LLM
                text = chain.invoke({"image_data": b64_encoded_string})

                services.load_to_vector_store(user,text.content)

                return JsonResponse({"message":"DB for image created successfully"}, status=200)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)

        else:
            return JsonResponse({"error": "Invalid file format. Only .pdf allowed."}, status=400)

    return JsonResponse({"error": "Invalid request method or missing file."}, status=400)

@csrf_exempt
def chat_with_image(request):
    if request.method == 'POST':
        # Parse the JSON data from the request body
        data = json.loads(request.body)
        question = data.get('question')
        user = data.get('user')
        chroma_vector_store = Chroma(
            persist_directory=user + "_db",
            collection_name='vector_index',
            embedding_function=EMBEDDING_MODEL,
        )
        retriever = chroma_vector_store.as_retriever()
        answer = services.chat(user, question, retriever)
        print(f'reponse : {answer}')
        return JsonResponse({'question': question, 'answer': answer})






