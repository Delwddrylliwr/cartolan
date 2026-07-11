'''
Copyright 2020 Tom Wilkinson, delwddrylliwr@gmail.com
'''

class Card:
    '''A template for cards that will modify other objects with buffs
    '''
    def __init__(self, game, card_type):
        self.game = game
        self.card_type = card_type
        self.buffs = None
        # self.card_id = card_type+str(random.random())
        self.card_id = game.register(self)

    def __hash__(self):
        return hash(self.card_id)
    
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.card_id == other.card_id
        else: return False
        
    def __ne__(self, other):
        if isinstance(other, Card):
            return not self.card_id == other.card_id
        else: return True

    def to_json(self):
        return {"card_type": self.card_type, "card_id": self.card_id}

#    def __deepcopy__(self, memo):
#        '''Excludes creation of new version from deep copying, copying only the reference
#        '''
#        return self
