from django.shortcuts import render

# Create your views here.
def view_camera(request):
    return render(request, 'webPage.html')