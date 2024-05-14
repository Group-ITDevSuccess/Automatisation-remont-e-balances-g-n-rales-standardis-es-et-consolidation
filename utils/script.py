import decimal
import json
import locale
import os
import uuid
from datetime import datetime, date
import calendar

import pyodbc
import pandas as pd
from django.conf import settings

from utils.ldap import write_log


def connexion(server, name, base, username, password):
    conn = None
    value_input = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database={base};UID={username};" \
                  f"PWD={password}"
    try:
        # print(value_input)
        conn = pyodbc.connect(value_input)
    # except pyodbc.Error as e:
    #     write_log(f"Erreur de connexion : {str(e)}")
    except Exception as e:
        # write_log(str(e))
        print(f"Erreur de connexion sur {name}: {value_input}")
        pass

    return conn


def get_data_sql(sql, connection, colonnes, societe, target, site):
    df = None
    try:
        sql = str(sql) \
            .replace('{table}', str(societe.table)) \
            .replace('<base>', str(societe.base)) \
            .replace('<value>', str(societe.value)) \
            .replace('<site>', str(site)) \
            .replace('<target>', str(target))

        # print("===============================")
        # print(f"SQL : {sql} ")
        # print("===============================")
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            if rows:
                rows = [tuple(row) for row in rows]
                if all(isinstance(row, tuple) for row in rows):
                    df = pd.DataFrame(rows, columns=colonnes)
                    if not df.empty:
                        df['UID'] = ''
                        df['CPTE_PCU'] = 0
                        df['CPTE_STU'] = 0
                        df['FICHE'] = 0
                        df['ECART'] = 0
                        df['VAL_ECART'] = 0
                        df['ACTEUR'] = None
                        df['COMMENT'] = ''
                    else:
                        print("Warning: DataFrame is empty. 'ECART' column not added.")

    except pyodbc.Error as e:
        write_log(f"Erreur execute_sql : {str(e)}")
        print(f"Erreur execute_sql by pydodbc : {str(e)}")
        print("===============================")
        print(f"SQL : {sql} ")
        print("===============================")
    except Exception as e:
        write_log(f"Erreur execute_sql : {str(e)}")
        print(f"Erreur execute_sql : {str(e)}")
    return df


def clean_decimal(value):
    if value:
        try:
            return decimal.Decimal(value.strip())  # Remove leading/trailing whitespace
        except decimal.InvalidOperation:
            return None  # Set to None if conversion fails
    return None


def get_all_site(conn, societe, sql):
    code_choices = []
    try:
        cursor = conn.cursor()
        sql = str(sql).replace('{table}', societe.table).replace('<value>', societe.value)
        # print("===============================")
        # print(f"SQL : {sql} ")
        # print("===============================")
        cursor.execute(sql)

        # Récupération des résultats
        rows = cursor.fetchall()
        if rows:
            rows = [tuple(row) for row in rows]
            if all(isinstance(row, tuple) for row in rows):
                df = pd.DataFrame(rows, columns=['CODE', 'SOCIETE'])
                grouped_options = df.groupby('SOCIETE')['CODE'].apply(lambda x: list(zip(x, x))).reset_index()
                for _, group in grouped_options.iterrows():
                    code_choices.append((group['SOCIETE'], group['CODE']))
        cursor.close()
        conn.close()

    except pyodbc.Error as e:
        print("Erreur lors de la connexion à la base de données:", str(e))
        # write_log(str(e))
    except Exception as e:
        # write_log(f"{str(e)}")
        pass
    return code_choices


def get_sql_in_json(chemin_fichier):
    try:
        with open(chemin_fichier, 'r') as fichier:
            contenu_json = json.load(fichier)
            return contenu_json
    except FileNotFoundError:
        print(f"Le fichier {chemin_fichier} n'a pas été trouvé.")
    except json.JSONDecodeError as e:
        print(f"Erreur lors de la lecture du fichier JSON : {e}")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")


def get_sql(path):
    base, query, value = extract_from_path(path)

    file = os.path.join(settings.BASE_DIR, 'sql.json')
    contenu = get_sql_in_json(file)
    valeur = None
    if contenu is not None:
        try:
            valeur = contenu[base][query][value]
        except KeyError as e:
            print(f"La clé {e} n'a pas été trouvée dans le fichier JSON.")
        except TypeError as e:
            print(f"Erreur de type : {e}")

    return valeur


def get_month_names(year, local_value=True):
    if local_value:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    current_year = datetime.now().year

    year = int(year)
    if year != current_year:
        return [calendar.month_name[i].capitalize() for i in range(1, 13)]
    else:
        current_month = datetime.now().month
        return [calendar.month_name[i].capitalize() for i in range(1, current_month + 1)]


def extract_from_path(path):
    segments = path.lstrip('/').split('/')

    if len(segments) >= 3:
        base = segments[0]
        query = segments[1]
        table = segments[2]

        return base, query, table
    else:
        return None


def are_valid_uuids(values):
    if isinstance(values, list):
        uuids = []

        for value in values:
            try:
                uid = uuid.UUID(value)
                uuids.append(uid)
            except ValueError:
                return None

        return uuids
    else:
        try:
            uid = uuid.UUID(values)
            return uid
        except ValueError:
            return None


def get_data(sql, conn, columns=None):
    df = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

            if rows:
                rows = [tuple(row) for row in rows]
                if all(isinstance(row, tuple) for row in rows):
                    df = pd.DataFrame(rows, columns=columns)
            else:
                return df

        return df
    except Exception as e:
        write_log(f"Erreur execute_sql : {str(e)}")
        return df
