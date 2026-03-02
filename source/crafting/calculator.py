

class heavy_turret():
    def __init__(self,metal,poly,elec,paste):
        self.metal_cost = 560
        self.poly_cost = 70
        self.elec_cost = 270
        self.paste_cost = 200
        self.metal = metal
        self.poly = poly
        self.elec = elec
        self.paste = paste

    def calculate(self):
        quant_metal = self.metal / self.metal_cost
        quant_poly = self.poly / self.poly_cost
        quant_elec = self.elec / self.elec_cost
        quant_paste = self.paste / self.paste_cost 
        return min(quant_metal,quant_poly,quant_elec,quant_paste) // 1
    
    def craft(self):
        amount = self.calculate()
        
