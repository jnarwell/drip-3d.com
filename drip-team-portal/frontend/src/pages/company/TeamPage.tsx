import React, { useEffect, useState, useRef } from 'react';
import Navigation from '../../components/company/Navigation';
import { useScrollAnimation } from '../../hooks/useScrollAnimation';
import { loadData } from '../../utils/drip';

interface TeamMember {
  id: string;
  name: string;
  role: string;
  title?: string;
  badge?: string;
  photo?: string;
  bio?: {
    full: string;
    responsibilities?: string[];
    expertise?: string[];
  };
  social?: {
    email?: string;
  };
}

interface TeamData {
  current: TeamMember[];
  openPositions: any[];
  advisors: any[];
  alumniSupport: any[];
}

const TeamPage: React.FC = () => {
  const [teamData, setTeamData] = useState<TeamData | null>(null);
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [formStatus, setFormStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [formMessage, setFormMessage] = useState('');
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<any>({});
  const formRef = useRef<HTMLFormElement>(null);

  // Initialize scroll animations
  useScrollAnimation();

  // Load team data with debugging
  useEffect(() => {
    loadData<TeamData>('team.json')
      .then(data => {
        if (data) {
          setTeamData(data);
          console.log('[DEBUG] Team data loaded:', {
            memberCount: data.current?.length,
            firstMember: data.current?.[0]
          });
        } else {
          setLoadingError('No team data available');
        }
      })
      .catch(err => {
        setLoadingError(err.message || 'Failed to load team data');
      });
  }, []);

  // Debug CSS and rendering
  useEffect(() => {
    const timer = setTimeout(() => {
      const debug: any = {};
      
      // Check if styles are loaded
      const stylesheets = Array.from(document.styleSheets);
      debug.stylesheetCount = stylesheets.length;
      debug.stylesheetUrls = stylesheets.map(s => s.href).filter(Boolean);
      
      // Check team-card styles
      const testCard = document.createElement('div');
      testCard.className = 'team-card';
      document.body.appendChild(testCard);
      const cardStyles = window.getComputedStyle(testCard);
      debug.teamCardStyles = {
        display: cardStyles.display,
        visibility: cardStyles.visibility,
        backgroundColor: cardStyles.backgroundColor,
        borderRadius: cardStyles.borderRadius,
        boxShadow: cardStyles.boxShadow,
        width: cardStyles.width,
        height: cardStyles.height,
        opacity: cardStyles.opacity,
        position: cardStyles.position,
        zIndex: cardStyles.zIndex
      };
      document.body.removeChild(testCard);
      
      // Check grid styles
      const grid = document.querySelector('.grid.grid--3');
      if (grid) {
        const gridStyles = window.getComputedStyle(grid);
        debug.gridStyles = {
          display: gridStyles.display,
          gridTemplateColumns: gridStyles.gridTemplateColumns,
          gap: gridStyles.gap,
          width: gridStyles.width
        };
      }
      
      // Check actual rendered cards
      const renderedCards = document.querySelectorAll('.team-card');
      debug.renderedCardCount = renderedCards.length;
      if (renderedCards.length > 0) {
        const firstCard = renderedCards[0];
        const firstCardRect = firstCard.getBoundingClientRect();
        const firstCardStyles = window.getComputedStyle(firstCard);
        debug.firstCardInfo = {
          dimensions: {
            width: firstCardRect.width,
            height: firstCardRect.height,
            top: firstCardRect.top,
            left: firstCardRect.left
          },
          computedStyles: {
            display: firstCardStyles.display,
            visibility: firstCardStyles.visibility,
            opacity: firstCardStyles.opacity,
            backgroundColor: firstCardStyles.backgroundColor,
            position: firstCardStyles.position,
            zIndex: firstCardStyles.zIndex
          },
          hasContent: firstCard.innerHTML.length > 0,
          childElements: firstCard.children.length
        };
      }
      
      // Check images
      const images = document.querySelectorAll('.team-card__photo img');
      debug.imageCount = images.length;
      debug.imageInfo = Array.from(images).map((img: any) => ({
        src: img.src,
        loaded: img.complete,
        width: img.width,
        height: img.height,
        display: window.getComputedStyle(img).display
      }));
      
      setDebugInfo(debug);
      console.log('[DEBUG] Full debug info:', debug);
    }, 1000); // Wait for styles to load
    
    return () => clearTimeout(timer);
  }, [teamData]);


  // Handle escape key for modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && modalOpen) {
        closeModal();
      }
    };

    if (modalOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [modalOpen]);

  const openModal = (memberId: string) => {
    const member = teamData?.current.find(m => m.id === memberId);
    if (member) {
      setSelectedMember(member);
      setModalOpen(true);
      document.body.style.overflow = 'hidden';
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedMember(null);
    document.body.style.overflow = '';
  };

  const handleModalClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).classList.contains('modal')) {
      closeModal();
    }
  };

  const handleContactSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormStatus('loading');
    
    const form = e.currentTarget;
    const formData = new FormData(form);
    const name = formData.get('name') as string;
    const email = formData.get('email') as string;
    const message = formData.get('message') as string;
    
    // Create mailto link
    const subject = `DRIP Contact from ${name}`;
    const body = `From: ${name}\nEmail: ${email}\n\nMessage:\n${message}`;
    const mailtoLink = `mailto:jamie@drip-3d.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    // Small delay to show loading state
    setTimeout(() => {
      window.location.href = mailtoLink;
      setFormStatus('success');
      setFormMessage('Message sent! Your email client should open shortly.');
      
      // Reset form
      if (formRef.current) {
        formRef.current.reset();
      }
      
      // Auto-hide success message after 5 seconds
      setTimeout(() => {
        setFormStatus('idle');
        setFormMessage('');
      }, 5000);
    }, 500);
  };

  return (
    <>
      {/* Navigation */}
      <Navigation activePage="team" />

      {/* Current Team */}
      <section className="section" style={{paddingTop: '100px'}}>
        <div className="container">
          <h2 className="text-center mb-xl">Current Team Members</h2>
          
          {/* Loading/Error State */}
          {!teamData && !loadingError && (
            <div className="text-center">
              <p>Loading team members...</p>
            </div>
          )}
          
          {loadingError && (
            <div className="text-center" style={{color: 'red'}}>
              <p>Error loading team data: {loadingError}</p>
            </div>
          )}
          
          {/* Debug Panel */}
          {Object.keys(debugInfo).length > 0 && (
            <div style={{
              backgroundColor: '#f0f0f0',
              border: '2px solid #333',
              borderRadius: '8px',
              padding: '20px',
              marginBottom: '20px',
              fontFamily: 'monospace',
              fontSize: '12px',
              maxHeight: '400px',
              overflow: 'auto'
            }}>
              <h3 style={{marginTop: 0}}>Debug Information</h3>
              <details open>
                <summary style={{cursor: 'pointer', fontWeight: 'bold'}}>Stylesheet Info</summary>
                <div style={{marginLeft: '20px', marginTop: '10px'}}>
                  <div>Total stylesheets: {debugInfo.stylesheetCount}</div>
                  <div>URLs: {JSON.stringify(debugInfo.stylesheetUrls, null, 2)}</div>
                </div>
              </details>
              <details open>
                <summary style={{cursor: 'pointer', fontWeight: 'bold', marginTop: '10px'}}>Team Card Styles</summary>
                <pre style={{marginLeft: '20px', marginTop: '10px'}}>
                  {JSON.stringify(debugInfo.teamCardStyles, null, 2)}
                </pre>
              </details>
              <details open>
                <summary style={{cursor: 'pointer', fontWeight: 'bold', marginTop: '10px'}}>Grid Info</summary>
                <pre style={{marginLeft: '20px', marginTop: '10px'}}>
                  {JSON.stringify(debugInfo.gridStyles, null, 2)}
                </pre>
              </details>
              <details open>
                <summary style={{cursor: 'pointer', fontWeight: 'bold', marginTop: '10px'}}>Rendered Cards</summary>
                <div style={{marginLeft: '20px', marginTop: '10px'}}>
                  <div>Card count: {debugInfo.renderedCardCount}</div>
                  {debugInfo.firstCardInfo && (
                    <pre>{JSON.stringify(debugInfo.firstCardInfo, null, 2)}</pre>
                  )}
                </div>
              </details>
              <details open>
                <summary style={{cursor: 'pointer', fontWeight: 'bold', marginTop: '10px'}}>Images</summary>
                <div style={{marginLeft: '20px', marginTop: '10px'}}>
                  <div>Image count: {debugInfo.imageCount}</div>
                  <pre>{JSON.stringify(debugInfo.imageInfo, null, 2)}</pre>
                </div>
              </details>
            </div>
          )}
          
          {/* Test Card with inline styles */}
          <div style={{marginBottom: '20px'}}>
            <h3>Test Card (should be visible):</h3>
            <div style={{
              backgroundColor: 'white',
              border: '2px solid blue',
              borderRadius: '8px',
              padding: '20px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              cursor: 'pointer',
              width: '300px'
            }}>
              <div style={{height: '200px', backgroundColor: '#e0e0e0', marginBottom: '10px'}}>
                Image placeholder
              </div>
              <h4>Test Member</h4>
              <p>Test Role</p>
            </div>
          </div>

          <div className="grid grid--3" id="team-grid">
            {teamData?.current.map((member, index) => (
                <div 
                  key={member.id}
                  className={`team-card reveal stagger-${Math.min(index + 1, 6)}`} 
                  data-member-id={member.id}
                  data-debug={`card-${index}`}
                  onClick={() => openModal(member.id)}
                  style={{
                    // Temporary debug styles
                    border: '2px solid red',
                    minHeight: '300px'
                  }}
                >
                  <div className="team-card__photo">
                    {member.photo ? (
                      <img 
                        src={`/${member.photo}`} 
                        alt={member.name} 
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = 'none';
                        }} 
                      />
                    ) : (
                      <div className="team-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="60" height="60">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                      </div>
                    )}
                    <div className="role-badge">{member.badge || member.role}</div>
                  </div>
                  <div className="team-card__content">
                    <h3 className="team-card__name">{member.name}</h3>
                    <p className="team-card__title">{member.title || member.role}</p>
                  </div>
                </div>
            ))}
          </div>
        </div>
      </section>

      {/* Join Section */}
      <section className="section join-section" id="contact">
        <div className="container container--content">
          <h2>Contact DRIP</h2>
          <p className="text-lg mb-xl">
            Interested in learning more about DRIP or collaborating with our team? 
            We'd love to hear from you.
          </p>
          
          <form 
            ref={formRef}
            id="contact-form" 
            className="contact-form" 
            onSubmit={handleContactSubmit}
          >
            <input 
              type="text" 
              name="name" 
              placeholder="Your Name" 
              required 
              disabled={formStatus === 'loading'}
            />
            <input 
              type="email" 
              name="email" 
              placeholder="Your Email" 
              required 
              disabled={formStatus === 'loading'}
            />
            <textarea 
              name="message" 
              placeholder="Tell us about yourself and your interest in DRIP" 
              rows={5} 
              required
              disabled={formStatus === 'loading'}
            ></textarea>
            <button 
              type="submit" 
              className={`btn btn--primary btn--large ${formStatus === 'loading' ? 'loading' : ''}`}
              disabled={formStatus === 'loading'}
            >
              {formStatus === 'loading' ? 'Sending...' : 'Send Message'}
            </button>
          </form>

          {/* Form Status Message */}
          {formMessage && (
            <div className={`form-message form-message--${formStatus}`}>
              {formMessage}
            </div>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="site-footer">
        <div className="container">
          <div className="footer__content">
            <div className="footer__section">
              <h4>Project</h4>
              <a href="/">Home</a>
              <a href="/progress">Development Progress</a>
              <a href="/team">Team</a>
            </div>
            <div className="footer__section">
              <h4>Contact</h4>
              <p className="text-sm">Email: <a href="mailto:jamie@drip-3d.com" style={{display: 'inline'}}>jamie@drip-3d.com</a><br/>
              Primary Contact: Jamie Marwell</p>
            </div>
          </div>
          <div className="footer__bottom">
            <p>&copy; 2025 Drip 3D Inc. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* Team Modal */}
      <div 
        className={`modal${modalOpen ? ' modal--open' : ''}`} 
        id="team-modal" 
        onClick={handleModalClick}
      >
        <div className="modal__content">
          <button 
            className="modal__close" 
            aria-label="Close modal" 
            onClick={closeModal}
          >
            &times;
          </button>
          {selectedMember && (
            <>
              <div className="modal__header">
                {selectedMember.photo && (
                  <img src={`/${selectedMember.photo}`} alt={selectedMember.name} className="modal__photo" />
                )}
                <div>
                  <h2 className="modal__name">{selectedMember.name}</h2>
                  <p className="modal__role">{selectedMember.role}</p>
                </div>
              </div>
              <div className="modal__body">
                <section className="bio">
                  <h3>Background</h3>
                  <p className="modal__bio">{selectedMember.bio?.full || 'No biography available.'}</p>
                </section>
                {selectedMember.bio?.responsibilities && selectedMember.bio.responsibilities.length > 0 && (
                  <section className="responsibilities">
                    <h3>Responsibilities</h3>
                    <ul className="modal__responsibilities">
                      {selectedMember.bio.responsibilities.map((resp, i) => (
                        <li key={i}>{resp}</li>
                      ))}
                    </ul>
                  </section>
                )}
                {selectedMember.bio?.expertise && selectedMember.bio.expertise.length > 0 && (
                  <section className="expertise">
                    <h3>Expertise</h3>
                    <ul className="modal__expertise">
                      {selectedMember.bio.expertise.map((exp, i) => (
                        <li key={i}>{exp}</li>
                      ))}
                    </ul>
                  </section>
                )}
              </div>
              {selectedMember.social?.email && (
                <div className="modal__footer">
                  <a 
                    href={`mailto:${selectedMember.social.email}`} 
                    className="btn btn--primary modal__contact"
                    onClick={(e) => {
                      e.preventDefault();
                      window.location.href = `mailto:${selectedMember.social?.email}`;
                    }}
                  >
                    Contact
                  </a>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default TeamPage;