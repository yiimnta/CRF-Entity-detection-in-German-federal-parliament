from program import ICCli

pro = ICCli("data/data_name.txt")
pro.exportCRFTraining('data/data_using_test.txt', 'output/result/result.txt');
pro.exportXML("output/result/result.txt","output/result/result.xml")