# messagerie/templatetags/message_filters.py
from django import template
import os

register = template.Library()


@register.filter
def basename(filepath):
    """Extrait le nom du fichier d'un chemin complet"""
    if filepath:
        return os.path.basename(filepath.name)
    return ''


@register.filter
def file_size(filepath):
    """Retourne la taille du fichier en format lisible"""
    if filepath:
        size = filepath.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
    return '0 B'
