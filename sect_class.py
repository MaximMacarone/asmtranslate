import re

dataSect_pattern = r"(?P<data>data) \"(?P<dname>.\w+)\"(?P<dcontent>.+?)end \"\2\";"

nobitsSect_pattern = r"(?P<nobits>nobits) \"(?P<nname>.\w+)\"(?P<ncontent>.+?)end \"\5\";"

codeSect_pattern = r"(?P<begin>begin) \"(?P<bname>.\w+)\"(?P<bcontent>.+?)end \"\8\";"

global_pattern = r"(.*?(?=begin|data|nobits))|(?=end \"\w+\";).*?"

allSect_pattern = re.compile(fr"{dataSect_pattern}|{nobitsSect_pattern}|{codeSect_pattern}", re.DOTALL)

class Program:

    inputFile = ""
    outputFile = ""
    content = ""
    short_content = ""
    sections = []

    def __init__(self, _inputfile):
        self.inputFile = _inputfile
        with open(self.inputFile) as inp:
            self.content = inp.read()
        self.short_content = self.content

    def deleteComments(self):
        self.content = re.sub(r"//.*?$", "", self.content, flags=re.MULTILINE)
        self.short_content = self.content

    def createSections(self):
        found = re.finditer(allSect_pattern, self.content)
        for match in found:
            if match.group('data'):
                self.sections.append(DataSect(match.group('dname'), match.group('dcontent')))
                self.short_content = re.sub(re.escape(match.group()), f"{match.group('dname')} [...]", self.short_content)
            elif match.group('nobits'):
                self.sections.append(NoBitsSect(match.group('nname'), match.group('ncontent')))
                self.short_content = self.short_content.replace(match.group(), f"{match.group('nname')} [...]")
            elif match.group('begin'):
                self.sections.append(CodeSect(match.group('bname'), match.group('bcontent')))
                self.short_content = self.short_content.replace(match.group(), f"{match.group('bname')} [...]")



class Section:
    name = ""
    content = ""
    processed = ""

    def __init__(self, _name = "", _content = ""):
        self.content = _content
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

    def __init__(self, _name, _content):
        super().__init__(_name, _content)
        self.has_set = bool(re.search(r"nb1|sb", _content))


    def process(self):
        for line in self.content.split("\n"):
            pass



class NoBitsSect(Section):
    temp = ""