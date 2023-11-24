import re

dataSect_pattern = r"(?P<data>data) \"(?P<dname>.\w+)\"(?P<dcontent>.+?)end \"\2\";"

nobitsSect_pattern = r"(?P<nobits>nobits) \"(?P<nname>.\w+)\"(?P<ncontent>.+?)end \"\5\";"

codeSect_pattern = r"(?P<begin>begin) \"(?P<bname>.\w+)\"(?P<bcontent>.+?)end \"\8\";"

global_pattern = r"(.*?(?=begin|data|nobits))|(?=end \"\w+\";).*?" # TODO хрень какая то не робит

allSect_pattern = re.compile(fr"{dataSect_pattern}|{nobitsSect_pattern}|{codeSect_pattern}", re.DOTALL)


class Program:

    inputFile = ""
    outputFile = ""
    content = ""
    short_content = ""
    processed = ""
    sections = {}
    order = []

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
                self.sections['data'] = (DataSect(match.group('dname'), match.group('dcontent')))
                self.short_content = re.sub(re.escape(match.group()), f"{match.group('dname')} [...]", self.short_content)
            elif match.group('nobits'):
                self.sections['nobits'] = (NoBitsSect(match.group('nname'), match.group('ncontent')))
                self.short_content = self.short_content.replace(match.group(), f"{match.group('nname')} [...]")
            elif match.group('begin'):
                self.sections['code'] = (CodeSect(match.group('bname'), match.group('bcontent')))
                self.short_content = self.short_content.replace(match.group(), f"{match.group('bname')} [...]")

    def construct(self):
        for key, value in self.sections.items():
            value.process()
            self.processed += value.processed
            self.processed += "\n"

    def defineOrder(self):
        for line in self.short_content.split("\n"):
            if "[...]" not in line:
                print(line)


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
        decl_pattern = r"(\w+): (\w+) = (\d+\w{0,})"
        arr_pattern = r"(\w+: )(?P<type>\w+)\[\d+](.*?)\);"
        struct_pattern = r"struct (\w+)\n(.*?)end (\1)" # TODO сделать разбор структур
        all_patterns = re.compile(fr"{decl_pattern}|{arr_pattern}", re.DOTALL)
        found = re.finditer(all_patterns, self.content)
        for match in found:
            if match.group(1):
                self.ops.append([match.group(), "decl", match])
            elif match.group(4):
                self.ops.append([match.group(), "arr", match])

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

    def process(self):
        self.split_op()
        self.processed += f".section .data{self.name}\n"
        for operation in self.ops:
            if operation[2].group(2) == "word":
                self.processed += "\t" + operation[2].group(1) + ": .long " + operation[2].group(3)
            if operation[2].group(2) == "long":
                self.processed += "\t" + operation[2].group(1) + ": .quad " + operation[2].group(3)
            self.processed += "\n"


class CodeSect(Section):
    has_set = False
    macro_set = (".macro SET reg,val\n" 
                 "#if __NM4__== 0)\n"
                     "\t\\reg = \\val; \n"
                 "#else\n"
                     "\tsir = \\val; \n"
                     "\t\\reg = sir;\n"
                 "#endif\n"
                 ".endm\n")

    def __init__(self, _name, _content):
        super().__init__(_name, _content)
        self.has_set = bool(re.search(r"nb1|sb", _content)) # TODO: добавить проверку на поиск других ключевых слов, я помню что там есть какие-то еще

    def process(self):
        if self.has_set:
            self.processed += self.macro_set + "\n"
        self.processed += f".section .text{self.name}"
        for line in self.content.split("\n"):
            if (re.search(r"<(\w+)>", line)):
                self.processed += (re.sub(r"<(\w+)>", r"\1:", line, 1))
            elif (re.search(r"nb1|sb", line)): # TODO: добавить проверку на поиск других ключевых слов
                self.processed += re.sub(r"(nb1|sb) +=( )+(.*?);", r"SET \1, \3", line)
            else:
                self.processed += line
            self.processed += "\n"


class NoBitsSect(Section):
    ops = []

    def __init__(self, _name, _content):
        super().__init__(_name, _content)
        self.split_op()

    def split_op(self):
        decl_pattern = r"(\w+): (\w+)"
        arr_pattern = r"(\w+: )(?P<type>\w+)\[\d+];"
        all_patterns = re.compile(fr"{decl_pattern}|{arr_pattern}", re.DOTALL)
        found = re.finditer(all_patterns, self.content)
        for match in found:
            if match.group(1):
                self.ops.append([match.group(), "decl", match])
            elif match.group(4):
                self.ops.append([match.group(), "arr", match])


    def process(self):
        self.processed += f".section .bss{self.name}\n"
        for operation in self.ops:
            if operation[2].group(2) == "word":
                self.processed += "\t" + operation[2].group(1) + ": .long "
            if operation[2].group(2) == "long":
                self.processed += "\t" + operation[2].group(1) + ": .quad "
            self.processed += "\n"

