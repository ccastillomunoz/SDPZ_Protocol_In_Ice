P = 104729          # Campo primo (operamos módulo p)
ALPHA = 12345       # Clave MAC global (conocida por todos)

def modp(x):
    return x % P    # Reducción módulo p

def generate_shares(secret):
    from random import randint
    share1 = randint(0, P - 1)              # Parte aleatoria
    share2 = modp(secret - share1)          # La otra parte, para que sumen al valor original
    mac1 = modp(ALPHA * share1)             # MAC de la parte 1
    mac2 = modp(ALPHA * share2)             # MAC de la parte 2
    return (share1, mac1), (share2, mac2)   # Devuelve 2 tuplas: cada parte con su MAC
