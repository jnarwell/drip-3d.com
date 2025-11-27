import React, { useEffect, useState } from 'react';

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

  useEffect(() => {
    // Initialize animations
    const initScrollAnimations = () => {
      const observerOptions = {
        threshold: 0.2,
        rootMargin: '0px 0px -100px 0px'
      };

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('active');
          }
        });
      }, observerOptions);

      const animatedElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
      animatedElements.forEach(el => observer.observe(el));
    };

    initScrollAnimations();

    // Load team data
    fetch('/data/team.json')
      .then(res => res.json())
      .then(data => setTeamData(data))
      .catch(err => console.error('Error loading team data:', err));

    // Handle escape key for modal
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && modalOpen) {
        closeModal();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
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

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const name = formData.get('name');
    const email = formData.get('email');
    const message = formData.get('message');
    
    // Create mailto link
    const subject = `DRIP Contact from ${name}`;
    const body = `From: ${name}\nEmail: ${email}\n\nMessage:\n${message}`;
    const mailtoLink = `mailto:jamie@drip-3d.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    window.location.href = mailtoLink;
  };

  return (
    <>
      {/* Header */}
      <header className="site-header">
        <div className="container">
          <div className="site-header__inner">
            <div className="logo">
              <a href="/">DRIP</a>
            </div>
            <nav className="main-nav">
              <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/progress">Progress</a></li>
                <li><a href="/team" className="active">Team</a></li>
              </ul>
            </nav>
            <button className="mobile-menu-toggle" aria-label="Toggle menu">☰</button>
          </div>
        </div>
      </header>

      {/* Current Team */}
      <section className="section" style={{paddingTop: '100px'}}>
        <div className="container">
          <h2 className="text-center mb-xl">Current Team Members</h2>
          <div className="grid grid--3" id="team-grid">
            {teamData?.current.map((member, index) => (
              <div 
                key={member.id}
                className={`team-card reveal stagger-${index + 1}`} 
                data-member-id={member.id}
                onClick={() => openModal(member.id)}
                style={{cursor: 'pointer'}}
              >
                <div className="team-card__photo">
                  {member.photo ? (
                    <img src={member.photo} alt={member.name} />
                  ) : (
                    <div className="team-placeholder">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
          
          <form id="contact-form" className="contact-form" onSubmit={handleContactSubmit}>
            <input type="text" name="name" placeholder="Your Name" required />
            <input type="email" name="email" placeholder="Your Email" required />
            <textarea name="message" placeholder="Tell us about yourself and your interest in DRIP" rows={5} required></textarea>
            <button type="submit" className="btn btn--primary btn--large">Send Message</button>
          </form>
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
      <div className={`modal${modalOpen ? ' modal--open' : ''}`} id="team-modal" onClick={(e) => {
        if ((e.target as HTMLElement).classList.contains('modal')) {
          closeModal();
        }
      }}>
        <div className="modal__content">
          <button className="modal__close" aria-label="Close modal" onClick={closeModal}>&times;</button>
          {selectedMember && (
            <>
              <div className="modal__header">
                {selectedMember.photo && (
                  <img src={selectedMember.photo} alt={selectedMember.name} className="modal__photo" />
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
                {selectedMember.bio?.responsibilities && (
                  <section className="responsibilities">
                    <h3>Responsibilities</h3>
                    <ul className="modal__responsibilities">
                      {selectedMember.bio.responsibilities.map((resp, i) => (
                        <li key={i}>{resp}</li>
                      ))}
                    </ul>
                  </section>
                )}
                {selectedMember.bio?.expertise && (
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
                  <a href={`mailto:${selectedMember.social.email}`} className="btn btn--primary modal__contact">Contact</a>
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