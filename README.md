
<p align="center">
  <img src="assets/images/logo.png" width="300" height="130">
</p>

[![pypi](https://img.shields.io/pypi/v/spectradb)](https://pypi.org/project/spectradb)
[![codecov](https://codecov.io/gh/acmoudleysa/SpectraDB/graph/badge.svg?token=AQWFO4NG6Q)](https://codecov.io/gh/acmoudleysa/SpectraDB)

# **SpectraDB: A Lightweight Spectroscopic Data Manager**

## Introduction
In many labs, data from instruments like FTIR, fluorescence, or NMR are saved as individual files (often in strange formats) and scattered across different folders. This can quickly lead to a cluttered system that’s hard to manage and search through. 

**SpectraDB** is designed to simplify this process by letting you store all your spectroscopic data in a single, organized SQLite database. Each type of spectroscopic data gets a unique `spec_id`, and every sample is given a `sample_id`. This means you can easily search and retrieve any analysis for any sample without digging through endless folders of files.

## How It Works (in Simple Terms)

1. **Collect Data from Instruments**:
   - After running a sample on an instrument (like FTIR or NMR), you typically copy the data file onto your computer. The file might be in an unusual format specific to the instrument, but don’t worry—**SpectraDB** handles that for you.

2. **Add the Data to SpectraDB**:
   - You can use built-in functionality to add the data to the database. SpectraDB will convert the raw file (whatever format it's in) into a format that’s easy to work with, and then store it in an SQLite database.
   - Along with the spectroscopic data, you’ll also be able to store metadata like `measurement_id`, `instrument_id`, experiment details, and anything else you want to track.

3. **Avoid Duplicates**:
   - SpectraDB is smart! It checks if the same sample and analysis already exist in the database, so you won’t accidentally store duplicate data. This helps keep things tidy.

4. **Query the Data Easily**:
   - Once your data is in the database, you can search by **sample** (using `sample_id`) to see what spectroscopic techniques have been run on that sample, or search by **spectroscopy type** (using `spec_id`) to pull all the relevant data for a particular technique (e.g., all FTIR results).
   - No more hunting through folders—just run a query, and you get what you need.

5. **What You Can Do Next**:
   - After pulling the data, you can visualize it, analyze trends, or run further processing as needed. You have all the information in one place!

## Key Features
- **Centralized Storage**: All spectroscopic data is stored in one SQLite database, making it easy to manage and search.
- **Automatic Conversion**: Raw data files from instruments are automatically converted to usable formats and stored efficiently in the database.
- **Unique IDs**: Each spectroscopic file gets a `spec_id`, and each sample gets a `sample_id`, allowing for simple and quick queries.
- **Duplicate Checks**: Built-in checks prevent duplicate entries, ensuring clean and organized data.
- **Query Flexibility**: Search by sample or spectroscopy type, and get a complete view of your data without hassle.

## Project Ideas
- Organize all your data in one place by converting raw instrument data into a database-friendly format.
- Query data based on sample (`sample_id`) to see all the spectroscopic analyses performed on that sample.
- Query based on spectroscopy type (`spec_id`) to retrieve specific data (e.g., only FTIR results).
- Visualize and analyze the data after retrieval for further insights.
