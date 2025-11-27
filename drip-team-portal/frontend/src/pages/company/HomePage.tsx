import React, { useEffect } from 'react';

const HomePage: React.FC = () => {
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

    // Initialize carousel
    const initCarousel = () => {
      const carousel = document.getElementById('subsystems-carousel');
      if (!carousel) return;

      const track = carousel.querySelector('.carousel__track');
      const slides = Array.from(carousel.querySelectorAll('.carousel__slide'));
      const dots = Array.from(carousel.querySelectorAll('.carousel__dot'));
      const prevButton = carousel.parentElement?.querySelector('.carousel__btn--prev');
      const nextButton = carousel.parentElement?.querySelector('.carousel__btn--next');

      let currentIndex = 0;

      const updateCarousel = () => {
        if (!track) return;
        const trackElement = track as HTMLElement;
        trackElement.style.transform = `translateX(-${currentIndex * 100}%)`;
        
        dots.forEach((dot, index) => {
          dot.classList.toggle('carousel__dot--active', index === currentIndex);
        });
      };

      const goToSlide = (index: number) => {
        currentIndex = index;
        updateCarousel();
      };

      const goToPrev = () => {
        currentIndex = currentIndex > 0 ? currentIndex - 1 : slides.length - 1;
        updateCarousel();
      };

      const goToNext = () => {
        currentIndex = currentIndex < slides.length - 1 ? currentIndex + 1 : 0;
        updateCarousel();
      };

      prevButton?.addEventListener('click', goToPrev);
      nextButton?.addEventListener('click', goToNext);
      
      dots.forEach((dot, index) => {
        dot.addEventListener('click', () => goToSlide(index));
      });
    };

    initCarousel();
  }, []);

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
                <li><a href="/" className="active">Home</a></li>
                <li><a href="/progress">Progress</a></li>
                <li><a href="/team">Team</a></li>
              </ul>
            </nav>
            <button className="mobile-menu-toggle" aria-label="Toggle menu">☰</button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="section--hero hero">
        <div className="container">
          <div className="hero__content">
            <div className="hero__model animate-fade-in-left">
              <div className="hero__model-placeholder">
                <p>3D System Visualization</p>
                <small>Coming Soon</small>
              </div>
            </div>
            <div className="hero__text animate-fade-in-right">
              <h1>Acoustic Deposition Manufacturing</h1>
              <p className="hero__tagline">Precision metal 3D printing without contact</p>
              <div className="hero__cta">
                <a href="/team#contact" className="btn btn--primary btn--large">Join the Team</a>
                <a href="https://calendar.app.google/a5oi75jJrwbRFFWG9" target="_blank" rel="noopener noreferrer" className="btn btn--secondary btn--large">Schedule Info Meeting</a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Specs Section */}
      <section className="section">
        <div className="container">
          <h2 className="text-center mb-xl reveal">POC System Capabilities</h2>
          <div className="grid grid--4">
            <div className="spec-card reveal stagger-1">
              <div className="spec-card__icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2v10.5a1.5 1.5 0 0 0 3 0V2a1 1 0 0 0-1-1h-2a1 1 0 0 0-1 1z"></path>
                  <path d="M14 22h2a1 1 0 0 0 1-1v-3.5a1.5 1.5 0 0 0-3 0V21a1 1 0 0 0 1 1z"></path>
                  <path d="M10 2v7.5a1.5 1.5 0 0 1-3 0V2a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1z"></path>
                  <path d="M7 22h1a1 1 0 0 0 1-1v-6.5a1.5 1.5 0 0 0-3 0V21a1 1 0 0 0 1 1z"></path>
                </svg>
              </div>
              <div className="spec-card__value">700-1200°C</div>
              <div className="spec-card__label">Temperature Range</div>
            </div>
            <div className="spec-card reveal stagger-2">
              <div className="spec-card__icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <circle cx="12" cy="12" r="6"></circle>
                  <circle cx="12" cy="12" r="2"></circle>
                </svg>
              </div>
              <div className="spec-card__value">±2mm</div>
              <div className="spec-card__label">Droplet Steering</div>
            </div>
            <div className="spec-card reveal stagger-3">
              <div className="spec-card__icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                  <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
                  <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
                  <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
                  <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                  <line x1="12" y1="22.08" x2="12" y2="12"></line>
                </svg>
              </div>
              <div className="spec-card__value">1 cm³/hr</div>
              <div className="spec-card__label">Production Rate</div>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Overview Section */}
      <section className="section bg-light tech-overview">
        <div className="container">
          <h2 className="text-center mb-xl reveal">How It Works</h2>
          <div className="tech-overview__grid">
            <div className="tech-overview__content reveal-left">
              <h3>Acoustic Steering Technology</h3>
              <p>DRIP uses acoustic deposition to manipulate molten metal, enabling contact-free 3D printing of complex geometries. Our system combines a crucible, acoustic phased array, and heated copper bed to achieve a novel form of material processing.</p>
              <p>This method overcomes the fundamental incompatibility between high temperature materials and traditional electromechanical components. Without high cost, specialty components and complex integration, motors, belt drives, and most electronics cease functioning before even reaching the desired 600-1200°C range. Our system is entirely static, so we can utilize low temp and low cost components through clever thermodynamic control.</p>
              <ul className="mt-lg">
                <li>✓ Contact-free processing prevents contamination</li>
                <li>✓ Works with aluminum, steel, and exotic alloys</li>
                <li>✓ Real-time droplet tracking and control</li>
              </ul>
            </div>
            <div className="reveal-right">
              <table className="tech-overview__table">
                <thead>
                  <tr>
                    <th>Specification</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Cost</td>
                    <td>$19,139</td>
                  </tr>
                  <tr>
                    <td>Build Volume</td>
                    <td>5×5×5 cm</td>
                  </tr>
                  <tr>
                    <td>Build Rate</td>
                    <td>1 cm³/hr</td>
                  </tr>
                  <tr>
                    <td>Power (AC)</td>
                    <td>11 kW</td>
                  </tr>
                  <tr>
                    <td>Resolution</td>
                    <td>±0.5 mm</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* Subsystems Carousel */}
      <section className="section">
        <div className="container">
          <h2 className="text-center mb-lg reveal">System Architecture</h2>
          <p className="text-center text-lg mb-xl reveal">Explore the key subsystems that make DRIP possible</p>
          
          <div className="carousel-container">
            <div className="carousel" id="subsystems-carousel">
              <div className="carousel__track">
                {/* Acoustic Array */}
                <div className="carousel__slide" data-subsystem="acoustic">
                  <div className="subsystem-card">
                    <div className="subsystem-card__model">
                      <div className="model-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                          <circle cx="12" cy="12" r="3"/>
                          <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"/>
                          <path d="M20.5 7.5L16 12l4.5 4.5M3.5 7.5L8 12l-4.5 4.5"/>
                        </svg>
                        <p>3D Model Coming Soon</p>
                      </div>
                    </div>
                    <div className="subsystem-card__content">
                      <h3>Acoustic Phased Array</h3>
                      <div className="subsystem-info">
                        <div className="info-section">
                          <h4>What It Is</h4>
                          <p>A high-density array of ultrasonic transducers that generates precisely controlled acoustic fields for droplet manipulation.</p>
                        </div>
                        <div className="info-section">
                          <h4>Why It Exists</h4>
                          <p>Enables contact-free manipulation of molten metal droplets, eliminating contamination and enabling processing of reactive materials.</p>
                        </div>
                        <div className="info-section">
                          <h4>How It Interfaces</h4>
                          <p>Connects to the Power & Control system via high-speed DACs and receives real-time commands from the control software.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Thermal System */}
                <div className="carousel__slide" data-subsystem="thermal">
                  <div className="subsystem-card">
                    <div className="subsystem-card__model">
                      <div className="model-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                          <path d="M14 2v10.5a1.5 1.5 0 0 0 3 0V2M14 22h2a1 1 0 0 0 1-1v-3.5a1.5 1.5 0 0 0-3 0V21a1 1 0 0 0 1 1z"/>
                          <path d="M10 2v7.5a1.5 1.5 0 0 1-3 0V2M7 22h1a1 1 0 0 0 1-1v-6.5a1.5 1.5 0 0 0-3 0V21a1 1 0 0 0 1 1z"/>
                        </svg>
                        <p>3D Model Coming Soon</p>
                      </div>
                    </div>
                    <div className="subsystem-card__content">
                      <h3>Thermal Management</h3>
                      <div className="subsystem-info">
                        <div className="info-section">
                          <h4>What It Is</h4>
                          <p>Induction heating crucible with precision temperature control and heated copper build platform.</p>
                        </div>
                        <div className="info-section">
                          <h4>Why It Exists</h4>
                          <p>Maintains metals in liquid state (700-1200°C) while protecting acoustic components from extreme temperatures.</p>
                        </div>
                        <div className="info-section">
                          <h4>How It Interfaces</h4>
                          <p>Thermocouples feed data to control system; power electronics regulate induction heater and bed heaters.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Power & Control */}
                <div className="carousel__slide" data-subsystem="power">
                  <div className="subsystem-card">
                    <div className="subsystem-card__model">
                      <div className="model-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                          <line x1="8" y1="21" x2="16" y2="21"/>
                          <line x1="12" y1="17" x2="12" y2="21"/>
                        </svg>
                        <p>3D Model Coming Soon</p>
                      </div>
                    </div>
                    <div className="subsystem-card__content">
                      <h3>Power & Control Electronics</h3>
                      <div className="subsystem-info">
                        <div className="info-section">
                          <h4>What It Is</h4>
                          <p>High-power amplifiers, signal generators, and real-time control hardware for system orchestration.</p>
                        </div>
                        <div className="info-section">
                          <h4>Why It Exists</h4>
                          <p>Provides the computational power and signal generation needed for real-time acoustic field control.</p>
                        </div>
                        <div className="info-section">
                          <h4>How It Interfaces</h4>
                          <p>NI DAQ for sensor input, Arduino for actuator control, custom PCBs for transducer driving.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Environment Control */}
                <div className="carousel__slide" data-subsystem="environment">
                  <div className="subsystem-card">
                    <div className="subsystem-card__model">
                      <div className="model-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                        </svg>
                        <p>3D Model Coming Soon</p>
                      </div>
                    </div>
                    <div className="subsystem-card__content">
                      <h3>Environment Control</h3>
                      <div className="subsystem-info">
                        <div className="info-section">
                          <h4>What It Is</h4>
                          <p>Inert gas management system with pressure and flow control for oxidation prevention.</p>
                        </div>
                        <div className="info-section">
                          <h4>Why It Exists</h4>
                          <p>Prevents oxidation of molten metals and ensures consistent processing conditions.</p>
                        </div>
                        <div className="info-section">
                          <h4>How It Interfaces</h4>
                          <p>Mass flow controllers regulated by control system, pressure sensors for feedback.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* User Interface */}
                <div className="carousel__slide" data-subsystem="ui">
                  <div className="subsystem-card">
                    <div className="subsystem-card__model">
                      <div className="model-placeholder">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                          <line x1="9" y1="9" x2="15" y2="9"/>
                          <line x1="9" y1="15" x2="15" y2="15"/>
                        </svg>
                        <p>3D Model Coming Soon</p>
                      </div>
                    </div>
                    <div className="subsystem-card__content">
                      <h3>User Interface</h3>
                      <div className="subsystem-info">
                        <div className="info-section">
                          <h4>What It Is</h4>
                          <p>Software interface for system control, monitoring, and real-time visualization of the printing process.</p>
                        </div>
                        <div className="info-section">
                          <h4>Why It Exists</h4>
                          <p>Provides operators with intuitive control and real-time feedback for process optimization.</p>
                        </div>
                        <div className="info-section">
                          <h4>How It Interfaces</h4>
                          <p>Communicates with control system via high-speed serial, displays sensor data and system status.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Carousel Controls */}
            <button className="carousel__btn carousel__btn--prev" aria-label="Previous subsystem">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
            </button>
            <button className="carousel__btn carousel__btn--next" aria-label="Next subsystem">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
            
            {/* Carousel Dots */}
            <div className="carousel__dots">
              <button className="carousel__dot carousel__dot--active" data-slide="0" aria-label="Go to slide 1"></button>
              <button className="carousel__dot" data-slide="1" aria-label="Go to slide 2"></button>
              <button className="carousel__dot" data-slide="2" aria-label="Go to slide 3"></button>
              <button className="carousel__dot" data-slide="3" aria-label="Go to slide 4"></button>
              <button className="carousel__dot" data-slide="4" aria-label="Go to slide 5"></button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section bg-gradient text-center">
        <div className="container container--content">
          <h2 className="mb-lg reveal">Ready to revolutionize manufacturing?</h2>
          <p className="text-lg mb-xl reveal">Join us in developing the future of metal 3D printing.</p>
          <div className="flex flex--center flex--wrap reveal">
            <a href="/progress" className="btn btn--secondary btn--large mr-md">View Progress</a>
            <a href="/team" className="btn btn--primary btn--large">Meet the Team</a>
          </div>
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
            <p>&copy; 2025 DRIP Acoustic Manufacturing. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </>
  );
};

export default HomePage;