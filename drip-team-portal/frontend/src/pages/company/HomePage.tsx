import React from 'react';
import Navigation from '../../components/company/Navigation';
import Footer from '../../components/company/Footer';
import { useFadeInWhenVisible } from '../../hooks/useFadeInWhenVisible';
import { useBodyBackground } from './useBodyBackground';
import { useMobile } from '../../hooks/useMobile';

const HomePage: React.FC = () => {
  // Set body background to match top section
  useBodyBackground('#354857');
  
  const section1Content = useFadeInWhenVisible();
  const section2 = useFadeInWhenVisible();
  const section3 = useFadeInWhenVisible();
  
  // Mobile detection
  const isMobile = useMobile();

  return (
    <div style={{ 
      minHeight: '100vh'
    }}>
      {/* Navigation */}
      <Navigation activePage="home" />
      
      {/* Section 1 - Gray Background */}
      <section style={{ 
        backgroundColor: '#ebf0f1',
        padding: isMobile ? '40px 20px' : '60px 42px'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', textAlign: 'center' }}>
          <h1 style={{ 
            color: '#354857',
            marginBottom: '20px',
            fontSize: isMobile ? '36px' : '48px',
            fontWeight: 'bold',
            textAlign: 'center'
          }}>
            Acoustic Deposition Manufacturing
          </h1>
          
          <p 
            ref={section1Content.ref}
            style={{
              color: '#666666',
              fontSize: isMobile ? '20px' : '24px',
              fontStyle: 'italic',
              opacity: section1Content.isVisible ? 1 : 0,
              transition: 'opacity 0.4s ease-in-out'
            }}>
            Precision AM at high temp
          </p>
        </div>
      </section>

      {/* Section 2 - Blue Background */}
      <section style={{ 
        backgroundColor: '#354857',
        padding: isMobile ? '40px 20px' : '60px 42px'
      }}>
        <div 
          ref={section2.ref}
          style={{ 
            maxWidth: '1200px', 
            margin: '0 auto',
            opacity: section2.isVisible ? 1 : 0,
            transition: 'opacity 0.4s ease-in-out'
          }}
        >
          <h2 style={{ 
            color: '#ffffff',
            fontSize: isMobile ? '28px' : '36px',
            fontWeight: 'bold',
            textAlign: 'center',
            marginBottom: isMobile ? '30px' : '40px'
          }}>
            L1 System Capabilities
          </h2>
          
          {/* Capabilities Cards */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
            gap: isMobile ? '20px' : '30px',
            maxWidth: '1080px',
            margin: '0 auto'
          }}>
            {/* Temperature Range Card */}
            <div style={{
              backgroundColor: '#ebf0f1',
              borderRadius: '8px',
              padding: '40px 30px',
              textAlign: 'center'
            }}>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: '600',
                marginBottom: '20px'
              }}>
                Temperature Range
              </h3>
              <p style={{
                color: '#354857',
                fontSize: '36px',
                fontWeight: 'bold',
                margin: 0
              }}>
                500-800°C
              </p>
            </div>
            
            {/* Droplet Steering Card */}
            <div style={{
              backgroundColor: '#ebf0f1',
              borderRadius: '8px',
              padding: '40px 30px',
              textAlign: 'center'
            }}>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: '600',
                marginBottom: '20px'
              }}>
                Droplet Steering
              </h3>
              <p style={{
                color: '#354857',
                fontSize: '36px',
                fontWeight: 'bold',
                margin: 0
              }}>
                ±5mm
              </p>
            </div>
            
            {/* Production Rate Card */}
            <div style={{
              backgroundColor: '#ebf0f1',
              borderRadius: '8px',
              padding: '40px 30px',
              textAlign: 'center'
            }}>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: '600',
                marginBottom: '20px'
              }}>
                Production Rate
              </h3>
              <p style={{
                color: '#354857',
                fontSize: '36px',
                fontWeight: 'bold',
                margin: 0
              }}>
                12cm³/hr
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 3 - Gray Background */}
      <section style={{ 
        backgroundColor: '#ebf0f1',
        padding: '60px 21px'
      }}>
        <div 
          ref={section3.ref}
          style={{ 
            maxWidth: '1200px', 
            margin: '0 auto',
            opacity: section3.isVisible ? 1 : 0,
            transition: 'opacity 0.4s ease-in-out'
          }}
        >
          <h2 style={{ 
            color: '#354857',
            fontSize: '36px',
            fontWeight: 'bold',
            textAlign: 'center',
            marginBottom: '40px'
          }}>
            How It Works
          </h2>
          
          {/* Content grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '100px',
            alignItems: 'flex-start'
          }}>
            {/* Left side - Text content */}
            <div>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: 'bold',
                marginBottom: '20px'
              }}>
                Acoustic Steering Technology
              </h3>
              
              <p style={{
                color: '#666666',
                fontSize: '16px',
                lineHeight: '1.8',
                marginBottom: '20px'
              }}>
                DRIP uses acoustic deposition to manipulate molten metal, enabling contact-free 3D printing of complex geometries. Our system combines a crucible, acoustic phased array, and heated copper bed to achieve a novel form of material processing.
              </p>
              
              <p style={{
                color: '#666666',
                fontSize: '16px',
                lineHeight: '1.8',
                marginBottom: '20px'
              }}>
                This method overcomes the fundamental incompatibility between high temperature materials and electromechanical components. Without high cost, specialty components and complex integration, motors, belt drives, and most electronics cease functioning before even reaching the desired 600-1200°C range. Our system is entirely static, so we can utilize low temp and low cost components through clever thermodynamic control.
              </p>
            </div>
            
            {/* Right side - Specifications Table */}
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              padding: '0',
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'center',
              overflow: 'hidden'
            }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                backgroundColor: '#ffffff',
                borderRadius: '8px',
                overflow: 'hidden'
              }}>
                <thead>
                  <tr style={{
                    backgroundColor: '#354857'
                  }}>
                    <th style={{
                      padding: '16px 32px',
                      textAlign: 'left',
                      color: '#ffffff',
                      fontSize: '18px',
                      fontWeight: '600',
                      borderRight: '1px solid rgba(255, 255, 255, 0.1)'
                    }}>
                      Specification
                    </th>
                    <th style={{
                      padding: '16px 32px',
                      textAlign: 'left',
                      color: '#ffffff',
                      fontSize: '18px',
                      fontWeight: '600'
                    }}>
                      Value
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{
                    borderBottom: '1px solid #e9ecef'
                  }}>
                    <td style={{
                      padding: '20px 32px',
                      color: '#354857',
                      fontSize: '16px',
                      fontWeight: '500'
                    }}>
                      Cost
                    </td>
                    <td style={{
                      padding: '20px 32px',
                      color: '#666666',
                      fontSize: '16px'
                    }}>
                      $35,500
                    </td>
                  </tr>
                  <tr style={{
                    borderBottom: '1px solid #e9ecef'
                  }}>
                    <td style={{
                      padding: '20px 32px',
                      color: '#354857',
                      fontSize: '16px',
                      fontWeight: '500'
                    }}>
                      Power
                    </td>
                    <td style={{
                      padding: '20px 32px',
                      color: '#666666',
                      fontSize: '16px'
                    }}>
                      8 kW
                    </td>
                  </tr>
                  <tr style={{
                    borderBottom: '1px solid #e9ecef'
                  }}>
                    <td style={{
                      padding: '20px 32px',
                      color: '#354857',
                      fontSize: '16px',
                      fontWeight: '500'
                    }}>
                      Resolution
                    </td>
                    <td style={{
                      padding: '20px 32px',
                      color: '#666666',
                      fontSize: '16px'
                    }}>
                      300 μm
                    </td>
                  </tr>
                  <tr>
                    <td style={{
                      padding: '20px 32px',
                      color: '#354857',
                      fontSize: '16px',
                      fontWeight: '500'
                    }}>
                      Build Volume
                    </td>
                    <td style={{
                      padding: '20px 32px',
                      color: '#666666',
                      fontSize: '16px'
                    }}>
                      ⌀80mm × 120mm
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default HomePage;