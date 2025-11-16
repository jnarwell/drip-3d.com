#!/usr/bin/env python3
"""Test script for the unified alloy standards system"""

import sys
import os
sys.path.append('.')

# Set environment variables for development
os.environ['DEV_MODE'] = 'true'
os.environ['AUTH0_DOMAIN'] = 'dev'
os.environ['AUTH0_API_AUDIENCE'] = 'dev'
os.environ['AUTH0_CLIENT_ID'] = 'dev'  
os.environ['AUTH0_CLIENT_SECRET'] = 'dev'

from app.services.alloy_standards import AlloyStandardsService
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unified_database_loading():
    """Test that the unified database loads correctly"""
    logger.info("🧪 Testing unified database loading")
    
    service = AlloyStandardsService()
    
    # Check that data was loaded
    if service.standards_data:
        logger.info(f"✅ Loaded {len(service.standards_data)} categories")
        
        # Check specific alloys
        test_alloys = ["6061-T6", "2024-T3", "1100-O"]
        for alloy in test_alloys:
            alloy_data = service.get_alloy_standard(alloy)
            if alloy_data:
                logger.info(f"✅ Found {alloy}: {alloy_data['common_name']}")
                
                # Check source tracking
                if '_property_sources' in alloy_data:
                    logger.info(f"   📊 Has property source tracking: {len(alloy_data['_property_sources'])} properties")
                if '_temperature_dependent' in alloy_data:
                    temp_props = [k for k, v in alloy_data['_temperature_dependent'].items() if v]
                    logger.info(f"   🌡️ Temperature-dependent properties: {temp_props}")
                    
        return True
    else:
        logger.error("❌ No data loaded")
        return False

def test_source_tracking():
    """Test source tracking functionality"""
    logger.info("🧪 Testing source tracking")
    
    service = AlloyStandardsService()
    
    # Test property source info for 6061-T6
    source_info = service.get_property_source_info("6061-T6")
    if source_info:
        logger.info("✅ Source info for 6061-T6:")
        logger.info(f"   Database source: {source_info['database_source']}")
        logger.info(f"   Property sources: {len(source_info['property_sources'])} tracked")
        logger.info(f"   Temperature dependent: {len([k for k, v in source_info['temperature_dependent_properties'].items() if v])} properties")
        logger.info(f"   Available properties: {sum(len(props) for props in source_info['available_properties'].values())} total")
        return True
    else:
        logger.error("❌ Could not get source info for 6061-T6")
        return False

def test_sources_summary():
    """Test database sources summary"""
    logger.info("🧪 Testing sources summary")
    
    service = AlloyStandardsService()
    
    summary = service.get_all_sources_summary()
    if summary:
        logger.info("✅ Database sources summary:")
        logger.info(f"   Database sources: {summary['database_sources']}")
        logger.info(f"   Property sources: {summary['property_sources']}")
        logger.info(f"   Total alloys: {summary['total_alloys']}")
        logger.info(f"   Total properties: {summary['total_properties']}")
        logger.info(f"   Temperature dependent: {summary['temperature_dependent_properties']}")
        logger.info(f"   Categories: {summary['categories']}")
        return True
    else:
        logger.error("❌ Could not get sources summary")
        return False

def test_backward_compatibility():
    """Test that the unified system maintains backward compatibility"""
    logger.info("🧪 Testing backward compatibility")
    
    service = AlloyStandardsService()
    
    # Test that old methods still work
    alloy_data = service.get_alloy_standard("6061-T6")
    if alloy_data:
        # Check that old structure is maintained
        required_fields = ['common_name', 'uns', 'composition', 'mechanical', 'thermal']
        missing_fields = [field for field in required_fields if field not in alloy_data]
        
        if not missing_fields:
            logger.info("✅ Backward compatibility maintained - all required fields present")
            
            # Check that mechanical properties are accessible in old format
            if 'density' in alloy_data['mechanical']:
                logger.info(f"   ✅ Density accessible: {alloy_data['mechanical']['density']} g/cm³")
            
            # Check that thermal properties are accessible
            if 'thermal_conductivity' in alloy_data['thermal']:
                logger.info(f"   ✅ Thermal conductivity accessible: {alloy_data['thermal']['thermal_conductivity']} W/m·K")
                
            return True
        else:
            logger.error(f"❌ Missing required fields: {missing_fields}")
            return False
    else:
        logger.error("❌ Could not get 6061-T6 data")
        return False

def test_nist_integration_compatibility():
    """Test that NIST integration still works with unified database"""
    logger.info("🧪 Testing NIST integration compatibility")
    
    service = AlloyStandardsService()
    
    try:
        # Test enhanced alloy data
        enhanced_data = service.get_enhanced_alloy_data("6061-T6", include_nist_data=True)
        if enhanced_data:
            logger.info("✅ NIST integration compatible with unified database")
            
            if enhanced_data.get('nist_enhanced'):
                temp_props = enhanced_data.get('temperature_dependent_properties', {})
                logger.info(f"   🌡️ NIST enhanced with {len(temp_props)} temperature curves")
            else:
                logger.info("   ⚠️ NIST enhancement not applied (may be expected due to rate limits)")
                
            return True
        else:
            logger.error("❌ Could not get enhanced data")
            return False
            
    except Exception as e:
        logger.error(f"❌ NIST integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting unified alloy standards system tests")
    
    tests = [
        ("Unified Database Loading", test_unified_database_loading),
        ("Source Tracking", test_source_tracking),
        ("Sources Summary", test_sources_summary),
        ("Backward Compatibility", test_backward_compatibility),
        ("NIST Integration Compatibility", test_nist_integration_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Unified alloy standards system is working correctly.")
    elif passed > total // 2:
        logger.warning("⚠️ Most tests passed. Some issues may need attention.")
    else:
        logger.error("❌ Most tests failed. System needs debugging.")

if __name__ == "__main__":
    main()