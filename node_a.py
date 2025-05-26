import Ice
import sys
import time
from spdz_utils import P, modp, generate_shares
import SPDZ

class NodeAI(SPDZ.Node):
    def __init__(self, communicator):
        self.communicator = communicator
        self.own_val = 45678  # Valor secreto de este nodo

        # Fase 1: Compartición secreta (Secret Sharing)
        # Genera dos shares y sus MACs para el valor secreto.
        # Se queda con el primer share y su MAC, el otro se enviará al otro nodo.
        self.shares, self.remote_shares = generate_shares(self.own_val)[0], None
        self.sum_share = None  # Aquí se almacenará la suma parcial (share, MAC)

    def sendShares(self, shareValue, shareMac, current=None):
        # Recibe el share y MAC del otro nodo y los almacena
        self.remote_shares = (shareValue, shareMac)

    def computeSum(self, current=None):
        # Fase 2: Suma segura de shares y MACs
        # Suma su propio share con el recibido del otro nodo (mod P)
        s1 = modp(self.shares[0] + self.remote_shares[0])
        m1 = modp(self.shares[1] + self.remote_shares[1])
        self.sum_share = (s1, m1)  # Guarda la suma parcial

    def revealSum(self, current=None):
        # Fase 3: Revelación de la suma parcial al otro nodo
        # Envía su suma parcial (share y MAC) al otro nodo para la reconstrucción
        proxy = SPDZ.NodePrx.checkedCast(self.communicator.stringToProxy("NodeB:default -p 10001"))
        proxy.receiveResult(self.sum_share[0], self.sum_share[1])

    def receiveResult(self, sum_val, mac_val, current=None):
        # Fase 4: Reconstrucción y verificación
        # Espera a que computeSum haya sido llamado antes de continuar
        while self.sum_share is None:
            time.sleep(0.05)
        # Reconstruye la suma total y el MAC total sumando ambas partes
        z = modp(self.sum_share[0] + sum_val)         # Suma total de los secretos
        gamma = modp(self.sum_share[1] + mac_val)     # Suma total de los MACs
        expected = modp(z * 12345)                    # MAC esperado usando la clave global
        print(f"[NodeA] z = {z}, gamma = {gamma}, expected = {expected}")
        print(f"[NodeA] Verificación: {'ÉXITO' if gamma == expected else 'FALLO'}")

with Ice.initialize(sys.argv) as communicator:
    # Inicializa el adaptador y el objeto remoto
    adapter = communicator.createObjectAdapterWithEndpoints("NodeA", "default -p 10000")
    nodeA = NodeAI(communicator)
    adapter.add(nodeA, communicator.stringToIdentity("NodeA"))
    adapter.activate()
    print("Nodo A listo")

    # Espera a que NodeB esté listo y disponible para recibir conexiones
    nodeB = None
    while nodeB is None:
        try:
            nodeB = SPDZ.NodePrx.checkedCast(communicator.stringToProxy("NodeB:default -p 10001"))
        except Exception:
            time.sleep(0.5)

    # Fase 1 (continuación): Enviar el segundo share y MAC a NodeB
    # (El nodo se queda con el primero, envía el segundo)
    nodeB.sendShares(*generate_shares(nodeA.own_val)[1])

    # Espera a recibir el share y MAC de NodeB
    while nodeA.remote_shares is None:
        time.sleep(0.1)

    # Fase 2: Calcular la suma parcial de shares y MACs
    nodeA.computeSum()

    # Fase 3: Revelar la suma parcial a NodeB
    nodeA.revealSum()

    # Espera indefinidamente a que termine la comunicación
    communicator.waitForShutdown()
