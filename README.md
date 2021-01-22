# Entity detection in historical Bundestag protocols

## Setup
* Install <a href="https://taku910.github.io/crfpp/" target="_blank">CRF++</a>
```bash
Windows
- Download CRF++ zip file in "Binary package for MS-Windows"
- Extract zip file.
- Edit Enviroment Variables. Select the Variable "Path" then click "Edit" and create and insert the path of your CRF++
```
* Install <a href="https://lxml.de/installation.html" target="_blank">LXML</a>
```bash
pip install lxml
```
* Install NLTK
```bash
pip install nltk
```
# How to Run
### Training
The file `data\name_paticipants.txt` contains a list of names of conference participants and we use it as a parameter to the `ICCli` class.

```python
program = ICCli("../data/name_paticipants.txt")
program.exportCRFTraining('<your path of file xml>', '<your path of result training file>')
```

For an example. Suppose we have a xml file as follows:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DOKUMENT>
  <WAHLPERIODE>18</WAHLPERIODE>
  <DOKUMENTART>PLENARPROTOKOLL</DOKUMENTART>
  <NR>18/1</NR>
  <DATUM>22.10.2013</DATUM>
  <TITEL>Plenarprotokoll vom 22.10.2013</TITEL>
  <TEXT>
       Plenarprotokoll 18/1
       Deutscher Bundestag
       Stenografischer Bericht
   </TEXT>
</DOKUMENT>
```

And the `Training file` like this:
```bash
Plenarprotokoll	 PLE  	Cap	   B-PLENARYPRO
18	         NUM    NoCap	   B-NUMBER
/	         DIV	NoCap	   B-DIV
1	         NUM    NoCap	   B-NUMBER
Deutscher	 PAR    Cap	   B-PARAGRAPH
Bundestag	 PAR	Cap	   I-PARAGRAPH
Stenografischer	 PAR    Cap	   I-PARAGRAPH
Bericht	         PAR    Cap	   I-PARAGRAPH
```

### Template file for CRF++
Columns for each row of data in the training file are understood as conditions that help CRF to tag each row accurately.
You can find out more <a href="https://taku910.github.io/crfpp/" target="_blank">here</a>
`bin\template_file`
```bash
# Unigram
U00:%x[0,0]/%x[1,0]/%x[2,0]
U01:%x[-1,0]
U02:%x[0,0]
U03:%x[1,0]
U04:%x[0,0]/%x[0,1]/%x[1,1]/%x[0,2]
U05:%x[-1,1]/%x[0,1]/%x[1,1]/%x[2,1]

# Bigram
B
```

### Training

### Testing
