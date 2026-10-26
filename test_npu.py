# Save as C:\Users\whydi\test_npu.py
import openvino_genai as ov_genai

print("Loading model onto NPU (first run takes 1-3 mins to compile)...")
pipe = ov_genai.LLMPipeline(
    "./llama_8b_npu", 
    "NPU", 
    CACHE_DIR="./npu_cache"
)

config = ov_genai.GenerationConfig()
config.max_new_tokens = 256
config.temperature = 0.2

prompt = "Write a fast Python function to compute a rolling VWAP using NumPy."
print("\n--- Generating Response ---\n")
print(pipe.generate(prompt, config))