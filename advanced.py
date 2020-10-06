import base
from regular import AdventurerRegular

class AdventurerAdvanced(AdventurerRegular):
    def __init__(self):
        super().__init__()
        
        self.max_upwind_moves_unburdened = 2
        self.max_land_moves_unburdened = 3