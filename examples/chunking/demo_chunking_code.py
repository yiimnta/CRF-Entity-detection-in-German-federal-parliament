import sys
sys.path.append('../../')
from program import ICCli
import io_utils

pro = ICCli("../../data/name_paticipants.txt")
path = '../../examples/chunking/'

##crate Training File
pro.exportCRFTraining(path + 'input/18003_input_emptyline_errors_fixed.xml', path + 'output/18003_train_file.txt');

##export XML
pro.exportXML(path + 'output/18003_train_file.txt', path+ 'output/18003_chunking_result.xml')