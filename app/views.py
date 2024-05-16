import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from app.forms import SearchForm
from app.models import Societe
from utils.ldap import write_log
from utils.script import connexion, get_data_sql


# Create your views here.
@login_required
def index(request):
    target = '---'
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
    data = json.loads(request.body)
    records = []
    page = data['page']
    if data['target'] != '---':
        societes = Societe.objects.filter(active__exact=True).order_by('name')
        try:
            for societe in societes:
                conn = None
                try:
                    conn = connexion(societe)
                    if conn is not None:
                        with conn:

                            gets = get_data_sql(connection=conn, societe=societe, value=data['value'],
                                                target=data['target'])
                            records.extend(gets.to_dict(orient='records'))

                            if gets is not None:
                                pass
                            # print("===============================")
                            # print(f"DATA : {gets} ")
                            # print("===============================")
                    else:
                        print("Connection not established for:", societe.name)

                except Exception as e:
                    write_log(str(e))
                    print("Error: ", data.get('value'), e)
                    pass
                finally:
                    if conn is not None:
                        conn.close()
        except Exception as e:
            write_log(str(e))
            print("Error in processing societes:", e)
    return JsonResponse({'last_page': page, 'data': records}, safe=False)
