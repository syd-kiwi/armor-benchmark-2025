# LLM Decision Framework

This project benchmarks the performance of Large Language Models (LLMs) against real-world military decision-making challenges using doctrine-grounded scenarios and policy-aligned prompts.

## Overview

The objective is to evaluate how effectively LLMs can interpret and respond to complex military scenarios by simulating decision-making processes that align with established doctrines and policies.([llm-strategist.github.io][1])

## Repository Structure

* llm_results/: Directory housing the results of LLM evaluations.
* foundation_prompts/: Collection of prompts based on military doctrines used to test LLM responses.

## Getting Started

### Prerequisites

* Python 3.8 or higher
* Jupyter Notebook
* Required Python packages (as specified in the notebook)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/syd-kiwi/llm-decision-framework.git
   cd llm-decision-framework
   ```



2. **Install necessary packages:**

   It's recommended to use a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```



*Note: If `requirements.txt` is not provided, please install the packages as specified in `llm_analysis.ipynb`.*

3. **Launch Jupyter Notebook:**

   ```bash
   jupyter notebook
   ```



Open `llm_analysis.ipynb` to explore the analysis.

## Usage

The `llm_analysis.ipynb` notebook guides you through the process of evaluating LLM responses to military decision-making scenarios. It includes:([llm-strategist.github.io][1])

* Loading and preprocessing of scenario data
* Generation of prompts aligned with military doctrines
* Interaction with selected LLMs
* Analysis of LLM responses against expected outcomes

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## Contact

For questions or inquiries, please contact [syd-kiwi](https://github.com/syd-kiwi).
