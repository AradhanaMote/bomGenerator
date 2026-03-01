# 🤖 AI-Based Bill of Materials (BOM) Generator

A powerful tool that generates structured Bill of Materials from simple product descriptions using Google's Gemini AI.

## ✨ Features

- **AI-Powered Extraction** - Automatically identifies major components and subcomponents
- **Structured Output** - JSON format with beautiful terminal tables
- **Manual Editing** - Add, edit, or delete components
- **Cost Estimation** - Calculates total cost based on component database
- **CSV Export** - Export BOMs for Excel/Google Sheets
- **Revision Control** - Tracks all changes with version history

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Gemini API key (free) from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AradhanaMote/bomGenerator.git
   cd bomGenerator

    Install dependencies
    bash

    pip install -r requirements.txt

    Set up your API key
    bash

    # Create .env file (this file is ignored by git)
    echo "GEMINI_API_KEY=your-actual-api-key-here" > .env

        ⚠️ IMPORTANT: Never commit your real API key! The .env file is in .gitignore.

    Run the application
    bash

    python src/main.py

📖 Usage Guide
Generate a BOM

    Select option 1 from the main menu

    Enter a product description (e.g., "Design a small electric scooter with lithium battery, disc brakes, LED display")

    Wait for AI processing (5-10 seconds)

    View the complete BOM with components and subcomponents

Edit Manually

    Option 3 lets you add, edit, or delete components

Export Results

    Option 4 exports to CSV format for further analysis

📊 Sample Output
text

```
------------------------------------------------------------
📊 BOM PREVIEW: Compact Electric Scooter with Disc Brakes and LED Display
------------------------------------------------------------
+----------+-------------------------------+------------+-------+--------+-----------------+
| ID       | Component                     | Category   | Qty   | Unit   | Subcomponents   |
+==========+===============================+============+=======+========+=================+
| comp-001 | Frame Assembly                | structural | 1     | piece  | 5               |
| comp-002 | Motor & Drive System          | electrical | 1     | piece  | 4               |
| comp-003 | Lithium Battery Pack          | electrical | 1     | piece  | 4               |
| comp-004 | Braking System                | mechanical | 1     | set    | 5               |
| comp-005 | Steering & Handlebar Assembly | mechanical | 1     | piece  | 4               |
| comp-006 | Wheels & Tires                | mechanical | 1     | set    | 4               |
| comp-007 | LED Display & Lighting        | electrical | 1     | set    | 4               |
| comp-008 | Charging System               | electrical | 1     | set    | 3               |
| comp-009 | Fenders & Accessories         | structural | 1     | set    | 4               |
| comp-010 | Fasteners & Hardware Kit      | hardware   | 1     | kit    | 4               |
+----------+-------------------------------+------------+-------+--------+-----------------+

💰 **TOTAL ESTIMATED COST: $460.55**
```

## 🏗️ Project Structure

```
bomGenerator/
├── src/
│   ├── main.py                 # Main application entry point
│   ├── llm_processor_gemini.py # Gemini API integration
│   ├── bom_parser.py           # BOM parsing and validation
│   ├── cost_estimator.py       # Cost calculation logic
│   ├── export_handler.py       # CSV/JSON export
│   ├── revision_control.py     # Version tracking
│   └── utils.py                # Helper functions
├── data/
│   ├── component_prices.json   # Price database for cost estimation
│   └── sample_outputs/         # Example BOM exports
├── requirements.txt            # Python dependencies
├── config.yaml                 # Configuration settings
└── .env.example                # Template for API key (copy to .env)
```

🔑 Getting a Gemini API Key

    Visit Google AI Studio

    Sign in with your Google account

    Click "Create API Key"

    Copy the key and add it to your .env file
