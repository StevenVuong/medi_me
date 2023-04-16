initialise:
	@echo "Initializing git..."
	git init
	@echo "Initializing Poetry"
	poetry init
	poetry env use /bin/python3.10
	
install: 
	@echo "Installing..."
	poetry install
	poetry run pre-commit install

activate:
	@echo "Activating virtual environment"
	poetry env use /bin/python3.10
	poetry shell

scrape_overview:
	clear
	@echo "Scraping all doctors overview."
	python ./src/scrape/doctor_overview.py

scrape_detail:
	clear
	@echo "Scraping doctor details"
	python ./src/scrape/doctor_detail.py

# create elastic search index and populate with data
setup_elastic_index:
	clear
	@echo "Creating elasticsearch index"
	python ./src/elastic_search/create_index.py
	@echo "Populating elasticsearch index"
	python ./src/elastic_search/populate_index.py

# run streamlit app
run_app:
	clear
	@echo "Running streamlit app"
	streamlit run ./app.py

format:
	@echo "Formatting..."
	black ./
	flake8 ./
	isort ./
	interrogate -vv ./

test:
	pytest

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache