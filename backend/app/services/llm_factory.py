import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm_with_fallbacks(structured_output_schema=None, temperature=0.7):
    """
    Returns an LLM instance (as a LangChain Runnable) with automatic 
    fallback to secondary models if the primary model fails.
    """
    primary_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    # List of reliable fallback models
    fallback_candidates = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
    
    # Ensure the primary model is at the front and fallbacks are unique
    models_to_try = [primary_model]
    for m in fallback_candidates:
        if m not in models_to_try:
            models_to_try.append(m)

    def create_runnable(model_name):
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        if structured_output_schema:
            return llm.with_structured_output(structured_output_schema)
        return llm

    # Create the sequence of runnables
    runnables = [create_runnable(m) for m in models_to_try]
    
    # The first one is the main, the rest are fallbacks
    main_runnable = runnables[0]
    fallbacks = runnables[1:]
    
    if fallbacks:
        return main_runnable.with_fallbacks(fallbacks)
    return main_runnable
