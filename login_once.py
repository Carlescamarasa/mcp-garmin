import getpass
import os
from garminconnect import Garmin

def main():
    print("--- Configuració inicial de Garmin Connect ---")
    email = input("Correu electrònic de Garmin: ")
    password = getpass.getpass("Contrasenya de Garmin: ")

    try:
        print(f"Connectant amb {email}...")
        # Inicialitzem l'API. La llibreria garminconnect gestiona internament el MFA
        # demanant el codi per consola si és necessari durant el login().
        api = Garmin(email, password)
        api.login()

        print("Login correcte!")

        # Guardem la sessió a un fitxer
        output_file = "session.json"
        # garth.dump guarda els tokens OAuth necessaris per a futures connexions
        api.garth.dump(output_file)
        
        print(f"✅ Sessió guardada correctament a: {os.path.abspath(output_file)}")
        print("Ara pots executar el servidor MCP sense introduir credencials.")

    except Exception as e:
        print(f"❌ Error durant el login: {e}")
        print("Assegura't que les credencials són correctes i que no tens bloquejos de seguretat.")

if __name__ == "__main__":
    main()
