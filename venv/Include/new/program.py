import re
import codecs
from Include.new import io_utils
from Include.new import data_utils

class ICCli():
    list_fraction = ['CDU/CSU', 'SPD', 'AFD', 'FDP', 'DIE$LINKE', 'BÜNDNIS$90/DIE$GRÜNEN']
    list_mood = ['Beifall','Heiterkeit','Zuruf','Widerspruch','Lachen']
    list_name_paticipants_defaults = []
    result = []
    is_begin = False
    data_name_path = ""

    def __init__(self, data_name_path):
        self.data_name_path = data_name_path

    def run(self, file_path):

        self.list_name_paticipants_defaults = []
        self.result = []
        self.is_begin = False

        data = io_utils.repareDataInOneLine(file_path)
        self.list_name_paticipants_defaults = io_utils.readFile(self.data_name_path)

        for row in data:
            self.matchUp(row)

        self.result = data_utils.convertBIOTag(self.result)

    def exportCRFTraining(self, input_file, output_file):
        self.run(input_file)
        crf_data = data_utils.convertCRFTraining(self.result)
        io_utils.exportData(output_file, crf_data)

    def exportCRFTesting(self, input_file, output_file):
        self.run(input_file)
        crf_data = data_utils.convertCRFTesting(self.result)
        io_utils.exportData(output_file, crf_data)

    def exportXML(self, input_file, output_file):
        data = io_utils.readFile(input_file)
        biotag_data = []
        had_break_line = False
        for row in data:
            if row == "" and had_break_line == False:
                biotag_data.append(("","","",""))
                had_break_line = True
            else:
                biotag_data.append(tuple(row.split("\t")))
                had_break_line = False

        chunk_data = data_utils.convertChunkTag(biotag_data)
        data_utils.convertXMLData(output_file, chunk_data)

    def matchUp(self, row):

        # trim
        row = row.strip()

        # don't make anything when row is empty or enter
        if row == "\n" or row == "":
            return

        #convert name of participants
        #Ex: Michael von Abercron => Michael$von$Abercron
        row = data_utils.convert_paticipants_name_format(row, self.list_name_paticipants_defaults)

        # convert name of fraction
        # Ex: DIE LINKE => DIE$LINKE
        row = data_utils.convert_fraction_format(row)

        #guess tag
        self.addTags(row)

    def addTags(self, row):
        tokens = data_utils.split(row)
        result = []
        word = None
        type = "O"
        tag = "O"
        is_begin_row = False
        is_title_before = False

        if re.search(r'^Beginn:.*(Uhr|Minute|Minuten)$', row) != None:
            is_begin_row = True

        for word in tokens:
            upcase = data_utils.getUpcaseCaption(word)

            if word == "Beginn" and is_begin_row:
                result.append((word, "BE", upcase, "BEGIN"))

            elif re.search(r'^Tagesordnungspunkt(|e|es|en|em)$', word) != None:
                result.append((word, "AGEN", upcase, "AGENDA"))

            elif re.search(r'^(Jahr|Monat|Uhr|Minute|Sekunde)(e|en|n|)$', word) != None:
                result.append((word, "TIME", upcase, "TIME"))

            elif re.search(r'^\-?\d{1,10}(?:\.\d{1,10})?$', word) != None:
                result.append((word, "NUM", upcase, "NUMBER"))

            elif word == ":":
                result.append((word, "COL", upcase, "COLON"))

            elif word == "(":
                result.append((word, "BBRACKET", upcase, "BBRACKET"))

            elif word == ")":
                result.append((word, "EBRACKET", upcase, "EBRACKET"))

            elif word == "." or word == "?" or word == "!" or word == ",":
                result.append((word, "DOT", upcase, "DOT"))

            elif word in self.list_fraction:
                for w in word.split("$"):
                    result.append((w, "FRACT", upcase, "FRACTION"))

            elif word in self.list_mood:
                result.append((word, "MOOD", upcase, "MOOD"))

            elif re.search(r'^(Präsident|Vizepräsident)(s|es|in|innen|en)*$', word) != None:

                result.append((word, "PRE", upcase, "PRESIDENT"))

            elif re.search(r'^(Dr.|Prof.|Doctor|Professor|Frau|Herr)$', word) != None:
                is_title_before = True
                result.append((word, "TITLE", upcase, "TITLE"))
            else:
                #check name
                text = word.replace("$"," ");
                if text in self.list_name_paticipants_defaults:
                    arr = text.split(" ")
                    for w in arr:
                        result.append((w, "NAME", upcase, "NAME"))
                elif is_title_before:
                    if word.istitle():
                        result.append((word, "NAME", upcase, "NAME"))
                        continue
                    else:
                        is_title_before = False
                    result.append((word, "PAR", upcase, "PARAGRAPH"))
                else:
                    result.append((word, "PAR", upcase, "PARAGRAPH"))

        result.append(("", "BREAK", "", "BREAK-LINE"))

        self.result += result

#pro = ICCli("data/data_name.txt")
#pro.exportCRFTraining('data/data_using_train.txt', 'output/train_file.txt');
#pro.exportCRFTesting('data/data_using_test.txt', 'output/result/test_file.txt');

#pro.exportXML("output/result.txt","output/result.xml")