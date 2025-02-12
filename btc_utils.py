import ecdsa
import hashlib
import base58
import requests 


def get_btc_balance(address):
    url = f"https://blockstream.info/api/address/{address}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        saldo_satoshis = data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0)
        saldo_btc = saldo_satoshis / 100_000_000  # Converter satoshis para BTC
        
        return {
            "saldo_satoshis": saldo_satoshis,
            "saldo_btc": saldo_btc
        }
    except requests.exceptions.RequestException as e:
        return {"erro": str(e)}

def is_balance(address, private_key_pad):
    balance = get_btc_balance(address)
    if balance.get("saldo_btc", 0) > 0:
        print(f"Endereço ENCONTRADO com SALDO: {address}")
        print(f"Saldo: {balance['saldo_btc']} BTC")
        print(f"Chave privada: {private_key_pad}")
        return True
    return False

balance = is_balance("15Scn264CFwEirEW7wpY7Ze8YrWkxCiuMh", "000000000000000000000000000000000000000000000004488E3677ABD0FD97")
print(balance)

def private_key_to_wif(private_key_hex, compressed=True, testnet=False):
     # Definir o prefixo da rede
    prefix = b'\xEF' if testnet else b'\x80'
    
    # Converter a chave privada hexadecimal para bytes
    private_key_bytes = bytes.fromhex(private_key_hex)
    
    # Adicionar byte de compressão (se necessário)
    if compressed:
        extended_key = prefix + private_key_bytes + b'\x01'
    else:
        extended_key = prefix + private_key_bytes
    
    # Calcular checksum (SHA256 duas vezes)
    first_sha = hashlib.sha256(extended_key).digest()
    second_sha = hashlib.sha256(first_sha).digest()
    checksum = second_sha[:4]
    
    # Adicionar o checksum ao final
    final_key = extended_key + checksum
    
    # Codificar em Base58 para obter a chave WIF
    wif = base58.b58encode(final_key).decode()
    
    return wif

def private_key_to_address(private_key_hex, compressed=True):
    """Converte uma chave privada em hexadecimal para um endereço Bitcoin P2PKH."""
    private_key_bytes = bytes.fromhex(private_key_hex)

    # 1️⃣ Gerar chave pública (formato não comprimido, com prefixo 0x04)
    sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    if compressed:
        # Chave pública comprimida (prefixo 0x02 ou 0x03)
        prefix = b"\x02" if vk.pubkey.point.y() % 2 == 0 else b"\x03"
        public_key_bytes = prefix + vk.pubkey.point.x().to_bytes(32, 'big')
    else:
        # Chave pública não comprimida (prefixo 0x04)
        public_key_bytes = b"\x04" + vk.to_string()

    # 2️⃣ Aplicar SHA-256 seguido de RIPEMD-160
    sha256_hash = hashlib.sha256(public_key_bytes).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()

    # 3️⃣ Adicionar o prefixo de rede Bitcoin Mainnet (0x00)
    network_byte = b"\x00" + ripemd160_hash

    # 4️⃣ Calcular o checksum (SHA-256 duas vezes e pegar os primeiros 4 bytes)
    checksum = hashlib.sha256(hashlib.sha256(network_byte).digest()).digest()[:4]

    # 5️⃣ Criar o endereço Bitcoin codificado em Base58
    binary_address = network_byte + checksum
    address = base58.b58encode(binary_address).decode()

    return address

def validate_private_key(private_key_hex, address):
    """Valida se uma chave privada corresponde a um endereço Bitcoin."""
    generated_address = private_key_to_address(private_key_hex)

    if generated_address == address:
        print(f"✅ Chave privada VALIDA {address}!")
        return True
    print(f"❌ Chave privada INVALIDA a {address}!")
    return False
