import json
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from app.forms import SearchForm
from app.models import Societe, Balance
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
            saved = Balance.objects.filter(target=int(target)).exists()
    else:
        form = SearchForm()
    return render(request, 'app/index.html', {
        'path': request.path,
        'target': target,
        'saved': saved,
        'search_form': form
    })


def get_societe_balances():
    # Récupérer toutes les sociétés actives
    societes = Societe.objects.filter(active=True)

    # Initialiser un dictionnaire pour stocker les données de solde
    balances_data = {}

    # Parcourir chaque société pour calculer son solde
    for societe in societes:
        # Récupérer les balances pour cette société et calculer le solde total
        solde_total = Balance.objects.filter(societe=societe).aggregate(
            solde=Sum('montant', field='debit - credit')
        )['solde'] or 0  # Si le solde est None, le remplacer par 0

        # Ajouter les données de solde au dictionnaire
        balances_data[societe.name] = solde_total

    return balances_data


@csrf_exempt
@login_required
def get_data_for_event(request):
    data = json.loads(request.body)
    print(data)
    records = []
    page = data['page']
    if data['target'] != '---':
        balances = Balance.objects.filter(target=int(data['target'])).order_by('societe__name')
        if data['value'] == 'BLG':
            if balances.exists():
                balances = balances.annotate(
                    UID=F('uid'),
                    DEBIT=F('debit'),
                    CREDIT=F('credit'),
                    SOLDE=F('montant'),
                    DESIGNATION=F('designation'),
                    COMPTE_SAGE=F('compte_sage'),
                    COMPTE_UNIF=F('compte_unif'),
                    SOCIETE=F('societe__name'),
                ).values('UID', 'SOCIETE', 'COMPTE_SAGE', 'COMPTE_UNIF', 'DEBIT', 'CREDIT', 'SOLDE', 'DESIGNATION')
                records = [{key: value for key, value in balance.items()} for balance in balances]
            else:
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

        elif data['value'] == 'ALL':
            if balances.exists():
                merged_records = defaultdict(
                    lambda: {'COMPTE': '', 'DESIGNATION': '', 'C1': '', 'C2': '', 'C3': '', 'CONSO': 0,
                             'CONSO_EURO': 0})

                for balance in balances:
                    key = balance.compte_unif
                    if key not in merged_records:
                        merged_records[key] = {
                            'COMPTE': balance.compte_unif,
                            'DESIGNATION': balance.designation,
                            'C1': balance.compte_unif[:1],
                            'C2': balance.compte_unif[:2],
                            'C3': balance.compte_unif[:3],
                            'CONSO': 0,  # Initialisation à 0
                            'CONSO_EURO': 0  # Initialisation à 0
                        }
                    merged_records[key][balance.societe.name] = balance.montant
                    merged_records[key]['CONSO'] += balance.montant
                    merged_records[key][
                        'CONSO_EURO'] += balance.montant / 4728.55
                records = list(merged_records.values())
                print(records)

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
                                        'target': data['target'],
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
