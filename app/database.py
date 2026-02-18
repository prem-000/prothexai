from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging
import dns.resolver

# Patch for Windows DNS resolution issues with SRV records
try:
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4', '1.1.1.1']
except Exception as e:
    logging.warning(f"Failed to patch DNS resolver: {e}")

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    db_instance.client = AsyncIOMotorClient(settings.MONGO_URI)
    db_instance.db = db_instance.client.get_database("prothex")
    logger.info("Connected to MongoDB.")
    
    # Create indexes for the new identity system
    await db_instance.db.patient_profiles.create_index("user_id", unique=True)
    await db_instance.db.daily_metrics.create_index("patient_id")
    
    # Feedback Indexes
    await db_instance.db.patient_feedback.create_index("patient_id")
    await db_instance.db.patient_feedback.create_index("status")
    
    # Analysis & Report Indexes
    await db_instance.db.analysis_results.create_index("user_id")
    await db_instance.db.analysis_results.create_index("record_id")
    await db_instance.db.analysis_results.create_index("created_at")
    await db_instance.db.weekly_reports.create_index("patient_id")
    await db_instance.db.weekly_reports.create_index("created_at")
    
    logger.info("MongoDB indexes created/verified.")

async def close_mongo_connection():
    db_instance.client.close()
    logger.info("MongoDB connection closed.")

def get_db():
    return db_instance.db
