import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm_with_fallbacks(structured_output_schema=None, temperature=0.7):
    """
    Returns an LLM instance (as a LangChain Runnable) with automatic 
    fallback to secondary models if the primary model fails.
    """
    primary_model = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    fallback_model = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")
    
    # Ensure the primary and fallback are different
    models_to_try = [primary_model]
    if fallback_model and fallback_model != primary_model:
        models_to_try.append(fallback_model)

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
