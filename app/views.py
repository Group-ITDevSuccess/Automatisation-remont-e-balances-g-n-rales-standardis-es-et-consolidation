from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from app.forms import SearchForm


# Create your views here.
@login_required
def index(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
    else:
        form = SearchForm()
    return render(request, 'app/index.html', {
        'path': request.path,
        'search_form': form
    })
