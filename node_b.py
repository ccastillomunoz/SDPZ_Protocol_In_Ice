import Ice
import sys
import time
from spdz_utils import P, modp, generate_shares
import SPDZ

class NodeBI(SPDZ.Node):
    def __init__(self, communicator):
        self.communicator = communicator
        self.own_val = 93214
        # Genera ambos shares, se queda con el primero
        self.shares, self.remote_shares = generate_shares(self.own_val)[0], None
        self.sum_share = None

    def sendShares(self, shareValue, shareMac, current=None):
        self.remote_shares = (shareValue, shareMac)

    def computeSum(self, current=None):
        s2 = modp(self.shares[0] + self.remote_shares[0])
        m2 = modp(self.shares[1] + self.remote_shares[1])
        self.sum_share = (s2, m2)

    def revealSum(self, current=None):
        proxy = SPDZ.NodePrx.checkedCast(self.communicator.stringToProxy("NodeA:default -p 10000"))
        proxy.receiveResult(self.sum_share[0], self.sum_share[1])

    def receiveResult(self, sum_val, mac_val, current=None):
        while self.sum_share is None:
            time.sleep(0.05)
        z = modp(self.sum_share[0] + sum_val)
        gamma = modp(self.sum_share[1] + mac_val)
        expected = modp(z * 12345)
        print(f"[NodeB] z = {z}, gamma = {gamma}, expected = {expected}")
        print(f"[NodeB] Verificación: {'ÉXITO' if gamma == expected else 'FALLO'}")

with Ice.initialize(sys.argv) as communicator:
    adapter = communicator.createObjectAdapterWithEndpoints("NodeB", "default -p 10001")
    nodeB = NodeBI(communicator)
    adapter.add(nodeB, communicator.stringToIdentity("NodeB"))
    adapter.activate()
    print("Nodo B listo")

    # Espera a que NodeA esté listo
    time.sleep(2)

    # Enviar mi share a NodeA (la segunda parte, la que no uso)
    nodeA = SPDZ.NodePrx.checkedCast(communicator.stringToProxy("NodeA:default -p 10000"))
    nodeA.sendShares(*generate_shares(nodeB.own_val)[1])

    # Espera a recibir el share de NodeA
    while nodeB.remote_shares is None:
        time.sleep(0.1)

    # Calcular suma
    nodeB.computeSum()

    # Revelar suma parcial a NodeA
    nodeB.revealSum()

    communicator.waitForShutdown()
