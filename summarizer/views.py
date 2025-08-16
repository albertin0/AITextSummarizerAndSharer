# summarizer_project/summarizer/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import json
from groq import Groq

from .models import Transcript

# Configure the Gemini API with the key from settings.py
client = Groq(api_key=settings.GROQ_API_KEY)

def home(request):
    """
    View for the main page. Handles transcript upload and summary generation.
    """
    if request.method == 'POST':
        transcript_file = request.FILES.get('transcript')
        custom_prompt = request.POST.get('prompt')

        if not transcript_file:
            return render(request, 'summarizer/home.html', {'error': 'Please upload a transcript file.'})

        try:
            transcript_text = transcript_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return render(request, 'summarizer/home.html', {'error': 'Invalid file format. Please upload a valid text file.'})

        # Call the new, real AI function
        summary = generate_ai_summary(transcript_text, custom_prompt)

        # If the API call failed, the summary will contain an error message
        if "API Error:" in summary:
             return render(request, 'summarizer/home.html', {'error': summary})

        transcript_obj = Transcript.objects.create(
            original_text=transcript_text,
            summary_text=summary
        )
        return redirect('summary_view', transcript_id=transcript_obj.id)

    return render(request, 'summarizer/home.html')

def generate_ai_summary(transcript, prompt):
    """
    Generates a summary using the Gemini API.
    """
    model = "llama-3.3-70b-versatile"
    
    # Construct a more robust prompt for the AI
    full_prompt = f"""
    **Instruction:**
    {prompt}

    **Transcript:**
    ---
    {transcript}
    ---

    Please provide a response based on the instruction above.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages = [
                {
                    "role":"user",
                    "content":full_prompt
                }
            ],
            model = model
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        # Handle potential API errors gracefully
        print(f"An error occurred with the Gemini API: {e}")
        return f"API Error: Could not generate summary. Please check the server logs. Details: {e}"


def summary_view(request, transcript_id):
    """
    Displays the generated summary for viewing and editing.
    """
    transcript = get_object_or_404(Transcript, id=transcript_id)
    return render(request, 'summarizer/summary.html', {'transcript': transcript})

def update_summary(request, transcript_id):
    """
    Handles AJAX request to update the summary text.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_summary = data.get('summary_text')
            transcript = get_object_or_404(Transcript, id=transcript_id)
            transcript.summary_text = new_summary
            transcript.save()
            return JsonResponse({'status': 'success', 'message': 'Summary updated successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


def share_summary(request, transcript_id):
    """
    Handles sharing the summary via email.
    """
    transcript = get_object_or_404(Transcript, id=transcript_id)
    if request.method == 'POST':
        recipients = request.POST.get('recipients')
        if recipients:
            recipient_list = [email.strip() for email in recipients.split(',')]
            
            subject = 'Your AI-Generated Summary'
            html_message = render_to_string('summarizer/email_template.html', {'summary': transcript.summary_text})
            
            try:
                send_mail(
                    subject,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    html_message=html_message,
                    fail_silently=False,
                )
                return JsonResponse({'status': 'success', 'message': f'Summary sent to {", ".join(recipient_list)}'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'An error occurred: {e}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)