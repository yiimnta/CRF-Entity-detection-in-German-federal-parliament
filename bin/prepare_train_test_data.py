from Include.new.program import ICCli

pro = ICCli("../data/name_paticipants.txt")
pro.exportCRFTraining('../data/xml/18001.xml', 'train_file.txt');
pro.exportCRFTesting('../data/xml/18002.xml', '../output/test_file.txt');