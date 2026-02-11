from Crypto.Cipher import Salsa20

KEY = b"Simulator Interface Packet GT7 ver 0.0"

def decrypt(dat: bytes) -> bytes:
    oiv = dat[0x40:0x44]
    iv1 = int.from_bytes(oiv, "little")
    iv2 = iv1 ^ 0xDEADBEAF

    iv = iv2.to_bytes(4, "little") + iv1.to_bytes(4, "little")
    cipher = Salsa20.new(KEY[:32], iv)

    ddata = cipher.decrypt(dat)
    magic = int.from_bytes(ddata[0:4], "little")

    if magic != 0x47375330:
        return b""

    return ddata