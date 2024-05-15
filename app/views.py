import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from app.forms import SearchForm
from app.models import Societe
from utils.ldap import write_log
from utils.script import connexion


# Create your views here.
@login_required
def index(request):
    target = date.today().year
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            target = form.cleaned_data['target']
    else:
        form = SearchForm()
    return render(request, 'app/index.html', {
        'path': request.path,
        'target': target,
        'search_form': form
    })


@csrf_exempt
@login_required
def get_data_for_table(request):
    print(request.body)
    data = json.loads(request.body)
    societes = Societe.objects.all().order_by('name')
    print(societes.count())
    try:
        for societe in societes:
            conn = None
            try:
                conn = connexion(societe)
                if conn is not None:
                    print(conn)
                    with conn:
                        print(conn)
                else:
                    print("Connection not established for:", societe.name)

            except Exception as e:
                write_log(str(e))
                print("Error:", e)
            finally:
                if conn is not None:
                    conn.close()
    except Exception as e:
        write_log(str(e))
        print("Error in processing societes:", e)
    return JsonResponse({'last_page': data.get('page'), 'data': []}, safe=False)
