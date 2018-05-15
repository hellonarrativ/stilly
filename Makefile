start:
	PYTHONPATH=sample:src python sample/stilly_app/system_example.py
test:
	PYTHONPATH=src py.test tests
