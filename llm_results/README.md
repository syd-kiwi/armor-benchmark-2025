# LLM Results
This directory contains the output files from evaluating Large Language Models (LLMs) on military decision-making scenarios. These evaluations are part of the broader llm-decision-framework project, which investigates how well LLMs align with ethical and legal standards in high-stakes operational contexts.

## Contents
Each file in this directory typically represents the evaluation results of one or more LLMs across specific prompts. Files may include:

Prompt: The input question or scenario posed to the LLM.

LLM Response: The model-generated response.

Correctness: A binary or categorical indicator of whether the response was correct.

Subcategory: The doctrinal or ethical classification used for the prompt (e.g., Positive Identification, Proportionality).

Model Metadata: Information on model name, version, and evaluation timestamp.

## Usage
These results are analyzed in llm_analysis.ipynb and other supporting scripts to:

Evaluate model accuracy across ethical and legal subcategories

Generate performance heatmaps and visualizations

Identify patterns and weaknesses in LLM decision-making

Support benchmark development and future model comparisons

Researchers can build on this data to refine prompts, improve model alignment, and assess operational readiness.
