"""
Hybrid queue system: Redis for enqueueing -> RabbitMQ for processing.

This system provides:
- Fast Redis-based enqueueing for immediate response
- Reliable RabbitMQ processing with persistence and acknowledgments
- Automatic forwarding from Redis to RabbitMQ
- Monitoring and health checks for both systems

Requirements covered: 5.1, 5.3, 5.5
"""

import json
import uuid
import time
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetim