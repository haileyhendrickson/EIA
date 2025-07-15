# EIA API

A GUI-based Python tool to query two reports from the EIA API. The program efficiently queries a Natural Gas Prices and Futures report, and an Electric Power Operations report from https://www.eia.gov/opendata/browser/natural-gas/pri and https://www.eia.gov/opendata/browser/electricity/facility-fuel, respectively.

## 🔧 Features
- No Python install needed!
- Select date ranges
- Quickly download and extract zipped data
- Export processed Excel files

## 📦 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/haileyhendrickson/EIA.git
   cd EIA

## Setup and Configuration
### 1. Get Your EIA API Key
1. Visit EIA's API registration page at https://www.eia.gov/opendata/register.php
2. Register for a free account
3. Copy your API key from your account dashboard
### 2. Configure API Key


## Use
1. Download the `.exe` file
2. Run the application
3. Select your report type
4. Choose date range
5. Click "Generate Report"
6. Export to Excel

## Running on a Local Machine:
- python -m venv venv  # create a new env
- source venv/Scripts/activate  # activate env
- pip install -r requirements.txt  # install dependencies

## Notes for use 
- Temporary partial files will appear during data retrieval but are deleted when processing completes.


## Version History -- Last updated: July 2025 (version 2) 
- v1.0: Initial release - Included Natural Gas Report
- v2.0: Added Energy Power Operations Report

## License
This project is licensed under the [MIT License](LICENSE).
