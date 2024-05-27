import json
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from app.forms import SearchForm
from app.models import Societe, Balance
from utils.ldap import write_log
from utils.script import connexion, get_data_sql, load_json_file, load_affectations_json_file


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
        'target_1': str(int(target) - 1) if target != '---' else '',
        'target_2': str(int(target) - 2) if target != '---' else '',
        'target_3': str(int(target) - 3) if target != '---' else '',
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
    print(data, data['value'])
    records = []
    page = data.get('page', '')

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
                    lambda: {'COMPTE': '', 'DESIGNATION': '', 'C1': '', 'C2': '', 'C3': '', 'CONSO': 0})

                try:
                    affectations = load_affectations_json_file('affectation.json')
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

                # Vérifiez si le fichier JSON est correctement chargé
                if not isinstance(affectations, list):
                    return JsonResponse({'error': 'Le fichier JSON doit être une liste de dictionnaires.'}, status=500)

                affectation_dict = {str(item["COMPTE UNIF"]): item for item in affectations}

                for balance in balances:
                    key = str(balance.compte_unif)  # Convertir en chaîne pour correspondre aux clés du dictionnaire
                    if key not in merged_records:
                        affectation = affectation_dict.get(key, {})
                        merged_records[key] = {
                            'COMPTE': balance.compte_unif,
                            'DESIGNATION': balance.designation,
                            'C1': balance.compte_unif[:1],
                            'C2': balance.compte_unif[:2],
                            'C3': balance.compte_unif[:3],
                            'CONSO': 0,
                            'ACTIF': affectation.get('ACTIF', ''),
                            'PASSIF': affectation.get('PASSIF', ''),
                            'AFFECTATION': affectation.get('AFFECTATION', '')
                        }

                    merged_records[key][balance.societe.value] = balance.montant
                    merged_records[key]['CONSO'] += balance.montant

                for key in merged_records:
                    total_conso = merged_records[key]['CONSO']
                    affectation = affectation_dict.get(key, {})
                    current_affectation = merged_records[key]['AFFECTATION']

                    if current_affectation == '#':
                        if total_conso > 0:
                            merged_records[key]['AFFECTATION'] = affectation.get('ACTIF', '')
                        elif total_conso <= 0:
                            merged_records[key]['AFFECTATION'] = affectation.get('PASSIF', '')
                records = list(merged_records.values())
        elif data['value'] in ['ACTIF', 'PASSIF']:
            if balances.exists():
                try:
                    bilan = load_affectations_json_file('bilan.json')
                    affectations = load_affectations_json_file('affectation.json')
                    affectation_table = load_json_file('config.json')

                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

                if not isinstance(bilan, list):
                    return JsonResponse({'error': 'Le fichier JSON doit être une liste de dictionnaires.'}, status=500)

                if not isinstance(affectations, list):
                    return JsonResponse({'error': 'Le fichier JSON doit être une liste de dictionnaires.'}, status=500)

                merged_records = defaultdict(
                    lambda: {'AFFECTATION': '', 'TYPE': '', 'GROUPE': '', 'CATEGORY': '', 'LIBEL': '',
                             'CONSO': 0, 'NET': 0, 'BRUT': 0, 'AMORTISSEMENT': 0}
                )

                bilan_dict = {str(item["AFFECTATION"]): item for item in bilan}
                affectation_dict = {str(item["COMPTE UNIF"]): item for item in affectations}

                for balance in balances:
                    key = str(balance.compte_unif)
                    affectation_key = affectation_dict.get(key, {}).get('AFFECTATION', '')

                    if affectation_key not in merged_records:
                        merged_records[affectation_key] = {
                            'AFFECTATION': affectation_key,
                            'TYPE': '',
                            'GROUPE': '',
                            'CATEGORY': '',
                            'LIBEL': '',
                            'CONSO': 0,
                            'NET': 0,
                            'BRUT': 0,
                            'AMORTISSEMENT': 0
                        }

                    merged_records[affectation_key]['CONSO'] += balance.montant

                for key in merged_records:
                    current_affectation = merged_records[key]['AFFECTATION']
                    if current_affectation:
                        bilan_info = bilan_dict.get(current_affectation, {})
                        merged_records[key]['TYPE'] = bilan_info.get('TYPE', '')
                        merged_records[key]['GROUPE'] = bilan_info.get('GROUPE', '')
                        merged_records[key]['CATEGORY'] = bilan_info.get('CATEGORY', '')
                        merged_records[key]['LIBEL'] = bilan_info.get('LIBEL', '')

                final_records = defaultdict(
                    lambda: {'AFFECTATION': '', 'TYPE': '', 'GROUPE': '', 'CATEGORY': '', 'LIBEL': '',
                             'CONSO': 0, 'NET': 0, 'BRUT': 0, 'AMORTISSEMENT': 0}
                )
                for record in merged_records.values():
                    key = (record['LIBEL'], record['CATEGORY'], record['GROUPE'], record['TYPE'])
                    final_records[key]['TYPE'] = record['TYPE']
                    final_records[key]['GROUPE'] = record['GROUPE']
                    final_records[key]['CATEGORY'] = record['CATEGORY']
                    final_records[key]['LIBEL'] = record['LIBEL']
                    if data['value'] == 'ACTIF':
                        final_records[key]['CONSO'] += record['CONSO']
                        if record['AFFECTATION'] in affectation_table['ASSIGNATION']['BRUT']:
                            final_records[key]['BRUT'] += record['CONSO']
                        elif record['AFFECTATION'] in affectation_table['ASSIGNATION']['AMORTISSEMENT']:
                            final_records[key]['AMORTISSEMENT'] += (-1 * record['CONSO'])

                        if final_records[key]['AFFECTATION']:
                            final_records[key]['AFFECTATION'] += ', ' + record['AFFECTATION']
                        else:
                            final_records[key]['AFFECTATION'] = record['AFFECTATION']
                    else:
                        final_records[key]['CONSO'] += (-1 * record['CONSO'])
                        final_records[key]['AFFECTATION'] = record['AFFECTATION']

                for record in final_records.values():
                    record['NET'] = record['BRUT'] - record['AMORTISSEMENT']

                records = list(final_records.values())
                records = sorted(records, key=lambda r: r['AFFECTATION'], reverse=False)

                if data['value'] == 'ACTIF':
                    exception = 'PASSIF'
                else:
                    exception = 'ACTIF'
                records = [record for record in records if
                           record['GROUPE'] != '' and record['TYPE'] != '' and record['TYPE'] != exception]

        else:
            if balances.exists():
                try:
                    cn = load_affectations_json_file('cn.json')
                    affectations = load_affectations_json_file('affectation.json')
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

                if not isinstance(cn, list):
                    return JsonResponse({'error': 'Le fichier JSON doit être une liste de dictionnaires.'}, status=500)

                if not isinstance(affectations, list):
                    return JsonResponse({'error': 'Le fichier JSON doit être une liste de dictionnaires.'}, status=500)

                merged_records = defaultdict(
                    lambda: {'AFFECTATION': '', 'ORDER': 0, 'LIBEL': '', 'CONSO': 0}
                )

                cn_dict = {str(item["AFFECTATION"]): item for item in cn}
                affectation_dict = {str(item["COMPTE UNIF"]): item for item in affectations}

                for balance in balances:
                    key = str(balance.compte_unif)
                    affectation_key = affectation_dict.get(key, {}).get('AFFECTATION', '')

                    if affectation_key not in merged_records and str(affectation_key)[:3] != 'BIL' and affectation_key not in ['#', '', ' ', None]:
                        merged_records[affectation_key] = {
                            'AFFECTATION': affectation_key,
                            'ORDER': cn_dict.get(affectation_key, {}).get('ORDER', 0),
                            'LIBEL': cn_dict.get(affectation_key, {}).get('DESIGNATION', ''),
                            'CONSO': 0,
                        }
                    montant = balance.montant
                    if affectation_key in ['CR01', 'CR02', 'CR03', 'CR08', 'CR11', 'CR12', 'CR1', 'CR15']:
                        montant = -1 *  montant

                    merged_records[affectation_key]['CONSO'] += montant


                # Order 4
                cr_values = ['CR01', 'CR02', 'CR03']
                conso_sum_4 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            conso_sum_4 += merged_records[cr]['CONSO']

                merged_records["I - PRODUCTION DE L'EXERCICE"] = {
                    'AFFECTATION': '-',
                    'ORDER': 4,
                    'LIBEL': "I - PRODUCTION DE L'EXERCICE",
                    'CONSO': conso_sum_4
                }

                # Order 7
                cr_values = ['CR04', 'CR05']
                conso_sum_7 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            conso_sum_7 += merged_records[cr]['CONSO']

                merged_records["II - CONSOMMATION DE L'EXERCICE"] = {
                    'AFFECTATION': '-',
                    'ORDER': 7,
                    'LIBEL': "II - CONSOMMATION DE L'EXERCICE",
                    'CONSO': conso_sum_7
                }
                

                # Order 8
                conso_sum_8 = conso_sum_4 - conso_sum_7
                merged_records["III - VALEUR AJOUTEE D'EXPLOITATION (I-II)"] = {
                    'AFFECTATION': '-',
                    'ORDER': 8,
                    'LIBEL': "III - VALEUR AJOUTEE D'EXPLOITATION (I-II)",
                    'CONSO': conso_sum_8
                }

                 # Order 11
                cr_values = ['CR06', 'CR07']
                conso_sum_11 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            conso_sum_11 += merged_records[cr]['CONSO']
                
                conso_sum_11 = conso_sum_8 - conso_sum_11

                merged_records["IV - EXCEDENT BRUT D'EXPLOITATION"] = {
                    'AFFECTATION': '-',
                    'ORDER': 11,
                    'LIBEL': "IV - EXCEDENT BRUT D'EXPLOITATION",
                    'CONSO': conso_sum_11
                }

                # Order 16
                cr_values = ['CR08', 'CR09', 'CR10', 'CR11']
                conso_sum_16 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            if cr in ['CR08', 'CR11']:
                                conso_sum_16 += merged_records[cr]['CONSO']
                            else:
                                conso_sum_16 -= merged_records[cr]['CONSO']
                
                conso_sum_16= conso_sum_11 + conso_sum_16

                merged_records["V - RESULTAT OPERATIONNEL"] = {
                    'AFFECTATION': '-',
                    'ORDER': 16,
                    'LIBEL': "V - RESULTAT OPERATIONNEL",
                    'CONSO': conso_sum_16
                }

                # Order 19
                cr_values = ['CR12', 'CR13']
                conso_sum_19 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            if cr in ['CR12']:
                                conso_sum_19 += merged_records[cr]['CONSO']
                            else:
                                conso_sum_19 -= merged_records[cr]['CONSO']
            

                merged_records["VI - RESULTAT FINANCIER"] = {
                    'AFFECTATION': '-',
                    'ORDER': 19,
                    'LIBEL': "VI - RESULTAT FINANCIER",
                    'CONSO': conso_sum_19
                }

                # Order 20
                conso_sum_20 = conso_sum_16 + conso_sum_19
                merged_records["VII - RESULTAT AVANT IMPOTS (V+VI)"] = {
                    'AFFECTATION': '-',
                    'ORDER': 20,
                    'LIBEL': "VII - RESULTAT AVANT IMPOTS (V+VI)",
                    'CONSO': conso_sum_20
                }

    
                # Order 23
                cr_values = ['CR08', 'CR11', 'CR12']
                conso_sum_23 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            conso_sum_23 += merged_records[cr]['CONSO']
                conso_sum_23 = conso_sum_4 + conso_sum_23
                merged_records["TOTAL DES PRODUITS DES ACTIVITES ORDINAIRES"] = {
                    'AFFECTATION': '-',
                    'ORDER': 23,
                    'LIBEL': "TOTAL DES PRODUITS DES ACTIVITES ORDINAIRES",
                    'CONSO': conso_sum_23
                }

                # Order 24
                cr_values = ['CR04', 'CR05', 'CR06', 'CR07', 'CR09', 'CR10', 'CR13', 'CR14']
                conso_sum_24 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            conso_sum_24 += merged_records[cr]['CONSO']
                merged_records["TOTAL DES CHARGES DES ACTIVITES ORDINAIRES"] = {
                    'AFFECTATION': '-',
                    'ORDER': 24,
                    'LIBEL': "TOTAL DES CHARGES DES ACTIVITES ORDINAIRES",
                    'CONSO': conso_sum_24
                }

                # Order 25
                conso_sum_25 = conso_sum_23 - conso_sum_24
                merged_records["VIII - RESULTAT NET DES ACTIVITES ORDINAIRES"] = {
                    'AFFECTATION': '-',
                    'ORDER': 25,
                    'LIBEL': "VIII - RESULTAT NET DES ACTIVITES ORDINAIRES",
                    'CONSO': conso_sum_25
                }

                # Order 28
                cr_values = ['CR15', 'CR16']
                conso_sum_28 = 0
                for cr in cr_values:
                    if cr in merged_records:
                            if cr in ['CR15']:
                                conso_sum_28 += merged_records[cr]['CONSO']
                            else:
                                conso_sum_28 -= merged_records[cr]['CONSO']
                merged_records["IX - RESULTAT EXTRAORDINAIRE"] = {
                    'AFFECTATION': '-',
                    'ORDER': 28,
                    'LIBEL': "IX - RESULTAT EXTRAORDINAIRE",
                    'CONSO': conso_sum_28
                }


                # Order 29
                conso_sum_29 = conso_sum_25 - conso_sum_28
                merged_records["X - RESULTAT NET DE L'EXERCICE"] = {
                    'AFFECTATION': '-',
                    'ORDER': 29,
                    'LIBEL': "X - RESULTAT NET DE L'EXERCICE",
                    'CONSO': conso_sum_29
                }



                records = list(merged_records.values())
                records = sorted(records, key=lambda r: r['ORDER'], reverse=False)

                records = [record for record in records if record['AFFECTATION'] != '']

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
                                        'designation': row['DESI    GNATION'],
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
