import codecs
import re
import xml.etree.ElementTree as ET
from lxml import etree
import data_utils

def readFile(file_path):
    rs = []
    with codecs.open(file_path, 'r', 'utf-8') as file:
        for row in file:
            row = row.replace("\r", "")
            row = row.replace("\n", "")
            rs.append(row)
    return rs

def check_name_paticipants(row, list_name_paticipants):
    name = re.sub(r'^(Dr.|Prof.|Doctor|Professor|Frau|Herr)?\s?', '', row)
    name = re.sub(r'\s?(\(\w+\))?$', '', name)
    return name in list_name_paticipants

def repareDataInOneLine(xml_file_path, list_name_paticipants):
    data = []
    dataRow = ""
    is_connected = False
    is_just_removed = False# remove -

    #read file xml
    root = ET.parse(xml_file_path).getroot()
    allRow = root.find("TEXT").text.split("\n")

    for row in allRow:
        row = row.replace("\r", "").replace("\t", " ").strip()

        if row == "I n h a l t :":
            if dataRow != "":
                data.append(dataRow.strip())
                dataRow = ""
                is_connected = False
                is_just_removed = False
            data.append(row)
            continue
        if row == "" and is_just_removed:
            continue
        if check_name_paticipants(row, list_name_paticipants) or re.search(r'(\)|:|\.|\?|\d\s[A-Z])$', row) != None or (row == "" and dataRow != "" and re.search(r'(-|–)$', dataRow) == None):
            if row != "":
                if is_connected:
                    if re.search(r"(-|–)$", dataRow) != None:
                        dataRow = dataRow[:-1]
                    dataRow += row
                else:
                    dataRow = row
            data.append(dataRow.strip())
            dataRow = ""
            is_connected = False
            is_just_removed = False
        else:
            if re.search(r'^Beginn:.*(Jahr|Monat|Uhr|Minute|Sekunde)(e|en|n|)$', row) != None:
                data.append(row)
                dataRow = ""
            else:
                if re.search(r'(-|–)$', row) != None:
                    row = row[:-1]
                    dataRow += row
                    is_just_removed = True
                else:
                    if is_just_removed == False:
                        dataRow += row + " "
                    else:
                        dataRow += row
                    is_just_removed = False

                is_connected = True

    if dataRow != "":
        data.append(dataRow)

    # with codecs.open('./output/data_oneline.txt', 'w+', 'utf-8') as file:
    #     file.write("\n".join(data))
    return data


def exportData(file_save, arr):
    with codecs.open(file_save, 'w+', 'utf-8') as file:
        file.write("\n".join(arr))

def exportXMLFile(file_save, xml_object):

    tree =  etree.fromstring(ET.tostring(xml_object))
    etree.indent(tree, space="    ")
    xmlstr = etree.tostring(tree,
                            encoding="UTF-8",
                            xml_declaration=True,
                            pretty_print=True,
                            doctype='<?xml-stylesheet href="dbtplenarprotokoll.css" type="text/css" charset="UTF-8"?>\n<!DOCTYPE dbtplenarprotokoll SYSTEM "dbtplenarprotokoll.dtd">');
    with codecs.open(file_save, 'w+', encoding='utf-8') as file:
        file.write(xmlstr.decode('utf-8'))