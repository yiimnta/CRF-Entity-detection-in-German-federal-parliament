python prepare_train_test_data.py
crf_learn template_file train_file.txt model_file
crf_test -m model_file ../output/test_file.txt > ../output/result_crf.txt
python export_xml.py