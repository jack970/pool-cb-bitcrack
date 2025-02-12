import requests
import subprocess
import time
import os
import sys
import select
from btc_utils import validate_private_key, is_balance

API_URL = "https://bitcoinflix.replit.app/api/big_block"
POOL_TOKEN = "318630e6a68b27fbaf6e28182a69872bb37635c1f1956e5e339e62d06d93daa9"
ADDITIONAL_ADDRESS = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def fetch_block_data():
    headers = {"pool-token": POOL_TOKEN}
    try:
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro ao buscar dados do bloco: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Erro ao fazer a requisição: {e}")
        return None

def save_addresses_to_file(addresses, additional_address, filename="in.txt"):
    try:
        with open(filename, "w") as file:
            for address in addresses:
                file.write(address + "\n")
            file.write(additional_address + "\n")  # Adicionando o endereço adicional
        print(f"Endereços salvos com sucesso no arquivo '{filename}'.")
    except Exception as e:
        print(f"Erro ao salvar endereços no arquivo: {e}")

def count_private_keys(out_file='out.txt'):
    """ Conta quantas linhas (chaves privadas) existem no arquivo. """
    try:
        with open(out_file, "r") as file:
            return len(file.readlines()) 
        
    except FileNotFoundError:
        return 0  # Retorna 0 se o arquivo ainda não existir


def run_program(start, end):
    keyspace = f"{start}"
    command = [
        "clBitCrack",
        "--keyspace", keyspace,
        "-i", "in.txt",
        "-o", "out.txt",
        "-t", "256",
        "-b", "128",
        "-p", "1024",
        "-f"
    ]
    try:
        print(f"Executando: {' '.join(command)}...")
          # Inicia o processo em segundo plano
        process = subprocess.Popen(command, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True,
                                   bufsize=1)
        start_time = time.time()

        while process.poll() is None:
            count_keys = count_private_keys()
            elapsed_time = time.time() - start_time
            minutes, seconds = divmod(elapsed_time, 60)
            time_formatted = f"{int(minutes)}m {seconds:.2f}s" if minutes > 0 else f"{seconds:.2f}s"

            ready_to_read, _, _ = select.select([process.stdout], [], [], 0.1)
            if process.stdout in ready_to_read:
                line = process.stdout.readline().strip()
                if line:
                    sys.stdout.write(f"\r{line} 🔍 Chaves detectadas: {count_keys} | Tempo: {time_formatted}")
                    sys.stdout.flush()

            if count_keys == 10:
                print(f"Chaves privadas encontradas: {count_private_keys()}")
                process.terminate()
                break
            time.sleep(1)
        
        process.wait()

    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o programa: {e}")

    except Exception as e:
        print(f"Erro inesperado: {e}")

def post_private_keys(private_keys, out_file='out.txt'):
    headers = {
        "pool-token": POOL_TOKEN,
        "Content-Type": "application/json"
    }
    data = {"privateKeys": private_keys}
    
    print(f"Enviando o seguinte array de chaves privadas ({len(private_keys)} chaves):")
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Chaves privadas enviadas com sucesso.")
            clear_file(out_file)
        else:
            print(f"Erro ao enviar chaves privadas: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Erro ao fazer a requisição POST: {e}")


def clear_file(filename):
    try:
        with open(filename, "w") as file:
            pass
        print(f"Arquivo '{filename}' limpo com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar o arquivo '{filename}': {e}")

def pad_private_key(private_key: str):
    private_key = private_key.lstrip("0x")  # Remover prefixo '0x' se existir
    padded_key = private_key.zfill(64)  # Preencher com zeros à esquerda
    return "0x" + padded_key  # Adicionar prefixo '0x'

def process_out_file(out_file="out.txt", in_file="in.txt", additional_address=ADDITIONAL_ADDRESS):
    private_keys = []

    # Removendo o endereço adicional para evitar inconsistência
    if additional_address in addresses:
        addresses.remove(additional_address)

    found_additional_address = False
    private_key_additional_addr = ''

    with open(out_file, "r") as file:
        current_address = None
        for line in file:
            line.strip()
            line_split = line.split(" ")
            current_address = line_split[0].strip()  # Obtém o address key
            private_key = line_split[1].strip()

            private_key_pad = pad_private_key(private_key)  # Obtém a private key

            validate_addr = validate_private_key(private_key, current_address)
            if not validate_addr:
                return True
            
            if is_balance(current_address, private_key_pad):
                return True

            # Verificar se a chave privada pertence a um dos endereços
            if current_address and private_key_pad:
                private_keys.append(private_key_pad)
            if current_address == additional_address:
                found_additional_address = True
                private_key_additional_addr = private_key

    if found_additional_address:
        print("Chave privada do endereço adicional encontrada! Parando o programa.")
        print(f"Chave encontrada: {private_key_additional_addr}")
        return True

    post_private_keys(private_keys)

if __name__ == "__main__":
    while True:
        clear_screen()
        block_data = fetch_block_data()
        if block_data:
            addresses = block_data.get("checkwork_addresses", [])
            if addresses:
                save_addresses_to_file(addresses, ADDITIONAL_ADDRESS)
                
                # Extraindo start e end do range
                range_data = block_data.get("range", {})
                start = range_data.get("start", "").replace("0x", "")
                end = range_data.get("end", "").replace("0x", "")
                
                if start and end:
                    run_program(start, end)
                    if process_out_file():
                        break
                else:
                    print("Erro: Start ou End não encontrado no range.")
            else:
                print("Nenhum endereço encontrado no bloco.")
        else:
            print("Erro ao buscar dados do bloco.")

        # Aguardar 2 segundos antes de reiniciar o loop
        time.sleep(2)
