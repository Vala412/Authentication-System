from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render


class IndexPageView(TemplateView):
    def get(self, request):
        return render(request, 'content/main/index.html')


class ChangeLanguageView(TemplateView):
    def get(self, request):
        # Logic to change the language can be added here
        return render(request, 'content/main/change_language.html')  # Update this path as needed
