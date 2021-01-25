import re
import nltk
from nltk.tree import Tree
from nltk.chunk import conlltags2tree
import xml.etree.ElementTree as ET
import io_utils
from xml.dom import minidom
import copy

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
    if checkUpcase(word):
        cap = 'Cap'

    return cap

def checkUpcase(word):
    return re.search(r'^[A-ZÄÖÜß]', word) != None

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
        CAGENDA:{<START-LINE>(<PARAGRAPH><AGENDA><NUMBER>)+(<PARAGRAPH>|<END>|<DIV>|<MONTH>|<MEETING>|<WEEKDAY>|<STATE>|<DOT>|<QUESTION>|<MOOD>|<NUMBER>|<TIME>|<TITLE>?<NAME>|<FRACTION><DIV>?<FRACTION>?|)*<COLON><BREAK-LINE>}
        CEND:{<START-LINE><BBRACKET><END><COLON><NUMBER><DOT><NUMBER><TIME><EBRACKET><BREAK-LINE>}
        CCOMMENT:{<START-LINE>(<BBRACKET>(<INTERQUESTION>|<MOOD>|<PARAGRAPH>|<END>|<COLON>|<MONTH>|<WEEKDAY>|<MEETING>|<STATE>|<TITLE>?<NAME>*|<FRACTION><DIV>?<FRACTION>?|<DOT>|<QUESTION>|<COLON>|<PRESIDENT>|<NUMBER>|<DIV>|<TITLE>)+<EBRACKET>)+<BREAK-LINE>}
        CPARAGRAPH:{<START-LINE>(<INTERQUESTION>|<NAME>|<PRESIDENT>|<TITLE>|<MONTH>|<WEEKDAY>|<END>|<MEETING>|<STATE>|<PRESIDENT>|<AGENDA>|<MOOD>|<NUMBER>|<TIME>|<FRACTION><DIV>?<FRACTION>?|<DIV>|<PARAGRAPH>|<DOT>|<COLON>|<QUESTION>|<BBRACKET>|<EBRACKET>)+(<DOT>|<COLON>|)<BREAK-LINE>}
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
    old_group_tag = content
    reder = None
    questioner = None
    is_president_before = False
    is_in_interQuestion = False
    interQuestion_tag = None
    president_tag = None

    for label, leaves in xml_data:
        line = ""
        for ch, tag in leaves:
            if tag not in ["DOT","COLON", "QUESTION"]:
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
            if is_president_before:
                list_group_tags = list(group_tag)
                if list_group_tags[-1].tag == "praesident":
                    if len(list_group_tags[-1]) == 1:
                        group_tag.remove(list_group_tags[-1])
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
            p_tag = ET.Element('p')
            p_tag.text = line
            group_tag = agenda_tag
            if president_tag != None:
                new_president_tag = ET.Element('preasident')
                new_name = copy.deepcopy(president_tag.find('name'))
                new_president_tag.append(new_name)
                group_tag.append(new_president_tag)
                new_president_tag.append(p_tag)
                parent_tag = new_president_tag
            else:
                agenda_tag.append(p_tag)
                parent_tag = agenda_tag

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
            president_tag = ET.Element('praesident')
            name = ET.SubElement(president_tag, 'name')
            rolle = ET.Element('rolle')

            for token, pos in leaves:
                if pos == "PRESIDENT":
                    rolle.text = token
                elif pos == "TITLE":
                    titel = ET.SubElement(name, 'titel')
                    titel.text = token
                elif pos == "NAME":
                    first_lastname = token.split(" ")
                    if len(first_lastname) > 1:
                        first_tag = ET.SubElement(name, 'vorname')
                        first_tag.text = ' '.join(first_lastname[:-1])
                    last_tag = ET.SubElement(name, 'nachname')
                    last_tag.text = ''.join(first_lastname[-1])
            name.append(rolle)

            if is_in_interQuestion == True:
                interQuestion_tag.append(president_tag)
            else:
                group_tag.append(president_tag)

        #<START-LINE><TITLE>?<NAME>+(<PARAGRAPH>|<BBRACKET><FRACTION><DIV>?<FRACTION>?<EBRACKET>|<BBRACKET><PARAGRAPH><EBRACKET>|<DOT>)*<COLON><BREAK-LINE>
        elif label == "CNAME":
            speak_tag = ET.Element('rede')
            p_tag = ET.SubElement(speak_tag, 'p')
            p_tag.set("klasse","redner")
            speaker_tag = ET.SubElement(p_tag,'redner')

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

            if is_in_interQuestion == True:
                is_equal_reder = compareSpeaker(speak_tag, reder)
                if questioner == None:
                    if is_equal_reder == False:
                        questioner = speak_tag
                else:
                    if is_equal_reder == False:
                        is_equal = compareSpeaker(speak_tag, questioner)
                        if is_equal == False:
                            is_in_interQuestion = False
                            questioner = None
                            reder = None
                            group_tag.append(speak_tag)
                            parent_tag = speak_tag
                            continue

                interQuestion_tag.append(speak_tag)
                parent_tag = speak_tag
                continue

            # if parent_tag.tag == "rede":
            #     is_equal = compareSpeaker(speak_tag, parent_tag)
            #
            #     if is_equal == True:
            #         tag_list = list(speak_tag)
            #         for e in tag_list:
            #             parent_tag.append(e)
            #     else:
            #         group_tag.append(speak_tag)
            #         parent_tag = speak_tag
            # else:
            group_tag.append(speak_tag)
            parent_tag = speak_tag


        elif label == "CCOMMENT":
            comment_tag = ET.SubElement(parent_tag, 'kommentar')
            comment_tag.text = line

        elif label == "CPARAGRAPH":

            is_interQuestion = False

            #check the sentence is a question or not
            #and whether the speaker is president or not
            if leaves[-2][1] == "QUESTION" and is_president_before:
                #check contains INTERQUESTION card or not?
                for token, tag in leaves:
                    if tag == "INTERQUESTION":
                        is_interQuestion = True
                        break
            if is_interQuestion:
                president_tag = list(group_tag)[-1]
                group_tag.remove(president_tag)
                interQuestion_tag = ET.SubElement(parent_tag, 'zwischenfrage')
                interQuestion_tag.append(president_tag)
                pre_sentence_tag = ET.SubElement(president_tag, 'p')
                pre_sentence_tag.text = line
                questioner = None
                reder = parent_tag
                is_in_interQuestion = True
                parent_tag = president_tag
            else:
                if is_president_before:
                    parent_tag = president_tag
                p_tag = ET.SubElement(parent_tag, 'p')
                p_tag.text = line

        if label == "CPRESIDENT":
            is_president_before = True
        else:
            is_president_before = False

    io_utils.exportXMLFile(file_path, wrapper)

def compareSpeaker(a_tag, b_tag):
    if a_tag.tag != "rede" or b_tag.tag != "rede":
        return False
    a_name = a_tag.find('p/redner/name')
    a_titel = a_name.find('titel')
    a_vor = a_name.find('vorname')
    a_nach = a_name.find('nachname')

    b_name = b_tag.find('p/redner/name')
    b_titel = b_name.find('titel')
    b_vor = b_name.find('vorname')
    b_nach = b_name.find('nachname')

    is_equal = True
    if a_titel != None and b_titel != None and a_titel.text != b_titel.text:
        is_equal = False
    if is_equal == True and a_vor != None and b_vor.text != None and a_vor.text != b_vor.text:
        is_equal = False
    if is_equal == True and a_nach != None and b_nach.text != None and a_nach.text != b_nach.text:
        is_equal = False

    return is_equal