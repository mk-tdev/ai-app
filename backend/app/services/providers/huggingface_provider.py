"""HuggingFace provider implementation."""
import logging
from typing import AsyncGenerator, Optional

from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

from app.config import get_settings

logger = logging.getLogger(__name__)


class HuggingFaceProvider:
    """LLM provider using HuggingFace transformers for local inference."""
    
    def __init__(self):
        """Initialize the HuggingFace provider."""
        self._llm: Optional[HuggingFacePipeline] = None
        self._tokenizer = None
        self._model = None
        self._pipeline = None
        self._model_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded
    
    def load_model(self) -> bool:
        """Load the HuggingFace model."""
        settings = get_settings()
        
        try:
            logger.info(f"Loading HuggingFace model: {settings.hf_model_name}...")
            
            # Determine device
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"
            logger.info(f"Using device: {device_name}")
            
            # Load tokenizer and model
            logger.info("Loading tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                settings.hf_model_name,
                token=settings.hf_api_token if settings.hf_api_token else None,
            )
            
            logger.info("Loading model...")
            self._model = AutoModelForCausalLM.from_pretrained(
                settings.hf_model_name,
                token=settings.hf_api_token if settings.hf_api_token else None,
                torch_dtype=torch.float16 if device == 0 else torch.float32,
                device_map="auto" if device == 0 else None,
            )
            
            # Create pipeline
            logger.info("Creating text generation pipeline...")
            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                max_new_tokens=settings.max_tokens,
                temperature=settings.temperature,
                device=device,
            )
            
            # Create LangChain wrapper
            self._llm = HuggingFacePipeline(pipeline=self._pipeline)
            
            self._model_loaded = True
            logger.info("HuggingFace model loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {e}")
            logger.error("Make sure you have enough memory and the model name is correct")
            return False
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response from the LLM."""
        if not self._pipeline or not self._model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        settings = get_settings()
        max_tokens = max_tokens or settings.max_tokens
        
        try:
            # Generate with pipeline
            outputs = self._pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=settings.temperature,
                do_sample=True,
                top_p=0.95,
            )
            
            # Extract generated text
            generated_text = outputs[0]["generated_text"]
            
            # Remove the prompt from the output if present
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise RuntimeError(f"Generation failed: {e}")
    
    async def generate_stream(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        if not self._model or not self._tokenizer or not self._model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        settings = get_settings()
        max_tokens = max_tokens or settings.max_tokens
        
        try:
            # Tokenize input
            inputs = self._tokenizer(prompt, return_tensors="pt")
            
            # Move to same device as model
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate tokens one at a time
            device = next(self._model.parameters()).device
            input_ids = inputs["input_ids"].to(device)
            attention_mask = inputs.get("attention_mask", torch.ones_like(input_ids)).to(device)
            
            generated_ids = input_ids
            prompt_length = input_ids.shape[1]
            
            for _ in range(max_tokens):
                # Generate next token
                with torch.no_grad():
                    outputs = self._model(
                        input_ids=generated_ids,
                        attention_mask=attention_mask,
                    )
                    next_token_logits = outputs.logits[:, -1, :]
                    
                    # Apply temperature
                    next_token_logits = next_token_logits / settings.temperature
                    
                    # Sample next token
                    probs = torch.softmax(next_token_logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                    
                    # Decode and yield
                    token_text = self._tokenizer.decode(next_token[0], skip_special_tokens=True)
                    if token_text:
                        yield token_text
                    
                    # Append to generated sequence
                    generated_ids = torch.cat([generated_ids, next_token], dim=-1)
                    attention_mask = torch.cat([
                        attention_mask,
                        torch.ones((1, 1), device=device)
                    ], dim=-1)
                    
                    # Check for end of sequence
                    if next_token.item() == self._tokenizer.eos_token_id:
                        break
                        
        except Exception as e:
            logger.error(f"HuggingFace streaming failed: {e}")
            raise RuntimeError(f"Streaming failed: {e}")
    
    def get_langchain_llm(self) -> HuggingFacePipeline:
        """Get LangChain LLM wrapper for chain integration."""
        if not self._llm or not self._model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        return self._llm
