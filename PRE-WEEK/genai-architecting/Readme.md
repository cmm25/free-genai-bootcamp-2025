# Infrastructure Investment for GenAI

## Background
- **Objective:** Own the GenAI infrastructure to protect user data privacy and control rising costs associated with managed services.
- **Investment:** Allocate an AI PC budget of **$10-15K**.
- **User Base:** Support **300 active students** located within Nagasaki.

## Assumptions
- **Hardware Capability:** Open-source LLMs selected will run efficiently on hardware within the $10-15K budget.
- **Network Requirements:** A single server connected to the internet in the office is assumed to provide sufficient bandwidth for 300 students.

## Data Strategy
- **Copyright Compliance:** Due to concerns over copyrighted materials, all necessary training and operational data must be purchased and stored internally in a controlled database.

## Access Models Based on Cheapest, Best Performing
- **Cost-Effective Model Access:** Instead of being tied to a single vendor solution, the architecture should enable access to models based on their cost-performance balance. Evaluate open-source and accessible models that deliver high-quality results without prohibitive licensing fees.
- **Criteria for Selection:** Prioritize models that are both inexpensive and high-performing. Look for open-source options that have been demonstrated to match or exceed the performance of proprietary models (e.g., models like DeepSeek R1, Mistral AI’s offerings, or Meta’s LLaMA variants) while maintaining transparency and reducing vendor lock-in.
- **Flexibility & Adaptability:** Ensure that the system can seamlessly swap or integrate multiple models over time to leverage innovations and further cost reductions.

## Caching Strategy
- **Query Cache:**
  - Primary cache for immediate response to repeated queries.
  - Provides a direct path to users for cache hits, thereby minimizing latency.
  - Must implement efficient invalidation rules to ensure data accuracy.
  
- **Prompt Cache:**
  - Stores optimized prompts for common query patterns.
  - Reduces the overhead involved in retrieval-augmented generation (RAG) processing.
  - Should include version control for prompt templates to ensure consistency and ease of updates.
  
- **Output Cache:**
  - Stores validated responses for reuse in future requests.
  - Implements a feedback loop to the RAG system for continuous improvement.
  - Critical for optimizing overall system performance and reducing computation costs.



