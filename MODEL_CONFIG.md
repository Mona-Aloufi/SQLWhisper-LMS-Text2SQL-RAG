# Model Configuration

This document describes the model configuration for SQLWhisper Text2SQL.

## Models Used

### 1. SQL Generation Model
- **Model**: `yasserrmd/Text2SQL-1.5B`
- **Type**: CausalLM (AutoModelForCausalLM)
- **Purpose**: Converts natural language questions into SQL queries
- **Used by**: `EnhancedText2SQLService` → `ModelHandler`
- **Environment Variable**: `MODEL_NAME`
- **Default**: `yasserrmd/Text2SQL-1.5B`

### 2. Summarization Model
- **Model**: `google/flan-t5-base`
- **Type**: Seq2SeqLM (AutoModelForSeq2SeqLM)
- **Purpose**: Converts SQL query results into natural language summaries
- **Used by**: `ResultSummarizationService` → `ModelHandler`
- **Environment Variable**: `SUMMARY_MODEL_NAME`
- **Default**: `google/flan-t5-base`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# SQL Generation Model
MODEL_NAME=yasserrmd/Text2SQL-1.5B

# Summarization Model
SUMMARY_MODEL_NAME=google/flan-t5-base

# Optional: Hugging Face Token (if needed)
HF_TOKEN=your_token_here
```

### Model Handler

The `ModelHandler` class automatically:
- Detects model type (CausalLM vs Seq2SeqLM)
- Loads models with appropriate architecture
- Caches models for reuse
- Handles both model types in generation

### Service Initialization

```python
# SQL Generation Service
from src.services.text2sql_service import EnhancedText2SQLService
t2s_service = EnhancedText2SQLService()
# Uses MODEL_NAME env var or default: yasserrmd/Text2SQL-1.5B

# Summarization Service
from src.services.summarization_service import ResultSummarizationService
summary_service = ResultSummarizationService()
# Uses SUMMARY_MODEL_NAME env var or default: google/flan-t5-base
```

## Model Characteristics

### yasserrmd/Text2SQL-1.5B
- **Architecture**: Causal Language Model
- **Size**: 1.5B parameters
- **Specialization**: Text-to-SQL conversion
- **Input**: Natural language question + database schema
- **Output**: SQL query

### google/flan-t5-base
- **Architecture**: Seq2Seq (Encoder-Decoder)
- **Size**: Base model (~250M parameters)
- **Specialization**: Instruction following, summarization
- **Input**: Query results + question
- **Output**: Natural language summary

## Model Loading

Both models are loaded lazily and cached:
- First use: Model downloads and loads into memory
- Subsequent uses: Model loaded from cache (faster)
- Memory: Models stay in memory for the session

## Device Configuration

Models automatically use:
- **GPU** (CUDA) if available
- **CPU** if no GPU available

You can override device:
```python
service = EnhancedText2SQLService(device="cpu")  # Force CPU
```

## Notes

- Both models are loaded separately and can run simultaneously
- Model caching prevents reloading the same model multiple times
- The ModelHandler automatically detects and handles different model architectures
- FLAN-T5 uses optimized prompts for better summarization results

