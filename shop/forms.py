from django import forms
from .models import Resource, Comment  

class ResourceUploadForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'file', 'lesson']

        from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escribe tu comentario'}),
            'rating': forms.Select(attrs={'class': 'form-select'}, choices=[(i, i) for i in range(1, 6)]),
        }