import requests
import csv
import os
import time
from fastapi import FastAPI, HTTPException

#===Inicializacion de la app===
app = FastAPI()

#Ruta donde se guarda la base de datos
RUTA_CSV = "pokemones.csv"

#===Funciones auxiliares===
def consultar_pokeapi(clave):
    "Consulta a la PokeAPI buscando por ID o nombre"
    busqueda = str(clave).lower().strip()
    url = f"https://pokeapi.co/api/v2/pokemon/{busqueda}"
    try: 
        #Consulta a la PokéAPI con un tiempo límite de 5 segundos 
        respuesta = requests.get(url, timeout=5) 
        
        #Si la PokéAPI nos devuelve algo distinto a 200 OK (por ejemplo, error 404), significa que el Pokémon no existe, 
        #así que devuelve None 
        if respuesta.status_code != 200:
            return None 
    
        #Convertimos la respuesta JSON a un diccionario de Python
        datos = respuesta.json()    
        #Estadisticas
        stats = {s["stat"]["name"]: s["base_stat"] for s in datos["stats"]}

        #Devolviendo los 10 atributos necesarios
        return {
            "id": datos["id"],
            "nombre": datos["name"],
            "tipo": datos["types"][0]["type"]["name"],
            "altura": datos["height"],
            "peso": datos["weight"],
            "experiencia_base": datos["base_experience"],
            "hp": stats.get("hp", 0),
            "ataque": stats.get("attack", 0),
            "defensa": stats.get("defense", 0),
            "velocidad": stats.get("speed", 0),
        }
    # Si ocurre un problema de red o conexión, atrapamos el error y devolvemos None         
    except requests.exceptions.RequestException: 
        return None
    
def buscar_en_csv(clave):
    "Busca un pokemon en el archivo CSV por nombre o ID, si lo encuentra, convierte los valores numericos como texto"
    clave_buscada = str(clave).lower().strip()  #La busqueda se pone en minuscula y sin espacios
    #Si en el archivo no existe, devuelve None 
    if not os.path.exists(RUTA_CSV):
        return None
    try:
        with open(RUTA_CSV, "r") as f:  #Abre el archivo en modo lectura
            lector = csv.DictReader(f)  #Lee la primer fila como encabezado y convierte cada fila en un diccionario.
            #En este for se compara si el nombre (en minuscula) o id es igual a clave_buscada 
            for fila in lector: 
                if fila["nombre"].lower() == clave_buscada or fila["id"] == clave_buscada:
                    #Devuelve el diccionario completo con los valores numericos como entero
                    return { 
                    "id": int(fila["id"]),
                    "nombre": fila["nombre"],
                    "tipo": fila["tipo"],
                    "altura": int(fila["altura"]),
                    "peso": int(fila["peso"]),
                    "experiencia_base": int(fila["experiencia_base"]),
                    "hp": int(fila["hp"]),
                    "ataque": int(fila["ataque"]),
                    "defensa": int(fila["defensa"]),
                    "velocidad": int(fila["velocidad"]),
                    }
        #En cambio, si recorrió todo y no encontró coincidencias, devuelve None
        return None
    except FileNotFoundError:
        pass
    
def guardar_en_csv(pokemon):
    """Inserta un nuevo pokemon en el archivo CSV en pokemones.csv, 
si el archivo no existe, escribe primero la fila de encabezados"""
    #Verifica que el archivo exista antes de abrirlo para escribir el encabezado o no.
    existe_archivo = os.path.exists(RUTA_CSV)
    with open(RUTA_CSV, "a", newline="") as f: #Abre el archivo en modo append
        #Lista ordenada con los 10 campos requeridos
        campos = [
            "id", 
            "nombre", 
            "tipo", 
            "altura", 
            "peso", 
            "experiencia_base", 
            "hp", 
            "ataque", 
            "defensa", 
            "velocidad",
            ]
        escritor = csv.DictWriter(f, fieldnames=campos) #Claves del diccionario con los nombres de las columnas
        #Si el archivo no existe, al crear el archivo, pone la primera fila como los nombres de las columnas
        if existe_archivo is False: 
            escritor.writeheader()      
        escritor.writerow(pokemon)  #Escribe los valores del pokemon como fila 


#===Endpoints de FastAPI===
@app.get("/")
def inicio():
    "Endpoint de bienvenida"
    return "Bienvenido a la PokeAPI"


@app.get("/pokemon/{clave}")
def buscar_pokemon(clave: str):
    """Endpoint principal que implementa el sistema de caché: 
        1. Verifica primero en pokemones.csv
        2. Si esta, responde con origen: CSV
        3. Si no esta, busca los datos en la PokeAPI, guarda los datos en CSV y responde con origen: PokeAPI
        4. Si no existe el pokemon, responde con un error"""
        
    t_inicio = time.perf_counter()   #Inicio cronometro
    #Busqueda en la cache local
    pokemon_csv = buscar_en_csv(clave)
    if pokemon_csv is not None:
        t_fin = time.perf_counter()    #Corta el cronometro y se realizan conversiones en ms
        tiempo_ms = round((t_fin - t_inicio) * 1000, 2)
        return {"origen": "CSV", "datos": pokemon_csv, "tiempo_ms": tiempo_ms}
    #Si no estaba en el CSV, consulta a la PokeAPI
    if pokemon_csv is None:
        pokemon_api = consultar_pokeapi(clave)
    #Si la PokeAPI devuelve un resultado valido, lo guarda en CSV y responde
    if pokemon_api is not None:
        guardar_en_csv(pokemon_api)
        t_fin = time.perf_counter()
        tiempo_ms = round((t_fin - t_inicio) * 1000, 2)     #Corta el cronometro y se realizan conversiones en ms
        return {"origen": "PokeAPI", "datos": pokemon_api, "tiempo_ms": tiempo_ms}
    
    #Si no existe el pokemon, responde con un error
    raise HTTPException(status_code=404, detail="Pokémon no encontrado")

#uvicorn main:app --reload para lanzar la web