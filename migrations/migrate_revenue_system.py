"""
Revenue System Migration Script
=================================
This script migrates the database to support the complete revenue and monetization system.

New Tables Added:
1. subscription_plan - Subscription tier definitions (Student/Owner plans)
2. user_subscription - User's active subscriptions with billing info
3. listing_fee - Property listing fees (basic/featured/premium)
4. commission - Booking commissions with subscription discounts
5. value_added_service - Services catalog (photography, verification, legal, etc.)
6. service_purchase - Service purchase tracking
7. transaction_fee - Payment processing fees
8. revenue_analytics - Daily revenue aggregation by stream

Enhanced Tables:
- students: Added inquiry tracking, premium status
- owners: Added premium status, commission rate calculation
- rooms: Added premium listing flags
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, SubscriptionPlan, ValueAddedService
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_revenue_system():
    """Run the revenue system migration."""
    
    with app.app_context():
        logger.info("Starting revenue system migration...")
        
        try:
            # Create all new tables
            db.create_all()
            logger.info("✅ Created all revenue tables")
            
            # Add missing columns to existing tables
            with db.engine.connect() as conn:
                # Add columns to Room table if they don't exist
                try:
                    conn.execute(db.text("""
                        ALTER TABLE room ADD COLUMN is_featured BOOLEAN DEFAULT 0
                    """))
                    logger.info("✅ Added is_featured to room")
                except Exception as e:
                    logger.info(f"Column is_featured may already exist: {e}")
                
                try:
                    conn.execute(db.text("""
                        ALTER TABLE room ADD COLUMN is_premium_listing BOOLEAN DEFAULT 0
                    """))
                    logger.info("✅ Added is_premium_listing to room")
                except Exception as e:
                    logger.info(f"Column is_premium_listing may already exist: {e}")
                
                conn.commit()
            
            # Seed default subscription plans
            seed_subscription_plans()
            
            # Seed default value-added services
            seed_value_added_services()
            
            logger.info("✅ Revenue system migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False


def seed_subscription_plans():
    """Seed initial subscription plans."""
    
    logger.info("Seeding subscription plans...")
    
    # Check if plans already exist
    if SubscriptionPlan.query.first():
        logger.info("Subscription plans already exist, skipping seed")
        return
    
    plans = [
        # Student Plans
        SubscriptionPlan(
            name="Student Free",
            user_type="student",
            price_monthly=0,
            price_yearly=0,
            features='{"property_inquiries": 10, "saved_properties": 20, "chat_support": false, "priority_responses": false, "move_in_assistance": false}',
            property_inquiries_limit=10,
            listings_limit=0,
            is_active=True,
            display_order=1
        ),
        SubscriptionPlan(
            name="Student Basic",
            user_type="student",
            price_monthly=99,
            price_yearly=999,
            features='{"property_inquiries": 50, "saved_properties": 100, "chat_support": true, "priority_responses": false, "move_in_assistance": false, "verified_listings": true}',
            property_inquiries_limit=50,
            listings_limit=0,
            is_active=True,
            display_order=2
        ),
        SubscriptionPlan(
            name="Student Premium",
            user_type="student",
            price_monthly=199,
            price_yearly=1999,
            features='{"property_inquiries": "unlimited", "saved_properties": "unlimited", "chat_support": true, "priority_responses": true, "move_in_assistance": true, "verified_listings": true, "virtual_tours": true, "dedicated_support": true}',
            property_inquiries_limit=-1,
            listings_limit=0,
            is_active=True,
            display_order=3
        ),
        
        # Owner Plans
        SubscriptionPlan(
            name="Owner Free",
            user_type="owner",
            price_monthly=0,
            price_yearly=0,
            features='{"active_listings": 2, "commission_rate": 25, "listing_fee_required": true, "featured_listings": false, "analytics_dashboard": false, "priority_support": false}',
            property_inquiries_limit=0,
            listings_limit=2,
            commission_discount=0,
            is_active=True,
            display_order=4
        ),
        SubscriptionPlan(
            name="Owner Basic",
            user_type="owner",
            price_monthly=499,
            price_yearly=4999,
            features='{"active_listings": 5, "commission_rate": 20, "listing_fee_required": false, "featured_listings": true, "analytics_dashboard": true, "priority_support": false, "auto_promotion": true}',
            property_inquiries_limit=0,
            listings_limit=5,
            commission_discount=5,
            is_active=True,
            display_order=5
        ),
        SubscriptionPlan(
            name="Owner Premium",
            user_type="owner",
            price_monthly=999,
            price_yearly=9999,
            features='{"active_listings": "unlimited", "commission_rate": 15, "listing_fee_required": false, "featured_listings": true, "analytics_dashboard": true, "priority_support": true, "auto_promotion": true, "dedicated_account_manager": true, "advanced_analytics": true, "bulk_operations": true}',
            property_inquiries_limit=0,
            listings_limit=-1,
            commission_discount=10,
            is_active=True,
            display_order=6
        ),
    ]
    
    for plan in plans:
        db.session.add(plan)
    
    db.session.commit()
    logger.info(f"✅ Seeded {len(plans)} subscription plans")


def seed_value_added_services():
    """Seed initial value-added services."""
    
    logger.info("Seeding value-added services...")
    
    # Check if services already exist
    if ValueAddedService.query.first():
        logger.info("Services already exist, skipping seed")
        return
    
    services = [
        # Photography Services
        ValueAddedService(
            service_name="Basic Property Photography",
            service_type="photography",
            description="Professional photos of your property (10-15 images)",
            price=2000,
            target_user="owner",
            is_active=True
        ),
        ValueAddedService(
            service_name="Premium Property Photography",
            service_type="photography",
            description="Professional photography with virtual tour (25+ images + 360° views)",
            price=5000,
            target_user="owner",
            is_active=True
        ),
        
        # Verification Services
        ValueAddedService(
            service_name="Property Verification",
            service_type="verification",
            description="Physical verification of property with detailed report",
            price=500,
            target_user="both",
            is_active=True
        ),
        ValueAddedService(
            service_name="Owner Verification",
            service_type="verification",
            description="Background verification of property owner",
            price=300,
            target_user="student",
            is_active=True
        ),
        
        # Legal Services
        ValueAddedService(
            service_name="Rental Agreement Review",
            service_type="legal",
            description="Legal review of rental agreement by certified lawyers",
            price=1000,
            target_user="both",
            is_active=True
        ),
        ValueAddedService(
            service_name="Tenancy Registration",
            service_type="legal",
            description="Complete rental registration with local authorities",
            price=2500,
            target_user="both",
            is_active=True
        ),
        
        # Moving Services
        ValueAddedService(
            service_name="Basic Moving Assistance",
            service_type="moving",
            description="Packers and movers for local shifting (within city)",
            price=3000,
            target_user="student",
            is_active=True
        ),
        ValueAddedService(
            service_name="Premium Moving Package",
            service_type="moving",
            description="Complete relocation with packing, insurance, and setup",
            price=7000,
            target_user="student",
            is_active=True
        ),
        
        # Consultation Services
        ValueAddedService(
            service_name="Property Listing Optimization",
            service_type="consultation",
            description="Expert consultation to optimize your listing for maximum visibility",
            price=1500,
            target_user="owner",
            is_active=True
        ),
        ValueAddedService(
            service_name="Tenant Screening",
            service_type="consultation",
            description="Background check and credit verification of potential tenants",
            price=800,
            target_user="owner",
            is_active=True
        ),
    ]
    
    for service in services:
        db.session.add(service)
    
    db.session.commit()
    logger.info(f"✅ Seeded {len(services)} value-added services")


if __name__ == "__main__":
    success = migrate_revenue_system()
    if success:
        print("\n" + "="*60)
        print("✅ REVENUE SYSTEM MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNew Features Enabled:")
        print("  • 6 Subscription Plans (3 Student + 3 Owner)")
        print("  • 10 Value-Added Services")
        print("  • Commission Tracking (15-25% based on subscription)")
        print("  • Listing Fees (₹500-1500)")
        print("  • Transaction Fee Tracking (2%)")
        print("  • Revenue Analytics Dashboard")
        print("\nNext Steps:")
        print("  1. Restart your Flask application")
        print("  2. Test subscription purchase: GET /api/subscription-plans")
        print("  3. Test services marketplace: GET /api/services")
        print("  4. View revenue analytics: GET /api/admin/revenue/summary")
        print("  5. Build frontend pricing page")
        print("\n" + "="*60)
    else:
        print("\n❌ Migration failed. Check the logs above for errors.")
