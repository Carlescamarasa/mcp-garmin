# Utilitzem una imatge base lleugera de Python
FROM python:3.11-slim

# Establim el directori de treball dins del contenidor
WORKDIR /app

# Copiem els fitxers de requeriments i instal·lem dependències
# (Crearem requirements.txt en el següent pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem la resta del codi
COPY . .

# IMPORTANT: No copiem session.json ni .env (s'han de muntar com a volums o generar al moment)

# Comanda per executar el servidor (ajusta segons com vulguis exposar-lo, 
# per MCP stdio sol ser python server.py, però en docker potser vols un servidor HTTP o similar
# si el connectes remotament. Per ara, deixem l'execució bàsica).
CMD ["python", "server.py"]
