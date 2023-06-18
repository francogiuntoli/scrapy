You'll need Docker to run this app snippet.
On terminal run `docker run -p 8050:8050 scrapinghub/splash`

Clone the project and activate environement `source /path/to/venv/bin/activate` replacing "/path/to" with the correct path.
Open a separate terminal without closing the previous one and run `scrapy crawl gorgias`.
It will create a CSV file in the root folder called **gorgias.csv** with the exact structure to run it through OpenAIs embeddings engine.
