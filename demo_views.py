from django.shortcuts import render
from django.views.generic import TemplateView


class DemoPremiumView(TemplateView):
    """Affiche la démonstration du design premium"""
    template_name = 'demo_premium.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Démonstration Design Premium'
        return context
