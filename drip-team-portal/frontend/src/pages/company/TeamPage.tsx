import React, { useEffect, useState } from 'react';
import Navigation from '../../components/company/Navigation';
import Footer from '../../components/company/Footer';
import { useFadeInWhenVisible } from '../../hooks/useFadeInWhenVisible';
import { useBodyBackground } from './useBodyBackground';
import { useScrollEasterEgg } from '../../hooks/useScrollEasterEgg';
import { teamMembers } from '../../data/teamMembers';
import { TeamMember } from '../../types/TeamMember';
import TeamMemberCard from '../../components/company/TeamMemberCard';

const TeamPage: React.FC = () => {
  // Debug logging
  console.log('[TeamPage] Component mounting');
  console.log('[TeamPage] Team members:', teamMembers);
  
  // Set body background color to match page edges
  useBodyBackground('#354857');
  
  // Easter egg hook
  const { isRevealed, scrollAttempts } = useScrollEasterEgg(15);
  
  // Log after hooks
  console.log('[TeamPage] Hooks initialized');
  
  const section2 = useFadeInWhenVisible();
  const section3 = useFadeInWhenVisible();
  const easterEgg = useFadeInWhenVisible();
  
  // Future: This will open a modal with more details from Linear
  const handleTeamMemberClick = (member: TeamMember) => {
    console.log('Team member clicked:', member.name);
    // TODO: Open modal with member details, projects from Linear, etc.
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: '#354857'
    }}>
      {/* Navigation */}
      <Navigation activePage="team" />
      
      {/* Section 1 - Gray Background (Team Members) */}
      <section style={{ 
        backgroundColor: '#ebf0f1',
        padding: '60px 42px'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1 style={{ 
            color: '#354857',
            marginBottom: '40px',
            fontSize: '48px',
            fontWeight: 'bold',
            textAlign: 'center'
          }}>
            Team Members
          </h1>
          
          {/* Team member cards container - max 3 per row */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '30px',
            marginTop: '40px',
            maxWidth: '1200px',
            margin: '40px auto 0'
          }}>
            {teamMembers.map((member) => (
              <TeamMemberCard
                key={member.id}
                member={member}
                onClick={() => handleTeamMemberClick(member)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Section 2 - Blue Background (Placeholder) */}
      <section style={{ 
        backgroundColor: '#354857',
        padding: '60px 42px'
      }}>
        <div 
          ref={section2.ref}
          style={{ 
            maxWidth: '1200px', 
            margin: '0 auto',
            opacity: section2.isVisible ? 1 : 0,
            transition: 'opacity 0.4s ease-in-out'
          }}>
          <p style={{
            color: '#ffffff',
            fontSize: '18px',
            textAlign: 'center',
            maxWidth: '600px',
            margin: '0 auto 40px',
            lineHeight: '1.6'
          }}>
            Interested in learning more about DRIP or collaborating with our team? We'd love to hear from you.
          </p>
          
          {/* Contact Form */}
          <form 
            id="contact-form"
            style={{
            width: '60%',
            margin: '0 auto'
          }}>
            <div style={{ marginBottom: '20px' }}>
              <input 
                type="text"
                placeholder="Name"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  fontSize: '16px',
                  border: 'none',
                  borderRadius: '4px',
                  backgroundColor: '#ebf0f1',
                  color: '#354857'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <input 
                type="email"
                placeholder="Email"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  fontSize: '16px',
                  border: 'none',
                  borderRadius: '4px',
                  backgroundColor: '#ebf0f1',
                  color: '#354857'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <textarea 
                placeholder="Message"
                rows={5}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  fontSize: '16px',
                  border: 'none',
                  borderRadius: '4px',
                  backgroundColor: '#ebf0f1',
                  color: '#354857',
                  resize: 'vertical',
                  minHeight: '120px'
                }}
              />
            </div>
            
            <button 
              type="submit"
              style={{
                width: '100%',
                padding: '14px 24px',
                fontSize: '16px',
                fontWeight: '600',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: '#ebf0f1',
                color: '#354857',
                cursor: 'pointer',
                transition: 'transform 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              Send Message
            </button>
          </form>
        </div>
      </section>

      {/* Easter Egg Section - Hidden until triggered */}
      {isRevealed && (
        <section 
          id="easter-egg-section"
          style={{ 
            minHeight: '100vh',
            backgroundColor: '#ebf0f1',
            padding: '60px 42px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
          <div style={{ 
              maxWidth: '800px', 
              margin: '0 auto',
              textAlign: 'center'
            }}>
            <h1 style={{ 
              color: '#354857',
              fontSize: '48px',
              fontWeight: 'bold',
              marginBottom: '10px'
            }}>
              The Real DRIP Roadmap
            </h1>
            <p style={{
              color: '#666666',
              fontSize: '20px',
              marginBottom: '40px',
              fontStyle: 'italic'
            }}>
              Beyond Aluminum: Our Journey to Functionally Graded Materials
            </p>
            
            {/* Current - Aluminum */}
            <div style={{
              backgroundColor: '#354857',
              color: '#ffffff',
              padding: '30px',
              borderRadius: '8px',
              marginBottom: '20px',
              textAlign: 'left',
              border: '3px solid #354857'
            }}>
              <h3 style={{
                fontSize: '24px',
                fontWeight: 'bold',
                marginBottom: '10px'
              }}>
                NOW: Aluminum (Al)
              </h3>
              <p style={{ fontSize: '16px', marginBottom: '10px' }}>
                <strong>Status:</strong> In Production
              </p>
              <p style={{ fontSize: '16px', lineHeight: '1.6' }}>
                <strong>Enables:</strong> Basic acoustic metamaterials, proof of concept designs, 
                lightweight structures with 2.7 g/cm³ density
              </p>
            </div>

            {/* Q1 2025 - Al-Mg */}
            <div style={{
              backgroundColor: '#ffffff',
              padding: '30px',
              borderRadius: '8px',
              marginBottom: '20px',
              textAlign: 'left',
              border: '2px solid #354857'
            }}>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: 'bold',
                marginBottom: '10px'
              }}>
                Q1 2025: Aluminum-Magnesium (Al-Mg)
              </h3>
              <p style={{ color: '#666666', fontSize: '16px', marginBottom: '10px' }}>
                <strong>Status:</strong> Testing Phase
              </p>
              <p style={{ color: '#666666', fontSize: '16px', lineHeight: '1.6' }}>
                <strong>Enables:</strong> 30% weight reduction, improved damping characteristics, 
                marine/underwater acoustic applications, enhanced corrosion resistance
              </p>
            </div>

            {/* Q3 2025 - Al-Mg-Cu */}
            <div style={{
              backgroundColor: '#ffffff',
              padding: '30px',
              borderRadius: '8px',
              marginBottom: '20px',
              textAlign: 'left',
              border: '2px dashed #354857'
            }}>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: 'bold',
                marginBottom: '10px'
              }}>
                Q3 2025: Aluminum-Magnesium-Copper (Al-Mg-Cu)
              </h3>
              <p style={{ color: '#666666', fontSize: '16px', marginBottom: '10px' }}>
                <strong>Status:</strong> R&D Phase
              </p>
              <p style={{ color: '#666666', fontSize: '16px', lineHeight: '1.6' }}>
                <strong>Enables:</strong> Aerospace-grade metamaterials, high-temperature acoustic stability, 
                precision frequency targeting, 2x strength improvement
              </p>
            </div>

            {/* 2026 - Metal-Metal FGM */}
            <div style={{
              backgroundColor: '#ebf0f1',
              padding: '30px',
              borderRadius: '8px',
              marginBottom: '20px',
              textAlign: 'left',
              border: '2px dashed #999'
            }}>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: 'bold',
                marginBottom: '10px'
              }}>
                2026: Metal-Metal FGMs
              </h3>
              <p style={{ color: '#666666', fontSize: '16px', marginBottom: '10px' }}>
                <strong>Status:</strong> Planning
              </p>
              <p style={{ color: '#666666', fontSize: '16px', lineHeight: '1.6' }}>
                <strong>Enables:</strong> Gradient acoustic impedance within single print, 
                seamless titanium-aluminum transitions, impossible geometries, 
                frequency-selective absorption layers
              </p>
            </div>

            {/* 2027 - Ultimate FGM */}
            <div style={{
              backgroundColor: '#ebf0f1',
              padding: '30px',
              borderRadius: '8px',
              marginBottom: '30px',
              textAlign: 'left',
              border: '2px dashed #999',
              position: 'relative' as const,
              overflow: 'hidden'
            }}>
              <div style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                backgroundColor: '#354857',
                color: '#ffffff',
                padding: '5px 10px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                ULTIMATE GOAL
              </div>
              <h3 style={{
                color: '#354857',
                fontSize: '24px',
                fontWeight: 'bold',
                marginBottom: '10px'
              }}>
                2027: Metal-Ceramic-Diamond-Bio FGMs
              </h3>
              <p style={{ color: '#666666', fontSize: '16px', marginBottom: '10px' }}>
                <strong>Status:</strong> Concept
              </p>
              <p style={{ color: '#666666', fontSize: '16px', lineHeight: '1.6' }}>
                <strong>Enables:</strong> Living acoustic materials, self-healing structures, 
                diamond-hard wear surfaces with metal cores, bio-integrated sensors, 
                active acoustic response, the impossible becomes possible
              </p>
            </div>

            <div style={{
              backgroundColor: '#ffffff',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              textAlign: 'center'
            }}>
              <p style={{
                color: '#354857',
                fontSize: '18px',
                fontWeight: '600'
              }}>
                You're seeing what others won't know for years.
              </p>
              <p style={{
                color: '#666666',
                fontSize: '16px',
                marginTop: '10px'
              }}>
                Interested in the future of materials?
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Footer - Always visible */}
      <Footer />
    </div>
  );
};

export default TeamPage;