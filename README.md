# Whatsapp Chat Data Development 

## Introduction
* This repository contains the codes used to convert html Whatsapp Chat data into xlsx.
* This was done for a research project led by Tel Aviv University.

## Overview of the project
### `aws_translate_multiprocess.py`:
1. Transcribe voice messages into english text using AWS Transcribe ().
### `webscraping_wodes.ipynb`:
2. Scrape the raw data (datetime, sender, text, etc.) from the html file of the Whatsapp chat data into tabular (csv) format.
- Ensure the validity of data through noticing common patterns and using regex.
- Encode Arabic characters and emojis to ensure data completeness.
3. Merge the transcribed data with scraped data.

## How to use
1. Clone the repository.
2. Create a `data/` and `secrets/` folder to include the raw html Whatsapp data, and the secrets for AWS key_id and access_key
3. Run `pip install -r requirements.txt` file to download the necessary packages.
4. Run the `aws_translate_multiprocess.py` file to transcribe the voice messages.
5. Navigate to the `webscraping_wodes.ipynb` file and run the codes according to the instructions to convert the html data into a csv file, and merge the transcribed data with the scraped data.
