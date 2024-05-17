import json
from datetime import date
from decimal import Decimal

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from app.forms import SearchForm
from app.models import Societe, Events, Balance
from utils.ldap import write_log
from utils.script import connexion, get_data_sql


# Create your views here.
@login_required
def index(request):
    target = '---'
    saved = False
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            target = form.cleaned_data['target']
            saved = Events.objects.filter(date=int(target)).exists()
    else:
        form = SearchForm()
    return render(request, 'app/index.html', {
        'path': request.path,
        'target': target,
        'saved': saved,
        'search_form': form
    })


@csrf_exempt
@login_required
def get_data_for_event(request):
    data = json.loads(request.body)
    print(data)
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


@csrf_exempt
@login_required
def add_data_for_event(request):
    data = json.loads(request.body)
    societes = Societe.objects.filter(active__exact=True).order_by('name')
    try:
        for societe in societes:
            conn = None
            try:
                conn = connexion(societe)
                if conn is not None:
                    with conn:
                        gets = get_data_sql(connection=conn, societe=societe, value='BLG', target=data['target'])
                        if not gets.empty:
                            for index, row in gets.iterrows():
                                debit = float(row.get('DEBIT', None))
                                credit = float(row.get('CREDIT', None))
                                montant = float(row.get('SOLDE', None))
                                balance, created = Balance.objects.get_or_create(
                                    societe=societe,
                                    compte_sage=row['COMPTE_SAGE'],
                                    defaults={
                                        'compte_unif': row['COMPTE_UNIF'],
                                        'designation': row['DESIGNATION'],
                                        'debit': debit,
                                        'credit': credit,
                                        'montant': montant,
                                        'created_at': timezone.now(),
                                        'updated_at': timezone.now()
                                    }
                                )
                                if not created:
                                    balance.compte_unif = row['COMPTE_UNIF']
                                    balance.designation = row['DESIGNATION']
                                    balance.debit = row['DEBIT']
                                    balance.credit = row['CREDIT']
                                    balance.montant = row['SOLDE']
                                    balance.updated_at = timezone.now()
                                    balance.save()

                                # Create or update Events
                                event, event_created = Events.objects.get_or_create(
                                    date=data['target'],  # Assuming DATE is the field in gets data
                                    defaults={'balance': balance}
                                )
                                if not event_created:
                                    event.balance = balance
                                    event.save()
            except Exception as e:
                write_log(str(e))
                print("Error in processing societes:", e)
                return JsonResponse({'success': False, 'error': str(e)})
            finally:
                if conn is not None:
                    conn.close()
    except Exception as e:
        write_log(str(e))
        print("Error in processing societes:", e)
        return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': True}, safe=False)
