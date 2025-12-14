# Lorenzo Grippo Chiachio - 823917
# João Vitor Seiji - 822767

class Auction:
    '''
    A classe possui os atributos:
        auctionId (int)
        currentBid (double or float)
        lot (string)
        active (boolean)
    '''
    
    def __init__(self, auctionId, initialBid, lot):
        self.putAuctionId(auctionId)
        self.putCurrentBid(initialBid)
        self.putLot()
        self.beginAuction()
        
#################################################### PUTS
    def putAuctionId(self, newId):
        self._auctionId = newId
    
    def putCurrentBid(self, bid):
        self._currentBid = bid
    
    def putLot(self, lot):
        self._lot = lot
    
    def beginAuction(self):
        self._active = True
    
    def endAuction(self):
        self._active = False
    
#################################################### GETS

    def placeBid(self, bid):
        if not isActive() || bid < self.getCurrentBid():
            #RETORNAR ERRO DE ALGUMA FORMA PARA O NAVEGADOR DO USUÁRIO
        self.putCurrentBid(bid)
    
    def getCurrentBid(self):
        return self._currentBid
    
#################################################### OTHERS        
    def isActive(self):
        return self._active

