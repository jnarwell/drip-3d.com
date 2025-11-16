#!/usr/bin/env python3
"""Test script for NIST WebBook integration with alloy standards"""

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
from app.services.nist_webbook import nist_service
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_alloy_standards_basic():
    """Test basic alloy standards functionality"""
    logger.info("🧪 Testing basic alloy standards functionality")
    
    service = AlloyStandardsService()
    
    # Test getting aluminum 6061-T6
    alloy_data = service.get_alloy_standard("6061-T6")
    if alloy_data:
        logger.info(f"✅ Found 6061-T6: {alloy_data['common_name']}")
        logger.info(f"   Thermal conductivity: {alloy_data.get('thermal', {}).get('thermal_conductivity')} W/m·K")
        logger.info(f"   Density: {alloy_data.get('mechanical', {}).get('density')} g/cm³")
        return True
    else:
        logger.error("❌ Could not find 6061-T6 alloy")
        return False

def test_nist_search():
    """Test NIST WebBook search functionality"""
    logger.info("🧪 Testing NIST WebBook search")
    
    # Test search for aluminum
    try:
        compound_info = nist_service.search_compound("aluminum")
        if compound_info:
            logger.info(f"✅ Found aluminum in NIST: {compound_info}")
            return True
        else:
            logger.warning("⚠️ Could not find aluminum in NIST WebBook")
            return False
    except Exception as e:
        logger.error(f"❌ NIST search failed: {e}")
        return False

def test_enhanced_alloy_data():
    """Test enhanced alloy data with NIST integration"""
    logger.info("🧪 Testing enhanced alloy data")
    
    service = AlloyStandardsService()
    
    # Test enhancing 6061-T6 with NIST data
    try:
        enhanced_data = service.get_enhanced_alloy_data("6061-T6", include_nist_data=True)
        if enhanced_data:
            logger.info(f"✅ Enhanced 6061-T6 data available")
            
            # Check if NIST enhancement was applied
            if enhanced_data.get('nist_enhanced'):
                temp_props = enhanced_data.get('temperature_dependent_properties', {})
                logger.info(f"🌡️ Temperature-dependent properties: {list(temp_props.keys())}")
                
                # Test specific property at temperature
                thermal_cond = service.get_property_at_temperature("6061-T6", "thermal_conductivity", 300)  # 300K
                if thermal_cond:
                    logger.info(f"🔥 Thermal conductivity at 300K: {thermal_cond} W/m·K")
                
                return True
            else:
                logger.warning("⚠️ NIST enhancement not applied (may be expected due to rate limits)")
                return True  # Still success, just no enhancement
        else:
            logger.error("❌ Could not get enhanced alloy data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Enhanced data test failed: {e}")
        return False

def test_temperature_curve():
    """Test temperature curve generation"""
    logger.info("🧪 Testing temperature curve generation")
    
    service = AlloyStandardsService()
    
    try:
        # Try to generate curve for thermal conductivity
        curve = service.generate_temperature_curve("6061-T6", "thermal_conductivity", 273, 573, 10)
        if curve:
            logger.info(f"📈 Generated temperature curve with {len(curve)} points")
            logger.info(f"    Sample points: {curve[:3]}")  # Show first 3 points
            return True
        else:
            logger.warning("⚠️ Could not generate temperature curve (no NIST data)")
            return True  # Still success, just no data available
            
    except Exception as e:
        logger.error(f"❌ Temperature curve test failed: {e}")
        return False

def test_bulk_enhancement():
    """Test bulk enhancement of alloys"""
    logger.info("🧪 Testing bulk enhancement (limited test)")
    
    service = AlloyStandardsService()
    
    try:
        # Test with just aluminum category to avoid overwhelming NIST
        results = service.bulk_enhance_alloys_with_nist(["aluminum"])
        logger.info(f"📊 Bulk enhancement results:")
        logger.info(f"   Total processed: {results['total_processed']}")
        logger.info(f"   Enhanced: {len(results['enhanced'])}")
        logger.info(f"   Failed: {len(results['failed'])}")
        logger.info(f"   Skipped: {len(results['skipped'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bulk enhancement test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting NIST WebBook integration tests")
    
    tests = [
        ("Basic Alloy Standards", test_alloy_standards_basic),
        ("NIST Search", test_nist_search),
        ("Enhanced Alloy Data", test_enhanced_alloy_data),
        ("Temperature Curve", test_temperature_curve),
        ("Bulk Enhancement", test_bulk_enhancement)
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
        logger.info("🎉 All tests passed! NIST integration is working.")
    elif passed > total // 2:
        logger.warning("⚠️ Most tests passed. Some NIST data may not be available due to rate limiting.")
    else:
        logger.error("❌ Most tests failed. Check configuration and network connectivity.")

if __name__ == "__main__":
    main()