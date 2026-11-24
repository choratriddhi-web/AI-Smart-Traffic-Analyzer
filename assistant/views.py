import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.decorators import mongo_login_required
from services.assistant_service import AITrafficAssistant

@mongo_login_required
def assistant_chat_view(request):
    """
    Renders the AI Traffic Chat Assistant and Voice Assistant Interface.
    Accessible to registered citizens and authenticated users.
    Integrated with Web Speech API for real-time speech-to-text and spoken audio output.
    """
    return render(request, 'assistant/index.html')

@csrf_exempt
def assistant_query_api(request):
    """
    API endpoint for text or voice assistant questions.
    Returns real, factual answers derived from system services.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            question = data.get('query', '')
        except Exception:
            question = request.POST.get('query', '')

        if not question:
            return JsonResponse({'status': 'error', 'message': 'No query provided.'}, status=400)

        response_data = AITrafficAssistant.ask(question)
        return JsonResponse({
            'status': 'success',
            'query': question,
            'answer': response_data['answer'],
            'intent': response_data.get('intent', 'unknown'),
            'sources': response_data.get('sources', [])
        })

    return JsonResponse({'status': 'error', 'message': 'Only POST method is supported.'}, status=405)
