# Cognitive Email Ecosystem

A hierarchical agent-based approach to email management that processes emails in layers instead of feeding an entire inbox to a single LLM at once.

## Architecture

The system consists of specialized components arranged in a hierarchical structure:

1. **Cognitive Email Ecosystem**: Core system that orchestrates multiple agent layers
2. **Ingestion Agent**: Normalizes email data for processing
3. **Observer Agent**: Categorizes emails and detects user traits
4. **Context Agent**: Analyzes external factors affecting email interpretation
5. **Social Graph Agent**: Maps and understands relationship networks
6. **Intent Decoder**: Determines the purpose and meaning behind emails
7. **Execution Specialists**: Handles specific email types with specialized logic

## Project Structure

```
.
├── cognitive_email_ecosystem.py  # Core hierarchical agent system
├── src/
│   ├── ingestionAgent.py         # Email data loading and normalization
│   ├── observerAgent.py          # Email categorization and user trait detection
│   ├── cognitive_email_adapter.py # Connects agents to the cognitive system
├── tests/                        # Unit tests
├── email_interface.py            # Flask web interface
├── observe_demo.py               # Demonstration script
├── data/
│   ├── syntheticEmails.json      # Sample email threads
│   ├── observerSessionData.json  # Thread data for the Observer Agent
│   ├── observerLongTermData.json # Long-term user trait storage
```

## Key Features

- Multi-layered email processing pipeline
- Email categorization into meaningful buckets (Work, Social, Bills, etc.)
- User trait detection based on email patterns
- Relationship mapping through social graph analysis
- Web interface for visualization and interaction

## Getting Started

1. Clone the repository
2. Install dependencies
3. Run the demonstration script:
   ```
   python observe_demo.py
   ```
4. Access the web interface:
   ```
   python email_interface.py
   ```

## Benefits Over Traditional Methods

The hierarchical agent-based approach provides:
- More targeted analysis through specialized components
- Better understanding of context and relationships
- More efficient processing by breaking down the task into manageable layers
- Improved user experience through adaptive categorization 