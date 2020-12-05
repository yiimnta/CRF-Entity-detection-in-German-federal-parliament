import codecs
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

def readFile(file_path):
    rs = []
    with codecs.open(file_path, 'r', 'utf-8') as file:
        for row in file:
            row = row.replace("\r", "")
            row = row.replace("\n", "")
            rs.append(row)
    return rs

def repareDataInOneLine(file_path):
    data = []
    dataRow = ""
    is_connected = False
    row = ""
    is_just_removed = False# remove -
    with codecs.open(file_path, 'r', 'utf-8') as file:
        for row in file:
            row = row.replace("\r", "")
            row = row.replace("\n", "")
            if re.search(r'(\)|:|\.|\?)$', row) != None or (row == "" and dataRow != "" and re.search(r'(-|–)$', dataRow) == None):
                if row != "":
                    if is_connected:
                        if re.search(r"(-|–)$", dataRow) != None:
                            dataRow = dataRow[:-1]
                    dataRow += row
                data.append(dataRow)
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

    if is_connected:
        if len(data) > 0:
            data[-1] += row

    # with codecs.open('data/data_oneline.txt', 'w+', 'utf-8') as file:
    #     file.write("\n".join(data))
    return data

def exportData(file_save, arr):
    with codecs.open(file_save, 'w+', 'utf-8') as file:
        file.write("\n".join(arr))

def exportXMLFile(file_save, xml_object):
    xmlstr = minidom.parseString(ET.tostring(xml_object)).toprettyxml(indent="   ")
    with codecs.open(file_save, 'w+', 'utf-8') as file:
        file.write(xmlstr)