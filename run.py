import uvicorn
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from backend.config import settings

def main():
    banner = f"""
========================================================================
   ____                              ___             
  / __ \ ___   ___  ____ _ ____ _   /   \ ____   ___ 
 / /_/ // _ \ (_-< / __ `// __ `/  / /| // __ \ (_-< 
/ _, _//  __//___/ \__, / \__, /  / ___// /_/ //___/ 
/_/ |_| \___/     /____/ /____/  /_/    \____/       
                                                     
   SRE Incident Response & Institutional Post-Mortem Copilot
   Powered by Hindsight Memory (Vectorize.io)
========================================================================
* Web UI running at : http://localhost:{settings.PORT}
* Hindsight Engine  : {"Cloud (Vectorize)" if settings.HINDSIGHT_API_KEY else "Local Persistent Bank (Ready)"}
* LLM Provider      : {"Groq (" + settings.GROQ_MODEL + ")" if settings.GROQ_API_KEY else ("Gemini" if settings.GEMINI_API_KEY else "Intelligent SRE Offline Engine")}
* Free Credits Tip  : Use promo code MEMHACK99 on ui.hindsight.vectorize.io
========================================================================
    """
    print(banner)
    uvicorn.run("backend.app:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

if __name__ == "__main__":
    main()
