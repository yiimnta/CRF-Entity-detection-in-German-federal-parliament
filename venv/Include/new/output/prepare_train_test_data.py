from Include.new.program import ICCli

pro = ICCli("../data/data_name.txt")
pro.exportCRFTraining('../data/data_using_train.txt', 'result/train_file.txt');
pro.exportCRFTesting('../data/data_using_test.txt', 'result/test_file.txt');