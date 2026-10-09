import requests

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