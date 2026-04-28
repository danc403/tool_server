import os
import json
import importlib.util
import sys
import asyncio
import time
import inspect
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- Constants (Fixed for Docker Environment) ---
TOOLS_DIRECTORY = "/app/tools"
LOGGING_LEVEL = logging.INFO

# --- Logging Setup ---
logging.basicConfig(level=LOGGING_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to store validated tool names found at startup
validated_tool_names = []

# --- Lifespan Context for Initial Tool Discovery ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global validated_tool_names

    logger.info("IDG Tool Server starting. Scanning /app/tools...")

    if not os.path.exists(TOOLS_DIRECTORY):
        logger.error(f"Tools directory not found: {TOOLS_DIRECTORY}")
        raise RuntimeError(f"Critical Error: {TOOLS_DIRECTORY} missing.")

    discovered_tools = []
    for filename in os.listdir(TOOLS_DIRECTORY):
        if filename.endswith(".py") and filename != "__init__.py":
            tool_name = filename[:-3]
            tool_path = os.path.join(TOOLS_DIRECTORY, filename)

            try:
                # Basic validation: Check if file contains an async function with the same name
                spec = importlib.util.spec_from_file_location(f"init_{tool_name}", tool_path)
                if spec is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                tool_function = getattr(module, tool_name, None)

                if tool_function and asyncio.iscoroutinefunction(tool_function):
                    discovered_tools.append(tool_name)
                    logger.info(f"Discovered Tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to validate {filename}: {e}")

    validated_tool_names = sorted(list(set(discovered_tools)))
    logger.info(f"Startup complete. {len(validated_tool_names)} tools active.")
    yield
    logger.info("Shutting down.")

app = FastAPI(lifespan=lifespan, title="IDG Tool Server", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

async def load_tool_function(tool_name: str):
    """Loads a specific tool dynamically without persistent caching."""
    tool_path = os.path.join(TOOLS_DIRECTORY, f"{tool_name}.py")
    try:
        spec = importlib.util.spec_from_file_location(f"run_{tool_name}_{time.time()}", tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, tool_name, None)
    except Exception as e:
        logger.error(f"Error loading {tool_name}: {e}")
        return None

@app.get("/status")
async def status():
    return JSONResponse(content={"status": "Server Online", "tools_loaded": len(validated_tool_names)})

@app.get("/")
async def list_available():
    """Generates OpenAI-compatible function definitions for all tools."""
    detailed_tools = []
    for tool_name in validated_tool_names:
        tool_func = await load_tool_function(tool_name)
        if not tool_func: continue

        doc = inspect.getdoc(tool_func) or f"Execute {tool_name}"
        params = {"type": "object", "properties": {}, "required": []}
        sig = inspect.signature(tool_func)

        for p_name, p in sig.parameters.items():
            if p.kind in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD]:
                continue
            
            p_type = "string"
            if p.annotation is int: p_type = "integer"
            elif p.annotation is float: p_type = "number"
            elif p.annotation is bool: p_type = "boolean"
            
            params["properties"][p_name] = {"type": p_type}
            if p.default is inspect.Parameter.empty:
                params["required"].append(p_name)

        detailed_tools.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": doc.strip(),
                "parameters": params
            }
        })
    return JSONResponse(content={"available_tools": detailed_tools})

@app.post("/tool/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """Executes a tool and returns strict JSON results."""
    if tool_name not in validated_tool_names:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool_func = await load_tool_function(tool_name)
    if not tool_func:
        raise HTTPException(status_code=500, detail="Failed to load tool")

    try:
        body = await request.body()
        args = json.loads(body) if body else {}
        logger.info(f"Running {tool_name} with {args}")
        
        result = await tool_func(**args)
        return JSONResponse(content={"tool": tool_name, "result": result})
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
