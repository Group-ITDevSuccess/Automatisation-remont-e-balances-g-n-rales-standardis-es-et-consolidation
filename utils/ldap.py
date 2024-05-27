import logging
import os
from datetime import datetime

import ldap3
from django.conf import settings
from ldap3 import Server, Connection
from ldap3.core.exceptions import LDAPException

today = datetime.today().strftime('%d-%m-%Y')


def ldap_search_attributes(conn, username):
    search_base = settings.DN_LDAP
    # search_filter = f"(&(sAMAccountName={username}))"
    search_filter = f"(&(sAMAccountName={username}))"
    try:
        conn.search(search_base, search_filter, attributes=['mail', 'sn', 'givenName'])

        if len(conn.entries) > 0:
            entry = conn.entries[0]
            # write_log(f"Utilisateur Trouver : {entry}", level=logging.INFO)

            email = entry.mail[0] if 'mail' in entry else None
            lastname = entry.sn[0] if 'sn' in entry else None
            firstname = entry.givenname[0] if 'givenName' in entry else None

            return {
                'email': email,
                'lastname': lastname,
                'firstname': firstname
            }
    except LDAPException as e:
        write_log(f"Erreur de recherche LDAP : {str(e)}")
        return False


# Définition de la fonction pour la connection LDAP
def ldap_login_connection(username, password):
    user = f"SMTP-GROUP\\{username}".strip()
    # write_log(f"DN: {user} : {password}", level=logging.INFO)
    try:
        server = Server(settings.SERVER_LDAP, get_info=ldap3.ALL)

        with Connection(
                server=server,
                user=user,
                password=password,
                authentication=ldap3.SIMPLE,
                client_strategy=ldap3.SYNC) as conn:

            if not conn.bind():
                write_log("Bind Error !", level=logging.ERROR)
                return False
            write_log("Bind Successfully !", level=logging.INFO)
            return ldap_search_attributes(conn, username)

    except LDAPException as e:
        write_log(f"Erreur de connexion LDAP : {str(e)}")
        return False


def write_log(logs, level=None):
    log_file = os.path.join('logs', f'{today}.log')

    logging.basicConfig(filename=log_file, encoding='utf-8', level=level,
                        format='%(asctime)s - %(name)s - %(levelname)s : %(message)s')

    logger = logging.getLogger(__name__)

    if level == logging.ERROR:
        logger.error(logs)
    elif level == logging.INFO:
        logger.info(logs)
    elif level == logging.CRITICAL:
        logger.critical(logs)
    else:
        logger.exception(logs)
