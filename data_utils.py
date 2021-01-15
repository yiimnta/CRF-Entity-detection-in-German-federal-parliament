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
    row = row.replace("DIE LINKE", "DIE$LINKE").replace("BÜNDNIS 90", "BÜNDNIS$90").replace("DIE GRÜNEN", "DIE$GRÜNEN")
    return row

def convert_state_format(row):
    row = re.sub(r'Baden(\s|-)+Württemberg', 'Baden$Württemberg', row, flags=re.IGNORECASE)
    row = re.sub(r'Mecklenburg(\s|-)+Vorpommern', 'Mecklenburg$Vorpommern', row, flags=re.IGNORECASE)
    row = re.sub(r'Nordrhein(\s|-)+Westfalen', 'Nordrhein$Westfalen', row, flags=re.IGNORECASE)
    row = re.sub(r'Rheinland(\s|-)+Pfalz', 'Rheinland$Pfalz', row, flags=re.IGNORECASE)
    row = re.sub(r'Sachsen(\s|-)+Anhalt', 'Sachsen$Anhalt', row, flags=re.IGNORECASE)
    row = re.sub(r'Schleswig(\s|-)+Holstein', 'Schleswig$Holstein', row, flags=re.IGNORECASE)

    return row

def split(row):
    rs = []
    words = row.split(' ');
    list_frac = [ "DIE$LINKE", "BÜNDNIS$90", "DIE$GRÜNEN"]
    for w in words:
        if len(w.split("$")) > 1 and any(frac in w for frac in list_frac) == False:
            while w[0] in [':', ',', '(', ')', '[', ']','!','?','<','>', '\\', '/', '.']:
                rs.append(w[0])
                w = w[1:]
            tail = []
            while w[-1] in [':', ',', '(', ')', '[', ']','!','?','<','>', '\\', '/', '.']:
                tail.append(w[-1])
                w = w[:-1]
            rs.append(w)
            if len(tail) > 0:
                rs = rs + tail[::-1]
        else:
            tokens = list(filter(None, re.split('([,\(\)])?', w)))
            word = ''
            is_name = False
            for t in tokens:
                if t in [':', ',', '(', ')', '[', ']', '!', '?', '<', '>', '\\', '/'] or (
                        t == "." and is_name == False and word not in ['Dr', 'Prof']):
                    if word != '':
                        rs.append(word)
                        word = ""
                    rs.append(t)
                    is_name = False
                elif t.strip() == '':
                    if word != '':
                        rs.append(word)
                        is_name = False
                        word = ''
                else:
                    word += t

            if word != '':
                rs.append(word)
                word = ""

    return rs

def getUpcaseCaption(word):
    # check uppercase
    cap = 'NoCap'
    if re.search(r'^[A-ZÄÖÜß]', word) != None:
        cap = 'Cap'

    return cap

def convertBIOTag(arr):
    output = []
    prevTag = None

    for item in arr:
        li = list(item)  # convert tuple to list

        if prevTag != li[3]:
            prevTag = li[3]
            li[3] = 'B-' + li[3]
        else:
            li[3] = 'I-' + li[3]
        output.append(tuple(li))

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

    chunk_data.append(("", "START", "B-START-LINE"))
    for (word, ty, cap, tag) in arr:
        if tag == "":
            chunk_data.append(("", "BREAK", "B-BREAK-LINE"))
            chunk_data.append(("", "START", "B-START-LINE"))
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

def monthStringToNumber(string):

    s = string.strip()[:3].lower()

    if s == "mär":
        return "3"

    m = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr':4,
        'may':5,
        'jun':6,
        'jul':7,
        'aug':8,
        'sep':9,
        'okt':10,
        'nov':11,
        'dez':12
        }

    try:
        out = m[s]
        return str(out)
    except:
        raise ValueError('Not a month')

def convertXMLData(file_path, chunk_data):
    xml_data = []
    grammar = r"""
        CPLENARYPRO:{<START-LINE><PLENARYPRO><NUMBER><DIV><NUMBER><PARAGRAPH><BREAK-LINE>}
        CMEETING:{<START-LINE><NUMBER><DOT><MEETING><BREAK-LINE>}
        CCONTENT:{<START-LINE><CONTENT><BREAK-LINE>}
        CBEGIN:{<START-LINE><BEGIN><COLON><NUMBER><DOT><NUMBER><TIME><BREAK-LINE>}
        CEVENTDATE:{<START-LINE><STATE><DOT><WEEKDAY><DOT><PARAGRAPH>?<NUMBER><DOT>?<MONTH><DOT>?<NUMBER><BREAK-LINE>}
        CPRESIDENT:{<START-LINE><PRESIDENT><TITLE>?<NAME>+<COLON><BREAK-LINE>}
        CNAME:{<START-LINE><TITLE>?<NAME>+(<PARAGRAPH>|<BBRACKET><FRACTION><DIV>?<FRACTION>?<EBRACKET>|<BBRACKET><PARAGRAPH><EBRACKET>|<DOT>)*<COLON><BREAK-LINE>}
        CAGENDA:{<START-LINE>(<PARAGRAPH><AGENDA><NUMBER>)+(<PARAGRAPH>|<DIV>|<MONTH>|<MEETING>|<WEEKDAY>|<STATE>|<DOT>|<MOOD>|<NUMBER>|<TIME>|<TITLE>?<NAME>|<FRACTION><DIV>?<FRACTION>?|)*<COLON><BREAK-LINE>}
        CEND:{<START-LINE><BBRACKET><END><COLON><NUMBER><DOT><NUMBER><TIME><EBRACKET><BREAK-LINE>}
        CCOMMENT:{<START-LINE>(<BBRACKET>(<MOOD>|<PARAGRAPH>|<COLON>|<MONTH>|<WEEKDAY>|<MEETING>|<STATE>|<TITLE>?<NAME>*|<FRACTION><DIV>?<FRACTION>?|<DOT>|<COLON>|<PRESIDENT>|<NUMBER>|<DIV>|<TITLE>)+<EBRACKET>)+<BREAK-LINE>}
        CPARAGRAPH:{<START-LINE>(<TITLE><PRESIDENT>|<TITLE>?<DOT>?|<MONTH>|<WEEKDAY>|<MEETING>|<STATE>|<PRESIDENT>|<AGENDA>|<MOOD>|<NUMBER>|<TIME>|<TITLE>?<NAME>|<FRACTION><DIV>?<FRACTION>?|<DIV>|<PARAGRAPH>|<DOT>|<COLON>|<BBRACKET>|<EBRACKET>)+(<DOT>|<COLON>|)<BREAK-LINE>}
    """
    cp = nltk.RegexpParser(grammar)
    dt = cp.parse(chunk_data)
    for e in dt:
        if type(e) == Tree:
            xml_data.append((e.label(), e.leaves()))

    #create XML-Wrapper
    wrapper = ET.Element("dbtplenarprotokoll")
    header = ET.SubElement(wrapper, "vorspann")
    content = ET.SubElement(wrapper,'sitzungsverlauf')
    anlagen = ET.SubElement(wrapper, 'anlagen')
    datenHead = ET.SubElement(header, "kopfdaten")
    parent_tag = datenHead
    #create XML item
    is_bracket_before = False
    is_head_tag = True
    group_tag = content #tagesordnungspunkt or sitzungsbeginn
    old_rede = None

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

        #<START-LINE><PLENARYPRO><NUMBER><DIV><NUMBER><PARAGRAPH><BREAK-LINE>
        if is_head_tag and label == "CPLENARYPRO":
            plenaryProNumber = ET.SubElement(datenHead, 'plenarprotokoll-nummer')
            plenaryProNumber.text = 'Plenarprotokoll '
            electoralTerm =  ET.SubElement(plenaryProNumber, 'wahlperiode')
            electoralTerm.text = leaves[2][0]
            electoralTerm.tail = '/'
            wrapper.set("wahlperiode", leaves[2][0])
            sessionNum = ET.SubElement(plenaryProNumber, 'sitzungsnr')
            sessionNum.text = leaves[4][0]
            wrapper.set("sitzung-nr", leaves[4][0])
            if "Deutscher Bundestag" in leaves[5][0]:
                editor = ET.SubElement(datenHead, 'herausgeber')
                editor.text = "Deutscher Bundestag"
                wrapper.set("herausgeber", "Deutscher Bundestag")
            if "Stenografischer Bericht" in leaves[5][0]:
                reportArt = ET.SubElement(datenHead, 'berichtart')
                reportArt.text = "Stenografischer Bericht"

        #<START-LINE><NUMBER><DOT><MEETING><BREAK-LINE>
        elif is_head_tag and label == "CMEETING":
            meeting = ET.SubElement(datenHead, 'sitzungstitel')
            meetingNum = ET.SubElement(meeting, 'sitzungsnr')
            meetingNum.text = leaves[1][0]
            meetingNum.tail = '. Sitzung'

        #<START-LINE><STATE><DOT><WEEKDAY><DOT><PARAGRAPH>?<NUMBER><DOT>?<MONTH><DOT>?<NUMBER><BREAK-LINE>
        elif is_head_tag and label == "CEVENTDATE":
            eventDate = ET.SubElement(datenHead, 'veranstaltungsdaten')
            ort = ET.SubElement(eventDate, 'ort')
            ort.text = leaves[1][0] #STATE token
            ort.tail = ", "
            wrapper.set("sitzung-ort", leaves[1][0]) #STATE token
            datum = ET.SubElement(eventDate, 'datum')
            datum.text = re.sub(leaves[1][0]+'\s?(\.|,|)\s?', '', line)

            #get date string dd.MM.YYYY
            get_day_yet = True
            dateStr = "";
            for token, lbl in leaves:
                if get_day_yet and lbl == "NUMBER":
                    dateStr = token + "."
                    get_day_yet = False
                elif lbl == "MONTH":
                    dateStr += monthStringToNumber(token) + "."
                elif lbl == "NUMBER":
                    dateStr += token

            datum.set("date", dateStr)
            wrapper.set("sitzung-datum", dateStr)

        elif is_head_tag and label == "CCONTENT":
            ccontent = ET.SubElement(header, "inhaltsverzeichnis")
            ivzTitel = ET.SubElement(ccontent, "ivz-titel")
            ivzTitel.text = "Inhalt:"
            is_head_tag = False
            parent_tag = ccontent

        elif is_head_tag and label != "CBEGIN":
            p = ET.SubElement(header, 'p')
            p.text = line

        elif label == "CPLENARYPRO" or label == "CMEETING" or label == "CCONTENT":
            p = ET.SubElement(parent_tag, 'p')
            p.text = line

        #<START-LINE><BEGIN><COLON><NUMBER><DOT><NUMBER><TIME><BREAK-LINE>
        elif label == "CBEGIN":
            begin = ET.SubElement(content, 'sitzungsbeginn')
            time = ""
            is_begin_number = False
            for token,pos in leaves:
                if is_begin_number:
                    if pos == "TIME":
                        break;
                    time += token
                elif pos == "NUMBER":
                    time += token
                    is_begin_number = True

            begin.set("sitzung-start-uhrzeit", time)
            wrapper.set("sitzung-start-uhrzeit", time)
            parent_tag = begin
            group_tag = begin

        elif label == "CAGENDA":
            agenda_tag = ET.SubElement(content, 'tagesordnungspunkt')
            num = -1
            topId = ""
            for token, lbl in leaves:
                if lbl == "AGENDA":
                    topId = token
                    num = 0 #to check the before tag is an agenda
                elif lbl == "NUMBER" and num == 0:
                    topId += " " + token
                    break

            agenda_tag.set("top-id", topId)
            p_tag = ET.SubElement(agenda_tag, 'p')
            p_tag.text = line
            parent_tag = agenda_tag
            group_tag = agenda_tag

        #<START-LINE><BBRACKET><END><COLON><NUMBER><TIME><EBRACKET><BREAK-LINE>
        elif label == "CEND":
            end = ET.SubElement(content, 'sitzungsende')
            time = ""
            is_begin_number = False
            for token, pos in leaves:
                if is_begin_number:
                    if pos == "TIME":
                        break;
                    time += token
                elif pos == "NUMBER":
                    time += token
                    is_begin_number = True

            end.set("sitzung-ende-uhrzeit", time)
            wrapper.set("sitzung-ende-uhrzeit", time)
            parent_tag = anlagen

        # CPRESIDENT:{<START-LINE><PRESIDENT><TITLE>?<NAME>+<COLON><BREAK-LINE>}
        elif label == "CPRESIDENT":
            rolle = ET.SubElement(parent_tag, 'rolle')
            name = ET.SubElement(parent_tag, 'name')
            name.text = ""
            for token, pos in leaves:
                if pos == "PRESIDENT":
                    rolle.text = token
                elif pos == "TITLE" or pos == "NAME":
                    name.text += token
            name.text += ":"

        #<START-LINE><TITLE>?<NAME>+(<PARAGRAPH>|<BBRACKET><FRACTION><DIV>?<FRACTION>?<EBRACKET>|<BBRACKET><PARAGRAPH><EBRACKET>|<DOT>)*<COLON><BREAK-LINE>
        elif label == "CNAME":
            speak_tag = ET.SubElement(group_tag, 'rede')
            #TODO SET ID

            p_tag = ET.SubElement(speak_tag, 'p')
            p_tag.set("klasse","redner")
            speaker_tag = ET.SubElement(p_tag,'redner')

            #TODO: add id of redner

            name_tag = ET.SubElement(speaker_tag, 'name')
            fraktion_tag = ""
            start_fraktion_tag = False
            start_role_tag = False
            is_name_completed = False
            role = ""
            for token,pos in leaves:
                if start_fraktion_tag:
                    if pos == "DIV" or pos == "FRACTION":
                        before_tag.text += token
                    elif pos == "COLON":
                        break
                elif start_role_tag:
                    if pos == "COLON":
                        break;
                    role += token
                elif pos == "TITLE":
                    title = ET.SubElement(name_tag, 'titel')
                    title.text = token
                elif pos == "NAME":
                    first_lastname = token.split(" ")

                    if len(first_lastname) > 1:
                        first_tag = ET.SubElement(name_tag, 'vorname')
                        first_tag.text = ' '.join(first_lastname[:-1])

                    last_tag = ET.SubElement(name_tag, 'nachname')
                    last_tag.text = ''.join(first_lastname[-1])
                    is_name_completed = True

                elif is_name_completed:
                    if pos == "DOT":
                        start_role_tag = True
                    elif pos == "FRACTION":
                        fraction_tag = ET.SubElement(name_tag, 'fraktion')
                        fraction_tag.text = token
                        before_tag = fraction_tag
                        start_fraktion_tag = True
            if role != "":
                role_tag = ET.SubElement(name_tag, 'rolle')
                role_tag.text = role

            speaker_tag.tail = line
            if parent_tag.tag == "rede" and old_rede != None:
                # get redner tag
                name = speak_tag.find('p/redner/name')
                name_titel = name.find('titel')
                name_vor = name.find('vorname')
                name_nach = name.find('nachname')
                parent_name = parent_tag.find('p/redner/name')
                parent_titel = parent_name.find('titel')
                parent_vor = parent_name.find('vorname')
                parent_nach = parent_name.find('nachname')

                is_equal = True
                if name_titel != None and parent_titel != None and name_titel.text != parent_titel.text:
                    is_equal = False
                if is_equal == True and name_vor != None and parent_vor.text != None and name_vor.text != parent_vor.text:
                    is_equal = False
                if is_equal == True and name_nach != None and parent_nach.text != None and name_nach.text != parent_nach.text:
                    is_equal = False
                if is_equal == True:
                    tag_list = list(speak_tag)
                    for e in tag_list:
                        parent_tag.append(e)
                    group_tag.remove(speak_tag)
                else:
                    parent_tag = speak_tag
                    old_rede = speak_tag
            else:
                parent_tag = speak_tag
                old_rede = speak_tag

        elif label == "CCOMMENT":
            comment_tag = ET.SubElement(parent_tag, 'kommentar')
            comment_tag.text = line

        elif label == "CPARAGRAPH":
            p_tag = ET.SubElement(parent_tag, 'p')
            p_tag.text = line

    io_utils.exportXMLFile(file_path, wrapper)