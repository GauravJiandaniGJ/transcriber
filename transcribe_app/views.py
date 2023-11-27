from django.shortcuts import render, redirect
from .forms import AudioFileForm, SummarizeTextForm
import speech_recognition as sr
from pydub import AudioSegment
from multiprocessing import Pool
from django.http import FileResponse, HttpResponse
import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")


def transcribe_audio_view(request):
    """
    View for handling audio transcription and text summarization.
    """
    if request.method == "POST":
        action = request.POST["action"]

        if action == "transcribe":
            form = AudioFileForm(request.POST, request.FILES)
            if form.is_valid():
                instance = form.save()
                wav_file_path = convert_audio_to_wav(instance.audio.path)

                # Split audio into 5-minute chunks
                audio = AudioSegment.from_wav(wav_file_path)
                chunk_length = 5 * 60 * 1000  # 5 minutes in milliseconds
                chunks = [
                    audio[i : i + chunk_length]
                    for i in range(0, len(audio), chunk_length)
                ]
                chunk_paths = []

                # Export each chunk as a separate WAV file
                for index, chunk in enumerate(chunks):
                    chunk_path = f"{wav_file_path}_chunk_{index}.wav"
                    chunk.export(chunk_path, format="wav")
                    chunk_paths.append(chunk_path)

                # Transcribe each chunk in parallel using multiprocessing
                with Pool(processes=4) as pool:
                    transcriptions = pool.map(transcribe_audio_chunk, chunk_paths)

                # Combine all transcriptions into one final transcription
                final_transcription = " ".join(transcriptions)

                # Save the transcription to a text file
                transcription_file_path = f"{wav_file_path}.txt"
                with open(transcription_file_path, "w") as file:
                    file.write(final_transcription)

                # Clean up temporary files
                os.remove(wav_file_path)
                for chunk_path in chunk_paths:
                    os.remove(chunk_path)

                # Serve the transcription text file for download
                response = FileResponse(
                    open(transcription_file_path, "rb"),
                    as_attachment=True,
                    filename="transcription.txt",
                )
                return response

        elif action == "summarize":
            form = SummarizeTextForm(request.POST, request.FILES)
            if form.is_valid():
                text_file = request.FILES["text_data"]

                # Read the contents of the uploaded text file
                text_to_summarize = text_file.read().decode("utf-8")

                # Call the OpenAI API to summarize the text
                try:
                    response = openai.ChatCompletion.create(
                        model="text-davinci-003",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant.",
                            },
                            {
                                "role": "user",
                                "content": "Summarize the following text:",
                            },
                            {"role": "user", "content": text_to_summarize},
                        ],
                    )
                    summary = response["choices"][0]["message"]["content"]

                except Exception as e:
                    print("Error occurred while calling OpenAI API:", e)
                    return HttpResponse(e)

                # Create a response with the summary as a downloadable text file
                response = HttpResponse(summary, content_type="text/plain")
                response["Content-Disposition"] = 'attachment; filename="summary.txt"'
                return response

    else:
        form = AudioFileForm()

    return render(request, "upload.html", {"form": form})


def convert_audio_to_wav(file_path):
    """
    Converts an audio file to WAV format.
    """
    audio = AudioSegment.from_file(file_path)

    # Adjusting the audio properties
    audio = audio.set_frame_rate(16000)  # Set to 16kHz
    audio = audio.set_channels(1)  # Convert stereo to mono

    wav_file_path = file_path + ".wav"
    audio.export(wav_file_path, format="wav")
    return wav_file_path


def transcribe_audio_chunk(audio_chunk_path):
    """
    Transcribes a single audio chunk using speech recognition.
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_chunk_path) as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_sphinx(audio_data)
    return text
