import requests
import sqlite3
import os
import time
from fastapi import FastAPI, HTTPException

#===Inicializacion de la app===
app = FastAPI()

#Ruta donde se guarda la base de datos
RUTA_DB = "pokemones.db"

def crear_tabla_db():
    "Funcion que crea la tabla en pokemones.db"
    con = sqlite3.connect(RUTA_DB)    #Conectando con el archivo
    cur = con.cursor()    #Permitir ejecutar consultas
    #Ejecutando sentencia SQL de crear tabla con sus tipos y datos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pokemones(
            id INTEGER PRIMARY KEY, 
            nombre TEXT, 
            tipo TEXT, 
            altura INTEGER, 
            peso INTEGER, 
            experiencia_base INTEGER, 
            hp INTEGER, 
            ataque INTEGER, 
            defensa INTEGER, 
            velocidad INTEGER)""")
    con.commit() #Confirmando los cambios y cerrando la conexion
    con.close()

#Creamos la tabla apenas arranca la API
crear_tabla_db()


#===Funciones===

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
    # Si ocurre un problema de red o conexión, atrapamos el error y devuelve None         
    except requests.exceptions.RequestException: 
        return None
  
  
def buscar_en_db(clave):
    "Busca en la base de datos SQLite por nombre o ID"
    clave_buscada = str(clave).lower().strip()  #La busqueda se pone en minuscula y sin espacios
    con = sqlite3.connect(RUTA_DB)    #Conectando con el archivo
    con.row_factory = sqlite3.Row     #Obtiene las filas como diccionarios 
    cur = con.cursor()      #Permitir ejecutar consultas
    cur.execute("SELECT * FROM pokemones WHERE nombre=? OR id=?", (clave_buscada, clave_buscada)) #Sentencia SQL para buscar un Pokémon por nombre o id.
    fila = cur.fetchone()   #Trae una fila  
    con.close()     #Cerrando la conexión
    
    if fila is not None:    #Si no es None, devuelve el objeto como un diccionario, sino, devuelve None
        return dict(fila) 
    else:
        return None

    
def guardar_en_db(pokemon):
    "Inserta un nuevo pokemon en en la base de datos SQLite en pokemones.db"
    con = sqlite3.connect(RUTA_DB)     #Conectando con el archivo
    cur = con.cursor()       #Permitir ejecutar consultas
    #Sentencia SQL 
    cur.execute("""     
        INSERT INTO pokemones (id, nombre, tipo, altura, peso, experiencia_base, hp, ataque, defensa, velocidad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pokemon["id"], 
            pokemon["nombre"], 
            pokemon["tipo"], 
            pokemon["altura"], 
            pokemon["peso"], 
            pokemon["experiencia_base"], 
            pokemon["hp"], 
            pokemon["ataque"], 
            pokemon["defensa"], 
            pokemon["velocidad"]),
    )
    con.commit()    #Confirmando los cambios y cerrando la conexion
    con.close()


#===Endpoints de FastAPI===
@app.get("/")
def inicio():
    "Endpoint de bienvenida"
    return "Bienvenido a la PokeAPI"


@app.get("/pokemon/{clave}")
def buscar_pokemon(clave: str):
    """Endpoint principal que implementa el sistema de caché: 
    1. Verifica primero en SQLite
    2. Si esta, responde con origen: SQLite
    3. Si no esta, busca los datos en la PokeAPI, guarda los datos en SQLite y responde con origen: PokeAPI
    4. Si no existe, responde con un error"""
    
    t_inicio = time.perf_counter()   #Inicio cronometro
    #Busqueda en la cache local
    pokemon_db = buscar_en_db(clave)

    if pokemon_db is not None:
        t_fin = time.perf_counter()     #Corta el cronometro y se realizan conversiones en ms
        tiempo_ms = round((t_fin - t_inicio) * 1000, 2)
        return {"origen": "SQLite", "datos": pokemon_db, "tiempo_ms": tiempo_ms} 
    #Si no estaba, consulta a la PokeAPI
    if pokemon_db is None:
        pokemon_api = consultar_pokeapi(clave)
    #Si la PokeAPI devuelve los datos, guarda  y responde
    if pokemon_api is not None:
        guardar_en_db(pokemon_api)
        t_fin = time.perf_counter()     #Corta el cronometro y se realizan conversiones en ms
        tiempo_ms = round((t_fin - t_inicio) * 1000, 2)
        return {"origen": "PokeAPI", "datos": pokemon_api, "tiempo_ms": tiempo_ms}
    
    #Si no existe el pokemon, responde con un error
    raise HTTPException(status_code=404, detail="Pokémon no encontrado")

#uvicorn main_db:app --reload para lanzar la web