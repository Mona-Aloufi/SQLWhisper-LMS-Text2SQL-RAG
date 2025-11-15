# src/services/model_handler.py
import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
from dotenv import load_dotenv

load_dotenv()

class ModelHandler:
    _model_cache = {}  # ✅ Cache models by name

    def __init__(self, model_name=None, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name or os.getenv("MODEL_NAME", "yasserrmd/Text2SQL-1.5B")
        self.hf_token = os.getenv("HF_TOKEN")
        self.logger = logging.getLogger(__name__)

        self.tokenizer = None
        self.model = None

        self._load_model_with_cache()

    def _load_model_with_cache(self):
        """Load model from cache if available."""
        if self.model_name in ModelHandler._model_cache:
            self.logger.info(f"✅ Using cached model: {self.model_name}")
            cache_entry = ModelHandler._model_cache[self.model_name]
            self.tokenizer = cache_entry['tokenizer']
            self.model = cache_entry['model']
            return

        self.logger.info(f"🚀 Loading model into cache: {self.model_name}")
        self._load_model()

        # Store in cache
        ModelHandler._model_cache[self.model_name] = {
            'tokenizer': self.tokenizer,
            'model': self.model
        }
        self.logger.info(f"✅ Model cached successfully: {self.model_name}")

    def _load_model(self):
        """Load the primary model with fallback.
        Automatically detects if model is CausalLM or Seq2SeqLM.
        """
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )

            # Check if this is a Seq2Seq model (like FLAN-T5)
            # Common Seq2Seq model names/patterns
            seq2seq_models = [
                'flan-t5', 't5', 'bart', 'pegasus', 'mT5', 'ul2'
            ]
            is_seq2seq = any(pattern.lower() in self.model_name.lower() for pattern in seq2seq_models)
            
            if is_seq2seq:
                self.logger.info(f"Detected Seq2Seq model: {self.model_name}")
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    token=self.hf_token,
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                ).to(self.device)
            else:
                # Try CausalLM first (for most text generation models)
                try:
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        token=self.hf_token,
                        trust_remote_code=True,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                    ).to(self.device)
                except Exception as causal_error:
                    # If CausalLM fails, try Seq2SeqLM
                    self.logger.info(f"CausalLM failed, trying Seq2SeqLM: {causal_error}")
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(
                        self.model_name,
                        token=self.hf_token,
                        trust_remote_code=True,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                    ).to(self.device)

            self.logger.info("✅ Model loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load primary model: {e}")
            self._load_fallback_model()

    def _load_fallback_model(self):
        """Load fallback model if primary fails."""
        try:
            self.logger.info("⚙️ Loading fallback model: google/flan-t5-base")
            self.model_name = "google/flan-t5-base"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            self.logger.info("✅ Fallback model loaded successfully")
        except Exception as e:
            self.logger.error(f"Fallback model failed: {e}")
            raise e

    def generate_with_confidence(self, prompt: str, max_new_tokens: int = 256):
        """Generate text with confidence scoring.
        Works with both CausalLM and Seq2SeqLM models.
        """
        try:
            # Set pad_token if not already set (important for Seq2Seq models)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=1024,
                truncation=True,
                padding=True
            ).to(self.device)

            # Generation parameters - adjusted for both model types
            generation_kwargs = {
                "max_new_tokens": max_new_tokens,
                "num_return_sequences": 1,
                "do_sample": False,
            }
            
            # Set pad_token_id and eos_token_id
            if self.tokenizer.pad_token_id is not None:
                generation_kwargs["pad_token_id"] = self.tokenizer.pad_token_id
            if self.tokenizer.eos_token_id is not None:
                generation_kwargs["eos_token_id"] = self.tokenizer.eos_token_id
            
            # For CausalLM models, try to get confidence scores
            # Seq2Seq models typically don't support output_scores
            is_seq2seq = isinstance(self.model, AutoModelForSeq2SeqLM)
            if not is_seq2seq:
                try:
                    generation_kwargs["output_scores"] = True
                    generation_kwargs["return_dict_in_generate"] = True
                except:
                    pass

            outputs = self.model.generate(**inputs, **generation_kwargs)

            confidences = []
            sequences = None
            
            # Extract sequences and scores based on model type and output format
            if isinstance(outputs, dict):
                # Output is a dictionary (from return_dict_in_generate=True)
                if 'sequences' in outputs:
                    sequences = outputs['sequences']
                    if hasattr(outputs, 'scores') and outputs.scores:
                        for score in outputs.scores:
                            if isinstance(score, torch.Tensor):
                                conf = torch.softmax(score, dim=-1).max().item()
                                confidences.append(conf)
            elif isinstance(outputs, torch.Tensor):
                # Output is directly a tensor (common for Seq2Seq)
                sequences = outputs
            elif isinstance(outputs, (list, tuple)):
                # Output is a list/tuple of tensors
                sequences = outputs[0] if len(outputs) > 0 else outputs
            else:
                # Fallback: try to get sequences attribute
                sequences = getattr(outputs, 'sequences', outputs)

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            # Decode the generated text
            # Handle different sequence formats
            if isinstance(sequences, torch.Tensor):
                sequence_to_decode = sequences
            elif isinstance(sequences, (list, tuple)) and len(sequences) > 0:
                sequence_to_decode = sequences[0] if isinstance(sequences[0], torch.Tensor) else sequences
            else:
                sequence_to_decode = sequences
            
            # For Seq2Seq models, the output is already just the generated tokens
            # For CausalLM, we need to extract only the new tokens (not the input)
            if isinstance(self.model, AutoModelForSeq2SeqLM):
                # Seq2Seq models return only the generated sequence (no input included)
                if isinstance(sequence_to_decode, torch.Tensor):
                    # Handle 2D tensors (batch_size, seq_len) - take first sequence
                    if len(sequence_to_decode.shape) == 2:
                        sequence_to_decode = sequence_to_decode[0]
                    # Convert to list for decoding if needed
                    if isinstance(sequence_to_decode, torch.Tensor):
                        generated_text = self.tokenizer.decode(
                            sequence_to_decode.cpu().tolist() if hasattr(sequence_to_decode, 'cpu') else sequence_to_decode,
                            skip_special_tokens=True
                        )
                    else:
                        generated_text = self.tokenizer.decode(
                            sequence_to_decode,
                            skip_special_tokens=True
                        )
                else:
                    # Fallback for unexpected format
                    generated_text = str(sequence_to_decode)
            else:
                # CausalLM models return input + generated, so extract only new tokens
                input_length = inputs['input_ids'].shape[1]
                if isinstance(sequence_to_decode, torch.Tensor):
                    # Handle 2D tensors (batch_size, seq_len) - take first sequence
                    if len(sequence_to_decode.shape) == 2:
                        sequence_to_decode = sequence_to_decode[0]
                    
                    if sequence_to_decode.shape[0] > input_length:
                        # Extract only the generated part
                        generated_ids = sequence_to_decode[input_length:]
                        # Convert to list for decoding
                        generated_text = self.tokenizer.decode(
                            generated_ids.cpu().tolist() if hasattr(generated_ids, 'cpu') else generated_ids,
                            skip_special_tokens=True
                        )
                    else:
                        # Decode everything
                        generated_text = self.tokenizer.decode(
                            sequence_to_decode.cpu().tolist() if hasattr(sequence_to_decode, 'cpu') else sequence_to_decode,
                            skip_special_tokens=True
                        )
                else:
                    # Fallback
                    generated_text = str(sequence_to_decode)

            return {
                'generated_text': generated_text,
                'confidence': avg_confidence,
                'confidences': confidences,
                'tokens_generated': len(outputs.sequences[0]) - inputs['input_ids'].shape[1]
            }

        except Exception as e:
            self.logger.error(f"Generation error: {e}")
            return {
                'generated_text': "",
                'confidence': 0.0,
                'confidences': [],
                'error': str(e)
            }

    def get_model_info(self):
        """Get model information."""
        return {
            'model_name': self.model_name,
            'device': str(self.device),
            'tokenizer_type': type(self.tokenizer).__name__,
            'model_type': type(self.model).__name__,
            'cached_models': list(ModelHandler._model_cache.keys())
        }
