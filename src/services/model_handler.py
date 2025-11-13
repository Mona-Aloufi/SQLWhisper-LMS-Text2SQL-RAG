# src/services/model_handler.py
import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
from dotenv import load_dotenv

load_dotenv()

class ModelHandler:
    def __init__(self, model_name=None, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name or os.getenv("MODEL_NAME", "yasserrmd/Text2SQL-1.5B")
        self.hf_token = os.getenv("HF_TOKEN")
        self.logger = logging.getLogger(__name__)
        
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the primary model with fallback."""
        try:
            self.logger.info(f"Loading model: {self.model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=self.hf_token,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
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
            self.logger.info("Loading fallback model: google/flan-t5-base")
            self.model_name = "google/flan-t5-base"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            self.logger.info("✅ Fallback model loaded successfully")
        except Exception as e:
            self.logger.error(f"Fallback model failed: {e}")
            raise e
    
    def generate_with_confidence(self, prompt: str, max_new_tokens: int = 256):
        """Generate text with confidence scoring."""
        try:
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=1024, 
                truncation=True
            ).to(self.device)
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_return_sequences=1,
                temperature=0.1,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                early_stopping=True,
                output_scores=True,
                return_dict_in_generate=True
            )
            
            # Calculate token-level confidence
            confidences = []
            if hasattr(outputs, 'scores') and outputs.scores:
                for score in outputs.scores:
                    conf = torch.softmax(score, dim=-1).max().item()
                    confidences.append(conf)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Decode the generated text
            generated_text = self.tokenizer.decode(
                outputs.sequences[0], 
                skip_special_tokens=True
            )
            
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
            'model_type': type(self.model).__name__
        }