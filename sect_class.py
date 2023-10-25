import re


#class Program:

class Section:
    type = ""
    name = ""
    content = ""

    def __init__(self, _content = "", _type = "", _name = ""):
        self.content = _content
        self.type = _type
        self.name = _name

    def process(self):
        pass



class DataSect(Section):
    declarations = []
    mask_type = ""
    mask = []
    weights = []

    def exctractWeights(self):
        w = re.compile(r"(?<=Weights: )(?P<type>\w+)\[\d+](.*?)(?=;)", re.DOTALL)
        weights = re.search(w, self.content)
        if weights is not None:
            w_vals = re.finditer(r"(\dl)(<<)(\d+)", weights.group())
            for val in w_vals:
                self.weights.append([val.group(1), val.group(2), val.group(3)])

    def extractMask(self):
        masks = re.compile(r"(?<=Masks: )(?P<type>\w+)\[\d+](.*?)(?=;)", re.DOTALL)
        mask_vals = re.finditer(r"\d+hl", self.content)
        try:
            next(mask_vals)
        except StopIteration:
            pass
        else:
            self.mask_type = masks.search(self.content).group("type")
        for val in mask_vals:
            self.mask.append(val.group())

    def extractDeclarations(self):
        decs = re.finditer(r"(\w+): (\w+) = (\d+)", self.content)
        for val in decs:
            self.declarations.append([val.group(1), val.group(2), val.group(3)])


class CodeSect(Section):
    has_set = False

    def __init__(self, _content, _type, _name):
        super().__init__(_content, _type, _name)
        self.has_set = bool(re.search(r"nb1|sb", _content))


class NoBitsSect(Section):
    temp = ""