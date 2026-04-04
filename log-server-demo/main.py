import logging
import time
import json
import random
import threading
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

# Configure logging with live updates
LOG_FILE = "app.log"

# Create a custom logger
logger = logging.getLogger("zerch-server")
logger.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create file handler with unbuffered writing
file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

app = FastAPI(title="Heavy Log Generator Server", version="1.0.0")

# Global variables
request_counter = 0
error_counter = 0


def generate_heavy_logs():
    """Generate heavy amount of logs in background"""
    operations = [
        "Database query executed",
        "Cache hit for key",
        "External API call made",
        "File processed",
        "Authentication verified",
        "Data validation passed",
        "Processing chunk",
        "Computing hash",
        "Compressing data",
        "Encrypting payload"
    ]
    
    while True:
        try:
            # Generate random number of logs per cycle
            num_logs = random.randint(5, 15)
            
            for _ in range(num_logs):
                operation = random.choice(operations)
                log_level = random.choice([
                    ("DEBUG", logger.debug),
                    ("INFO", logger.info),
                    ("WARNING", logger.warning),
                ])
                
                request_id = f"REQ-{random.randint(1000, 9999)}"
                duration_ms = random.randint(10, 500)
                user_id = f"USER-{random.randint(100, 999)}"
                
                message = f"{operation} | RequestID={request_id} | UserID={user_id} | Duration={duration_ms}ms"
                
                log_level[1](message)
                time.sleep(random.uniform(0.01, 0.1))  # Small delay between logs
            
            # Periodic status update
            logger.info("=" * 80)
            logger.info(f"Cycle completed. Total requests: {request_counter}, Errors: {error_counter}")
            logger.info("=" * 80)
            
            time.sleep(random.uniform(1, 3))  # Wait between log cycles
            
        except Exception as e:
            logger.error(f"Error in log generation: {str(e)}", exc_info=True)
            time.sleep(1)


@app.on_event("startup")
async def startup_event():
    """Start background log generation on server startup"""
    logger.info("🚀 Server starting up...")
    logger.info(f"Log file location: {LOG_FILE}")
    logger.info("Initializing heavy log generator...")
    
    # Start background log generation
    log_thread = threading.Thread(target=generate_heavy_logs, daemon=True)
    log_thread.start()
    logger.info("✅ Background log generator started")


@app.get("/")
async def root():
    """Root endpoint"""
    global request_counter
    request_counter += 1
    logger.info(f"GET / - Request #{request_counter}")
    return {
        "status": "online",
        "message": "Heavy Log Generator Server",
        "timestamp": datetime.now().isoformat(),
        "total_requests": request_counter
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "requests_served": request_counter,
        "errors": error_counter
    }


@app.get("/logs/stream")
async def stream_logs():
    """Stream live logs from the log file"""
    logger.info("Client connected to log stream")
    
    def log_generator():
        try:
            # Start reading from end of file
            with open(LOG_FILE, 'r') as f:
                # Go to end of file
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        yield f"data: {line}\n\n"
                        time.sleep(0.01)
                    else:
                        time.sleep(0.1)  # Wait for new logs
        except Exception as e:
            logger.error(f"Error streaming logs: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get("/logs")
async def get_logs(lines: int = 100):
    """Get last N lines from log file"""
    global error_counter
    logger.info(f"Requested last {lines} log lines")
    
    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            recent_logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {
                "status": "success",
                "total_lines": len(all_lines),
                "returned_lines": len(recent_logs),
                "logs": recent_logs,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        error_counter += 1
        logger.error(f"Error reading logs: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/logs/tail")
async def tail_logs(lines: int = 50):
    """Get tail of log file (last N lines as plain text)"""
    global error_counter
    logger.info(f"Tail requested for {lines} lines")
    
    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return {
            "status": "success",
            "content": "".join(tail),
            "lines_count": len(tail)
        }
    except Exception as e:
        error_counter += 1
        logger.error(f"Error getting tail: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    global error_counter
    try:
        with open(LOG_FILE, 'r') as f:
            total_log_lines = len(f.readlines())
        
        file_size = __import__('os').path.getsize(LOG_FILE)
        
        logger.info("Stats requested")
        return {
            "status": "success",
            "total_requests": request_counter,
            "total_errors": error_counter,
            "log_file": LOG_FILE,
            "log_file_size_bytes": file_size,
            "log_file_size_mb": round(file_size / (1024 * 1024), 2),
            "total_log_lines": total_log_lines,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_counter += 1
        logger.error(f"Error getting stats: {str(e)}")
        return {"status": "error", "message": str(e)}


@app.get("/simulate-error")
async def simulate_error(message: str = "Simulated error"):
    """Simulate an error for testing"""
    global error_counter
    error_counter += 1
    logger.error(f"Simulated error: {message}")
    logger.exception("Traceback for error simulation")
    return {
        "status": "error_simulated",
        "message": message,
        "error_count": error_counter
    }


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🎯 Heavy Log Generator Server - Initializing")
    logger.info("=" * 80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Disable uvicorn default logging to use ours
    )
