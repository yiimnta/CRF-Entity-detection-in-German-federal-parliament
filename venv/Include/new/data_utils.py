import re
import nltk
from nltk.tree import Tree
from nltk.chunk import conlltags2tree
import xml.etree.ElementTree as ET
from Include.new import io_utils
from xml.dom import minidom

def printData(arr):
    print('\n'.join(arr))

def convert_paticipants_name_format(row, list_name_paticipants):
    for word in list_name_paticipants:
        if word in row:
            row = row.replace(word, word.replace(" ", "$"))

    return row


def convert_fraction_format(row):
    row = row.replace("DIE LINKE", "DIE$LINKE")
    row = row.replace("BÜNDNIS 90/DIE GRÜNEN", "BÜNDNIS$90/DIE$GRÜNEN")
    return row


def split(row):
    tokens = list(filter(None, re.split('([,\(\)])?', row)))
    rs = []
    word = ''
    for t in tokens:
        if t in [':', ',', '(', ')', '[', ']','!','?','<','>']:
            if word != '':
                if re.search("^\w+\.$", word) != None:
                    if word not in ['Dr.','Prof.']:
                        word = word[:-1]
                        rs.append(word)
                        rs.append('.')
                    else:
                        rs.append(word)
                else:
                    rs.append(word)
                word = ''
            rs.append(t)
        elif t != '' and t != ' ':
            word += t
        else:
            if word != '':
                if re.search("^\w+\.$", word) != None:
                    if word not in ['Dr.', 'Prof.']:
                        word = word[:-1]
                        rs.append(word)
                        rs.append('.')
                    else:
                        rs.append(word)
                else:
                    rs.append(word)
                word = ''
    if word != '':
        if re.search("^\w+\.$", word) != None:
            if word not in ['Dr.', 'Prof.']:
                word = word[:-1]
                rs.append(word)
                rs.append('.')
            else:
                rs.append(word)
        else:
            rs.append(word)
        word = ''
    return rs

def getUpcaseCaption(word):
    # check uppercase
    cap = 'NoCap'
    if re.search(r'^[A-ZÄÖÜß]', word) != None:
        cap = 'Cap'

    return cap

def convertBIOTag(arr):
    output = []
    isBegin = True
    prevTag = None

    for item in arr:
        li = list(item)  # convert tuple to list

        if isBegin == True or prevTag != li[3]:
            isBegin = False
            prevTag = li[3]
            li[3] = 'B-' + li[3]
        else:
            li[3] = 'I-' + li[3]
        output.append(tuple(li))

        if li[3] == "BREAK-LINE":
            isBegin = True

    return output

def convertCRFTraining(arr):
    """ Parse "raw" ingredient lines into CRF-ready output """
    output = []
    for (word, type, cap, tag) in arr:
        if word == "":
            output.append("")
            continue
        output.append(word + "\t" + type + "\t" + cap  + '\t' + tag)

    return output

def convertCRFTesting(arr):
    """ Parse "raw" ingredient lines into CRF-ready output """
    output = []
    for (word, type, cap, tag) in arr:
        if word == "":
            output.append("")
            continue
        output.append(word + "\t" + type + "\t" + cap)

    return output

def convertChunkTag(arr):
    chunk_data = []

    for (word, ty, cap, tag) in arr:
        if tag == "":
            chunk_data.append(("", "BREAK", "B-BREAK-LINE"))
        else:
            chunk_data.append((word, ty, tag))

    ne_tree = conlltags2tree(chunk_data)
    output = []
    for subtree in ne_tree:
        if type(subtree) == Tree:
            original_label = subtree.label()
            original_string = " ".join([token for token, pos in subtree.leaves()])
            output.append((original_string, original_label))

    return output

def convertXMLData(file_path, chunk_data):
    xml_data = []
    grammar = r"""
        SBEGIN:{<BEGIN><COLON><NUMBER><TIME><BREAK-LINE>}
        SPRESIDENT:{<PRESIDENT><TITLE>?<NAME>+<COLON><BREAK-LINE>}
        SNAME:{<TITLE>?<NAME>+(<PARAGRAPH>|<BBRACKET><FRACTION><EBRACKET>|<BBRACKET><PARAGRAPH><EBRACKET>|<DOT>)*<COLON><BREAK-LINE>}
        SAGENDA:{<PARAGRAPH><AGENDA><NUMBER><PARAGRAPH><COLON><BREAK-LINE>}
        SCOMMENT:{<BBRACKET>(<MOOD>|<PARAGRAPH>|<COLON>|<TITLE>?<NAME>*|<FRACTION>|<DOT>|<COLON>|<BREAK-LINE>|<PRESIDENT>|<TITLE>)+<EBRACKET><BREAK-LINE>}
        SPARAGRAPH:{(<TITLE><PRESIDENT>|<TITLE>?<DOT>?|<PRESIDENT>|<MOOD>|<NUMBER>|<TIME>|<TITLE>?<NAME>|<FRACTION>|<PARAGRAPH>|<DOT>|<COLON>)+(<DOT>|<COLON>|)<BREAK-LINE>}
    """
    cp = nltk.RegexpParser(grammar)
    dt = cp.parse(chunk_data)
    for e in dt:
        if type(e) == Tree:
            xml_data.append((e.label(), e.leaves()))

    #create XML-Wrapper
    wrapper = ET.Element("sitzungsverlauf")
    parent_tag = wrapper
    group_tag = None
    president = ""
    #create XML item
    is_bracket_before = False

    for label, leaves in xml_data:
        line = ""
        for ch, tag in leaves:
            if tag not in ["DOT","COLON"]:
                if tag not in ["BBRACKET","EBRACKET"]:
                    if is_bracket_before:
                        is_bracket_before = False
                    else:
                        line+=" "
                else:
                    is_bracket_before = True
            line += ch

        line = line.strip()

        if label == "SBEGIN":
            begin_tag = ET.SubElement(wrapper, 'sitzungsbeginn')
            time = "0:00"
            for token,pos in leaves:
                if pos == "NUMBER":
                    time = token.replace(".",":")
            begin_tag.set("sitzung-start-uhrzeit", time)
            parent_tag = begin_tag
            group_tag = begin_tag

        elif label == "SAGENDA":
            agenda_tag = ET.SubElement(wrapper, 'tagesordnungspunkt')
            time = "0:00"
            num = -1
            for token, pos in leaves:
                if pos == "AGENDA":
                    num = 0
                elif pos == "NUMBER" and num == 0:
                    num = token
                    break
                else:
                    num+=1
            agenda_tag.set("top-id", num)
            president_tag = ET.SubElement(agenda_tag, 'name')
            president_tag.text = president
            p_tag = ET.SubElement(agenda_tag, 'p')
            p_tag.text = line
            parent_tag = agenda_tag
            group_tag = agenda_tag

        elif label == "SPRESIDENT":
            president_tag = ET.SubElement(parent_tag, 'p')
            # TODO: add klasse of president
            president_tag.text = line
            president = line
        elif label == "SNAME":

            """NAME:{<TITLE>?<NAME>+(<PARAGRAPH>|<BBRACKET><FRACTION><EBRACKET>|<BBRACKET><PARAGRAPH><EBRACKET>|<DOT>)*<COLON><BREAK-LINE>}"""
            speak_tag = ET.SubElement(group_tag, 'rede')
            #TODO SET ID

            p_tag = ET.SubElement(speak_tag, 'p')
            p_tag.set("klasse","redner")
            speaker_tag = ET.SubElement(p_tag,'redner')

            #TODO: add id of redner

            name_tag = ET.SubElement(speaker_tag, 'name')
            for token,pos in leaves:
                if pos == "TITLE":
                    title = ET.SubElement(name_tag, 'titel')
                    title.text = token
                elif pos == "NAME":
                    first_lastname = token.split(" ")

                    if len(first_lastname) > 1:
                        first_tag = ET.SubElement(name_tag, 'vorname')
                        first_tag.text = ''.join(first_lastname[:-1])

                    last_tag = ET.SubElement(name_tag, 'nachname')
                    last_tag.text = ''.join(first_lastname[-1])
                elif pos == "FRACTION":
                    fraction_tag = ET.SubElement(name_tag, 'fraktion')
                    fraction_tag.text = token

            speaker_tag.text = line
            parent_tag = speak_tag

        elif label == "SCOMMENT":
            comment_tag = ET.SubElement(parent_tag, 'kommentar')
            comment_tag.text = line

        elif label == "SPARAGRAPH":
            p_tag = ET.SubElement(parent_tag, 'p')
            # TODO: add klasse of paragraph
            p_tag.text = line
        # xmlstr = minidom.parseString(ET.tostring(wrapper)).toprettyxml(indent="   ")
        # print(xmlstr)

    io_utils.exportXMLFile(file_path, wrapper)