
from django.http import JsonResponse


def handler404(request, exception):
    message = ('Route not found')
    response = JsonResponse(data={'error': message})
    response.status_code = 404
    return response
    # return render(request, '404.html', status=404)


def handler500(request):
    message = ('Internal server error. Please try again later')
    response = JsonResponse(data={'error': message})
    response.status_code = 500
    return response
