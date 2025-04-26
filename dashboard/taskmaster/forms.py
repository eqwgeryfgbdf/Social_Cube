from django import forms
from .models import Task, TaskTag


class TaskForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=TaskTag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'status', 'due_date', 'tags']
        
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tags'].initial = self.instance.tag_assignments.values_list('tag', flat=True)


class TaskTagForm(forms.ModelForm):
    class Meta:
        model = TaskTag
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }