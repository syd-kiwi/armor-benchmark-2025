# LLM Decision Framework

This project benchmarks the performance of Large Language Models (LLMs) against real-world military decision-making challenges using doctrine-grounded scenarios and policy-aligned prompts.

## Overview

Objective: Evaluate how effectively LLMs can interpret and respond to complex military scenarios by simulating decision-making processes that align with established doctrines and policies.([llm-strategist.github.io][1])

Approach: Utilize doctrine-grounded prompts to simulate real-world military decision-making situations.

Evaluation: Analyze LLM responses for consistency, accuracy, and alignment with established military guidelines.

## Repository Structure

* `llm_results/`: Directory housing the results of LLM evaluations.
   * `model_outputs/`: Raw responses from various LLMs to the benchmark questions. Files are named to reflect the model used.
   * `evaluation_scores.csv`: Contains scoring results for each model, measuring correctness and category-wise performance.
   * `summary_heatmaps/`: Visualizations of model performance across doctrinal subcategories (e.g., accuracy heatmaps, confusion matrices).
     
* `foundation_prompts/`: Collection of prompts based on military doctrines used to test LLM responses.
   * Contains CSV files with doctrinally grounded multiple-choice questions.
   * These are grouped into subcategories: `ethics_questions.csv` based on ethical dilemmas from ADA590672 and `roe_questions.csv` based on rules of engagement from TBS B130936.
   * Each row in these files includes the question, answer choices, and the correct answer label.

## Evaluation Metrics
* Doctrine Alignment: Measures how well LLM responses align with established military doctrines.
* Decision Accuracy: Assesses the correctness of decisions made by LLMs in simulated scenarios.
* Response Consistency: Evaluates the consistency of LLM outputs across similar scenarios.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## Contact

For questions or inquiries, please contact [syd-kiwi](https://github.com/syd-kiwi).
