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
The file `data\name_paticipants.txt` contains a list of names of conference participants and the content is collected from <a href="https://www.bundestag.de/parlament/plenum/abstimmung/liste" target="_blank">here</a>.
We use this file as a parameter to the `ICCli` class.


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

Full example is found <a href="https://github.com/yiimnta/CRF-Entity-detection-in-German-federal-parliament/tree/main/examples/crf/create_training_testing_files" target="_blank">here</a>

### Template file for CRF++
- Columns of each row of data in the training file are understood as conditions that help for the POS Tagging of CRF++ accurately. Through the template file you can customize the conditions as you want.
- You can find more information <a href="https://taku910.github.io/crfpp/" target="_blank">here</a>
- `bin\template_file`
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

### CRF++ Training
Create a model file for the CRF model

```bash
crf_learn <template file path> <training file path> <model file name>
```
For an example:
```bash
crf_learn template_file train_file.txt model_file
```
Full example is found <a href="https://github.com/yiimnta/CRF-Entity-detection-in-German-federal-parliament/blob/main/examples/crf/crf%2B%2B/crf_learn.sh" target="_blank">here</a>

### Testing
Create data for testing

```python
program = ICCli("../data/name_paticipants.txt")
program.exportCRFTesting('<your path of file xml>', '<your path of result testing file>')
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
Plenarprotokoll	 PLE  	Cap
18	         NUM    NoCap
/	         DIV	NoCap
1	         NUM    NoCap
Deutscher	 PAR    Cap
Bundestag	 PAR	Cap
Stenografischer	 PAR    Cap
Bericht	         PAR    Cap
```

Full example is found <a href="https://github.com/yiimnta/CRF-Entity-detection-in-German-federal-parliament/tree/main/examples/crf/create_training_testing_files" target="_blank">here</a>

### CRF++ Testing

