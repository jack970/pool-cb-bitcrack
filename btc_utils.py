import ecdsa
import hashlib
import base58

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
    else:
        print(f"❌ Chave privada INVALIDA a {address}!")
        return False