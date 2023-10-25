import re
import os
from sect_class import *


sects = []
def createSections(_filetext, sects):
    # data section
    data = re.compile(
        r"data \"(.\w+)\"(.+?)end \"\1\";",
        re.DOTALL
    )
    # nobits section
    nobits = re.compile(
        r"nobits \"(.\w+)\"(.+?)end \"\1\";",
        re.DOTALL
    )
    # code section
    code = re.compile(
        r"begin \"(.\w+)\"(.+?)end \"\1\";",
        re.DOTALL
    )

    found_data = re.search(data, _filetext)
    found_code = re.search(code, _filetext)
    found_bss = re.search(nobits, _filetext)

    if found_data:
        sects.append(DataSect(found_data.group(2), "data", found_data.group(1)))
    if found_code:
        sects.append(CodeSect(found_code.group(2), "code", found_code.group(1)))
    if found_bss:
        sects.append(NoBitsSect(found_bss.group(2), "bss", found_bss.group(1)))


def findmask(section):
    masks = re.compile(r"(?<=Masks: )(?P<type>\w+)\[\d+](.*?)(?=;)", re.DOTALL)

    mv = re.finditer(r"\d+hl", re.search(masks, section.content).group())

    for match in mv:
        section.Masks.append(match.group())


input_file = "Step11.asm"


file = open(input_file, 'r')
filetext = file.read()
file.close()


createSections(filetext, sects)

print(sects)

sects[0].exctractWeights()
print(sects[0].weights)

for section in sects:
    section.process()


#findmask(data_sect)

#print(data_sect.Masks)





