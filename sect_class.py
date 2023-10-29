import re

#class Program:

class Section:
    type = ""
    name = ""
    content = ""
    processed = ""

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
    arrays = []
    structs = []
    ops = []

    def split_op(self):
        decl_pattern = r"(\w+): (\w+) = (\d+)"
        arr_pattern = r"(\w+: )(?P<type>\w+)\[\d+](.*?)\);"
        struct_pattern = r"struct (\w+)\n(.*?)end (\1)"
        all_patterns = re.compile(fr"{decl_pattern}|{arr_pattern}", re.DOTALL)
        found = re.finditer(all_patterns, self.content)
        for match in found:
            if match.group(1):
                self.ops.append([match.group(), "decl"])
            elif match.group(4):
                self.ops.append([match.group(), "arr"])

        return self.ops

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
    macro_set = (r".macro SET reg,val"
                 "#if __NM4__== 0)"
                     "\\reg = \\val; "
                 "#else"
                     "sir = \\val; "
                     "\\reg = sir;"
                 "#endif"
                 ".endm")

    def __init__(self, _content, _type, _name):
        super().__init__(_content, _type, _name)
        self.has_set = bool(re.search(r"nb1|sb", _content))


    def process(self):
        for line in self.content.split("\n"):
            pass



class NoBitsSect(Section):
    temp = ""