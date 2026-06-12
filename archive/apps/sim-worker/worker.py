"""
AvaSim Simulation Worker - Python batch orchestration and analytics

Consumes jobs from Redis queue and processes batch simulation requests.
"""

import os
import time
import json
import redis
from typing import Dict, Any


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
QUEUE_NAME = "avasim:jobs"


def process_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a simulation job (stub implementation)."""
    print(f"📋 Processing job: {job_data.get('job_id', 'unknown')}")

    # Stub: simulate work
    time.sleep(0.5)

    result = {
        "job_id": job_data.get("job_id"),
        "status": "completed",
        "message": "Job processed (stub implementation - Phase 3+)",
        "processed_at": time.time(),
    }

    print(f"✅ Job completed: {result['job_id']}")
    return result


def main():
    """Main worker loop - consume jobs from Redis queue."""
    print("🚀 AvaSim Simulation Worker starting...")
    print(f"   Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"   Queue: {QUEUE_NAME}")

    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return

    print("👂 Listening for jobs...")

    while True:
        try:
            # Blocking pop from queue (5 second timeout)
            result = r.brpop(QUEUE_NAME, timeout=5)

            if result:
                queue_name, job_json = result
                job_data = json.loads(job_json)

                # Process the job
                job_result = process_job(job_data)

                # Store result (stub: just log it)
                result_key = f"avasim:result:{job_result['job_id']}"
                r.setex(result_key, 3600, json.dumps(job_result))

        except KeyboardInterrupt:
            print("\n👋 Worker shutting down...")
            break
        except Exception as e:
            print(f"⚠️  Error processing job: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
