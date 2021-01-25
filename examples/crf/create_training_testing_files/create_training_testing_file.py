import sys
sys.path.append('../../../')
from program import ICCli
import io_utils

pro = ICCli("../../../data/name_paticipants.txt")
path = '../../../examples/crf/create_training_testing_files/'

##crate Training File
pro.exportCRFTraining('../../../data/xml/18001.xml', path + 'output/18001_train_file.txt');

##crate Testing File
pro.exportCRFTesting('../../../data/xml/18002.xml', path + 'output/18002_test_file.txt');
