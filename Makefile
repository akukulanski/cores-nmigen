


.phony: test clean

test:
	python3 -m pytest -v cores_nmigen

clean:
	-rm -rf *.vcd sim_build/ .pytest_cache/ ./**/__pycache__/ ./*/**/__pycache__/ *.egg-info