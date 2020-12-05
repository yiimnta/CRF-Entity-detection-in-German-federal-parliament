python prepare_train_test_data.py
crf_learn template_file result/train_file.txt model_file
crf_test -m model_file result/test_file.txt > result/result.txt
python export_xml.py