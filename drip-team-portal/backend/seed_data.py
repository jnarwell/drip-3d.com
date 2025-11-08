import asyncio
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models import Base, Component, Test, TestResult, User
from app.models.component import ComponentStatus, ComponentCategory
from app.models.test import TestStatus, TestResultStatus
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with test data"""
    db = SessionLocal()
    
    try:
        # Create test users
        users = []
        for name, email in [
            ("Alex Chen", "alex@drip-3d.com"),
            ("Jordan Taylor", "jordan@drip-3d.com"),
            ("Sam Rodriguez", "sam@drip-3d.com"),
            ("Test User", "test@drip-3d.com")
        ]:
            user = User(
                email=email,
                name=name,
                auth0_id=f"dev|{email.split('@')[0]}",
                created_at=datetime.utcnow()
            )
            db.add(user)
            users.append(user)
        
        db.commit()
        
        # Create components
        components = []
        component_data = [
            ("Acoustic Transducer v2.1", ComponentCategory.ACOUSTIC, ComponentStatus.VERIFIED),
            ("Temperature Control Module", ComponentCategory.THERMAL, ComponentStatus.IN_TESTING),
            ("Pressure Sensor Module", ComponentCategory.MECHANICAL, ComponentStatus.VERIFIED),
            ("Power Control Board", ComponentCategory.ELECTRICAL, ComponentStatus.NOT_TESTED),
            ("Material Feed System", ComponentCategory.MATERIAL, ComponentStatus.IN_TESTING),
            ("Cooling System", ComponentCategory.THERMAL, ComponentStatus.VERIFIED),
            ("High Voltage PSU", ComponentCategory.ELECTRICAL, ComponentStatus.FAILED),
            ("Acoustic Dampener", ComponentCategory.ACOUSTIC, ComponentStatus.VERIFIED),
        ]
        
        for i, (name, category, status) in enumerate(component_data):
            component = Component(
                component_id=f"CMP-{i+1:03d}",
                name=name,
                part_number=f"DRP-{category.value[:3].upper()}-{random.randint(1000, 9999)}",
                category=category,
                status=status,
                unit_cost=random.uniform(50, 5000),
                quantity=random.randint(1, 5),
                tech_specs={
                    "voltage": f"{random.choice([12, 24, 48, 120])}V" if category == ComponentCategory.ELECTRICAL else None,
                    "frequency_range": f"{random.randint(20, 100)}-{random.randint(100, 500)}kHz" if category == ComponentCategory.ACOUSTIC else None,
                    "max_temp": f"{random.randint(60, 120)}°C" if category == ComponentCategory.THERMAL else None
                },
                supplier=random.choice(["ACME Corp", "TechSupply Inc", "Precision Parts Ltd", "Global Components"]),
                lead_time_days=random.randint(7, 45),
                order_date=datetime.utcnow() - timedelta(days=random.randint(10, 60)),
                updated_by=random.choice(users).email
            )
            component.expected_delivery = component.order_date + timedelta(days=component.lead_time_days)
            db.add(component)
            components.append(component)
        
        db.commit()
        
        # Create tests
        tests = []
        test_categories = ["Acoustic", "Thermal", "Integration", "System", "Physics Validation"]
        
        for i, component in enumerate(components):
            # Create 2-3 tests per component
            for j in range(random.randint(2, 3)):
                test_category = random.choice(test_categories)
                status = random.choice([TestStatus.NOT_STARTED, TestStatus.IN_PROGRESS, TestStatus.COMPLETED, TestStatus.BLOCKED])
                
                test = Test(
                    test_id=f"TST-{i+1:03d}-{j+1:02d}",
                    name=f"{test_category} Test for {component.name}",
                    category=test_category,
                    purpose=f"Validate {test_category.lower()} performance of {component.name}",
                    duration_hours=random.uniform(0.5, 8),
                    prerequisites=["Safety training", "Equipment calibration"],
                    status=status,
                    executed_date=datetime.utcnow() - timedelta(days=random.randint(0, 7)) if status == TestStatus.COMPLETED else None,
                    engineer=random.choice(users).name if status != TestStatus.NOT_STARTED else None,
                    notes=f"Test setup for {component.name}" if status != TestStatus.NOT_STARTED else None,
                    linear_issue_id=f"LIN-{random.randint(100, 999)}" if random.random() > 0.5 else None
                )
                
                db.add(test)
                tests.append(test)
        
        db.commit()
        
        # Create test results for completed tests
        for test in tests:
            if test.status == TestStatus.COMPLETED:
                # Create 1-2 test results per completed test
                for k in range(random.randint(1, 2)):
                    component = random.choice(components)
                    result_status = random.choice([TestResultStatus.PASS, TestResultStatus.FAIL, TestResultStatus.PARTIAL])
                    
                    result = TestResult(
                        test_id=test.id,
                        component_id=component.id,
                        result=result_status,
                        steering_force=random.uniform(10, 50) if random.random() > 0.3 else None,
                        bonding_strength=random.uniform(100, 500) if random.random() > 0.3 else None,
                        temperature_max=random.uniform(25, 85) if random.random() > 0.3 else None,
                        drip_number=random.uniform(0.5, 2.0) if random.random() > 0.3 else None,
                        physics_validated=result_status == TestResultStatus.PASS and random.random() > 0.3,
                        evidence_files=[f"test_{test.test_id}_evidence_{k+1}.pdf"] if random.random() > 0.5 else None,
                        executed_at=test.executed_date,
                        executed_by=test.engineer,
                        notes=f"Result for {component.name}" if result_status == TestResultStatus.FAIL else None
                    )
                    db.add(result)
        
        db.commit()
        
        print("Database seeded successfully!")
        print(f"Created {len(users)} users")
        print(f"Created {len(components)} components")
        print(f"Created {len(tests)} tests")
        print(f"Created {db.query(TestResult).count()} test results")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Seed the database
    seed_database()